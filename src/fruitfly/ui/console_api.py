from __future__ import annotations

import json
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response

from fruitfly.evaluation.brain_asset_manifest import load_brain_asset_manifest, with_runtime_asset_urls
from fruitfly.evaluation.console_session import ConsoleSession
from fruitfly.evaluation.runtime_activity_artifacts import (
    DISPLAY_NEUROPIL_MANIFEST,
    RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    build_replay_brain_view_payload,
    build_replay_timeline_payload,
    materialize_runtime_activity_artifacts,
)
from fruitfly.evaluation.timeline import build_shared_timeline_payload
from fruitfly.ui.replay_frame_worker import ReplayFrameWorkerClient
from fruitfly.ui.replay_runtime import ReplayRuntime


@dataclass(frozen=True, slots=True)
class ConsoleApiConfig:
    compiled_graph_dir: Path
    eval_dir: Path
    checkpoint_path: Path | None = None
    replay_renderer_python: Path | None = None
    brain_asset_dir: Path | None = None
    mode: str = "Experiment"
    task: str = "straight_walking"
    environment_physics: dict[str, str] = field(
        default_factory=lambda: {
            "Terrain": "flat",
            "Friction": "1.00",
            "Wind": "0.00",
            "Rain": "0.00",
        }
    )
    sensory_inputs: dict[str, str] = field(
        default_factory=lambda: {
            "Temperature": "0.00",
            "Odor": "0.00",
        }
    )


