def test_observation_adapter_flattens_sections() -> None:
    from fruitfly.adapters.flybody_obs import adapt_observation

    obs = {"proprio": [1.0, 2.0], "command": [3.0]}
    adapted = adapt_observation(obs)
    assert adapted.shape[0] == 3
