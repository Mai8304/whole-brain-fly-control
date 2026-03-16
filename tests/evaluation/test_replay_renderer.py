from __future__ import annotations

from pathlib import Path

import numpy as np

from fruitfly.evaluation.inspector_trace import dump_replay_trace
from fruitfly.evaluation.replay_renderer import ReplayRenderer


def test_replay_renderer_renders_same_step_from_different_presets(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_completed": 4,
        },
        state_arrays={
            "step_id": np.asarray([1, 2, 3, 4], dtype=np.int64),
            "sim_time": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
            "qpos": np.asarray([[0.0, 1.0], [2.0, 3.0], [4.0, 5.0], [6.0, 7.0]], dtype=np.float64),
            "qvel": np.asarray([[0.5, 1.5], [2.5, 3.5], [4.5, 5.5], [6.5, 7.5]], dtype=np.float64),
            "ctrl": np.asarray([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]], dtype=np.float64),
            "reward": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
            "terminated": np.asarray([False, False, False, True], dtype=bool),
            "body_upright": np.asarray([0.9, 0.91, 0.92, 0.93], dtype=np.float64),
            "forward_velocity": np.asarray([0.4, 0.3, 0.2, 0.1], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1, 2, 3, 4], dtype=np.int64),
            "node_activity": np.asarray([[0.1, 0.2], [0.2, 0.3], [0.3, 0.4], [0.4, 0.5]], dtype=np.float32),
            "afferent_activity": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.2, 0.3, 0.4, 0.5], dtype=np.float32),
            "efferent_activity": np.asarray([0.3, 0.4, 0.5, 0.6], dtype=np.float32),
        },
        events=[{"step_id": 4, "event_type": "rollout_completed"}],
    )

    class FakePhysicsData:
        def __init__(self) -> None:
            self.qpos = np.zeros((2,), dtype=np.float64)
            self.qvel = np.zeros((2,), dtype=np.float64)
            self.ctrl = np.zeros((2,), dtype=np.float64)
            self.time = 0.0

    class FakePhysics:
        def __init__(self) -> None:
            self.data = FakePhysicsData()

        def forward(self) -> None:
            return None

        def render(self, *, width: int, height: int, camera_id: str | None = None):
            camera_value = {
                "walker/track1": 32,
                "walker/side": 96,
                "top_camera": 160,
                "walker/hero": 224,
            }[camera_id or "walker/track1"]
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[..., 0] = camera_value
            frame[..., 1] = int(self.data.qpos[0] * 10) % 255
            frame[..., 2] = int(self.data.qvel[0] * 10) % 255
            return frame

    class FakeEnv:
        def __init__(self) -> None:
            self.physics = FakePhysics()

    renderer = ReplayRenderer.from_eval_dir(eval_dir, env_factory=FakeEnv)

    side_frame = renderer.render_frame(step=4, camera="side")
    top_frame = renderer.render_frame(step=4, camera="top")

    assert side_frame.content_type == "image/jpeg"
    assert top_frame.content_type == "image/jpeg"
    assert side_frame.bytes != top_frame.bytes
    assert np.allclose(renderer.environment.physics.data.qpos, np.asarray([6.0, 7.0], dtype=np.float64))
    assert np.allclose(renderer.environment.physics.data.qvel, np.asarray([6.5, 7.5], dtype=np.float64))
    assert np.allclose(renderer.environment.physics.data.ctrl, np.asarray([0.7, 0.8], dtype=np.float64))
