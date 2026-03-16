from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .timeline import build_shared_timeline_payload

DISPLAY_NEUROPIL_MANIFEST = (
    ("AL", "AL"),
    ("LH", "LH"),
    ("PB", "PB"),
    ("FB", "FB"),
    ("EB", "EB"),
    ("NO", "NO"),
    ("LAL", "LAL"),
    ("GNG", "GNG"),
)

NEUROPIL_TO_DISPLAY_GROUP = {
    "AL_L": "AL",
    "AL_R": "AL",
    "AL": "AL",
    "LH_L": "LH",
    "LH_R": "LH",
    "LH": "LH",
    "PB": "PB",
    "FB": "FB",
    "EB": "EB",
    "NO": "NO",
    "LAL_L": "LAL",
    "LAL_R": "LAL",
    "LAL": "LAL",
    "GNG": "GNG",
}


def materialize_runtime_activity_artifacts(
    *,
    compiled_graph_dir: Path,
    eval_dir: Path,
    shell: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    trace_path = eval_dir / "activity_trace.json"
    final_node_activity_path = eval_dir / "final_node_activity.npy"
    summary_path = eval_dir / "summary.json"
    occupancy_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    node_index_path = compiled_graph_dir / "node_index.parquet"

    if not (
        trace_path.exists()
        and final_node_activity_path.exists()
        and summary_path.exists()
        and occupancy_path.exists()
        and node_index_path.exists()
    ):
        return None

    trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    final_node_activity = np.load(final_node_activity_path)

    occupancy_rows = pq.read_table(
        occupancy_path,
        columns=["source_id", "node_idx", "neuropil", "occupancy_fraction"],
    ).to_pylist()
    node_index_rows = pq.read_table(
        node_index_path,
        columns=["source_id", "node_idx"],
    ).to_pylist()

    brain_view_payload = _build_brain_view_payload(
        trace_payload=trace_payload,
        final_node_activity=final_node_activity,
        occupancy_rows=occupancy_rows,
        node_index_rows=node_index_rows,
        total_nodes=int(final_node_activity.shape[0]),
        shell=shell,
    )
    timeline_payload = _build_timeline_payload(
        trace_payload=trace_payload,
        summary_payload=summary_payload,
    )

    (eval_dir / "brain_view.json").write_text(
        json.dumps(brain_view_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (eval_dir / "timeline.json").write_text(
        json.dumps(timeline_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return brain_view_payload, timeline_payload


def build_replay_brain_view_payload(
    *,
    compiled_graph_dir: Path,
    step_id: int,
    node_activity: np.ndarray,
    afferent_activity: float | None,
    intrinsic_activity: float | None,
    efferent_activity: float | None,
    shell: dict[str, Any] | None = None,
) -> dict[str, Any]:
    occupancy_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    node_index_path = compiled_graph_dir / "node_index.parquet"
    occupancy_rows = pq.read_table(
        occupancy_path,
        columns=["source_id", "node_idx", "neuropil", "occupancy_fraction"],
    ).to_pylist()
    node_index_rows = pq.read_table(
        node_index_path,
        columns=["source_id", "node_idx"],
    ).to_pylist()
    return _build_brain_view_payload_for_step(
        node_activity=np.asarray(node_activity, dtype=np.float32),
        occupancy_rows=occupancy_rows,
        node_index_rows=node_index_rows,
        total_nodes=int(np.asarray(node_activity).shape[0]),
        afferent_activity=afferent_activity,
        intrinsic_activity=intrinsic_activity,
        efferent_activity=efferent_activity,
        step_id=step_id,
        shell=shell,
    )


def build_replay_timeline_payload(
    *,
    summary_payload: dict[str, Any],
    current_step: int,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = build_shared_timeline_payload(
        steps_requested=int(summary_payload.get("steps_requested", 0)),
        steps_completed=int(summary_payload.get("steps_completed", 0)),
        current_step=int(current_step),
        events=events,
    )
    payload["data_status"] = "recorded"
    return payload


def _build_brain_view_payload(
    *,
    trace_payload: dict[str, Any],
    final_node_activity: np.ndarray,
    occupancy_rows: list[dict[str, Any]],
    node_index_rows: list[dict[str, Any]],
    total_nodes: int,
    shell: dict[str, Any] | None,
) -> dict[str, Any]:
    snapshots = list(trace_payload.get("snapshots") or [])
    final_snapshot = snapshots[-1] if snapshots else {}
    return _build_brain_view_payload_for_step(
        node_activity=final_node_activity,
        occupancy_rows=occupancy_rows,
        node_index_rows=node_index_rows,
        total_nodes=total_nodes,
        afferent_activity=_float_or_none(final_snapshot.get("afferent_activity")),
        intrinsic_activity=_float_or_none(final_snapshot.get("intrinsic_activity")),
        efferent_activity=_float_or_none(final_snapshot.get("efferent_activity")),
        step_id=int(final_snapshot.get("step_id", trace_payload.get("steps_completed", 0) or 0)),
        shell=shell,
        top_active_nodes=list(final_snapshot.get("top_active_nodes") or []),
    )


def _build_brain_view_payload_for_step(
    *,
    node_activity: np.ndarray,
    occupancy_rows: list[dict[str, Any]],
    node_index_rows: list[dict[str, Any]],
    total_nodes: int,
    afferent_activity: float | None,
    intrinsic_activity: float | None,
    efferent_activity: float | None,
    step_id: int,
    shell: dict[str, Any] | None,
    top_active_nodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    activity_by_group = {roi_id: 0.0 for roi_id, _ in DISPLAY_NEUROPIL_MANIFEST}
    node_membership = {roi_id: set() for roi_id, _ in DISPLAY_NEUROPIL_MANIFEST}
    dominant_group_by_node_idx: dict[int, tuple[str, float]] = {}

    for row in occupancy_rows:
        node_idx = int(row["node_idx"])
        mapped_group = NEUROPIL_TO_DISPLAY_GROUP.get(str(row["neuropil"]))
        if mapped_group is None:
            continue
        occupancy_fraction = float(row["occupancy_fraction"])
        if node_idx < 0 or node_idx >= total_nodes:
            continue
        contribution = abs(float(node_activity[node_idx])) * occupancy_fraction
        activity_by_group[mapped_group] += contribution
        node_membership[mapped_group].add(node_idx)

        previous = dominant_group_by_node_idx.get(node_idx)
        if previous is None or occupancy_fraction > previous[1]:
            dominant_group_by_node_idx[node_idx] = (mapped_group, occupancy_fraction)

    region_activity = [
        {
            "roi_id": roi_id,
            "roi_name": display_name,
            "activity_value": float(activity_by_group[roi_id]),
            "activity_delta": 0.0,
            "node_count": len(node_membership[roi_id]),
        }
        for roi_id, display_name in DISPLAY_NEUROPIL_MANIFEST
    ]
    top_regions = sorted(
        region_activity,
        key=lambda region: (-float(region["activity_value"]), str(region["roi_id"])),
    )[:5]

    source_id_by_node_idx = {int(row["node_idx"]): str(row["source_id"]) for row in node_index_rows}
    top_nodes = []
    for node in top_active_nodes or []:
        node_idx = int(node["node_idx"])
        dominant_group = dominant_group_by_node_idx.get(node_idx, ("unmapped", 0.0))[0]
        top_nodes.append(
            {
                "node_idx": node_idx,
                "source_id": source_id_by_node_idx.get(node_idx, "unknown"),
                "activity_value": float(node["activity_value"]),
                "flow_role": str(node["flow_role"]),
                "roi_name": dominant_group,
            }
        )

    mapped_nodes = len(set().union(*node_membership.values())) if node_membership else 0
    payload: dict[str, Any] = {
        "data_status": "recorded",
        "step_id": int(step_id),
        "semantic_scope": "neuropil",
        "view_mode": "neuropil-occupancy",
        "mapping_coverage": {
            "roi_mapped_nodes": int(mapped_nodes),
            "total_nodes": int(total_nodes),
        },
        "region_activity": region_activity,
        "top_regions": top_regions,
        "top_nodes": top_nodes,
        "afferent_activity": _float_or_none(afferent_activity),
        "intrinsic_activity": _float_or_none(intrinsic_activity),
        "efferent_activity": _float_or_none(efferent_activity),
    }
    if shell is not None:
        payload["shell"] = shell
    return payload


def _build_timeline_payload(
    *,
    trace_payload: dict[str, Any],
    summary_payload: dict[str, Any],
) -> dict[str, Any]:
    snapshots = list(trace_payload.get("snapshots") or [])
    events = _build_timeline_events(snapshots)
    return build_replay_timeline_payload(
        summary_payload=summary_payload,
        current_step=int(summary_payload.get("steps_completed", 0)),
        events=events,
    )


def _build_timeline_events(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not snapshots:
        return []

    candidates = [
        _event_for_snapshot(snapshots[0], event_type="rollout_started", label="Recorded rollout start"),
        _peak_event(snapshots, key="afferent_activity", event_type="afferent_peak", label="Afferent activity peak"),
        _peak_event(snapshots, key="intrinsic_activity", event_type="intrinsic_peak", label="Intrinsic activity peak"),
        _peak_event(snapshots, key="efferent_activity", event_type="efferent_peak", label="Efferent activity peak"),
        _event_for_snapshot(snapshots[-1], event_type="rollout_completed", label="Recorded rollout complete"),
    ]

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for event in candidates:
        if event is None:
            continue
        marker = (int(event["step_id"]), str(event["event_type"]))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(event)
    return deduped


def _peak_event(
    snapshots: list[dict[str, Any]],
    *,
    key: str,
    event_type: str,
    label: str,
) -> dict[str, Any] | None:
    selected = max(snapshots, key=lambda snapshot: float(snapshot.get(key, 0.0)), default=None)
    if selected is None:
        return None
    return _event_for_snapshot(selected, event_type=event_type, label=label)


def _event_for_snapshot(snapshot: dict[str, Any], *, event_type: str, label: str) -> dict[str, Any]:
    return {
        "step_id": int(snapshot["step_id"]),
        "event_type": event_type,
        "label": label,
    }


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
