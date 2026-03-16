def test_probe_walk_imitation_reports_basic_summary() -> None:
    from fruitfly.adapters.flybody_probe import probe_walk_imitation

    class FakeTimeStep:
        def __init__(self, reward, observation):
            self.reward = reward
            self.observation = observation

    class FakeEnv:
        def reset(self):
            return FakeTimeStep(0.0, {"joint_pos": [0.0], "vel": [0.0]})

        def step(self, action):
            assert len(action) == 59
            return FakeTimeStep(1.5, {"joint_pos": [0.1], "vel": [0.2]})

    payload = probe_walk_imitation(env_factory=lambda: FakeEnv())

    assert payload["status"] == "ok"
    assert payload["action_dim"] == 59
    assert payload["reset_observation_keys"] == ["joint_pos", "vel"]
    assert payload["step_reward"] == 1.5


def test_probe_walk_imitation_passes_numpy_action() -> None:
    import numpy as np

    from fruitfly.adapters.flybody_probe import probe_walk_imitation

    class FakeTimeStep:
        def __init__(self, reward, observation):
            self.reward = reward
            self.observation = observation

    class FakeEnv:
        def reset(self):
            return FakeTimeStep(0.0, {"joint_pos": [0.0]})

        def step(self, action):
            assert isinstance(action, np.ndarray)
            assert action.shape == (59,)
            return FakeTimeStep(0.0, {"joint_pos": [0.0]})

    probe_walk_imitation(env_factory=lambda: FakeEnv())