def create_console_api(config: ConsoleApiConfig) -> FastAPI:
    replay_runtime: ReplayRuntime | None = None
    replay_frame_client: Any | None = None

    def get_or_create_replay_runtime() -> ReplayRuntime:
        nonlocal replay_runtime
        if replay_runtime is None:
            try:
                replay_runtime = ReplayRuntime.from_eval_dir(config.eval_dir)
            except FileNotFoundError as exc:
                raise HTTPException(
                    status_code=404,
                    detail="Replay inspector artifacts are unavailable",
                ) from exc
        return replay_runtime

    def get_or_create_replay_frame_client() -> Any:
        nonlocal replay_frame_client
        if replay_frame_client is None:
            replay_frame_client = _create_replay_frame_client(config=config)
        return replay_frame_client

    def close_replay_frame_client() -> None:
        nonlocal replay_frame_client
        if replay_frame_client is None:
            return
        with suppress(Exception):
            replay_frame_client.close()
        replay_frame_client = None

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            close_replay_frame_client()

    app = FastAPI(
        title="Fruitfly Neural Console API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/console/session")
    def session() -> dict[str, Any]:
        return _build_session_payload(config)

    @app.get("/api/console/pipeline")
    def pipeline() -> dict[str, Any]:
        return {
            "stages": [
                {"name": "Environment / Input", "status": "done"},
                {"name": "Afferent", "status": "done"},
                {"name": "Whole-Brain", "status": "done"},
                {"name": "Efferent", "status": "done"},
                {"name": "Decoder", "status": "done"},
                {"name": "Body", "status": "done"},
            ]
        }

    @app.get("/api/console/summary")
    def summary() -> dict[str, Any]:
        if _summary_path(config).exists():
            payload = dict(_read_json(_summary_path(config)))
            payload["data_status"] = "recorded"
            payload["video_url"] = "/api/console/video" if _video_path(config).exists() else None
            return payload
        return _build_unavailable_summary_payload(config)

    @app.get("/api/console/brain-view")
    def brain_view() -> dict[str, Any]:
        truth_state = _formal_neuropil_truth_state(config)
        if not truth_state["graph_scope_validation_passed"]:
            return _build_unavailable_brain_view_payload(
                config,
                truth_state=truth_state,
                artifact_origin="initial-materialized",
            )
        _ensure_runtime_activity_artifacts(config)
        payload_path = config.eval_dir / "brain_view.json"
        if payload_path.exists():
            payload = dict(_read_json(payload_path))
            payload.setdefault("artifact_contract_version", RUNTIME_ACTIVITY_ARTIFACT_VERSION)
            payload.setdefault("artifact_origin", "initial-materialized")
            payload.setdefault("shell", _brain_shell_payload(config))
            payload.setdefault("data_status", "recorded")
            payload.setdefault("semantic_scope", "neuropil")
            payload.setdefault("view_mode", "grouped-neuropil-v1")
            payload.setdefault("mapping_mode", "node_neuropil_occupancy")
            payload.setdefault("activity_metric", "activity_mass")
            return _attach_brain_view_provenance(payload, truth_state=truth_state)
        return _build_unavailable_brain_view_payload(
            config,
            truth_state=truth_state,
            artifact_origin="initial-materialized",
        )

    @app.get("/api/console/brain-assets")
    def brain_assets() -> dict[str, Any]:
        manifest = _brain_asset_manifest(config)
        return with_runtime_asset_urls(manifest, shell_asset_url="/api/console/brain-shell")

    @app.get("/api/console/timeline")
    def timeline() -> dict[str, Any]:
        _ensure_runtime_activity_artifacts(config)
        payload_path = config.eval_dir / "timeline.json"
        if payload_path.exists():
            payload = dict(_read_json(payload_path))
            payload.setdefault("data_status", "recorded")
            return payload
        return _build_unavailable_timeline_payload(config)

    @app.get("/api/console/artifacts")
    def artifacts() -> dict[str, Any]:
        return {
            "compiled_graph_dir": str(config.compiled_graph_dir),
            "eval_dir": str(config.eval_dir),
            "checkpoint": str(config.checkpoint_path),
            "summary_url": "/api/console/summary",
            "brain_view_url": "/api/console/brain-view",
            "timeline_url": "/api/console/timeline",
            "video_url": "/api/console/video" if _video_path(config).exists() else None,
        }

    @app.get("/api/console/replay/session")
    def replay_session() -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        return {
            **runtime.trace.session,
            "current_step": runtime.current_step,
            "status": runtime.status,
            "speed": runtime.speed,
            "camera": runtime.camera_preset,
        }

    @app.post("/api/console/replay/seek")
    def replay_seek(payload: dict[str, Any]) -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        runtime.seek(int(payload["step"]))
        return {"current_step": runtime.current_step}

    @app.post("/api/console/replay/control")
    def replay_control(payload: dict[str, Any]) -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        action = str(payload["action"])
        if action == "play":
            runtime.play()
        elif action == "pause":
            runtime.pause()
        elif action == "next":
            runtime.next_step()
        elif action == "prev":
            runtime.prev_step()
        else:
            raise HTTPException(status_code=400, detail=f"unsupported replay control: {action}")
        return {"status": runtime.status, "current_step": runtime.current_step}

    @app.post("/api/console/replay/camera")
    def replay_camera(payload: dict[str, Any]) -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        runtime.set_camera(str(payload["camera"]))
        return {"camera": runtime.camera_preset, "current_step": runtime.current_step}

    @app.get("/api/console/replay/summary")
    def replay_summary() -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        return runtime.current_summary()

    @app.get("/api/console/replay/brain-view")
    def replay_brain_view() -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        truth_state = _formal_neuropil_truth_state(config)
        if not truth_state["graph_scope_validation_passed"]:
            payload = _build_unavailable_brain_view_payload(
                config,
                truth_state=truth_state,
                artifact_origin="replay-live-step",
            )
            payload["step_id"] = runtime.current_step
            return payload
        brain_payload = runtime.current_brain_payload()
        payload = build_replay_brain_view_payload(
            compiled_graph_dir=config.compiled_graph_dir,
            step_id=int(brain_payload["step_id"]),
            node_activity=brain_payload["node_activity"],
            afferent_activity=float(brain_payload["afferent_activity"])
            if brain_payload.get("afferent_activity") is not None
            else None,
            intrinsic_activity=float(brain_payload["intrinsic_activity"])
            if brain_payload.get("intrinsic_activity") is not None
            else None,
            efferent_activity=float(brain_payload["efferent_activity"])
            if brain_payload.get("efferent_activity") is not None
            else None,
            shell=_brain_shell_payload(config),
            top_active_nodes=list(brain_payload.get("top_active_nodes") or []),
            formal_truth=truth_state,
        )
        return _attach_brain_view_provenance(payload, truth_state=truth_state)

    @app.get("/api/console/replay/timeline")
    def replay_timeline() -> dict[str, Any]:
        runtime = get_or_create_replay_runtime()
        return build_replay_timeline_payload(
            summary_payload=runtime.summary_payload,
            current_step=runtime.current_step,
            events=list(runtime.trace.events),
        )

    @app.get("/api/console/replay/frame")
    def replay_frame(width: int = 320, height: int = 240) -> Response:
        runtime = get_or_create_replay_runtime()
        try:
            frame_bytes = _render_replay_frame_bytes(
                step=runtime.current_step,
                camera=runtime.camera_preset,
                width=int(width),
                height=int(height),
                client=get_or_create_replay_frame_client(),
            )
        except Exception as exc:
            close_replay_frame_client()
            message = str(exc).strip() or "replay frame rendering failed"
            raise HTTPException(status_code=503, detail=message) from exc
        return Response(content=frame_bytes, media_type="image/jpeg")

    @app.get("/api/console/video")
    def video() -> FileResponse:
        video_path = _video_path(config)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="rollout.mp4 not found")
        return FileResponse(video_path, media_type="video/mp4", filename=video_path.name)

    @app.get("/api/console/brain-shell")
    def brain_shell() -> FileResponse:
        manifest = _brain_asset_manifest(config)
        shell_path = _brain_shell_path(config, manifest)
        if not shell_path.exists():
            raise HTTPException(status_code=404, detail=f"{shell_path.name} not found")
        return FileResponse(shell_path, media_type="model/gltf-binary", filename=shell_path.name)

    @app.get("/api/console/brain-mesh/{neuropil}")
    def brain_mesh(neuropil: str) -> FileResponse:
        manifest = _brain_asset_manifest(config)
        entry = _find_grouped_neuropil_asset(manifest, neuropil)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"{neuropil} mesh not found")
        assert config.brain_asset_dir is not None
        mesh_path = config.brain_asset_dir / str(entry["render_asset_path"])
        if not mesh_path.exists():
            raise HTTPException(status_code=404, detail=f"{mesh_path.name} not found")
        return FileResponse(mesh_path, media_type="model/gltf-binary", filename=mesh_path.name)

    return app


