def test_rate_model_outputs_action_distribution_shapes() -> None:
    import torch

    from fruitfly.models.rate_model import WholeBrainRateModel

    model = WholeBrainRateModel(
        num_nodes=4,
        hidden_dim=8,
        action_dim=59,
        afferent_indices=[0],
        efferent_indices=[3],
        edge_index=[(0, 1), (1, 2), (2, 3)],
    )
    obs = torch.randn(2, 16)
    state = model.initial_state(batch_size=2)

    mean, log_std, next_state = model(obs, state)

    assert mean.shape == (2, 59)
    assert log_std.shape == (2, 59)
    assert next_state.shape == state.shape
