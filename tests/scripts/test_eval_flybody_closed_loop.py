import json
from pathlib import Path


def test_eval_flybody_closed_loop_cli_writes_summary_and_video(tmp_path, monkeypatch, capsys) -> None:
    from scripts import eval_flybody_closed_loop

    class FakeTimestep:
        def __init__(self, reward=0.0, done=False):
            self.reward = reward
            self._done = done
            self.observation = {
                "walker/gyro": [0.0, 0.0, 0.1],
                "walker/velocimeter": [0.25, 0.0, 0.0],
                "walker/world_zaxis": [0.0, 0.0, 1.0],
            }

        def last(self):
            return self._done

    class FakePhysics:
        def render(self, **kwargs):
            return [[[0, 0, 0] for _ in range(2)] for _ in range(2)]

    class FakeEnv:
        physics = FakePhysics()

        def reset(self):
            return FakeTimestep()

        def step(self, action):
            return FakeTimestep(reward=1.0, done=True)

    class FakePolicy:
        def reset(self):
            return None

        def act(self, observation):
            return [0.1, 0.2]

    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "load_checkpoint_bundle",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "ClosedLoopPolicyWrapper",
        lambda bundle: FakePolicy(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_require_walk_imitation_env_factory",
        lambda: FakeEnv,
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_write_rollout_video",
        lambda *, output_path, frames, fps: Path(output_path).write_bytes(b"fake-mp4"),
    )

    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint",
            str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir",
            str(tmp_path / "compiled"),
            "--task",
            "straight_walking",
            "--max-steps",
            "4",
            "--save-video",
            "--output-dir",
            str(tmp_path / "eval"),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["task"] == "straight_walking"
    assert payload["reward_mean"] == 1.0
    assert payload["forward_velocity_mean"] == 0.25
    assert payload["forward_velocity_std"] == 0.0
    assert payload["body_upright_mean"] == 1.0
    assert payload["video_path"] == str(tmp_path / "eval" / "rollout.mp4")
    assert (tmp_path / "eval" / "summary.json").exists()
    assert (tmp_path / "eval" / "rollout.mp4").exists()


def test_eval_flybody_closed_loop_failure_preserves_summary(tmp_path, monkeypatch, capsys) -> None:
    from scripts import eval_flybody_closed_loop

    class FakeTimestep:
        def __init__(self):
            self.reward = 0.0
            self.observation = {"walker/gyro": [0.0, 0.0, 0.0]}

        def last(self):
            return False

    class FakeEnv:
        def reset(self):
            return FakeTimestep()

        def step(self, action):
            raise RuntimeError("step failed")

    class FakePolicy:
        def reset(self):
            return None

        def act(self, observation):
            return [0.1, 0.2]

    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "load_checkpoint_bundle",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "ClosedLoopPolicyWrapper",
        lambda bundle: FakePolicy(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_require_walk_imitation_env_factory",
        lambda: FakeEnv,
    )

    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint",
            str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir",
            str(tmp_path / "compiled"),
            "--task",
            "straight_walking",
            "--max-steps",
            "4",
            "--output-dir",
            str(tmp_path / "eval"),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "failed"
    assert payload["error"] == "step failed"
    assert (tmp_path / "eval" / "summary.json").exists()
