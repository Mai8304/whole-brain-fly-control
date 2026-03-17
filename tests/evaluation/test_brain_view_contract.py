def test_build_brain_view_payload_exposes_formal_neuropil_contract() -> None:
    from fruitfly.evaluation.brain_view_contract import build_brain_view_payload

    payload = build_brain_view_payload(
        semantic_scope="neuropil",
        view_mode="grouped-neuropil-v1",
        mapping_mode="node_neuropil_occupancy",
        activity_metric="activity_mass",
        mapping_coverage={"neuropil_mapped_nodes": 2, "total_nodes": 4},
        formal_truth={
            "validation_passed": True,
            "graph_scope_validation_passed": True,
            "roster_alignment_passed": False,
        },
        region_activity=[
            {
                "neuropil_id": "AL",
                "display_name": "AL",
                "raw_activity_mass": 0.9,
                "signed_activity": -0.1,
                "covered_weight_sum": 1.0,
                "node_count": 2,
                "is_display_grouped": True,
            },
        ],
        top_nodes=[
            {
                "node_idx": 1,
                "source_id": "20",
                "activity_value": 0.6,
                "flow_role": "intrinsic",
                "neuropil_memberships": [
                    {"neuropil": "AL_L", "occupancy_fraction": 0.75, "synapse_count": 3}
                ],
                "display_group_hint": "AL",
            }
        ],
    )

    assert payload["mapping_mode"] == "node_neuropil_occupancy"
    assert payload["region_activity"][0]["neuropil_id"] == "AL"
    assert payload["top_nodes"][0]["neuropil_memberships"][0]["neuropil"] == "AL_L"
