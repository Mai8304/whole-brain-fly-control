from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np


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
class MujocoFlyBrowserViewerBackend:
    checkpoint_path: Path | None
    env_factory: Callable[[], Any] = _default_walk_imitation_env_factory
    policy_loader: Callable[[Path], object] = _default_policy_loader
    distribution_inferer: Callable[[object, Mapping[str, Any]], tuple[list[float], list[float]]] = (
        _default_distribution_inferer
    )
    environment: Any = field(init=False)
    policy: object | None = field(init=False, default=None)
    timestep: Any = field(init=False)
    running: bool = field(init=False, default=False)
    current_camera: str = field(init=False, default="track")
    frame_id: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.environment = self.env_factory()
        if self.checkpoint_path is not None and (self.checkpoint_path / "saved_model.pb").exists():
            self.policy = self.policy_loader(self.checkpoint_path)
        self.timestep = self.environment.reset()

    def start(self) -> None:
        if self.policy is None:
            raise RuntimeError("Official walking policy checkpoint is unavailable")
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.running = False
        self.timestep = self.environment.reset()
        self.frame_id = 0

    def current_viewer_state(self) -> dict[str, object]:
        if self.running:
            self._step_once()
        self.frame_id += 1
        return {
            "frame_id": self.frame_id,
            "sim_time": float(getattr(self.environment.physics.data, "time", 0.0)),
            "running_state": "running" if self.running else "paused",
            "current_camera": self.current_camera,
            "scene_version": "flybody-walk-imitation-v1",
            "body_poses": _extract_body_poses(self.environment.physics),
            "geom_poses": _extract_geom_poses(self.environment.physics),
        }

    def close(self) -> None:
        self.running = False

    def _step_once(self) -> None:
        if self.policy is None:
            raise RuntimeError("Official walking policy checkpoint is unavailable")
        mean, _std = self.distribution_inferer(self.policy, self.timestep.observation)
        self.timestep = self.environment.step(np.asarray(mean, dtype=float))
        last = getattr(self.timestep, "last", None)
        if callable(last) and bool(last()):
            self.timestep = self.environment.reset()


def _extract_body_poses(physics: Any) -> list[dict[str, object]]:
    xpos = physics.named.data.xpos
    xquat = physics.named.data.xquat
    row_names = getattr(getattr(xpos, "axes", None), "row", None)
    if row_names is None or not hasattr(row_names, "names"):
        raise RuntimeError("Official flybody physics does not expose named body poses")

    body_poses: list[dict[str, object]] = []
    for body_name in row_names.names:
        if not isinstance(body_name, str) or not body_name or body_name == "world":
            continue
        body_poses.append(
            {
                "body_name": body_name,
                "position": [float(value) for value in xpos[body_name]],
                "quaternion": [float(value) for value in xquat[body_name]],
            }
        )
    return body_poses


def _extract_geom_poses(physics: Any) -> list[dict[str, object]]:
    geom_xpos = physics.named.data.geom_xpos
    geom_xmat = physics.named.data.geom_xmat
    row_names = getattr(getattr(geom_xpos, "axes", None), "row", None)
    if row_names is None or not hasattr(row_names, "names"):
        raise RuntimeError("Official flybody physics does not expose named geom poses")

    geom_poses: list[dict[str, object]] = []
    for geom_name in row_names.names:
        if not isinstance(geom_name, str) or not geom_name or geom_name == "groundplane":
            continue
        geom_poses.append(
            {
                "geom_name": geom_name,
                "position": [float(value) for value in geom_xpos[geom_name]],
                "rotation_matrix": [float(value) for value in geom_xmat[geom_name]],
            }
        )
    return geom_poses
