from __future__ import annotations

import pytest


def test_official_render_session_payload_requires_runtime_fields() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_session_payload

    payload = validate_official_render_session_payload(
        {
            "available": True,
            "running_state": "paused",
            "current_camera": "track",
            "checkpoint_loaded": True,
            "reason": None,
        }
    )

    assert payload["available"] is True
    assert payload["running_state"] == "paused"
    assert payload["current_camera"] == "track"
    assert payload["checkpoint_loaded"] is True
    assert payload["reason"] is None


def test_official_render_session_payload_rejects_invalid_camera_preset() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_session_payload

    with pytest.raises(ValueError, match="camera"):
        validate_official_render_session_payload(
            {
                "available": True,
                "running_state": "paused",
                "current_camera": "freecam",
                "checkpoint_loaded": True,
                "reason": None,
            }
        )


def test_official_render_session_payload_requires_boolean_runtime_flags() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_session_payload

    with pytest.raises(ValueError, match="available"):
        validate_official_render_session_payload(
            {
                "available": "true",
                "running_state": "paused",
                "current_camera": "track",
                "checkpoint_loaded": True,
                "reason": None,
            }
        )

    with pytest.raises(ValueError, match="checkpoint_loaded"):
        validate_official_render_session_payload(
            {
                "available": True,
                "running_state": "paused",
                "current_camera": "track",
                "checkpoint_loaded": "false",
                "reason": None,
            }
        )


def test_official_render_frame_request_requires_positive_dimensions() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_frame_request

    with pytest.raises(ValueError, match="width"):
        validate_official_render_frame_request(
            {
                "width": 0,
                "height": 540,
                "camera": "track",
            }
        )

    with pytest.raises(ValueError, match="height"):
        validate_official_render_frame_request(
            {
                "width": 960,
                "height": -1,
                "camera": "track",
            }
        )


def test_official_render_frame_request_accepts_supported_camera_preset() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_frame_request

    payload = validate_official_render_frame_request(
        {
            "width": 960,
            "height": 540,
            "camera": "side",
        }
    )

    assert payload == {
        "width": 960,
        "height": 540,
        "camera": "side",
    }


def test_official_render_camera_preset_maps_to_official_camera_id() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import official_render_camera_id_for_preset

    assert official_render_camera_id_for_preset("track") == "walker/track1"
    assert official_render_camera_id_for_preset("side") == "walker/side"
    assert official_render_camera_id_for_preset("back") == "walker/back"
    assert official_render_camera_id_for_preset("top") == "top_camera"


def test_official_render_frame_request_rejects_unknown_camera_preset() -> None:
    from fruitfly.ui.mujoco_fly_official_render_contract import validate_official_render_frame_request

    with pytest.raises(ValueError, match="camera"):
        validate_official_render_frame_request(
            {
                "width": 960,
                "height": 540,
                "camera": "hero",
            }
        )
