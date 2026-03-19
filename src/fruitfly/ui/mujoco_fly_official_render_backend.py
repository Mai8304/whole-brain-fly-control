from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
from PIL import Image


def _default_walk_imitation_env_factory() -> Any:
    from flybody.fly_envs import walk_imitation

    return walk_imitation()


def _default_policy_loader(checkpoint_path: Path) -> object:
    from fruitfly.adapters.flybody_export import _load_saved_model_policy

    return _load_saved_model_policy(checkpoint_path)


def _default_distribution_inferer(
    policy: object,
    observation: Mapping[str, Any],
) -> tuple[list[float], list[float]]:
    from fruitfly.adapters.flybody_export import _infer_distribution

    return _infer_distribution(policy, observation)


@dataclass
class MujocoFlyOfficialRenderBackend:
    checkpoint_path: Path
    env_factory: Callable[[], Any] = _default_walk_imitation_env_factory
    policy_loader: Callable[[Path], object] = _default_policy_loader
    distribution_inferer: Callable[[object, Mapping[str, Any]], tuple[list[float], list[float]]] = (
        _default_distribution_inferer
    )
    environment: Any = field(init=False)
    policy: object = field(init=False)
    timestep: Any = field(init=False)
    running: bool = field(init=False, default=False)
    current_camera_id: str = field(init=False, default="walker/track1")

    def __post_init__(self) -> None:
        self.environment = self.env_factory()
        self.policy = self.policy_loader(self.checkpoint_path)
        self.timestep = self.environment.reset()

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.running = False
        self.timestep = self.environment.reset()

    def set_camera_preset(self, camera_id: str) -> None:
        self.current_camera_id = str(camera_id)

    def render_frame(self, *, width: int, height: int, camera_id: str) -> bytes:
        self.current_camera_id = str(camera_id)
        if self.running:
            self._step_once()
        physics = getattr(self.environment, "physics", None)
        render = getattr(physics, "render", None)
        if not callable(render):
            raise RuntimeError("Official flybody environment physics does not support render()")
        frame = render(
            width=int(width),
            height=int(height),
            camera_id=self.current_camera_id,
        )
        return _encode_jpeg(np.asarray(frame, dtype=np.uint8))

    def close(self) -> None:
        self.running = False

    def _step_once(self) -> None:
        mean, _std = self.distribution_inferer(self.policy, self.timestep.observation)
        self.timestep = self.environment.step(np.asarray(mean, dtype=float))
        last = getattr(self.timestep, "last", None)
        if callable(last) and bool(last()):
            self.timestep = self.environment.reset()


def _encode_jpeg(frame: np.ndarray) -> bytes:
    image = Image.fromarray(np.asarray(frame, dtype=np.uint8), mode="RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
