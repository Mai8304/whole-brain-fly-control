from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SYNAPSE_NEUROPIL_ASSIGNMENT_SCHEMA = pa.schema(
    [
        pa.field("synapse_id", pa.int64(), nullable=False),
        pa.field("root_id", pa.int64(), nullable=False),
        pa.field("direction", pa.string(), nullable=False),
        pa.field("neuropil", pa.string(), nullable=False),
        pa.field("materialization", pa.int64(), nullable=False),
        pa.field("dataset", pa.string(), nullable=False),
    ]
)


def compile_synapse_assignment_rows(
    *,
    synapse_rows: Iterable[dict[str, Any]],
    query_ids: set[int],
    materialization: int | str,
    dataset: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in synapse_rows:
        synapse_id = int(row["id"])
        neuropil = row.get("neuropil")
        if neuropil in (None, ""):
            continue

        pre_root = int(row["pre_pt_root_id"])
        post_root = int(row["post_pt_root_id"])

        if pre_root in query_ids:
            rows.append(
                {
                    "synapse_id": synapse_id,
                    "root_id": pre_root,
                    "direction": "pre",
                    "neuropil": str(neuropil),
                    "materialization": materialization,
                    "dataset": dataset,
                }
            )
        if post_root in query_ids:
            rows.append(
                {
                    "synapse_id": synapse_id,
                    "root_id": post_root,
                    "direction": "post",
                    "neuropil": str(neuropil),
                    "materialization": materialization,
                    "dataset": dataset,
                }
            )
    return sorted(rows, key=lambda item: (int(item["root_id"]), int(item["synapse_id"]), str(item["direction"])))


def write_synapse_assignment(path: Path, *, rows: list[dict[str, Any]]) -> None:
    table = rows_to_synapse_assignment_table(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def rows_to_synapse_assignment_table(rows: list[dict[str, Any]]) -> pa.Table:
    return pa.table(
        {
            "synapse_id": [int(row["synapse_id"]) for row in rows],
            "root_id": [int(row["root_id"]) for row in rows],
            "direction": [str(row["direction"]) for row in rows],
            "neuropil": [str(row["neuropil"]) for row in rows],
            "materialization": [int(row["materialization"]) for row in rows],
            "dataset": [str(row["dataset"]) for row in rows],
        },
        schema=SYNAPSE_NEUROPIL_ASSIGNMENT_SCHEMA,
    )