def _build_session_payload(config: ConsoleApiConfig) -> dict[str, Any]:
    checkpoint_value = str(config.checkpoint_path) if config.checkpoint_path is not None else "unavailable"
    session = ConsoleSession.create(
        mode=config.mode,
        checkpoint=checkpoint_value,
        task=config.task,
        environment_physics=config.environment_physics,
        sensory_inputs=config.sensory_inputs,
    )
    return {
        "mode": session.mode,
        "checkpoint": session.checkpoint,
        "task": session.task,
        "applied_state": session.applied_state,
        "pending_state": session.pending_state,
        "pending_changes": int(bool(session.pending_changes)),
        "intervention_log": [
            "type: physical + sensory",
            "no direct action override",
            "no joint override",
            "actions are model-generated",
        ],
        "action_provenance": session.action_provenance,
    }


def _build_unavailable_brain_view_payload(
    config: ConsoleApiConfig,
    *,
    truth_state: dict[str, Any] | None = None,
    artifact_origin: str = "initial-materialized",
) -> dict[str, Any]:
    graph_stats = _graph_stats(config)
    node_count = int(graph_stats["node_count"])
    if truth_state is None:
        truth_state = _formal_neuropil_truth_state(config)
    payload = {
        "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
        "artifact_origin": artifact_origin,
        "semantic_scope": "neuropil",
        "view_mode": "grouped-neuropil-v1",
        "mapping_mode": "node_neuropil_occupancy",
        "activity_metric": "activity_mass",
        "data_status": "unavailable",
        "shell": _brain_shell_payload(config),
        "mapping_coverage": {
            "neuropil_mapped_nodes": truth_state["mapped_nodes"],
            "total_nodes": node_count,
        },
        "region_activity": [],
        "top_regions": [],
        "top_nodes": [],
        "afferent_activity": None,
        "intrinsic_activity": None,
        "efferent_activity": None,
        "formal_truth": truth_state,
    }
    return _attach_brain_view_provenance(payload, truth_state=truth_state)


