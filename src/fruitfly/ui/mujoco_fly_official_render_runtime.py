from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from fruitfly.ui.mujoco_fly_official_render_contract import (
    official_render_camera_id_for_preset,
    validate_official_render_frame_request,
    validate_official_render_session_payload,
)


class OfficialRenderBackend(Protocol):
    def start(self) -> None: ...

    def pause(self) -> None: ...

    def reset(self) -> None: ...

    def set_camera_preset(self, camera_id: str) -> None: ...

    def render_frame(self, *, width: int, height: int, camera_id: str) -> bytes: ...


@dataclass(frozen=True, slots=True)
class MujocoFlyOfficialRenderRuntimeConfig:
    scene_dir: Path | None = None
    policy_checkpoint_path: Path | None = None
    default_camera: str = "track"


@dataclass(frozen=True, slots=True)
class RenderedOfficialFrame:
    bytes: bytes
    content_type: str
    camera: str
    width: int
    height: int


@dataclass
class MujocoFlyOfficialRenderRuntime:
    config: MujocoFlyOfficialRenderRuntimeConfig
    scene_version: str
    available: bool
    running_state: str
    checkpoint_loaded: bool
    current_camera: str
    reason: str | None
    backend: OfficialRenderBackend | None = None

    def session_payload(self) -> dict[str, Any]:
        return validate_official_render_session_payload(
            {
                "available": self.available,
                "running_state": self.running_state,
                "current_camera": self.current_camera,
                "checkpoint_loaded": self.checkpoint_loaded,
                "reason": self.reason,
            }
        )

    def start(self) -> None:
        backend = self._require_backend()
        backend.start()
        self.running_state = "running"
        self.reason = None

    def pause(self) -> None:
        backend = self._require_backend()
        backend.pause()
        self.running_state = "paused"
        self.reason = None

    def reset(self) -> None:
        backend = self._require_backend()
        backend.reset()
        self.running_state = "paused"
        self.reason = None

    def set_camera_preset(self, camera_preset: str) -> None:
        backend = self._require_backend()
        camera_id = official_render_camera_id_for_preset(camera_preset)
        backend.set_camera_preset(camera_id)
        self.current_camera = camera_preset
        self.reason = None

    def render_frame(self, *, width: int, height: int, camera: str | None = None) -> RenderedOfficialFrame:
        backend = self._require_backend()
        request = validate_official_render_frame_request(
            {
                "width": width,
                "height": height,
                "camera": camera or self.current_camera,
            }
        )
        camera_id = official_render_camera_id_for_preset(request["camera"])
        payload = bytes(
            backend.render_frame(
                width=request["width"],
                height=request["height"],
                camera_id=camera_id,
            )
        )
        self.current_camera = request["camera"]
        self.reason = None
        return RenderedOfficialFrame(
            bytes=payload,
            content_type="image/jpeg",
            camera=request["camera"],
            width=request["width"],
            height=request["height"],
        )

    def _require_backend(self) -> OfficialRenderBackend:
        if not self.available or self.backend is None:
            raise RuntimeError(f"Official MuJoCo fly render runtime is unavailable: {self.reason}")
        return self.backend


def create_mujoco_fly_official_render_runtime(
    config: MujocoFlyOfficialRenderRuntimeConfig,
    *,
    backend_factory: Callable[[MujocoFlyOfficialRenderRuntimeConfig], OfficialRenderBackend] | None = None,
) -> MujocoFlyOfficialRenderRuntime:
    scene_version = _load_scene_version(config.scene_dir)
    current_camera = config.default_camera

    if config.scene_dir is None or not config.scene_dir.exists():
        return MujocoFlyOfficialRenderRuntime(
            config=config,
            scene_version=scene_version,
            available=False,
            running_state="unavailable",
            checkpoint_loaded=False,
            current_camera=current_camera,
            reason="Official walk scene bundle is unavailable",
        )

    manifest_path = config.scene_dir / "manifest.json"
    if not manifest_path.exists():
        return MujocoFlyOfficialRenderRuntime(
            config=config,
            scene_version=scene_version,
            available=False,
            running_state="unavailable",
            checkpoint_loaded=False,
            current_camera=current_camera,
            reason="Official walk scene manifest is unavailable",
        )

    checkpoint_loaded = bool(
        config.policy_checkpoint_path is not None and config.policy_checkpoint_path.exists()
    )
    if not checkpoint_loaded:
        return MujocoFlyOfficialRenderRuntime(
            config=config,
            scene_version=scene_version,
            available=False,
            running_state="unavailable",
            checkpoint_loaded=False,
            current_camera=current_camera,
            reason="Official walking policy checkpoint is unavailable",
        )

    if backend_factory is None:
        return MujocoFlyOfficialRenderRuntime(
            config=config,
            scene_version=scene_version,
            available=False,
            running_state="unavailable",
            checkpoint_loaded=True,
            current_camera=current_camera,
            reason="Official MuJoCo render backend is unavailable",
        )

    official_render_camera_id_for_preset(current_camera)
    backend = backend_factory(config)
    return MujocoFlyOfficialRenderRuntime(
        config=config,
        scene_version=scene_version,
        available=True,
        running_state="paused",
        checkpoint_loaded=True,
        current_camera=current_camera,
        reason=None,
        backend=backend,
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
