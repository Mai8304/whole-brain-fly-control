from __future__ import annotations

from pathlib import Path

import pytest


class _FakeOfficialRenderBackend:
    def __init__(self) -> None:
        self.started = False
        self.paused = False
        self.reset_called = False
        self.current_camera = "walker/track1"
        self.last_render_camera = None

    def start(self) -> None:
        self.started = True
        self.paused = False

    def pause(self) -> None:
        self.paused = True

    def reset(self) -> None:
        self.reset_called = True
        self.paused = True

    def set_camera_preset(self, camera_id: str) -> None:
        self.current_camera = camera_id

    def render_frame(self, *, width: int, height: int, camera_id: str) -> bytes:
        self.last_render_camera = camera_id
        return f"{camera_id}:{width}x{height}".encode("utf-8")


def _materialize_scene_bundle(scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "manifest.json").write_text(
        '{"entry_xml":"walk_imitation.xml","scene_version":"flybody-walk-imitation-v1"}',
        encoding="utf-8",
    )


def test_official_render_runtime_reports_unavailable_when_checkpoint_missing(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_runtime import (
        MujocoFlyOfficialRenderRuntimeConfig,
        create_mujoco_fly_official_render_runtime,
    )

    scene_dir = tmp_path / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)

    runtime = create_mujoco_fly_official_render_runtime(
        MujocoFlyOfficialRenderRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=tmp_path / "missing.ckpt",
        )
    )

    payload = runtime.session_payload()

    assert payload["available"] is False
    assert payload["running_state"] == "unavailable"
    assert payload["checkpoint_loaded"] is False
    assert "checkpoint" in str(payload["reason"]).lower()


def test_official_render_runtime_lifecycle_controls_delegate_to_backend(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_runtime import (
        MujocoFlyOfficialRenderRuntimeConfig,
        create_mujoco_fly_official_render_runtime,
    )

    scene_dir = tmp_path / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    checkpoint_path = tmp_path / "policy.ckpt"
    checkpoint_path.write_text("checkpoint", encoding="utf-8")
    backend = _FakeOfficialRenderBackend()

    runtime = create_mujoco_fly_official_render_runtime(
        MujocoFlyOfficialRenderRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=checkpoint_path,
        ),
        backend_factory=lambda _config: backend,
    )

    runtime.start()
    runtime.pause()
    runtime.reset()

    payload = runtime.session_payload()

    assert payload["available"] is True
    assert payload["running_state"] == "paused"
    assert payload["checkpoint_loaded"] is True
    assert backend.started is True
    assert backend.paused is True
    assert backend.reset_called is True


def test_official_render_runtime_renders_frame_through_backend_seam(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_runtime import (
        MujocoFlyOfficialRenderRuntimeConfig,
        create_mujoco_fly_official_render_runtime,
    )

    scene_dir = tmp_path / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    checkpoint_path = tmp_path / "policy.ckpt"
    checkpoint_path.write_text("checkpoint", encoding="utf-8")
    backend = _FakeOfficialRenderBackend()

    runtime = create_mujoco_fly_official_render_runtime(
        MujocoFlyOfficialRenderRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=checkpoint_path,
        ),
        backend_factory=lambda _config: backend,
    )

    frame = runtime.render_frame(width=960, height=540, camera="track")

    assert frame.content_type == "image/jpeg"
    assert frame.camera == "track"
    assert frame.width == 960
    assert frame.height == 540
    assert frame.bytes == b"walker/track1:960x540"
    assert backend.last_render_camera == "walker/track1"


def test_official_render_runtime_rejects_unsupported_camera_preset(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_runtime import (
        MujocoFlyOfficialRenderRuntimeConfig,
        create_mujoco_fly_official_render_runtime,
    )

    scene_dir = tmp_path / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    checkpoint_path = tmp_path / "policy.ckpt"
    checkpoint_path.write_text("checkpoint", encoding="utf-8")

    runtime = create_mujoco_fly_official_render_runtime(
        MujocoFlyOfficialRenderRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=checkpoint_path,
        ),
        backend_factory=lambda _config: _FakeOfficialRenderBackend(),
    )

    with pytest.raises(ValueError, match="camera"):
        runtime.set_camera_preset("hero")


def test_official_render_runtime_maps_page_camera_preset_to_official_camera_id(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_runtime import (
        MujocoFlyOfficialRenderRuntimeConfig,
        create_mujoco_fly_official_render_runtime,
    )

    scene_dir = tmp_path / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    checkpoint_path = tmp_path / "policy.ckpt"
    checkpoint_path.write_text("checkpoint", encoding="utf-8")
    backend = _FakeOfficialRenderBackend()

    runtime = create_mujoco_fly_official_render_runtime(
        MujocoFlyOfficialRenderRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=checkpoint_path,
        ),
        backend_factory=lambda _config: backend,
    )

    runtime.set_camera_preset("back")

    assert runtime.session_payload()["current_camera"] == "back"
    assert backend.current_camera == "walker/back"
