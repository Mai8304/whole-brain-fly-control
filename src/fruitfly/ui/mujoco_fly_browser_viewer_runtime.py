from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
    validate_browser_viewer_bootstrap_payload,
    validate_browser_viewer_pose_payload,
    validate_browser_viewer_session_payload,
    build_unavailable_browser_viewer_pose_payload,
)


class BrowserViewerBackend(Protocol):
    def start(self) -> None: ...

    def pause(self) -> None: ...

    def reset(self) -> None: ...

    def current_viewer_state(self) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class MujocoFlyBrowserViewerRuntimeConfig:
    scene_dir: Path | None = None
    policy_checkpoint_path: Path | None = None
    default_camera: str = "track"


@dataclass
class MujocoFlyBrowserViewerRuntime:
    config: MujocoFlyBrowserViewerRuntimeConfig
    scene_version: str
    available: bool
    running_state: str
    checkpoint_loaded: bool
    current_camera: str
    reason: str | None
    _bootstrap_payload: dict[str, Any]
    backend: BrowserViewerBackend | None = None

    def bootstrap_payload(self) -> dict[str, Any]:
        payload = dict(self._bootstrap_payload)
        payload["checkpoint_loaded"] = self.checkpoint_loaded
        return validate_browser_viewer_bootstrap_payload(payload)

    def session_payload(self) -> dict[str, Any]:
        return validate_browser_viewer_session_payload(
            {
                "available": self.available,
                "running_state": self.running_state,
                "checkpoint_loaded": self.checkpoint_loaded,
                "current_camera": self.current_camera,
                "scene_version": self.scene_version,
                "reason": self.reason,
            }
        )

    def current_viewer_state(self) -> dict[str, Any]:
        backend = self.backend
        if not self.available or backend is None:
            return build_unavailable_browser_viewer_pose_payload(
                reason=self.reason,
                scene_version=self.scene_version,
                current_camera=self.current_camera,
            )

        payload = dict(backend.current_viewer_state())
        payload.setdefault("scene_version", self.scene_version)
        payload.setdefault("current_camera", self.current_camera)
        if self.reason:
            payload.setdefault("reason", self.reason)
        normalized = validate_browser_viewer_pose_payload(payload)
        self.running_state = normalized["running_state"]
        self.current_camera = normalized["current_camera"]
        return normalized

    def start(self) -> None:
        backend = self._require_backend()
        if not self.checkpoint_loaded:
            raise RuntimeError("Official walking policy checkpoint is unavailable")
        backend.start()
        self.running_state = "running"
        self.reason = None

    def pause(self) -> None:
        backend = self._require_backend()
        backend.pause()
        self.running_state = "paused"

    def reset(self) -> None:
        backend = self._require_backend()
        backend.reset()
        self.running_state = "paused"

    def _require_backend(self) -> BrowserViewerBackend:
        if not self.available or self.backend is None:
            raise RuntimeError(f"Official MuJoCo browser viewer runtime is unavailable: {self.reason}")
        return self.backend


PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RUNTIME_MODE = "official-flybody-browser-viewer"


def create_mujoco_fly_browser_viewer_runtime(
    config: MujocoFlyBrowserViewerRuntimeConfig,
    *,
    backend_factory: Callable[[MujocoFlyBrowserViewerRuntimeConfig], BrowserViewerBackend] | None = None,
) -> MujocoFlyBrowserViewerRuntime:
    resolved_checkpoint_path = _resolve_browser_viewer_policy_checkpoint_path(
        config.policy_checkpoint_path,
        root=PROJECT_ROOT,
    )
    effective_config = MujocoFlyBrowserViewerRuntimeConfig(
        scene_dir=config.scene_dir,
        policy_checkpoint_path=resolved_checkpoint_path,
        default_camera=config.default_camera,
    )
    scene_version = _load_scene_version(effective_config.scene_dir)

    if effective_config.scene_dir is None or not effective_config.scene_dir.exists():
        return _unavailable_runtime(
            config=effective_config,
            scene_version=scene_version,
            reason="Official walk scene bundle is unavailable",
        )

    manifest_path = effective_config.scene_dir / "manifest.json"
    if not manifest_path.exists():
        return _unavailable_runtime(
            config=effective_config,
            scene_version=scene_version,
            reason="Official walk scene manifest is unavailable",
        )

    manifest = _read_manifest(manifest_path)
    bootstrap_payload = _build_bootstrap_payload(
        scene_dir=effective_config.scene_dir,
        manifest=manifest,
        checkpoint_loaded=bool(
            effective_config.policy_checkpoint_path is not None
            and effective_config.policy_checkpoint_path.exists()
        ),
        default_camera=effective_config.default_camera,
    )

    if backend_factory is None:
        return _unavailable_runtime(
            config=effective_config,
            scene_version=scene_version,
            reason="Official MuJoCo browser viewer backend is unavailable",
            checkpoint_loaded=bootstrap_payload["checkpoint_loaded"],
            bootstrap_payload=bootstrap_payload,
        )

    backend = backend_factory(effective_config)
    checkpoint_loaded = bootstrap_payload["checkpoint_loaded"]
    reason = None if checkpoint_loaded else "Official walking policy checkpoint is unavailable"
    return MujocoFlyBrowserViewerRuntime(
        config=effective_config,
        scene_version=scene_version,
        available=True,
        running_state="paused",
        checkpoint_loaded=checkpoint_loaded,
        current_camera=effective_config.default_camera,
        reason=reason,
        _bootstrap_payload=bootstrap_payload,
        backend=backend,
    )


