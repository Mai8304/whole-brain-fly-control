from __future__ import annotations

from typing import Any


def validate_viewer_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    frame_id = int(payload["frame_id"])
    sim_time = float(payload["sim_time"])
    running_state = str(payload["running_state"])
    scene_version = str(payload["scene_version"])
    body_poses = payload.get("body_poses")
    if not isinstance(body_poses, list):
        raise ValueError("body_poses must be a list")

    normalized_body_poses: list[dict[str, Any]] = []
    for pose in body_poses:
        if not isinstance(pose, dict):
            raise ValueError("body pose entry must be an object")
        body_name = pose.get("body_name")
        if not isinstance(body_name, str) or not body_name:
            raise ValueError("body_name is required for every body pose")

        position = pose.get("position")
        if not isinstance(position, list) or len(position) != 3:
            raise ValueError("position must contain exactly 3 values")

        quaternion = pose.get("quaternion")
        if not isinstance(quaternion, list) or len(quaternion) != 4:
            raise ValueError("quaternion must contain exactly 4 values")

        normalized_body_poses.append(
            {
                "body_name": body_name,
                "position": [float(value) for value in position],
                "quaternion": [float(value) for value in quaternion],
            }
        )

    return {
        "frame_id": frame_id,
        "sim_time": sim_time,
        "running_state": running_state,
        "scene_version": scene_version,
        "body_poses": normalized_body_poses,
    }


def build_unavailable_viewer_state(*, reason: str | None = None, scene_version: str = "unavailable") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "frame_id": 0,
        "sim_time": 0.0,
        "running_state": "unavailable",
        "scene_version": scene_version,
        "body_poses": [],
    }
    if reason:
        payload["reason"] = reason
    return payload