def _build_unavailable_timeline_payload(config: ConsoleApiConfig) -> dict[str, Any]:
    summary = _summary_payload(config)
    steps_requested = int(summary["steps_requested"])
    steps_completed = int(summary["steps_completed"])
    payload = build_shared_timeline_payload(
        steps_requested=steps_requested,
        steps_completed=steps_completed,
        current_step=steps_completed,
        events=[],
    )
    payload["data_status"] = "unavailable"
    return payload


def _build_unavailable_summary_payload(config: ConsoleApiConfig) -> dict[str, Any]:
    return {
        "data_status": "unavailable",
        "status": "unavailable",
        "task": config.task,
        "steps_requested": 0,
        "steps_completed": 0,
        "terminated_early": False,
        "reward_mean": 0.0,
        "final_reward": 0.0,
        "mean_action_norm": 0.0,
        "forward_velocity_mean": 0.0,
        "forward_velocity_std": 0.0,
        "body_upright_mean": 0.0,
        "final_heading_delta": 0.0,
        "video_url": None,
    }


def _render_replay_frame_bytes(
    *,
    step: int,
    camera: str,
    width: int,
    height: int,
    client: Any,
) -> bytes:
    payload = client.render_frame(
        step=int(step),
        camera=str(camera),
        width=int(width),
        height=int(height),
    )
    if isinstance(payload, bytes):
        return payload
    return bytes(getattr(payload, "bytes"))


def _create_replay_frame_client(*, config: ConsoleApiConfig) -> ReplayFrameWorkerClient:
    renderer_python = _resolve_replay_renderer_python(config)
    if renderer_python is None:
        raise RuntimeError("replay renderer environment is not configured")

    worker_script = Path(__file__).resolve().parents[3] / "scripts" / "replay_frame_worker.py"
    if not worker_script.exists():
        raise RuntimeError("replay frame renderer worker script is not available")

    return ReplayFrameWorkerClient.start(
        python_executable=renderer_python,
        worker_script=worker_script,
        eval_dir=config.eval_dir,
    )


def _resolve_replay_renderer_python(config: ConsoleApiConfig) -> Path | None:
    if config.replay_renderer_python is not None:
        return config.replay_renderer_python
    candidate = Path(__file__).resolve().parents[3] / ".venv-flybody" / "bin" / "python"
    if candidate.exists():
        return candidate
    return None


def _graph_stats(config: ConsoleApiConfig) -> dict[str, Any]:
    return _read_json(config.compiled_graph_dir / "graph_stats.json")


def _ensure_runtime_activity_artifacts(config: ConsoleApiConfig) -> None:
    brain_view_path = config.eval_dir / "brain_view.json"
    timeline_path = config.eval_dir / "timeline.json"
    if _runtime_activity_artifacts_are_current(
        config=config,
        brain_view_path=brain_view_path,
        timeline_path=timeline_path,
    ):
        return
    truth_state = _formal_neuropil_truth_state(config)
    if not truth_state["graph_scope_validation_passed"]:
        return
    materialize_runtime_activity_artifacts(
        compiled_graph_dir=config.compiled_graph_dir,
        eval_dir=config.eval_dir,
        shell=_brain_shell_payload(config),
    )


