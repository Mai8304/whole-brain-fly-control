from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .roi_manifest import build_v1_roi_manifest

REQUIRED_NODE_ROI_MAP_COLUMNS = {"source_id", "node_idx", "roi_id"}


def load_node_roi_map(
    path: Path,
    *,
    roi_manifest: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    missing_columns = REQUIRED_NODE_ROI_MAP_COLUMNS - set(table.column_names)
    if missing_columns:
        raise ValueError(f"node_roi_map missing columns: {sorted(missing_columns)}")

    rows = table.select(sorted(REQUIRED_NODE_ROI_MAP_COLUMNS)).to_pylist()
    typed_rows = [
        {
            "source_id": int(row["source_id"]),
            "node_idx": int(row["node_idx"]),
            "roi_id": None if row["roi_id"] is None else str(row["roi_id"]),
        }
        for row in rows
    ]
    _validate_roi_ids(typed_rows, roi_manifest=roi_manifest)
    return typed_rows


def _validate_roi_ids(
    rows: list[dict[str, Any]],
    *,
    roi_manifest: list[dict[str, Any]] | None = None,
) -> None:
    valid_roi_ids = {
        str(entry["roi_id"]) for entry in (roi_manifest if roi_manifest is not None else build_v1_roi_manifest())
    }
    for row in rows:
        roi_id = row["roi_id"]
        if roi_id is None:
            continue
        roi_id = str(roi_id)
        if roi_id not in valid_roi_ids:
            raise ValueError(f"node_roi_map contains unknown roi_id: {roi_id}")
