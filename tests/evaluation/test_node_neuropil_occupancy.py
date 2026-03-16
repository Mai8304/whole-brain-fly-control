from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from fruitfly.evaluation.node_neuropil_occupancy import (
    aggregate_node_neuropil_occupancy_rows,
    write_node_neuropil_occupancy,
)


def test_aggregate_node_neuropil_occupancy_rows_groups_by_node_and_neuropil() -> None:
    rows = aggregate_node_neuropil_occupancy_rows(
        synapse_assignment_rows=[
            {"synapse_id": 1, "root_id": 11, "direction": "pre", "neuropil": "FB", "materialization": 783, "dataset": "public"},
            {"synapse_id": 2, "root_id": 11, "direction": "post", "neuropil": "FB", "materialization": 783, "dataset": "public"},
            {"synapse_id": 3, "root_id": 11, "direction": "pre", "neuropil": "LAL", "materialization": 783, "dataset": "public"},
            {"synapse_id": 4, "root_id": 22, "direction": "post", "neuropil": "GNG", "materialization": 783, "dataset": "public"},
        ],
        node_index_rows=[
            {"source_id": 11, "node_idx": 0},
            {"source_id": 22, "node_idx": 1},
        ],
    )

    assert rows == [
        {
            "source_id": 11,
            "node_idx": 0,
            "neuropil": "FB",
            "pre_count": 1,
            "post_count": 1,
            "synapse_count": 2,
            "occupancy_fraction": 2 / 3,
            "materialization": 783,
            "dataset": "public",
        },
        {
            "source_id": 11,
            "node_idx": 0,
            "neuropil": "LAL",
            "pre_count": 1,
            "post_count": 0,
            "synapse_count": 1,
            "occupancy_fraction": 1 / 3,
            "materialization": 783,
            "dataset": "public",
        },
        {
            "source_id": 22,
            "node_idx": 1,
            "neuropil": "GNG",
            "pre_count": 0,
            "post_count": 1,
            "synapse_count": 1,
            "occupancy_fraction": 1.0,
            "materialization": 783,
            "dataset": "public",
        },
    ]


def test_aggregate_node_neuropil_occupancy_rows_requires_node_index_match() -> None:
    try:
        aggregate_node_neuropil_occupancy_rows(
            synapse_assignment_rows=[
                {"synapse_id": 1, "root_id": 11, "direction": "pre", "neuropil": "FB", "materialization": 783, "dataset": "public"},
            ],
            node_index_rows=[],
        )
    except ValueError as exc:
        assert "missing node_idx mapping" in str(exc)
    else:
        raise AssertionError("expected ValueError when node_index mapping is missing")


def test_write_node_neuropil_occupancy_writes_parquet(tmp_path: Path) -> None:
    output_path = tmp_path / "node_neuropil_occupancy.parquet"
    write_node_neuropil_occupancy(
        output_path,
        rows=[
            {
                "source_id": 11,
                "node_idx": 0,
                "neuropil": "FB",
                "pre_count": 1,
                "post_count": 2,
                "synapse_count": 3,
                "occupancy_fraction": 1.0,
                "materialization": 783,
                "dataset": "public",
            }
        ],
    )

    table = pq.read_table(output_path)
    assert table.column_names == [
        "source_id",
        "node_idx",
        "neuropil",
        "pre_count",
        "post_count",
        "synapse_count",
        "occupancy_fraction",
        "materialization",
        "dataset",
    ]
    assert table.to_pylist()[0]["neuropil"] == "FB"