def _runtime_activity_artifacts_are_current(
    *,
    config: ConsoleApiConfig,
    brain_view_path: Path,
    timeline_path: Path,
) -> bool:
    if not brain_view_path.exists() or not timeline_path.exists():
        return False
    brain_view_payload = _try_read_json_payload(brain_view_path)
    timeline_payload = _try_read_json_payload(timeline_path)
    if brain_view_payload is None or timeline_payload is None:
        return False
    latest_dependency_mtime = _latest_runtime_activity_dependency_mtime(config)
    if latest_dependency_mtime is None:
        return False
    try:
        brain_view_mtime = brain_view_path.stat().st_mtime
        timeline_mtime = timeline_path.stat().st_mtime
    except OSError:
        return False
    if brain_view_mtime < latest_dependency_mtime or timeline_mtime < latest_dependency_mtime:
        return False
    return _brain_view_artifact_is_current(brain_view_payload) and _timeline_artifact_is_current(
        timeline_payload
    )


def _brain_view_artifact_is_current(payload: dict[str, Any]) -> bool:
    if not _artifact_contract_version_matches(payload):
        return False
    if payload.get("semantic_scope") != "neuropil":
        return False
    if payload.get("view_mode") != "grouped-neuropil-v1":
        return False
    if payload.get("mapping_mode") != "node_neuropil_occupancy":
        return False
    if payload.get("activity_metric") != "activity_mass":
        return False
    if payload.get("artifact_origin") != "initial-materialized":
        return False
    mapping_coverage = payload.get("mapping_coverage")
    if not isinstance(mapping_coverage, dict) or "neuropil_mapped_nodes" not in mapping_coverage:
        return False
    formal_truth = payload.get("formal_truth")
    if not isinstance(formal_truth, dict):
        return False
    region_activity = payload.get("region_activity")
    if not isinstance(region_activity, list):
        return False
    display_region_activity = payload.get("display_region_activity")
    if not isinstance(display_region_activity, list):
        return False
    if not all(_display_region_activity_entry_is_current(entry) for entry in display_region_activity):
        return False
    top_regions = payload.get("top_regions")
    if not isinstance(top_regions, list):
        return False
    top_nodes = payload.get("top_nodes")
    if not isinstance(top_nodes, list):
        return False
    return all(
        isinstance(node, dict) and isinstance(node.get("neuropil_memberships"), list)
        for node in top_nodes
    )


def _display_region_activity_entry_is_current(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    group_neuropil_id = entry.get("group_neuropil_id")
    if not isinstance(group_neuropil_id, str):
        return False
    approved_group_ids = {group_id for group_id, _label in DISPLAY_NEUROPIL_MANIFEST}
    if group_neuropil_id not in approved_group_ids:
        return False
    if not _is_json_number(entry.get("raw_activity_mass")):
        return False
    if not _is_json_number(entry.get("signed_activity")):
        return False
    if not _is_json_number(entry.get("covered_weight_sum")):
        return False
    node_count = entry.get("node_count")
    if not isinstance(node_count, int) or isinstance(node_count, bool) or node_count < 0:
        return False
    if entry.get("view_mode") != "grouped-neuropil-v1":
        return False
    if entry.get("is_display_transform") is not True:
        return False
    member_neuropils = entry.get("member_neuropils")
    return isinstance(member_neuropils, list) and all(
        isinstance(neuropil, str) for neuropil in member_neuropils
    )


def _is_json_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _timeline_artifact_is_current(payload: dict[str, Any]) -> bool:
    if not _artifact_contract_version_matches(payload):
        return False
    if payload.get("data_status") != "recorded":
        return False
    if not isinstance(payload.get("steps_requested"), int):
        return False
    if not isinstance(payload.get("steps_completed"), int):
        return False
    if not isinstance(payload.get("current_step"), int):
        return False
    if payload.get("brain_view_ref") != "step_id":
        return False
    if payload.get("body_view_ref") != "step_id":
        return False
    return isinstance(payload.get("events"), list)


def _try_read_json_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _artifact_contract_version_matches(payload: dict[str, Any]) -> bool:
    try:
        version = int(payload.get("artifact_contract_version", 0))
    except (TypeError, ValueError):
        return False
    return version == RUNTIME_ACTIVITY_ARTIFACT_VERSION


def _latest_runtime_activity_dependency_mtime(config: ConsoleApiConfig) -> float | None:
    dependency_paths = [
        config.eval_dir / "activity_trace.json",
        config.eval_dir / "final_node_activity.npy",
        config.eval_dir / "summary.json",
        config.compiled_graph_dir / "node_neuropil_occupancy.parquet",
        config.compiled_graph_dir / "neuropil_truth_validation.json",
        config.compiled_graph_dir / "node_index.parquet",
    ]
    if any(not path.exists() for path in dependency_paths):
        return None
    try:
        return max(path.stat().st_mtime for path in dependency_paths)
    except OSError:
        return None


def _brain_asset_manifest(config: ConsoleApiConfig) -> dict[str, Any]:
    if config.brain_asset_dir is None:
        raise HTTPException(status_code=404, detail="brain asset manifest not configured")
    manifest_path = config.brain_asset_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="brain asset manifest not found")
    return load_brain_asset_manifest(manifest_path)


