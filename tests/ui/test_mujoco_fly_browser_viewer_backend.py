from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import numpy as np


class _FakeTimeStep:
    def __init__(self, observation: dict[str, np.ndarray], *, terminal: bool = False) -> None:
        self.observation = observation
        self._terminal = terminal

    def last(self) -> bool:
        return self._terminal


class _FakeFieldIndexer:
    def __init__(self, rows: dict[str, list[float]]) -> None:
        self._rows = rows
        self.axes = SimpleNamespace(row=SimpleNamespace(names=list(rows.keys())))

    def __getitem__(self, key: str) -> list[float]:
        return self._rows[key]


class _FakePhysics:
    def __init__(self) -> None:
        self.data = SimpleNamespace(time=0.0)
        self.named = SimpleNamespace(
            data=SimpleNamespace(
                xpos=_FakeFieldIndexer(
                    {
                        "world": [0.0, 0.0, 0.0],
                        "walker/": [0.0, 0.0, 0.1278],
                        "walker/thorax": [0.0, 0.0, 0.1278],
                    }
                ),
                xquat=_FakeFieldIndexer(
                    {
                        "world": [1.0, 0.0, 0.0, 0.0],
                        "walker/": [1.0, 0.0, 0.0, 0.0],
                        "walker/thorax": [1.0, 0.0, 0.0, 0.0],
                    }
                ),
            )
        )


class _FakeEnv:
    def __init__(self) -> None:
        self.physics = _FakePhysics()
        self.reset_calls = 0
        self.step_calls = 0

    def reset(self) -> _FakeTimeStep:
        self.reset_calls += 1
        self.physics.data.time = 0.0
        return _FakeTimeStep({"walker/joints_pos": np.asarray([0.0], dtype=np.float32)})

    def step(self, action: np.ndarray) -> _FakeTimeStep:
        self.step_calls += 1
        self.physics.data.time += 0.02
        self.physics.named.data.xpos._rows["walker/thorax"] = [float(action[0]), 0.0, 0.1278]
        return _FakeTimeStep({"walker/joints_pos": np.asarray([float(action[0])], dtype=np.float32)})


def test_browser_viewer_backend_emits_static_pose_without_checkpoint(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_backend import MujocoFlyBrowserViewerBackend

    env = _FakeEnv()
    backend = MujocoFlyBrowserViewerBackend(
        checkpoint_path=None,
        env_factory=lambda: env,
    )

    payload = backend.current_viewer_state()

    assert payload["running_state"] == "paused"
    assert payload["body_poses"][0]["body_name"] == "walker/"
    assert payload["body_poses"][1]["body_name"] == "walker/thorax"
    assert env.step_calls == 0


def test_browser_viewer_backend_only_steps_when_running_and_policy_loaded(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_backend import MujocoFlyBrowserViewerBackend

    checkpoint_dir = tmp_path / "walking"
    checkpoint_dir.mkdir()
    (checkpoint_dir / "saved_model.pb").write_bytes(b"model")
    env = _FakeEnv()

    backend = MujocoFlyBrowserViewerBackend(
        checkpoint_path=checkpoint_dir,
        env_factory=lambda: env,
        policy_loader=lambda _path: object(),
        distribution_inferer=lambda _policy, _observation: ([0.25], [0.1]),
    )

    paused_payload = backend.current_viewer_state()
    assert paused_payload["running_state"] == "paused"
    assert env.step_calls == 0

    backend.start()
    running_payload = backend.current_viewer_state()

    assert env.step_calls == 1
    assert running_payload["running_state"] == "running"
    assert running_payload["sim_time"] == 0.02
    assert running_payload["body_poses"][1]["position"][0] == 0.25


def test_browser_viewer_backend_start_rejects_missing_checkpoint(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_backend import MujocoFlyBrowserViewerBackend

    backend = MujocoFlyBrowserViewerBackend(
        checkpoint_path=None,
        env_factory=lambda: _FakeEnv(),
    )

    try:
        backend.start()
    except RuntimeError as exc:
        assert "checkpoint" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("backend.start() should fail without a checkpoint-backed policy")
