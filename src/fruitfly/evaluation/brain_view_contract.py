from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_brain_view_payload(
    *,
    shell: dict[str, Any] | None = None,
    mapping_coverage: dict[str, int],
    region_activity: Sequence[dict[str, Any]],
    top_nodes: Sequence[dict[str, Any]] | None = None,
    top_region_count: int = 5,
) -> dict[str, Any]:
    normalized_regions = [
        {
            "roi_id": str(region["roi_id"]),
            "roi_name": str(region["roi_name"]),
            "activity_value": float(region["activity_value"]),
            "activity_delta": float(region.get("activity_delta", 0.0)),
            "node_count": int(region["node_count"]),
        }
        for region in region_activity
    ]
    sorted_regions = sorted(
        normalized_regions,
        key=lambda region: (-region["activity_value"], region["roi_id"]),
    )
    payload: dict[str, Any] = {
        "view_mode": "region-aggregated",
        "mapping_coverage": {
            "roi_mapped_nodes": int(mapping_coverage["roi_mapped_nodes"]),
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
        payload["top_nodes"] = [
            {
                "node_idx": int(node["node_idx"]),
                "activity_value": float(node["activity_value"]),
                "flow_role": str(node["flow_role"]),
            }
            for node in top_nodes
        ]
    return payload
