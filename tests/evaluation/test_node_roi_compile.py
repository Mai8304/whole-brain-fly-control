from __future__ import annotations

from fruitfly.evaluation.node_roi_compile import (
    build_v1_neuropil_to_roi_map,
    compile_node_roi_map_rows,
)


def test_build_v1_neuropil_to_roi_map_collapses_bilateral_names() -> None:
    lookup = build_v1_neuropil_to_roi_map()

    assert lookup["AL_L"] == "AL"
    assert lookup["AL_R"] == "AL"
    assert lookup["LAL_L"] == "LAL"
    assert lookup["GNG"] == "GNG"


def test_compile_node_roi_map_rows_assigns_dominant_roi_from_synapse_counts() -> None:
    captured: dict[str, object] = {}

    def fake_synapse_count_fetcher(*args, **kwargs):
        queried = set(args[0])
        assert queried == {11, 22}
        captured["kwargs"] = kwargs
        return [
            {"id": 11, "neuropil": "AL_L", "pre": 7, "post": 0},
            {"id": 11, "neuropil": "LH_R", "pre": 1, "post": 1},
            {"id": 22, "neuropil": "FB", "pre": 4, "post": 1},
            {"id": 22, "neuropil": "GNG", "pre": 0, "post": 2},
        ]

    rows, summary = compile_node_roi_map_rows(
        node_index_rows=[
            {"source_id": 11, "node_idx": 0},
            {"source_id": 22, "node_idx": 1},
        ],
        synapse_count_fetcher=fake_synapse_count_fetcher,
        batch_size=2,
    )

    assert rows == [
        {"source_id": 11, "node_idx": 0, "roi_id": "AL"},
        {"source_id": 22, "node_idx": 1, "roi_id": "FB"},
    ]
    assert captured["kwargs"] == {
        "by_neuropil": True,
        "filtered": True,
        "materialization": "latest",
        "dataset": "public",
        "progress": False,
        "batch_size": 2,
    }
    assert summary["mapped_nodes"] == 2
    assert summary["roi_counts"]["AL"] == 1
    assert summary["roi_counts"]["FB"] == 1


def test_compile_node_roi_map_rows_assigns_null_when_top_roi_evidence_ties() -> None:
    def fake_synapse_count_fetcher(*args, **kwargs):
        return [
            {"id": 11, "neuropil": "AL_L", "pre": 4, "post": 0},
            {"id": 11, "neuropil": "LAL_R", "pre": 0, "post": 4},
        ]

    rows, summary = compile_node_roi_map_rows(
        node_index_rows=[{"source_id": 11, "node_idx": 0}],
        synapse_count_fetcher=fake_synapse_count_fetcher,
        batch_size=1,
    )

    assert rows == [{"source_id": 11, "node_idx": 0, "roi_id": None}]
    assert summary["mapped_nodes"] == 0
    assert summary["roi_counts"]["AL"] == 0


def test_compile_node_roi_map_rows_assigns_null_without_target_roi_evidence() -> None:
    def fake_synapse_count_fetcher(*args, **kwargs):
        return [{"id": 11, "neuropil": "SMP_L", "pre": 9, "post": 3}]

    rows, summary = compile_node_roi_map_rows(
        node_index_rows=[{"source_id": 11, "node_idx": 0}],
        synapse_count_fetcher=fake_synapse_count_fetcher,
        batch_size=1,
    )

    assert rows == [{"source_id": 11, "node_idx": 0, "roi_id": None}]
    assert summary["mapped_nodes"] == 0
    assert summary["mapping_coverage"] == 0.0