def _brain_shell_payload(config: ConsoleApiConfig) -> dict[str, Any] | None:
    if config.brain_asset_dir is None:
        return None
    manifest_path = config.brain_asset_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = load_brain_asset_manifest(manifest_path)
    shell = manifest["shell"]
    return {
        "asset_id": manifest["asset_id"],
        "asset_url": "/api/console/brain-shell",
        "base_color": shell["base_color"],
        "opacity": shell["opacity"],
    }


def _brain_shell_path(config: ConsoleApiConfig, manifest: dict[str, Any]) -> Path:
    assert config.brain_asset_dir is not None
    return config.brain_asset_dir / manifest["shell"]["render_asset_path"]


def _find_grouped_neuropil_asset(
    manifest: dict[str, Any],
    neuropil: str,
) -> dict[str, Any] | None:
    entries = manifest.get("neuropil_manifest")
    if not isinstance(entries, list):
        return None
    return next(
        (entry for entry in entries if str(entry.get("neuropil")) == str(neuropil)),
        None,
    )


def _formal_neuropil_truth_state(config: ConsoleApiConfig) -> dict[str, Any]:
    occupancy_path = config.compiled_graph_dir / "node_neuropil_occupancy.parquet"
    validation_path = config.compiled_graph_dir / "neuropil_truth_validation.json"
    occupancy_exists = occupancy_path.exists()
    validation_payload: dict[str, Any] | None = None
    if validation_path.exists():
        validation_payload = _read_json(validation_path)
    validation_passed = bool(validation_payload and validation_payload.get("validation_passed") is True)
    graph_scope_validation_passed = validation_passed
    validation_scope = str(validation_payload.get("validation_scope")) if validation_payload else None
    roster_alignment = dict(validation_payload.get("roster_alignment") or {}) if validation_payload else {}
    roster_alignment_passed = bool(roster_alignment.get("alignment_passed"))
    occupancy_summary = _read_occupancy_truth_summary(occupancy_path) if occupancy_exists else {
        "mapped_nodes": 0,
        "materialization": None,
        "dataset": None,
    }
    mapped_nodes = int(occupancy_summary["mapped_nodes"])
    if occupancy_exists and validation_passed:
        if roster_alignment_passed is False:
            reason = "graph-scoped formal neuropil truth present; proofread roster alignment differs"
        else:
            reason = "formal neuropil truth present, but runtime activity recording is not available"
    elif occupancy_exists:
        if validation_scope == "graph_source_ids":
            reason = "formal neuropil occupancy exists, but graph-scoped official validation has not passed"
        else:
            reason = "formal neuropil occupancy exists, but official validation has not passed"
    else:
        reason = "formal neuropil occupancy artifact not found"
    return {
        "occupancy_exists": occupancy_exists,
        "validation_path": str(validation_path),
        "validation_passed": validation_passed,
        "graph_scope_validation_passed": graph_scope_validation_passed,
        "validation_scope": validation_scope,
        "roster_alignment_passed": roster_alignment_passed,
        "graph_only_root_count": roster_alignment.get("graph_only_root_count"),
        "proofread_only_root_count": roster_alignment.get("proofread_only_root_count"),
        "mapped_nodes": mapped_nodes,
        "materialization": occupancy_summary["materialization"],
        "dataset": occupancy_summary["dataset"],
        "reason": reason,
    }


