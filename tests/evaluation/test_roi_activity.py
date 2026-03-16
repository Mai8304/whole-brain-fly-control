def test_aggregate_roi_activity_groups_node_activity_by_roi() -> None:
    from fruitfly.evaluation.roi_activity import aggregate_roi_activity
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    result = aggregate_roi_activity(
        node_activity=[0.2, -0.4, 0.9, 0.3],
        node_roi_rows=[
            {"source_id": 1, "node_idx": 0, "roi_id": "AL"},
            {"source_id": 2, "node_idx": 1, "roi_id": "AL"},
            {"source_id": 3, "node_idx": 2, "roi_id": "FB"},
            {"source_id": 4, "node_idx": 3, "roi_id": "LAL"},
        ],
        roi_manifest=build_v1_roi_manifest(),
    )

    assert result["mapping_coverage"] == {"roi_mapped_nodes": 4, "total_nodes": 4}
    assert result["region_activity"][0]["roi_id"] == "AL"
    assert result["region_activity"][0]["activity_value"] == 0.30000000000000004
    assert result["region_activity"][0]["node_count"] == 2
    assert result["region_activity"][3]["roi_id"] == "FB"
    assert result["region_activity"][3]["activity_value"] == 0.9


def test_aggregate_roi_activity_computes_delta_and_top_regions() -> None:
    from fruitfly.evaluation.roi_activity import aggregate_roi_activity
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    result = aggregate_roi_activity(
        node_activity=[0.2, 0.4, 0.9, 0.3],
        node_roi_rows=[
            {"source_id": 1, "node_idx": 0, "roi_id": "AL"},
            {"source_id": 2, "node_idx": 1, "roi_id": "AL"},
            {"source_id": 3, "node_idx": 2, "roi_id": "FB"},
            {"source_id": 4, "node_idx": 3, "roi_id": "LAL"},
        ],
        roi_manifest=build_v1_roi_manifest(),
        previous_activity={"AL": 0.1, "FB": 0.7, "LAL": 0.25},
        top_k=2,
    )

    assert result["top_regions"] == [
        result["region_activity"][3],
        result["region_activity"][0],
    ]
    assert result["region_activity"][0]["activity_delta"] == 0.20000000000000004
    assert result["region_activity"][3]["activity_delta"] == 0.20000000000000007
    assert result["region_activity"][6]["activity_delta"] == 0.04999999999999999


def test_aggregate_roi_activity_preserves_manifest_priority_for_output_rows() -> None:
    from fruitfly.evaluation.roi_activity import aggregate_roi_activity
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    result = aggregate_roi_activity(
        node_activity=[0.5],
        node_roi_rows=[
            {"source_id": 1, "node_idx": 0, "roi_id": "GNG"},
        ],
        roi_manifest=build_v1_roi_manifest(),
    )

    assert [entry["roi_id"] for entry in result["region_activity"]] == [
        "AL",
        "LH",
        "PB",
        "FB",
        "EB",
        "NO",
        "LAL",
        "GNG",
    ]


def test_aggregate_roi_activity_ignores_null_roi_rows_for_activity_and_coverage() -> None:
    from fruitfly.evaluation.roi_activity import aggregate_roi_activity
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    result = aggregate_roi_activity(
        node_activity=[0.5, 0.8],
        node_roi_rows=[
            {"source_id": 1, "node_idx": 0, "roi_id": "AL"},
            {"source_id": 2, "node_idx": 1, "roi_id": None},
        ],
        roi_manifest=build_v1_roi_manifest(),
    )

    assert result["mapping_coverage"] == {"roi_mapped_nodes": 1, "total_nodes": 2}
    assert result["region_activity"][0]["roi_id"] == "AL"
    assert result["region_activity"][0]["node_count"] == 1
    assert result["region_activity"][0]["activity_value"] == 0.5
