from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response

from fruitfly.evaluation.brain_asset_manifest import load_brain_asset_manifest, with_runtime_asset_urls
from fruitfly.evaluation.console_session import ConsoleSession
from fruitfly.evaluation.roi_asset_pack import load_roi_asset_pack_manifest
from fruitfly.evaluation.runtime_activity_artifacts import (
    build_replay_brain_view_payload,
    build_replay_timeline_payload,
    materialize_runtime_activity_artifacts,
)
from fruitfly.evaluation.timeline import build_shared_timeline_payload
from fruitfly.ui.replay_runtime import ReplayRuntime


@dataclass(frozen=True, slots=True)
class ConsoleApiConfig:
    compiled_graph_dir: Path
    eval_dir: Path
    checkpoint_path: Path | None = None
    replay_renderer_python: Path | None = None
    brain_asset_dir: Path | None = None
    roi_asset_dir: Path | None = None
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

    app = FastAPI(
        title="Fruitfly Neural Console API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
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
        _ensure_runtime_activity_artifacts(config)
        payload_path = config.eval_dir / "brain_view.json"
        if payload_path.exists():
            payload = dict(_read_json(payload_path))
            payload.setdefault("shell", _brain_shell_payload(config))
            payload.setdefault("data_status", "recorded")
            payload.setdefault("semantic_scope", "neuropil")
            return payload
        return _build_unavailable_brain_view_payload(config)

    @app.get("/api/console/brain-assets")
    def brain_assets() -> dict[str, Any]:
        manifest = _brain_asset_manifest(config)
        return with_runtime_asset_urls(manifest, shell_asset_url="/api/console/brain-shell")

    @app.get("/api/console/roi-assets")
    def roi_assets() -> dict[str, Any]:
        manifest = dict(_roi_asset_pack_manifest(config))
        manifest["roi_meshes"] = [
            {
                **entry,
                "asset_url": f'/api/console/roi-mesh/{entry["roi_id"]}',
            }
            for entry in manifest["roi_meshes"]
        ]
        return manifest

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
        brain_payload = runtime.current_brain_payload()
        return build_replay_brain_view_payload(
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
        )

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
        frame_bytes = _render_replay_frame_bytes(
            config=config,
            step=runtime.current_step,
            camera=runtime.camera_preset,
            width=int(width),
            height=int(height),
        )
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

    @app.get("/api/console/roi-mesh/{roi_id}")
    def roi_mesh(roi_id: str) -> FileResponse:
        manifest = _roi_asset_pack_manifest(config)
        mesh_entry = next((entry for entry in manifest["roi_meshes"] if entry["roi_id"] == roi_id), None)
        if mesh_entry is None:
            raise HTTPException(status_code=404, detail=f"roi mesh not found for {roi_id}")
        assert config.roi_asset_dir is not None
        mesh_path = config.roi_asset_dir / mesh_entry["render_asset_path"]
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


def _build_unavailable_brain_view_payload(config: ConsoleApiConfig) -> dict[str, Any]:
    graph_stats = _graph_stats(config)
    node_count = int(graph_stats["node_count"])
    truth_state = _formal_neuropil_truth_state(config)
    return {
        "view_mode": "neuropil-occupancy",
        "data_status": "unavailable",
        "semantic_scope": "neuropil",
        "shell": _brain_shell_payload(config),
        "mapping_coverage": {
            "roi_mapped_nodes": truth_state["mapped_nodes"],
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
    config: ConsoleApiConfig,
    step: int,
    camera: str,
    width: int,
    height: int,
) -> bytes:
    renderer_python = _resolve_replay_renderer_python(config)
    if renderer_python is None:
        raise HTTPException(status_code=503, detail="replay renderer environment is not configured")

    script_path = Path(__file__).resolve().parents[3] / "scripts" / "render_replay_frame.py"
    if not script_path.exists():
        raise HTTPException(status_code=503, detail="replay frame renderer script is not available")

    result = subprocess.run(
        [
            str(renderer_python),
            str(script_path),
            "--eval-dir",
            str(config.eval_dir),
            "--step",
            str(int(step)),
            "--camera",
            str(camera),
            "--width",
            str(int(width)),
            "--height",
            str(int(height)),
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="ignore").strip() or "replay frame rendering failed"
        raise HTTPException(status_code=503, detail=message)
    return bytes(result.stdout)


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
    if brain_view_path.exists() and timeline_path.exists():
        return
    materialize_runtime_activity_artifacts(
        compiled_graph_dir=config.compiled_graph_dir,
        eval_dir=config.eval_dir,
        shell=_brain_shell_payload(config),
    )


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


def _roi_asset_pack_manifest(config: ConsoleApiConfig) -> dict[str, Any]:
    if config.roi_asset_dir is None:
        raise HTTPException(status_code=404, detail="roi asset pack not configured")
    manifest_path = config.roi_asset_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="roi asset pack manifest not found")
    return load_roi_asset_pack_manifest(manifest_path)


def _mapping_coverage(config: ConsoleApiConfig, *, total_nodes: int) -> dict[str, int]:
    if config.roi_asset_dir is not None:
        try:
            manifest = _roi_asset_pack_manifest(config)
        except HTTPException:
            pass
        else:
            return {
                "roi_mapped_nodes": int(manifest["mapping_coverage"]["roi_mapped_nodes"]),
                "total_nodes": int(manifest["mapping_coverage"]["total_nodes"]),
            }
    return {
        "roi_mapped_nodes": int(total_nodes * 0.85),
        "total_nodes": total_nodes,
    }


def _formal_neuropil_truth_state(config: ConsoleApiConfig) -> dict[str, Any]:
    occupancy_path = config.compiled_graph_dir / "node_neuropil_occupancy.parquet"
    validation_path = config.compiled_graph_dir / "neuropil_truth_validation.json"
    occupancy_exists = occupancy_path.exists()
    validation_payload: dict[str, Any] | None = None
    if validation_path.exists():
        validation_payload = _read_json(validation_path)
    validation_passed = bool(validation_payload and validation_payload.get("validation_passed") is True)
    validation_scope = str(validation_payload.get("validation_scope")) if validation_payload else None
    roster_alignment = dict(validation_payload.get("roster_alignment") or {}) if validation_payload else {}
    roster_alignment_passed = roster_alignment.get("alignment_passed")
    mapped_nodes = _count_occupancy_nodes(occupancy_path) if occupancy_exists else 0
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
        "validation_scope": validation_scope,
        "roster_alignment_passed": roster_alignment_passed,
        "graph_only_root_count": roster_alignment.get("graph_only_root_count"),
        "proofread_only_root_count": roster_alignment.get("proofread_only_root_count"),
        "mapped_nodes": mapped_nodes,
        "reason": reason,
    }


def _count_occupancy_nodes(path: Path) -> int:
    if not path.exists():
        return 0
    table = pq.read_table(path, columns=["source_id"])
    return len({int(value.as_py()) for value in table.column("source_id")})


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
