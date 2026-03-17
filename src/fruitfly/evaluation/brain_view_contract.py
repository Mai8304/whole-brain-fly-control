from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_brain_view_payload(
    *,
    semantic_scope: str,
    view_mode: str,
    mapping_mode: str,
    activity_metric: str,
    formal_truth: dict[str, Any],
    shell: dict[str, Any] | None = None,
    mapping_coverage: dict[str, int],
    region_activity: Sequence[dict[str, Any]],
    top_nodes: Sequence[dict[str, Any]] | None = None,
    top_region_count: int = 5,
) -> dict[str, Any]:
    normalized_regions = [
        {
            "neuropil_id": str(region["neuropil_id"]),
            "display_name": str(region["display_name"]),
            "raw_activity_mass": float(region["raw_activity_mass"]),
            "signed_activity": float(region["signed_activity"]),
            "covered_weight_sum": float(region["covered_weight_sum"]),
            "node_count": int(region["node_count"]),
            "is_display_grouped": bool(region["is_display_grouped"]),
        }
        for region in region_activity
    ]
    sorted_regions = sorted(
        normalized_regions,
        key=lambda region: (-region["raw_activity_mass"], region["neuropil_id"]),
    )
    payload: dict[str, Any] = {
        "semantic_scope": str(semantic_scope),
        "view_mode": str(view_mode),
        "mapping_mode": str(mapping_mode),
        "activity_metric": str(activity_metric),
        "formal_truth": {
            "validation_passed": bool(formal_truth["validation_passed"]),
            "graph_scope_validation_passed": bool(
                formal_truth["graph_scope_validation_passed"]
            ),
            "roster_alignment_passed": bool(formal_truth["roster_alignment_passed"]),
        },
        "mapping_coverage": {
            "neuropil_mapped_nodes": int(mapping_coverage["neuropil_mapped_nodes"]),
            "total_nodes": int(mapping_coverage["total_nodes"]),
        },
        "region_activity": normalized_regions,
        "top_regions": sorted_regions[: max(0, int(top_region_count))],
    }
    if shell is not None:
        payload["shell"] = {
            "asset_id": str(shell["asset_id"]),
            "asset_url": str(shell["asset_url"]),
            "base_color": str(shell["base_color"]),
            "opacity": float(shell["opacity"]),
        }
    if top_nodes is not None:
        normalized_top_nodes: list[dict[str, Any]] = []
        for node in top_nodes:
            normalized_node: dict[str, Any] = {
                "node_idx": int(node["node_idx"]),
                "source_id": str(node["source_id"]),
                "activity_value": float(node["activity_value"]),
                "flow_role": str(node["flow_role"]),
                "neuropil_memberships": [
                    {
                        "neuropil": str(membership["neuropil"]),
                        "occupancy_fraction": float(
                            membership["occupancy_fraction"]
                        ),
                        "synapse_count": int(membership["synapse_count"]),
                    }
                    for membership in node.get("neuropil_memberships", [])
                ],
            }
            if "display_group_hint" in node:
                normalized_node["display_group_hint"] = str(node["display_group_hint"])
            normalized_top_nodes.append(normalized_node)
        payload["top_nodes"] = normalized_top_nodes
    return payload
