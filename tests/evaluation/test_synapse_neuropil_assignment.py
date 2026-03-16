from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq


def test_compile_synapse_assignment_rows_emits_pre_and_post_views() -> None:
    from fruitfly.evaluation.synapse_neuropil_assignment import compile_synapse_assignment_rows

    rows = compile_synapse_assignment_rows(
        synapse_rows=[
            {
                "id": 101,
                "pre_pt_root_id": 11,
                "post_pt_root_id": 22,
                "neuropil": "FB",
            }
        ],
        query_ids={11, 22},
        materialization=783,
        dataset="public",
    )

    assert rows == [
        {
            "synapse_id": 101,
            "root_id": 11,
            "direction": "pre",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        },
        {
            "synapse_id": 101,
            "root_id": 22,
            "direction": "post",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        },
    ]


def test_compile_synapse_assignment_rows_ignores_rows_without_neuropil_or_query_match() -> None:
    from fruitfly.evaluation.synapse_neuropil_assignment import compile_synapse_assignment_rows

    rows = compile_synapse_assignment_rows(
        synapse_rows=[
            {"id": 101, "pre_pt_root_id": 11, "post_pt_root_id": 22, "neuropil": None},
            {"id": 102, "pre_pt_root_id": 33, "post_pt_root_id": 44, "neuropil": "FB"},
        ],
        query_ids={11, 22},
        materialization=783,
        dataset="public",
    )

    assert rows == []


def test_write_synapse_assignment_writes_required_schema(tmp_path: Path) -> None:
    from fruitfly.evaluation.synapse_neuropil_assignment import write_synapse_assignment

    output_path = tmp_path / "synapse_neuropil_assignment.parquet"
    write_synapse_assignment(
        output_path,
        rows=[
            {
                "synapse_id": 101,
                "root_id": 11,
                "direction": "pre",
                "neuropil": "FB",
                "materialization": 783,
                "dataset": "public",
            }
        ],
    )

    rows = pq.read_table(output_path).to_pylist()
    assert rows == [
        {
            "synapse_id": 101,
            "root_id": 11,
            "direction": "pre",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        }
    ]
