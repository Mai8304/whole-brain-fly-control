from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any


def aggregate_roi_activity(
    *,
    node_activity: Sequence[float],
    node_roi_rows: Sequence[dict[str, Any]],
    roi_manifest: Sequence[dict[str, Any]],
    previous_activity: dict[str, float] | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    activity_by_roi: dict[str, list[float]] = defaultdict(list)
    mapped_node_count = 0
    for row in node_roi_rows:
        node_idx = int(row["node_idx"])
        roi_id = row["roi_id"]
        if roi_id is None:
            continue
        roi_id = str(roi_id)
        activity_by_roi[roi_id].append(abs(float(node_activity[node_idx])))
        mapped_node_count += 1

    previous_activity = previous_activity or {}
    region_activity: list[dict[str, Any]] = []
    priority_by_roi = {str(entry["roi_id"]): int(entry["priority"]) for entry in roi_manifest}
    name_by_roi = {str(entry["roi_id"]): str(entry["display_name"]) for entry in roi_manifest}

    for entry in roi_manifest:
        roi_id = str(entry["roi_id"])
        values = activity_by_roi.get(roi_id, [])
        if values:
            activity_value = sum(values) / len(values)
        else:
            activity_value = 0.0
        region_activity.append(
            {
                "roi_id": roi_id,
                "roi_name": name_by_roi[roi_id],
                "activity_value": activity_value,
                "activity_delta": activity_value - float(previous_activity.get(roi_id, 0.0)),
                "node_count": len(values),
            }
        )

    top_regions = sorted(
        region_activity,
        key=lambda entry: (-float(entry["activity_value"]), priority_by_roi[str(entry["roi_id"])]),
    )[: max(0, int(top_k))]

    return {
        "region_activity": region_activity,
        "top_regions": top_regions,
        "mapping_coverage": {
            "roi_mapped_nodes": int(mapped_node_count),
            "total_nodes": int(len(node_activity)),
        },
    }
