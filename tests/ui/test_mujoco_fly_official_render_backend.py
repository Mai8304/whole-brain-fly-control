from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


class _FakeTimeStep:
    def __init__(self, observation: dict[str, np.ndarray]) -> None:
        self.observation = observation
        self.reward = 1.0

    def last(self) -> bool:
        return False


class _FakePhysics:
    def __init__(self, env: "_FakeEnv") -> None:
        self._env = env

    def render(self, *, width: int, height: int, camera_id: str) -> np.ndarray:
        value = self._env.frame_value
        frame = np.full((height, width, 3), fill_value=value, dtype=np.uint8)
        if camera_id.endswith("side"):
            frame[:, :, 1] = min(255, value + 1)
        return frame


class _FakeEnv:
    def __init__(self) -> None:
        self.physics = _FakePhysics(self)
        self.frame_value = 16
        self.reset_calls = 0
        self.step_calls = 0

    def reset(self) -> _FakeTimeStep:
        self.reset_calls += 1
        self.frame_value = 16
        return _FakeTimeStep({"walker/joints_pos": np.asarray([0.0], dtype=np.float32)})

    def step(self, action: np.ndarray) -> _FakeTimeStep:
        self.step_calls += 1
        self.frame_value = 16 + self.step_calls
        return _FakeTimeStep({"walker/joints_pos": np.asarray([float(action[0])], dtype=np.float32)})


def _decode_first_pixel(payload: bytes) -> tuple[int, int, int]:
    import io

    image = Image.open(io.BytesIO(payload))
    pixel = image.convert("RGB").getpixel((0, 0))
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def test_official_render_backend_only_steps_when_running(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_backend import MujocoFlyOfficialRenderBackend

    checkpoint_dir = tmp_path / "walking"
    checkpoint_dir.mkdir()

    env = _FakeEnv()

    backend = MujocoFlyOfficialRenderBackend(
        checkpoint_path=checkpoint_dir,
        env_factory=lambda: env,
        policy_loader=lambda _path: object(),
        distribution_inferer=lambda _policy, _observation: ([0.25], [0.1]),
    )

    paused_payload = backend.render_frame(width=32, height=24, camera_id="walker/track1")

    assert env.step_calls == 0
    assert _decode_first_pixel(paused_payload)[0] == 16

    backend.start()
    running_payload = backend.render_frame(width=32, height=24, camera_id="walker/track1")

    assert env.step_calls == 1
    assert _decode_first_pixel(running_payload)[0] == 17


def test_official_render_backend_reset_restores_initial_pose_and_pauses(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_backend import MujocoFlyOfficialRenderBackend

    checkpoint_dir = tmp_path / "walking"
    checkpoint_dir.mkdir()

    env = _FakeEnv()

    backend = MujocoFlyOfficialRenderBackend(
        checkpoint_path=checkpoint_dir,
        env_factory=lambda: env,
        policy_loader=lambda _path: object(),
        distribution_inferer=lambda _policy, _observation: ([0.5], [0.1]),
    )

    backend.start()
    backend.render_frame(width=32, height=24, camera_id="walker/track1")
    backend.reset()
    reset_payload = backend.render_frame(width=32, height=24, camera_id="walker/side")

    assert env.reset_calls >= 2
    assert env.step_calls == 1
    assert abs(_decode_first_pixel(reset_payload)[0] - 16) <= 2
