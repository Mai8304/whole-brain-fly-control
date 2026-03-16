from __future__ import annotations

from fruitfly.evaluation.neuropil_truth_validation import validate_node_neuropil_occupancy


def test_validate_node_neuropil_occupancy_passes_when_counts_match() -> None:
    result = validate_node_neuropil_occupancy(
        occupancy_rows=[
            {
                "source_id": 11,
                "node_idx": 0,
                "neuropil": "FB",
                "pre_count": 2,
                "post_count": 1,
                "synapse_count": 3,
                "occupancy_fraction": 0.75,
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
                "occupancy_fraction": 0.25,
                "materialization": 783,
                "dataset": "public",
            },
        ],
        official_pre_rows=[
            {"root_id": 11, "neuropil": "FB", "count": 2},
            {"root_id": 11, "neuropil": "LAL", "count": 1},
        ],
        official_post_rows=[
            {"root_id": 11, "neuropil": "FB", "count": 1},
            {"root_id": 11, "neuropil": "LAL", "count": 0},
        ],
    )

    assert result["validation_passed"] is True
    assert result["pre_mismatch_count"] == 0
    assert result["post_mismatch_count"] == 0
    assert result["example_mismatches"] == []


def test_validate_node_neuropil_occupancy_reports_mismatches() -> None:
    result = validate_node_neuropil_occupancy(
        occupancy_rows=[
            {
                "source_id": 11,
                "node_idx": 0,
                "neuropil": "FB",
                "pre_count": 2,
                "post_count": 1,
                "synapse_count": 3,
                "occupancy_fraction": 1.0,
                "materialization": 783,
                "dataset": "public",
            }
        ],
        official_pre_rows=[
            {"root_id": 11, "neuropil": "FB", "count": 3},
        ],
        official_post_rows=[
            {"root_id": 11, "neuropil": "FB", "count": 0},
        ],
    )

    assert result["validation_passed"] is False
    assert result["pre_mismatch_count"] == 1
    assert result["post_mismatch_count"] == 1
    assert result["example_mismatches"] == [
        {
            "direction": "pre",
            "root_id": 11,
            "neuropil": "FB",
            "expected_count": 3,
            "actual_count": 2,
        },
        {
            "direction": "post",
            "root_id": 11,
            "neuropil": "FB",
            "expected_count": 0,
            "actual_count": 1,
        },
    ]


def test_validate_node_neuropil_occupancy_detects_missing_directional_rows() -> None:
    result = validate_node_neuropil_occupancy(
        occupancy_rows=[],
        official_pre_rows=[
            {"root_id": 22, "neuropil": "GNG", "count": 4},
        ],
        official_post_rows=[],
    )

    assert result["validation_passed"] is False
    assert result["pre_mismatch_count"] == 1
    assert result["post_mismatch_count"] == 0
    assert result["example_mismatches"] == [
        {
            "direction": "pre",
            "root_id": 22,
            "neuropil": "GNG",
            "expected_count": 4,
            "actual_count": 0,
        }
    ]
