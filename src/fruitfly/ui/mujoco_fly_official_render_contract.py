from __future__ import annotations

from typing import Any

ALLOWED_OFFICIAL_RENDER_CAMERA_PRESETS = {
    "track",
    "side",
    "back",
    "top",
}

OFFICIAL_RENDER_CAMERA_PRESET_TO_CAMERA_ID = {
    "track": "walker/track1",
    "side": "walker/side",
    "back": "walker/back",
    "top": "top_camera",
}


def validate_official_render_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    available = _validate_bool(payload.get("available"), field_name="available")
    running_state = str(payload["running_state"])
    current_camera = _validate_camera_preset(payload.get("current_camera"))
    checkpoint_loaded = _validate_bool(
        payload.get("checkpoint_loaded"),
        field_name="checkpoint_loaded",
    )

    reason = payload.get("reason")
    if reason is not None:
        reason = str(reason)

    return {
        "available": available,
        "running_state": running_state,
        "current_camera": current_camera,
        "checkpoint_loaded": checkpoint_loaded,
        "reason": reason,
    }


def validate_official_render_frame_request(payload: dict[str, Any]) -> dict[str, Any]:
    width = int(payload["width"])
    if width <= 0:
        raise ValueError("width must be a positive integer")

    height = int(payload["height"])
    if height <= 0:
        raise ValueError("height must be a positive integer")

    camera = _validate_camera_preset(payload.get("camera"))

    return {
        "width": width,
        "height": height,
        "camera": camera,
    }


def _validate_camera_preset(value: Any) -> str:
    camera = str(value or "")
    if camera not in ALLOWED_OFFICIAL_RENDER_CAMERA_PRESETS:
        raise ValueError(
            "camera must be one of "
            + ", ".join(sorted(ALLOWED_OFFICIAL_RENDER_CAMERA_PRESETS))
        )
    return camera


def official_render_camera_id_for_preset(camera_preset: str) -> str:
    camera = _validate_camera_preset(camera_preset)
    return OFFICIAL_RENDER_CAMERA_PRESET_TO_CAMERA_ID[camera]


def _validate_bool(value: Any, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value
