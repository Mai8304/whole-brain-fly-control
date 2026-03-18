from __future__ import annotations

import pytest


def test_mujoco_fly_viewer_state_requires_body_name() -> None:
    from fruitfly.ui.mujoco_fly_contract import validate_viewer_state_payload

    with pytest.raises(ValueError, match="body_name"):
        validate_viewer_state_payload(
            {
                "frame_id": 1,
                "sim_time": 0.1,
                "running_state": "paused",
                "scene_version": "flybody-walk-imitation-v1",
                "body_poses": [
                    {
                        "position": [0.0, 0.0, 0.0],
                        "quaternion": [1.0, 0.0, 0.0, 0.0],
                    }
                ],
            }
        )


def test_mujoco_fly_viewer_state_rejects_index_only_payloads() -> None:
    from fruitfly.ui.mujoco_fly_contract import validate_viewer_state_payload

    with pytest.raises(ValueError, match="body_name"):
        validate_viewer_state_payload(
            {
                "frame_id": 1,
                "sim_time": 0.1,
                "running_state": "paused",
                "scene_version": "flybody-walk-imitation-v1",
                "body_poses": [
                    {
                        "body_index": 3,
                        "position": [0.0, 0.0, 0.0],
                        "quaternion": [1.0, 0.0, 0.0, 0.0],
                    }
                ],
            }
        )


def test_mujoco_fly_viewer_state_rejects_malformed_quaternions() -> None:
    from fruitfly.ui.mujoco_fly_contract import validate_viewer_state_payload

    with pytest.raises(ValueError, match="quaternion"):
        validate_viewer_state_payload(
            {
                "frame_id": 1,
                "sim_time": 0.1,
                "running_state": "paused",
                "scene_version": "flybody-walk-imitation-v1",
                "body_poses": [
                    {
                        "body_name": "walker/thorax",
                        "position": [0.0, 0.0, 0.0],
                        "quaternion": [1.0, 0.0, 0.0],
                    }
                ],
            }
        )


def test_mujoco_fly_viewer_state_accepts_valid_body_pose_payload() -> None:
    from fruitfly.ui.mujoco_fly_contract import validate_viewer_state_payload

    payload = validate_viewer_state_payload(
        {
            "frame_id": 3,
            "sim_time": 0.5,
            "running_state": "paused",
            "scene_version": "flybody-walk-imitation-v1",
            "body_poses": [
                {
                    "body_name": "walker/thorax",
                    "position": [0.0, 0.1, 0.2],
                    "quaternion": [1.0, 0.0, 0.0, 0.0],
                }
            ],
        }
    )

    assert payload["frame_id"] == 3
    assert payload["body_poses"][0]["body_name"] == "walker/thorax"
