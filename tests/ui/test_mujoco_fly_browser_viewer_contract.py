from __future__ import annotations

import pytest


def test_validate_browser_viewer_bootstrap_payload_normalizes_body_and_geom_manifests() -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
        validate_browser_viewer_bootstrap_payload,
    )

    payload = validate_browser_viewer_bootstrap_payload(
        {
            "scene_version": "flybody-walk-imitation-v1",
            "runtime_mode": "official-flybody-browser-viewer",
            "entry_xml": "walk_imitation.xml",
            "checkpoint_loaded": True,
            "default_camera": "track",
            "camera_presets": ["track", "side", "back", "top"],
            "camera_manifest": [
                {
                    "preset": "track",
                    "camera_name": "walker/track1",
                    "mode": "trackcom",
                    "position": ["0.6", 0.6, 0.22],
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
                    "mesh_asset": "/mujoco-fly/flybody-official-walk/thorax_body.obj",
                    "mesh_scale": ["0.1", 0.1, 0.1],
                    "local_position": ["0", 0, 0.25],
                    "local_quaternion": [1, 0, 0, 0],
                    "material_name": "walker/body",
                    "material_rgba": [0.67, 0.35, 0.14, 1],
                    "material_specular": 0,
                    "material_shininess": "0.6",
                }
            ],
        }
    )

    assert payload["checkpoint_loaded"] is True
    assert payload["default_camera"] == "track"
    assert payload["camera_presets"] == ["track", "side", "back", "top"]
    assert payload["camera_manifest"][0]["camera_name"] == "walker/track1"
    assert payload["camera_manifest"][0]["position"] == [0.6, 0.6, 0.22]
    assert payload["body_manifest"][0]["body_name"] == "walker/thorax"
    assert payload["geom_manifest"][0]["mesh_asset"].endswith("thorax_body.obj")
    assert payload["geom_manifest"][0]["mesh_scale"] == [0.1, 0.1, 0.1]
    assert payload["geom_manifest"][0]["local_position"] == [0.0, 0.0, 0.25]
    assert payload["geom_manifest"][0]["material_name"] == "walker/body"
    assert payload["geom_manifest"][0]["material_rgba"] == [0.67, 0.35, 0.14, 1.0]


def test_validate_browser_viewer_bootstrap_payload_rejects_missing_body_name() -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
        validate_browser_viewer_bootstrap_payload,
    )

    with pytest.raises(ValueError, match="body_name"):
        validate_browser_viewer_bootstrap_payload(
            {
                "scene_version": "flybody-walk-imitation-v1",
                "runtime_mode": "official-flybody-browser-viewer",
                "entry_xml": "walk_imitation.xml",
                "checkpoint_loaded": False,
                "default_camera": "track",
                "camera_presets": ["track"],
                "body_manifest": [{"parent_body_name": None}],
                "geom_manifest": [],
            }
        )


def test_validate_browser_viewer_session_payload_requires_boolean_checkpoint_flag() -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
        validate_browser_viewer_session_payload,
    )

    with pytest.raises(ValueError, match="checkpoint_loaded"):
        validate_browser_viewer_session_payload(
            {
                "available": True,
                "running_state": "paused",
                "checkpoint_loaded": "true",
                "current_camera": "track",
                "scene_version": "flybody-walk-imitation-v1",
            }
        )


def test_validate_browser_viewer_pose_payload_normalizes_body_poses() -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
        validate_browser_viewer_pose_payload,
    )

    payload = validate_browser_viewer_pose_payload(
        {
            "frame_id": 4,
            "sim_time": "1.25",
            "running_state": "running",
            "current_camera": "track",
            "scene_version": "flybody-walk-imitation-v1",
            "body_poses": [
                {
                    "body_name": "walker/thorax",
                    "position": ["0", 0.5, 1],
                    "quaternion": [1, 0, 0, 0],
                }
            ],
        }
    )

    assert payload["frame_id"] == 4
    assert payload["sim_time"] == 1.25
    assert payload["body_poses"][0]["position"] == [0.0, 0.5, 1.0]


def test_build_unavailable_browser_viewer_pose_payload_marks_stream_unavailable() -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_contract import (
        build_unavailable_browser_viewer_pose_payload,
    )

    payload = build_unavailable_browser_viewer_pose_payload(
        reason="Official walking policy checkpoint is unavailable",
        scene_version="flybody-walk-imitation-v1",
    )

    assert payload["running_state"] == "unavailable"
    assert payload["scene_version"] == "flybody-walk-imitation-v1"
    assert payload["body_poses"] == []
    assert "checkpoint" in str(payload["reason"]).lower()
