import torch


def test_summarize_neural_activity_exposes_partition_means_and_top_nodes() -> None:
    from fruitfly.evaluation.neural_activity import summarize_neural_activity

    state = torch.tensor(
        [
            [
                [0.5, 0.5],
                [1.0, 1.0],
                [2.0, 2.0],
            ]
        ],
        dtype=torch.float32,
    )
    snapshot = summarize_neural_activity(
        state=state,
        afferent_mask=torch.tensor([True, False, False]),
        intrinsic_mask=torch.tensor([False, True, False]),
        efferent_mask=torch.tensor([False, False, True]),
        top_k=2,
    )

    assert snapshot["afferent_activity"] == 0.5
    assert snapshot["intrinsic_activity"] == 1.0
    assert snapshot["efferent_activity"] == 2.0
    assert snapshot["top_active_nodes"] == [
        {"node_idx": 2, "activity_value": 2.0, "flow_role": "efferent"},
        {"node_idx": 1, "activity_value": 1.0, "flow_role": "intrinsic"},
    ]
