def test_build_brain_view_payload_exposes_region_contract() -> None:
    from fruitfly.evaluation.brain_view_contract import build_brain_view_payload

    payload = build_brain_view_payload(
        shell={
            "asset_id": "flywire_brain_v141",
            "asset_url": "/api/console/brain-shell",
            "base_color": "#89a5ff",
            "opacity": 0.18,
        },
        mapping_coverage={"roi_mapped_nodes": 12, "total_nodes": 20},
        region_activity=[
            {
                "roi_id": "MB",
                "roi_name": "Mushroom Body",
                "activity_value": 0.8,
                "activity_delta": 0.1,
                "node_count": 5,
            },
            {
                "roi_id": "LAL",
                "roi_name": "Lateral Accessory Lobe",
                "activity_value": 0.4,
                "activity_delta": -0.05,
                "node_count": 3,
            },
        ],
        top_nodes=[
            {"node_idx": 7, "activity_value": 1.2, "flow_role": "efferent"},
        ],
    )

    assert payload["view_mode"] == "region-aggregated"
    assert payload["shell"] == {
        "asset_id": "flywire_brain_v141",
        "asset_url": "/api/console/brain-shell",
        "base_color": "#89a5ff",
        "opacity": 0.18,
    }
    assert payload["mapping_coverage"] == {"roi_mapped_nodes": 12, "total_nodes": 20}
    assert len(payload["region_activity"]) == 2
    assert payload["top_regions"][0]["roi_id"] == "MB"
    assert payload["top_nodes"] == [
        {"node_idx": 7, "activity_value": 1.2, "flow_role": "efferent"},
    ]
