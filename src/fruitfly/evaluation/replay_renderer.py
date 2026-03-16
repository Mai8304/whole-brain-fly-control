from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from fruitfly.evaluation.inspector_trace import ReplayTracePayload, load_replay_trace

CAMERA_PRESET_TO_RENDER_ID = {
    "follow": "walker/track1",
    "side": "walker/side",
    "top": "top_camera",
    "front-quarter": "walker/hero",
}


@dataclass(frozen=True)
class RenderedReplayFrame:
    bytes: bytes
    content_type: str
    step_id: int
    camera: str
    width: int
    height: int


@dataclass
class ReplayRenderer:
    eval_dir: Path
    trace: ReplayTracePayload
    environment: Any
    render_width: int = 640
    render_height: int = 480

    @classmethod
    def from_eval_dir(
        cls,
        eval_dir: Path,
        *,
        env_factory: object | None = None,
        render_width: int = 640,
        render_height: int = 480,
    ) -> "ReplayRenderer":
        trace = load_replay_trace(eval_dir)
        environment = (env_factory or _require_walk_imitation_env_factory())()
        return cls(
            eval_dir=eval_dir,
            trace=trace,
            environment=environment,
            render_width=render_width,
            render_height=render_height,
        )

    def render_frame(self, *, step: int, camera: str) -> RenderedReplayFrame:
        if camera not in CAMERA_PRESET_TO_RENDER_ID:
            raise ValueError(f"Unsupported replay camera preset: {camera}")

        index = _index_for_step(self.trace.state_arrays, step)
        self._restore_state(index=index)
        frame = self._render(camera=camera)
        return RenderedReplayFrame(
            bytes=_encode_jpeg(frame),
            content_type="image/jpeg",
            step_id=int(step),
            camera=camera,
            width=int(frame.shape[1]),
            height=int(frame.shape[0]),
        )

    def _restore_state(self, *, index: int) -> None:
        physics = getattr(self.environment, "physics", None)
        if physics is None:
            raise RuntimeError("Replay environment does not expose physics")
        data = getattr(physics, "data", None)
        if data is None:
            raise RuntimeError("Replay environment physics does not expose data")

        data.qpos = np.asarray(self.trace.state_arrays["qpos"][index], dtype=np.float64).copy()
        data.qvel = np.asarray(self.trace.state_arrays["qvel"][index], dtype=np.float64).copy()
        data.ctrl = np.asarray(self.trace.state_arrays["ctrl"][index], dtype=np.float64).copy()

        sim_times = self.trace.state_arrays.get("sim_time")
        if sim_times is not None and index < len(sim_times):
            try:
                data.time = float(sim_times[index])
            except Exception:
                pass

        forward = getattr(physics, "forward", None)
        if callable(forward):
            forward()

    def _render(self, *, camera: str) -> np.ndarray:
        physics = getattr(self.environment, "physics", None)
        render = getattr(physics, "render", None)
        if not callable(render):
            raise RuntimeError("Replay environment physics does not support render()")
        frame = render(
            width=self.render_width,
            height=self.render_height,
            camera_id=CAMERA_PRESET_TO_RENDER_ID[camera],
        )
        return np.asarray(frame, dtype=np.uint8)


def _require_walk_imitation_env_factory() -> object:
    try:
        from flybody.fly_envs import walk_imitation
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "flybody is not installed in the current environment. Replay rendering requires the dedicated flybody environment."
        ) from exc
    return walk_imitation


def _index_for_step(arrays: dict[str, np.ndarray], step: int) -> int:
    step_ids = np.asarray(arrays.get("step_id", np.asarray([], dtype=np.int64)), dtype=np.int64)
    matches = np.nonzero(step_ids == int(step))[0]
    if matches.size == 0:
        raise ValueError(f"Replay step {step} is not available")
    return int(matches[0])


def _encode_jpeg(frame: np.ndarray) -> bytes:
    image = Image.fromarray(np.asarray(frame, dtype=np.uint8), mode="RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
