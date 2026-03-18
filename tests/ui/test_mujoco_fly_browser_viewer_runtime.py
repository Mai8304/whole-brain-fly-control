from __future__ import annotations

import json
from pathlib import Path

import pytest


class _FakeBrowserViewerBackend:
    def __init__(self) -> None:
        self.started = False
        self.paused = False
        self.reset_called = False
        self.state_requests = 0

    def start(self) -> None:
        self.started = True
        self.paused = False

    def pause(self) -> None:
        self.paused = True

    def reset(self) -> None:
        self.reset_called = True
        self.paused = True

    def current_viewer_state(self) -> dict[str, object]:
        self.state_requests += 1
        return {
            "frame_id": self.state_requests,
            "sim_time": 0.05 * self.state_requests,
            "running_state": "running" if self.started and not self.paused else "paused",
            "current_camera": "track",
            "scene_version": "flybody-walk-imitation-v1",
            "body_poses": [
                {
                    "body_name": "walker/thorax",
                    "position": [0.0, 0.0, 0.1278],
                    "quaternion": [1.0, 0.0, 0.0, 0.0],
                }
            ],
            "geom_poses": [
                {
                    "geom_name": "walker/thorax",
                    "position": [0.1, 0.0, 0.1278],
                    "rotation_matrix": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                }
            ],
        }


