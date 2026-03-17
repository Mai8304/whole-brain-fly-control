from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .brain_view_contract import build_brain_view_payload
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

RUNTIME_ACTIVITY_ARTIFACT_VERSION = 1


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
    formal_truth = _load_formal_truth(compiled_graph_dir)

    occupancy_rows = _read_occupancy_rows(occupancy_path)
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
        formal_truth=formal_truth,
        artifact_origin="initial-materialized",
    )
    timeline_payload = _build_timeline_payload(
        trace_payload=trace_payload,
        summary_payload=summary_payload,
    )
    timeline_payload["artifact_contract_version"] = RUNTIME_ACTIVITY_ARTIFACT_VERSION

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
    top_active_nodes: list[dict[str, Any]] | None = None,
    formal_truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if formal_truth is None:
        formal_truth = _load_formal_truth(compiled_graph_dir)
    occupancy_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    node_index_path = compiled_graph_dir / "node_index.parquet"
    occupancy_rows = _read_occupancy_rows(occupancy_path)
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
        top_active_nodes=top_active_nodes,
        formal_truth=formal_truth,
        artifact_origin="replay-live-step",
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
    formal_truth: dict[str, Any] | None = None,
    artifact_origin: str = "initial-materialized",
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
        formal_truth=formal_truth,
        artifact_origin=artifact_origin,
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
    formal_truth: dict[str, Any] | None = None,
    artifact_origin: str = "initial-materialized",
) -> dict[str, Any]:
    raw_activity_mass_by_neuropil: dict[str, float] = {}
    signed_activity_by_neuropil: dict[str, float] = {}
    covered_weight_sum_by_neuropil: dict[str, float] = {}
    display_name_by_neuropil: dict[str, str] = {}
    node_membership: dict[str, set[int]] = {}
    memberships_by_node_idx: dict[int, list[dict[str, Any]]] = {}
    group_weight_by_node_idx: dict[int, dict[str, float]] = {}

    for row in occupancy_rows:
        node_idx = int(row["node_idx"])
        formal_neuropil = str(row["neuropil"])
        display_name = NEUROPIL_TO_DISPLAY_GROUP.get(formal_neuropil, formal_neuropil)
        occupancy_fraction = float(row["occupancy_fraction"])
        if node_idx < 0 or node_idx >= total_nodes:
            continue
        activity_value = float(node_activity[node_idx])
        raw_activity_mass_by_neuropil[formal_neuropil] = (
            raw_activity_mass_by_neuropil.get(formal_neuropil, 0.0)
            + abs(activity_value) * occupancy_fraction
        )
        signed_activity_by_neuropil[formal_neuropil] = (
            signed_activity_by_neuropil.get(formal_neuropil, 0.0)
            + activity_value * occupancy_fraction
        )
        covered_weight_sum_by_neuropil[formal_neuropil] = (
            covered_weight_sum_by_neuropil.get(formal_neuropil, 0.0)
            + occupancy_fraction
        )
        display_name_by_neuropil[formal_neuropil] = display_name
        node_membership.setdefault(formal_neuropil, set()).add(node_idx)

        memberships_by_node_idx.setdefault(node_idx, []).append(
            {
                "neuropil": formal_neuropil,
                "occupancy_fraction": occupancy_fraction,
                "synapse_count": int(row.get("synapse_count", 0)),
            }
        )
        group_weight_by_node_idx.setdefault(node_idx, {})
        group_weight_by_node_idx[node_idx][display_name] = (
            group_weight_by_node_idx[node_idx].get(display_name, 0.0) + occupancy_fraction
        )

    region_activity = [
        {
            "neuropil_id": neuropil_id,
            "display_name": display_name_by_neuropil[neuropil_id],
            "raw_activity_mass": float(raw_activity_mass_by_neuropil[neuropil_id]),
            "signed_activity": float(signed_activity_by_neuropil[neuropil_id]),
            "covered_weight_sum": float(covered_weight_sum_by_neuropil[neuropil_id]),
            "node_count": len(node_membership[neuropil_id]),
            "is_display_grouped": display_name_by_neuropil[neuropil_id] != neuropil_id,
        }
        for neuropil_id in sorted(raw_activity_mass_by_neuropil)
    ]
    display_region_activity = _build_grouped_display_region_activity(
        region_activity,
        node_membership_by_neuropil=node_membership,
    )

    source_id_by_node_idx = {int(row["node_idx"]): str(row["source_id"]) for row in node_index_rows}
    top_nodes = []
    for node in top_active_nodes or []:
        node_idx = int(node["node_idx"])
        normalized_node: dict[str, Any] = {
            "node_idx": node_idx,
            "source_id": source_id_by_node_idx.get(node_idx, "unknown"),
            "activity_value": float(node["activity_value"]),
            "flow_role": str(node["flow_role"]),
            "neuropil_memberships": list(memberships_by_node_idx.get(node_idx, [])),
        }
        grouped_weights = group_weight_by_node_idx.get(node_idx, {})
        if grouped_weights:
            display_group_hint = sorted(
                grouped_weights.items(),
                key=lambda item: (-float(item[1]), str(item[0])),
            )[0][0]
            normalized_node["display_group_hint"] = display_group_hint
        top_nodes.append(normalized_node)

    mapped_nodes = len(set().union(*node_membership.values())) if node_membership else 0
    payload = build_brain_view_payload(
        semantic_scope="neuropil",
        view_mode="grouped-neuropil-v1",
        mapping_mode="node_neuropil_occupancy",
        activity_metric="activity_mass",
        formal_truth=_normalize_formal_truth(formal_truth),
        shell=shell,
        mapping_coverage={
            "neuropil_mapped_nodes": int(mapped_nodes),
            "total_nodes": int(total_nodes),
        },
        region_activity=region_activity,
        top_nodes=top_nodes,
    )
    payload.update(
        {
            "display_region_activity": display_region_activity,
            "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
            "artifact_origin": artifact_origin,
            "data_status": "recorded",
            "step_id": int(step_id),
            "afferent_activity": _float_or_none(afferent_activity),
            "intrinsic_activity": _float_or_none(intrinsic_activity),
            "efferent_activity": _float_or_none(efferent_activity),
        }
    )
    return payload