def _read_occupancy_truth_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "mapped_nodes": 0,
            "materialization": None,
            "dataset": None,
        }
    parquet_file = pq.ParquetFile(path)
    available_columns = set(parquet_file.schema_arrow.names)
    columns = [
        column
        for column in ("source_id", "materialization", "dataset")
        if column in available_columns
    ]
    source_ids: set[int] = set()
    materializations: set[int] = set()
    datasets: set[str] = set()
    for batch in parquet_file.iter_batches(columns=columns):
        batch_payload = batch.to_pydict()
        for value in batch_payload.get("source_id", []):
            if value is not None:
                source_ids.add(int(value))
        for value in batch_payload.get("materialization", []):
            if value is not None:
                materializations.add(int(value))
        for value in batch_payload.get("dataset", []):
            if value is not None:
                datasets.add(str(value))
    return {
        "mapped_nodes": len(source_ids),
        "materialization": next(iter(materializations)) if len(materializations) == 1 else None,
        "dataset": next(iter(datasets)) if len(datasets) == 1 else None,
    }


def _attach_brain_view_provenance(
    payload: dict[str, Any],
    *,
    truth_state: dict[str, Any],
) -> dict[str, Any]:
    formal_truth = dict(payload.get("formal_truth") or {})
    formal_truth.update(
        {
            "occupancy_exists": bool(truth_state.get("occupancy_exists")),
            "validation_path": truth_state.get("validation_path"),
            "validation_passed": bool(truth_state.get("validation_passed")),
            "graph_scope_validation_passed": bool(
                truth_state.get("graph_scope_validation_passed")
            ),
            "validation_scope": truth_state.get("validation_scope"),
            "roster_alignment_passed": bool(
                truth_state.get("roster_alignment_passed")
            ),
            "graph_only_root_count": truth_state.get("graph_only_root_count"),
            "proofread_only_root_count": truth_state.get("proofread_only_root_count"),
            "mapped_nodes": int(truth_state.get("mapped_nodes", 0)),
            "materialization": truth_state.get("materialization"),
            "dataset": truth_state.get("dataset"),
            "reason": truth_state.get("reason"),
        }
    )
    payload["formal_truth"] = formal_truth
    payload["validation_passed"] = bool(truth_state.get("validation_passed"))
    payload["graph_scope_validation_passed"] = bool(
        truth_state.get("graph_scope_validation_passed")
    )
    payload["roster_alignment_passed"] = bool(
        truth_state.get("roster_alignment_passed")
    )
    payload["validation_scope"] = truth_state.get("validation_scope")
    payload["materialization"] = truth_state.get("materialization")
    payload["dataset"] = truth_state.get("dataset")
    return payload


def _summary_payload(config: ConsoleApiConfig) -> dict[str, Any]:
    summary_path = _summary_path(config)
    if summary_path.exists():
        return _read_json(summary_path)
    return _build_unavailable_summary_payload(config)


def _summary_path(config: ConsoleApiConfig) -> Path:
    return config.eval_dir / "summary.json"


def _video_path(config: ConsoleApiConfig) -> Path:
    return config.eval_dir / "rollout.mp4"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    return json.loads(path.read_text(encoding="utf-8"))
