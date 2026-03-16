from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def _accumulate_synapse_assignment(
    *,
    source_id: int,
    direction: str,
    neuropil: str,
    materialization: int,
    dataset: str,
    node_idx_by_source_id: dict[int, int],
    counts_by_key: dict[tuple[int, str], dict[str, Any]],
    totals_by_source_id: defaultdict[int, int],
) -> None:
    if source_id not in node_idx_by_source_id:
        raise ValueError(f"missing node_idx mapping for source_id={source_id}")

    key = (source_id, neuropil)
    entry = counts_by_key.setdefault(
        key,
        {
            "source_id": source_id,
            "node_idx": node_idx_by_source_id[source_id],
            "neuropil": neuropil,
            "pre_count": 0,
            "post_count": 0,
            "synapse_count": 0,
            "materialization": materialization,
            "dataset": dataset,
        },
    )

    if direction == "pre":
        entry["pre_count"] += 1
    elif direction == "post":
        entry["post_count"] += 1
    else:
        raise ValueError(f"unsupported direction: {direction}")
    entry["synapse_count"] += 1
    totals_by_source_id[source_id] += 1


def _finalize_node_neuropil_occupancy_rows(
    *,
    counts_by_key: dict[tuple[int, str], dict[str, Any]],
    totals_by_source_id: defaultdict[int, int],
) -> list[dict[str, Any]]:
    aggregated_rows: list[dict[str, Any]] = []
    for (source_id, _neuropil), entry in sorted(counts_by_key.items(), key=lambda item: (item[0][0], item[0][1])):
        total_synapses = totals_by_source_id[source_id]
        aggregated_rows.append(
            {
                **entry,
                "occupancy_fraction": (entry["synapse_count"] / total_synapses) if total_synapses else 0.0,
            }
        )
    return aggregated_rows


def aggregate_node_neuropil_occupancy_rows(
    *,
    synapse_assignment_rows: Iterable[dict[str, Any]],
    node_index_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    node_idx_by_source_id = {int(row["source_id"]): int(row["node_idx"]) for row in node_index_rows}

    counts_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    totals_by_source_id: defaultdict[int, int] = defaultdict(int)

    for row in synapse_assignment_rows:
        _accumulate_synapse_assignment(
            source_id=int(row["root_id"]),
            direction=str(row["direction"]),
            neuropil=str(row["neuropil"]),
            materialization=int(row["materialization"]),
            dataset=str(row["dataset"]),
            node_idx_by_source_id=node_idx_by_source_id,
            counts_by_key=counts_by_key,
            totals_by_source_id=totals_by_source_id,
        )
    return _finalize_node_neuropil_occupancy_rows(
        counts_by_key=counts_by_key,
        totals_by_source_id=totals_by_source_id,
    )


def aggregate_node_neuropil_occupancy_rows_from_batches(
    *,
    synapse_assignment_batches: Iterable[pa.RecordBatch],
    node_index_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    node_idx_by_source_id = {int(row["source_id"]): int(row["node_idx"]) for row in node_index_rows}

    counts_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    totals_by_source_id: defaultdict[int, int] = defaultdict(int)

    for batch in synapse_assignment_batches:
        root_ids = batch.column(batch.schema.get_field_index("root_id"))
        directions = batch.column(batch.schema.get_field_index("direction"))
        neuropils = batch.column(batch.schema.get_field_index("neuropil"))
        materializations = batch.column(batch.schema.get_field_index("materialization"))
        datasets = batch.column(batch.schema.get_field_index("dataset"))

        for index in range(batch.num_rows):
            _accumulate_synapse_assignment(
                source_id=int(root_ids[index].as_py()),
                direction=str(directions[index].as_py()),
                neuropil=str(neuropils[index].as_py()),
                materialization=int(materializations[index].as_py()),
                dataset=str(datasets[index].as_py()),
                node_idx_by_source_id=node_idx_by_source_id,
                counts_by_key=counts_by_key,
                totals_by_source_id=totals_by_source_id,
            )
    return _finalize_node_neuropil_occupancy_rows(
        counts_by_key=counts_by_key,
        totals_by_source_id=totals_by_source_id,
    )


def write_node_neuropil_occupancy(path: Path, rows: list[dict[str, Any]]) -> None:
    table = pa.table(
        {
            "source_id": [int(row["source_id"]) for row in rows],
            "node_idx": [int(row["node_idx"]) for row in rows],
            "neuropil": [str(row["neuropil"]) for row in rows],
            "pre_count": [int(row["pre_count"]) for row in rows],
            "post_count": [int(row["post_count"]) for row in rows],
            "synapse_count": [int(row["synapse_count"]) for row in rows],
            "occupancy_fraction": [float(row["occupancy_fraction"]) for row in rows],
            "materialization": [int(row["materialization"]) for row in rows],
            "dataset": [str(row["dataset"]) for row in rows],
        },
        schema=pa.schema(
            [
                pa.field("source_id", pa.int64(), nullable=False),
                pa.field("node_idx", pa.int64(), nullable=False),
                pa.field("neuropil", pa.string(), nullable=False),
                pa.field("pre_count", pa.int64(), nullable=False),
                pa.field("post_count", pa.int64(), nullable=False),
                pa.field("synapse_count", pa.int64(), nullable=False),
                pa.field("occupancy_fraction", pa.float64(), nullable=False),
                pa.field("materialization", pa.int64(), nullable=False),
                pa.field("dataset", pa.string(), nullable=False),
            ]
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
