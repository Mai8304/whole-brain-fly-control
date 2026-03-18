from __future__ import annotations

from typing import Any


ALLOWED_BROWSER_VIEWER_CAMERA_PRESETS = {
    "track",
    "side",
    "back",
    "top",
}


def validate_browser_viewer_bootstrap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    scene_version = str(payload["scene_version"])
    runtime_mode = str(payload["runtime_mode"])
    entry_xml = str(payload["entry_xml"])
    checkpoint_loaded = _validate_bool(payload.get("checkpoint_loaded"), field_name="checkpoint_loaded")
    default_camera = _validate_camera_preset(payload.get("default_camera"))
    camera_presets_raw = payload.get("camera_presets")
    if not isinstance(camera_presets_raw, list) or not camera_presets_raw:
        raise ValueError("camera_presets must be a non-empty list")
    camera_presets = [_validate_camera_preset(value) for value in camera_presets_raw]
    camera_manifest_raw = payload.get("camera_manifest", [])
    if not isinstance(camera_manifest_raw, list):
        raise ValueError("camera_manifest must be a list when present")
    camera_manifest: list[dict[str, Any]] = []
    for entry in camera_manifest_raw:
        if not isinstance(entry, dict):
            raise ValueError("camera_manifest entry must be an object")
        preset = _validate_camera_preset(entry.get("preset"))
        camera_name = entry.get("camera_name")
        if not isinstance(camera_name, str) or not camera_name:
            raise ValueError("camera_name is required for every camera manifest entry")
        mode = entry.get("mode")
        if mode is not None:
            mode = str(mode)
        position = _validate_vector(entry.get("position"), size=3, field_name="position")
        quaternion = entry.get("quaternion")
        if quaternion is not None:
            quaternion = _validate_vector(quaternion, size=4, field_name="quaternion")
        xyaxes = entry.get("xyaxes")
        if xyaxes is not None:
            xyaxes = _validate_vector(xyaxes, size=6, field_name="xyaxes")
        fovy = entry.get("fovy")
        if fovy is not None:
            fovy = float(fovy)
        camera_manifest.append(
            {
                "preset": preset,
                "camera_name": camera_name,
                "mode": mode,
                "position": position,
                "quaternion": quaternion,
                "xyaxes": xyaxes,
                "fovy": fovy,
            }
        )

    body_manifest_raw = payload.get("body_manifest")
    if not isinstance(body_manifest_raw, list):
        raise ValueError("body_manifest must be a list")
    body_manifest: list[dict[str, Any]] = []
    for entry in body_manifest_raw:
        if not isinstance(entry, dict):
            raise ValueError("body_manifest entry must be an object")
        body_name = entry.get("body_name")
        if not isinstance(body_name, str) or not body_name:
            raise ValueError("body_name is required for every body manifest entry")
        parent_body_name = entry.get("parent_body_name")
        if parent_body_name is not None:
            parent_body_name = str(parent_body_name)
        renderable = bool(entry.get("renderable", False))
        geom_names_raw = entry.get("geom_names", [])
        if not isinstance(geom_names_raw, list):
            raise ValueError("geom_names must be a list when present")
        geom_names = [str(name) for name in geom_names_raw]
        body_manifest.append(
            {
                "body_name": body_name,
                "parent_body_name": parent_body_name,
                "renderable": renderable,
                "geom_names": geom_names,
            }
        )

    geom_manifest_raw = payload.get("geom_manifest")
    if not isinstance(geom_manifest_raw, list):
        raise ValueError("geom_manifest must be a list")
    geom_manifest: list[dict[str, Any]] = []
    for entry in geom_manifest_raw:
        if not isinstance(entry, dict):
            raise ValueError("geom_manifest entry must be an object")
        geom_name = entry.get("geom_name")
        if not isinstance(geom_name, str) or not geom_name:
            raise ValueError("geom_name is required for every geom manifest entry")
        body_name = entry.get("body_name")
        if not isinstance(body_name, str) or not body_name:
            raise ValueError("body_name is required for every geom manifest entry")
        mesh_asset = entry.get("mesh_asset")
        if not isinstance(mesh_asset, str) or not mesh_asset:
            raise ValueError("mesh_asset is required for every geom manifest entry")
        mesh_scale = _validate_vector(entry.get("mesh_scale"), size=3, field_name="mesh_scale")
        local_position = _validate_vector(entry.get("local_position"), size=3, field_name="local_position")
        local_quaternion = _validate_vector(
            entry.get("local_quaternion"), size=4, field_name="local_quaternion"
        )
        material_name = entry.get("material_name")
        if material_name is not None:
            material_name = str(material_name)
        material_rgba = entry.get("material_rgba")
        if material_rgba is not None:
            material_rgba = _validate_vector(material_rgba, size=4, field_name="material_rgba")
        material_specular = entry.get("material_specular")
        if material_specular is not None:
            material_specular = float(material_specular)
        material_shininess = entry.get("material_shininess")
        if material_shininess is not None:
            material_shininess = float(material_shininess)
        geom_manifest.append(
            {
                "geom_name": geom_name,
                "body_name": body_name,
                "mesh_asset": mesh_asset,
                "mesh_scale": mesh_scale,
                "local_position": local_position,
                "local_quaternion": local_quaternion,
                "material_name": material_name,
                "material_rgba": material_rgba,
                "material_specular": material_specular,
                "material_shininess": material_shininess,
            }
        )

    return {
        "scene_version": scene_version,
        "runtime_mode": runtime_mode,
        "entry_xml": entry_xml,
        "checkpoint_loaded": checkpoint_loaded,
        "default_camera": default_camera,
        "camera_presets": camera_presets,
        "camera_manifest": camera_manifest,
        "body_manifest": body_manifest,
        "geom_manifest": geom_manifest,
    }


