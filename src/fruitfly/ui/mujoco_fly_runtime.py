from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fruitfly.ui.mujoco_fly_contract import build_unavailable_viewer_state


@dataclass(frozen=True, slots=True)
class MujocoFlyRuntimeConfig:
    scene_dir: Path | None = None
    policy_checkpoint_path: Path | None = None


@dataclass
class MujocoFlyRuntime:
    config: MujocoFlyRuntimeConfig
    available: bool
    status: str
    reason: str | None
    scene_version: str

    def session_payload(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "status": self.status,
            "reason": self.reason,
            "scene_version": self.scene_version,
            "scene_dir": str(self.config.scene_dir) if self.config.scene_dir is not None else None,
            "policy_checkpoint_path": (
                str(self.config.policy_checkpoint_path)
                if self.config.policy_checkpoint_path is not None
                else None
            ),
        }

    def current_viewer_state(self) -> dict[str, Any]:
        if not self.available:
            return build_unavailable_viewer_state(
                reason=self.reason,
                scene_version=self.scene_version,
            )
        return {
            "frame_id": 0,
            "sim_time": 0.0,
            "running_state": self.status,
            "scene_version": self.scene_version,
            "body_poses": [],
        }

    def start(self) -> None:
        if not self.available:
            raise RuntimeError(f"Official MuJoCo fly runtime is unavailable: {self.reason}")
        raise RuntimeError("Official MuJoCo fly runtime start is not implemented")

    def pause(self) -> None:
        if not self.available:
            raise RuntimeError(f"Official MuJoCo fly runtime is unavailable: {self.reason}")
        self.status = "paused"

    def reset(self) -> None:
        if not self.available:
            raise RuntimeError(f"Official MuJoCo fly runtime is unavailable: {self.reason}")
        self.status = "paused"


def create_mujoco_fly_runtime(config: MujocoFlyRuntimeConfig) -> MujocoFlyRuntime:
    scene_version = _load_scene_version(config.scene_dir)

    if config.scene_dir is None or not config.scene_dir.exists():
        return MujocoFlyRuntime(
            config=config,
            available=False,
            status="unavailable",
            reason="Official walk scene bundle is unavailable",
            scene_version=scene_version,
        )

    manifest_path = config.scene_dir / "manifest.json"
    if not manifest_path.exists():
        return MujocoFlyRuntime(
            config=config,
            available=False,
            status="unavailable",
            reason="Official walk scene manifest is unavailable",
            scene_version=scene_version,
        )

    if config.policy_checkpoint_path is None or not config.policy_checkpoint_path.exists():
        return MujocoFlyRuntime(
            config=config,
            available=False,
            status="unavailable",
            reason="Official walking policy checkpoint is unavailable",
            scene_version=scene_version,
        )

    return MujocoFlyRuntime(
        config=config,
        available=False,
        status="unavailable",
        reason="Official MuJoCo fly runtime is not initialized",
        scene_version=scene_version,
    )


def _load_scene_version(scene_dir: Path | None) -> str:
    if scene_dir is None:
        return "unavailable"
    manifest_path = scene_dir / "manifest.json"
    if not manifest_path.exists():
        return "unavailable"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return "unavailable"
    scene_version = payload.get("scene_version")
    if isinstance(scene_version, str) and scene_version:
        return scene_version
    return "unavailable"