def _build_grouped_display_region_activity(
    region_activity: list[dict[str, Any]],
    *,
    node_membership_by_neuropil: dict[str, set[int]],
) -> list[dict[str, Any]]:
    group_order = {
        group_id: index
        for index, (group_id, _label) in enumerate(DISPLAY_NEUROPIL_MANIFEST)
    }
    grouped: dict[str, dict[str, Any]] = {}
    for region in region_activity:
        group_id = str(region["display_name"])
        if group_id not in group_order:
            continue
        entry = grouped.setdefault(
            group_id,
            {
                "group_neuropil_id": group_id,
                "raw_activity_mass": 0.0,
                "signed_activity": 0.0,
                "covered_weight_sum": 0.0,
                "node_idxs": set(),
                "member_neuropils": set(),
                "view_mode": "grouped-neuropil-v1",
                "is_display_transform": True,
            },
        )
        entry["raw_activity_mass"] += float(region["raw_activity_mass"])
        entry["signed_activity"] += float(region["signed_activity"])
        entry["covered_weight_sum"] += float(region["covered_weight_sum"])
        neuropil_id = str(region["neuropil_id"])
        entry["member_neuropils"].add(neuropil_id)
        entry["node_idxs"].update(node_membership_by_neuropil.get(neuropil_id, set()))

    return [
        {
            "group_neuropil_id": str(entry["group_neuropil_id"]),
            "raw_activity_mass": float(entry["raw_activity_mass"]),
            "signed_activity": float(entry["signed_activity"]),
            "covered_weight_sum": float(entry["covered_weight_sum"]),
            "node_count": len(entry["node_idxs"]),
            "member_neuropils": sorted(entry["member_neuropils"]),
            "view_mode": str(entry["view_mode"]),
            "is_display_transform": bool(entry["is_display_transform"]),
        }
        for entry in sorted(
            grouped.values(),
            key=lambda item: (
                int(group_order.get(str(item["group_neuropil_id"]), 9999)),
                str(item["group_neuropil_id"]),
            ),
        )
    ]


def _normalize_formal_truth(formal_truth: dict[str, Any] | None) -> dict[str, bool]:
    if formal_truth is None:
        return {
            "validation_passed": False,
            "graph_scope_validation_passed": False,
            "roster_alignment_passed": False,
        }
    return {
        "validation_passed": bool(formal_truth.get("validation_passed")),
        "graph_scope_validation_passed": bool(
            formal_truth.get(
                "graph_scope_validation_passed",
                formal_truth.get("validation_passed"),
            )
        ),
        "roster_alignment_passed": bool(
            formal_truth.get(
                "roster_alignment_passed",
                (formal_truth.get("roster_alignment") or {}).get("alignment_passed"),
            )
        ),
    }


def _load_formal_truth(compiled_graph_dir: Path) -> dict[str, bool]:
    validation_path = compiled_graph_dir / "neuropil_truth_validation.json"
    if not validation_path.exists():
        return _normalize_formal_truth(None)
    return _normalize_formal_truth(
        json.loads(validation_path.read_text(encoding="utf-8"))
    )


def _read_occupancy_rows(path: Path) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    selected_columns = [
        column
        for column in (
            "source_id",
            "node_idx",
            "neuropil",
            "occupancy_fraction",
            "synapse_count",
        )
        if column in table.column_names
    ]
    rows = table.select(selected_columns).to_pylist()
    if "synapse_count" not in selected_columns:
        for row in rows:
            row["synapse_count"] = 0
    return rows


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
