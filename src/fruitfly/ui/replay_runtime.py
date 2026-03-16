from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fruitfly.evaluation.inspector_trace import ReplayTracePayload, load_replay_trace

ALLOWED_CAMERA_PRESETS = {"follow", "side", "top", "front-quarter"}
ALLOWED_STATUSES = {"paused", "playing"}


@dataclass
class ReplayRuntime:
    eval_dir: Path
    trace: ReplayTracePayload
    summary_payload: dict[str, Any]
    current_step: int
    status: str = "paused"
    speed: float = 1.0
    camera_preset: str = "follow"
    renderer: Any | None = None

    @classmethod
    def from_eval_dir_with_options(
        cls,
        eval_dir: Path,
        *,
        renderer: Any | None = None,
    ) -> "ReplayRuntime":
        trace = load_replay_trace(eval_dir)
        summary_path = eval_dir / "summary.json"
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
        step_ids = _step_ids(trace.state_arrays)
        current_step = int(step_ids[0]) if step_ids.size else 0
        return cls(
            eval_dir=eval_dir,
            trace=trace,
            summary_payload=summary_payload,
            current_step=current_step,
            status="paused",
            speed=1.0,
            camera_preset=str(trace.session.get("default_camera", "follow")),
            renderer=renderer,
        )

    @classmethod
    def from_eval_dir(
        cls,
        eval_dir: Path,
        *,
        renderer: Any | None = None,
    ) -> "ReplayRuntime":
        return cls.from_eval_dir_with_options(eval_dir, renderer=renderer)

    def play(self) -> None:
        self.status = "playing"

    def pause(self) -> None:
        self.status = "paused"

    def set_speed(self, speed: float) -> None:
        self.speed = float(speed)

    def set_camera(self, camera_preset: str) -> None:
        if camera_preset not in ALLOWED_CAMERA_PRESETS:
            raise ValueError(f"Unsupported replay camera preset: {camera_preset}")
        self.camera_preset = camera_preset

    def seek(self, step: int) -> None:
        step_ids = _step_ids(self.trace.state_arrays)
        if step not in set(int(value) for value in step_ids.tolist()):
            raise ValueError(f"Replay step {step} is not available")
        self.current_step = int(step)

    def next_step(self) -> None:
        self.current_step = self._adjacent_step(direction=1)

    def prev_step(self) -> None:
        self.current_step = self._adjacent_step(direction=-1)

    def current_summary(self) -> dict[str, Any]:
        index = self._current_index()
        payload = dict(self.summary_payload)
        payload.update(
            {
                "step_id": self.current_step,
                "reward": float(self.trace.state_arrays["reward"][index]),
                "forward_velocity": float(self.trace.state_arrays["forward_velocity"][index]),
                "body_upright": float(self.trace.state_arrays["body_upright"][index]),
                "terminated": bool(self.trace.state_arrays["terminated"][index]),
            }
        )
        return payload

    def current_brain_payload(self) -> dict[str, Any]:
        index = self._current_neural_index()
        return {
            "step_id": self.current_step,
            "afferent_activity": float(self.trace.neural_arrays["afferent_activity"][index]),
            "intrinsic_activity": float(self.trace.neural_arrays["intrinsic_activity"][index]),
            "efferent_activity": float(self.trace.neural_arrays["efferent_activity"][index]),
            "node_activity": self.trace.neural_arrays["node_activity"][index],
        }

    def render_current_frame(self) -> Any:
        if self.renderer is None:
            raise RuntimeError("Replay renderer is not configured")
        return self.renderer.render_frame(step=self.current_step, camera=self.camera_preset)

    def _current_index(self) -> int:
        return _index_for_step(self.trace.state_arrays, self.current_step)

    def _current_neural_index(self) -> int:
        return _index_for_step(self.trace.neural_arrays, self.current_step)

    def _adjacent_step(self, *, direction: int) -> int:
        step_ids = [int(value) for value in _step_ids(self.trace.state_arrays).tolist()]
        if not step_ids:
            return 0
        current_idx = step_ids.index(self.current_step)
        next_idx = max(0, min(len(step_ids) - 1, current_idx + direction))
        return step_ids[next_idx]


def _step_ids(arrays: dict[str, np.ndarray]) -> np.ndarray:
    return np.asarray(arrays.get("step_id", np.asarray([], dtype=np.int64)), dtype=np.int64)


def _index_for_step(arrays: dict[str, np.ndarray], step: int) -> int:
    step_ids = _step_ids(arrays)
    matches = np.nonzero(step_ids == int(step))[0]
    if matches.size == 0:
        raise ValueError(f"Replay step {step} is not available")
    return int(matches[0])