def _unavailable_runtime(
    *,
    config: MujocoFlyBrowserViewerRuntimeConfig,
    scene_version: str,
    reason: str,
    checkpoint_loaded: bool = False,
    bootstrap_payload: dict[str, Any] | None = None,
) -> MujocoFlyBrowserViewerRuntime:
    payload = bootstrap_payload or {
        "scene_version": scene_version,
        "runtime_mode": _RUNTIME_MODE,
        "entry_xml": "walk_imitation.xml",
        "checkpoint_loaded": checkpoint_loaded,
        "default_camera": config.default_camera,
        "camera_presets": ["track", "side", "back", "top"],
        "body_manifest": [],
        "geom_manifest": [],
    }
    return MujocoFlyBrowserViewerRuntime(
        config=config,
        scene_version=scene_version,
        available=False,
        running_state="unavailable",
        checkpoint_loaded=checkpoint_loaded,
        current_camera=config.default_camera,
        reason=reason,
        _bootstrap_payload=payload,
    )


def _build_bootstrap_payload(
    *,
    scene_dir: Path,
    manifest: dict[str, Any],
    checkpoint_loaded: bool,
    default_camera: str,
) -> dict[str, Any]:
    geom_manifest_raw = manifest.get("geom_manifest")
    body_manifest_raw = manifest.get("body_manifest")
    if not isinstance(geom_manifest_raw, list) or not isinstance(body_manifest_raw, list):
        raise ValueError("Official walk scene manifest is missing body/geom manifests")

    geom_manifest: list[dict[str, Any]] = []
    for entry in geom_manifest_raw:
        if not isinstance(entry, dict):
            raise ValueError("geom manifest entry must be an object")
        asset_path = entry.get("mesh_asset_path")
        if not isinstance(asset_path, str) or not asset_path:
            raise ValueError("geom manifest entry is missing mesh_asset_path")
        geom_manifest.append(
            {
                "geom_name": str(entry["geom_name"]),
                "body_name": str(entry["body_name"]),
                "mesh_asset": _public_asset_url(scene_dir / asset_path),
                "mesh_scale": [float(value) for value in entry["mesh_scale"]],
                "local_position": [float(value) for value in entry["local_position"]],
                "local_quaternion": [float(value) for value in entry["local_quaternion"]],
            }
        )

    camera_presets = manifest.get("camera_presets")
    if not isinstance(camera_presets, list) or not camera_presets:
        camera_presets = ["track", "side", "back", "top"]

    return validate_browser_viewer_bootstrap_payload(
        {
            "scene_version": str(manifest.get("scene_version") or "unavailable"),
            "runtime_mode": _RUNTIME_MODE,
            "entry_xml": str(manifest.get("entry_xml") or "walk_imitation.xml"),
            "checkpoint_loaded": checkpoint_loaded,
            "default_camera": default_camera,
            "camera_presets": [str(value) for value in camera_presets],
            "body_manifest": body_manifest_raw,
            "geom_manifest": geom_manifest,
        }
    )


def _public_asset_url(path: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(_public_root().resolve())
    except ValueError as exc:
        raise ValueError(
            f"Official walk asset {resolved} is outside the public asset root {_public_root().resolve()}"
        ) from exc
    return "/" + relative.as_posix()


def _public_root() -> Path:
    return PROJECT_ROOT / "apps" / "neural-console" / "public"


def _read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_browser_viewer_policy_checkpoint_path(
    checkpoint_path: Path | None,
    *,
    root: Path,
) -> Path | None:
    if checkpoint_path is not None:
        return checkpoint_path

    base = root / "outputs" / "flybody-data" / "trained-fly-policies"
    direct_model = base / "saved_model.pb"
    if direct_model.exists():
        return base

    nested_walking_model = base / "walking" / "saved_model.pb"
    if nested_walking_model.exists():
        return nested_walking_model.parent

    return None


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