def _materialize_scene_bundle(scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "manifest.json").write_text(
        json.dumps(
            {
                "entry_xml": "walk_imitation.xml",
                "scene_version": "flybody-walk-imitation-v1",
                "camera_presets": ["track", "side", "back", "top"],
                "camera_manifest": [
                    {
                        "preset": "track",
                        "camera_name": "walker/track1",
                        "mode": "trackcom",
                        "position": [0.6, 0.6, 0.22],
                        "quaternion": [0.312, 0.221, 0.533, 0.754],
                        "xyaxes": None,
                        "fovy": None,
                    }
                ],
                "body_manifest": [
                    {
                        "body_name": "walker/thorax",
                        "parent_body_name": "walker/",
                        "renderable": True,
                        "geom_names": ["walker/thorax"],
                    }
                ],
                "geom_manifest": [
                    {
                        "geom_name": "walker/thorax",
                        "body_name": "walker/thorax",
                        "mesh_asset_path": "thorax_body.obj",
                        "mesh_scale": [0.1, 0.1, 0.1],
                        "local_position": [0.0, 0.0, 0.0],
                        "local_quaternion": [1.0, 0.0, 0.0, 0.0],
                        "material_name": "walker/body",
                        "material_rgba": [0.67, 0.35, 0.14, 1.0],
                        "material_specular": 0.0,
                        "material_shininess": 0.6,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_browser_viewer_runtime_reports_unavailable_when_scene_bundle_missing(tmp_path: Path) -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_runtime import (
        MujocoFlyBrowserViewerRuntimeConfig,
        create_mujoco_fly_browser_viewer_runtime,
    )

    runtime = create_mujoco_fly_browser_viewer_runtime(
        MujocoFlyBrowserViewerRuntimeConfig(
            scene_dir=tmp_path / "missing-scene",
            policy_checkpoint_path=tmp_path / "missing-policy",
        )
    )

    payload = runtime.session_payload()

    assert payload["available"] is False
    assert payload["running_state"] == "unavailable"
    assert payload["checkpoint_loaded"] is False


def test_browser_viewer_runtime_bootstrap_survives_missing_checkpoint_when_backend_is_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import fruitfly.ui.mujoco_fly_browser_viewer_runtime as runtime_module

    monkeypatch.setattr(runtime_module, "PROJECT_ROOT", tmp_path)

    scene_dir = tmp_path / "apps" / "neural-console" / "public" / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)

    runtime = runtime_module.create_mujoco_fly_browser_viewer_runtime(
        runtime_module.MujocoFlyBrowserViewerRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=tmp_path / "missing-policy",
        ),
        backend_factory=lambda _config: _FakeBrowserViewerBackend(),
    )

    session = runtime.session_payload()
    bootstrap = runtime.bootstrap_payload()
    pose = runtime.current_viewer_state()

    assert session["available"] is True
    assert session["checkpoint_loaded"] is False
    assert "checkpoint" in str(session["reason"]).lower()
    assert bootstrap["checkpoint_loaded"] is False
    assert bootstrap["body_manifest"][0]["body_name"] == "walker/thorax"
    assert bootstrap["geom_manifest"][0]["mesh_asset"] == "/flybody-official-walk/thorax_body.obj"
    assert bootstrap["geom_manifest"][0]["mesh_scale"] == [0.1, 0.1, 0.1]
    assert bootstrap["geom_manifest"][0]["material_name"] == "walker/body"
    assert bootstrap["camera_manifest"][0]["camera_name"] == "walker/track1"
    assert pose["body_poses"][0]["body_name"] == "walker/thorax"
    assert pose["geom_poses"][0]["geom_name"] == "walker/thorax"


def test_browser_viewer_runtime_rejects_start_when_checkpoint_missing_even_if_viewer_is_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import fruitfly.ui.mujoco_fly_browser_viewer_runtime as runtime_module

    monkeypatch.setattr(runtime_module, "PROJECT_ROOT", tmp_path)

    scene_dir = tmp_path / "apps" / "neural-console" / "public" / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)

    runtime = runtime_module.create_mujoco_fly_browser_viewer_runtime(
        runtime_module.MujocoFlyBrowserViewerRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=tmp_path / "missing-policy",
        ),
        backend_factory=lambda _config: _FakeBrowserViewerBackend(),
    )

    with pytest.raises(RuntimeError, match="checkpoint"):
        runtime.start()


def test_browser_viewer_runtime_lifecycle_controls_delegate_to_backend_when_checkpoint_loaded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import fruitfly.ui.mujoco_fly_browser_viewer_runtime as runtime_module

    monkeypatch.setattr(runtime_module, "PROJECT_ROOT", tmp_path)

    scene_dir = tmp_path / "apps" / "neural-console" / "public" / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    checkpoint_path = tmp_path / "walking"
    checkpoint_path.mkdir()
    (checkpoint_path / "saved_model.pb").write_bytes(b"model")
    backend = _FakeBrowserViewerBackend()

    runtime = runtime_module.create_mujoco_fly_browser_viewer_runtime(
        runtime_module.MujocoFlyBrowserViewerRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=checkpoint_path,
        ),
        backend_factory=lambda _config: backend,
    )

    runtime.start()
    runtime.pause()
    runtime.reset()

    session = runtime.session_payload()

    assert session["available"] is True
    assert session["checkpoint_loaded"] is True
    assert backend.started is True
    assert backend.paused is True
    assert backend.reset_called is True


def test_browser_viewer_runtime_resolves_repo_default_checkpoint_path(tmp_path: Path, monkeypatch) -> None:
    import fruitfly.ui.mujoco_fly_browser_viewer_runtime as runtime_module

    scene_dir = tmp_path / "apps" / "neural-console" / "public" / "flybody-official-walk"
    _materialize_scene_bundle(scene_dir)
    default_policy_dir = tmp_path / "outputs" / "flybody-data" / "trained-fly-policies" / "walking"
    default_policy_dir.mkdir(parents=True, exist_ok=True)
    (default_policy_dir / "saved_model.pb").write_bytes(b"model")

    monkeypatch.setattr(runtime_module, "PROJECT_ROOT", tmp_path)

    runtime = runtime_module.create_mujoco_fly_browser_viewer_runtime(
        runtime_module.MujocoFlyBrowserViewerRuntimeConfig(
            scene_dir=scene_dir,
            policy_checkpoint_path=None,
        ),
        backend_factory=lambda _config: _FakeBrowserViewerBackend(),
    )

    assert runtime.config.policy_checkpoint_path == default_policy_dir
