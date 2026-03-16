from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from fruitfly.evaluation.inspector_trace import dump_replay_trace
from fruitfly.ui.replay_runtime import ReplayRuntime


def test_replay_runtime_uses_one_shared_step_cursor_for_body_brain_and_summary(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_completed": 4,
            "steps_requested": 4,
        },
        state_arrays={
            "step_id": np.asarray([1, 2, 3, 4], dtype=np.int64),
            "reward": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
            "forward_velocity": np.asarray([0.4, 0.3, 0.2, 0.1], dtype=np.float64),
            "body_upright": np.asarray([0.9, 0.91, 0.92, 0.93], dtype=np.float64),
            "terminated": np.asarray([False, False, False, True], dtype=bool),
            "qpos": np.zeros((4, 2), dtype=np.float64),
            "qvel": np.zeros((4, 2), dtype=np.float64),
            "ctrl": np.zeros((4, 2), dtype=np.float64),
            "sim_time": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1, 2, 3, 4], dtype=np.int64),
            "node_activity": np.asarray(
                [
                    [0.1, 0.2],
                    [0.2, 0.3],
                    [0.3, 0.4],
                    [0.4, 0.5],
                ],
                dtype=np.float32,
            ),
            "afferent_activity": np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.2, 0.3, 0.4, 0.5], dtype=np.float32),
            "efferent_activity": np.asarray([0.3, 0.4, 0.5, 0.6], dtype=np.float32),
        },
        events=[{"step_id": 4, "event_type": "rollout_completed"}],
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "steps_requested": 4,
                "steps_completed": 4,
                "reward_mean": 0.25,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    runtime = ReplayRuntime.from_eval_dir(eval_dir)

    runtime.seek(3)

    assert runtime.current_step == 3
    assert runtime.current_summary()["step_id"] == 3
    assert runtime.current_brain_payload()["step_id"] == 3

    runtime.next_step()
    assert runtime.current_step == 4

    runtime.prev_step()
    assert runtime.current_step == 3

    runtime.set_speed(2.0)
    runtime.set_camera("top")
    runtime.play()
    assert runtime.status == "playing"
    assert runtime.speed == 2.0
    assert runtime.camera_preset == "top"

    runtime.pause()
    assert runtime.status == "paused"


def test_replay_runtime_delegates_current_frame_render_to_renderer(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_completed": 2,
            "steps_requested": 2,
        },
        state_arrays={
            "step_id": np.asarray([1, 2], dtype=np.int64),
            "reward": np.asarray([0.1, 0.2], dtype=np.float64),
            "forward_velocity": np.asarray([0.4, 0.5], dtype=np.float64),
            "body_upright": np.asarray([0.8, 0.9], dtype=np.float64),
            "terminated": np.asarray([False, True], dtype=bool),
            "qpos": np.zeros((2, 2), dtype=np.float64),
            "qvel": np.zeros((2, 2), dtype=np.float64),
            "ctrl": np.zeros((2, 2), dtype=np.float64),
            "sim_time": np.asarray([0.1, 0.2], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1, 2], dtype=np.int64),
            "node_activity": np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
            "afferent_activity": np.asarray([0.1, 0.3], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.2, 0.4], dtype=np.float32),
            "efferent_activity": np.asarray([0.0, 0.0], dtype=np.float32),
        },
        events=[],
    )

    class FakeRenderer:
        def __init__(self) -> None:
            self.calls: list[tuple[int, str]] = []

        def render_frame(self, *, step: int, camera: str):
            self.calls.append((step, camera))
            return {"step_id": step, "camera": camera}

    renderer = FakeRenderer()
    runtime = ReplayRuntime.from_eval_dir(eval_dir, renderer=renderer)
    runtime.seek(2)
    runtime.set_camera("side")

    frame = runtime.render_current_frame()

    assert frame == {"step_id": 2, "camera": "side"}
    assert renderer.calls == [(2, "side")]
