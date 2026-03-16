from __future__ import annotations

from pathlib import Path

import numpy as np

from fruitfly.evaluation.inspector_trace import dump_replay_trace, load_replay_trace


def test_dump_and_load_replay_trace_round_trips_session_state_and_neural_arrays(tmp_path: Path) -> None:
    trace_dir = tmp_path / "trace"
    dump_replay_trace(
        output_dir=trace_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_completed": 2,
        },
        state_arrays={
            "step_id": np.asarray([0, 1], dtype=np.int64),
            "qpos": np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([0, 1], dtype=np.int64),
            "node_activity": np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
        },
        events=[{"step_id": 1, "event_type": "rollout_completed"}],
    )

    payload = load_replay_trace(trace_dir)

    assert payload.session["default_camera"] == "follow"
    assert payload.state_arrays["qpos"].shape == (2, 2)
    assert payload.neural_arrays["node_activity"].shape == (2, 2)
    assert payload.events[0]["event_type"] == "rollout_completed"