def validate_browser_viewer_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    available = _validate_bool(payload.get("available"), field_name="available")
    checkpoint_loaded = _validate_bool(payload.get("checkpoint_loaded"), field_name="checkpoint_loaded")
    running_state = str(payload["running_state"])
    current_camera = _validate_camera_preset(payload.get("current_camera"))
    scene_version = str(payload["scene_version"])
    reason = payload.get("reason")
    if reason is not None:
        reason = str(reason)
    return {
        "available": available,
        "running_state": running_state,
        "checkpoint_loaded": checkpoint_loaded,
        "current_camera": current_camera,
        "scene_version": scene_version,
        "reason": reason,
    }


def validate_browser_viewer_pose_payload(payload: dict[str, Any]) -> dict[str, Any]:
    frame_id = int(payload["frame_id"])
    sim_time = float(payload["sim_time"])
    running_state = str(payload["running_state"])
    current_camera = _validate_camera_preset(payload.get("current_camera"))
    scene_version = str(payload["scene_version"])
    body_poses_raw = payload.get("body_poses")
    if not isinstance(body_poses_raw, list):
        raise ValueError("body_poses must be a list")
    body_poses: list[dict[str, Any]] = []
    for entry in body_poses_raw:
        if not isinstance(entry, dict):
            raise ValueError("body pose entry must be an object")
        body_name = entry.get("body_name")
        if not isinstance(body_name, str) or not body_name:
            raise ValueError("body_name is required for every body pose")
        position = _validate_vector(entry.get("position"), size=3, field_name="position")
        quaternion = _validate_vector(entry.get("quaternion"), size=4, field_name="quaternion")
        body_poses.append(
            {
                "body_name": body_name,
                "position": position,
                "quaternion": quaternion,
            }
        )
    reason = payload.get("reason")
    if reason is not None:
        reason = str(reason)
    return {
        "frame_id": frame_id,
        "sim_time": sim_time,
        "running_state": running_state,
        "current_camera": current_camera,
        "scene_version": scene_version,
        "body_poses": body_poses,
        "reason": reason,
    }


def build_unavailable_browser_viewer_pose_payload(
    *,
    reason: str | None = None,
    scene_version: str = "unavailable",
    current_camera: str = "track",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "frame_id": 0,
        "sim_time": 0.0,
        "running_state": "unavailable",
        "current_camera": _validate_camera_preset(current_camera),
        "scene_version": scene_version,
        "body_poses": [],
    }
    if reason:
        payload["reason"] = reason
    return payload


def _validate_camera_preset(value: Any) -> str:
    camera = str(value or "")
    if camera not in ALLOWED_BROWSER_VIEWER_CAMERA_PRESETS:
        raise ValueError(
            "camera must be one of "
            + ", ".join(sorted(ALLOWED_BROWSER_VIEWER_CAMERA_PRESETS))
        )
    return camera


def _validate_bool(value: Any, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _validate_vector(value: Any, *, size: int, field_name: str) -> list[float]:
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{field_name} must contain exactly {size} values")
    return [float(item) for item in value]
