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
        parent_body_name = entry.get("parent_body_name")
        if parent_body_name is not None:
            parent_body_name = str(parent_body_name)
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
                "parent_body_name": parent_body_name,
                "mode": mode,
                "position": position,
                "quaternion": quaternion,
                "xyaxes": xyaxes,
                "fovy": fovy,
            }
        )

    ground_manifest_raw = payload.get("ground_manifest")
    ground_manifest: dict[str, Any] | None = None
    if ground_manifest_raw is not None:
        if not isinstance(ground_manifest_raw, dict):
            raise ValueError("ground_manifest must be an object when present")
        geom_name = ground_manifest_raw.get("geom_name")
        if not isinstance(geom_name, str) or not geom_name:
            raise ValueError("geom_name is required for ground_manifest")
        material_name = ground_manifest_raw.get("material_name")
        if material_name is not None:
            material_name = str(material_name)
        texture_name = ground_manifest_raw.get("texture_name")
        if texture_name is not None:
            texture_name = str(texture_name)
        texture_builtin = ground_manifest_raw.get("texture_builtin")
        if texture_builtin is not None:
            texture_builtin = str(texture_builtin)
        texture_mark = ground_manifest_raw.get("texture_mark")
        if texture_mark is not None:
            texture_mark = str(texture_mark)
        ground_manifest = {
            "geom_name": geom_name,
            "size": _validate_vector(ground_manifest_raw.get("size"), size=3, field_name="size"),
            "material_name": material_name,
            "friction": float(ground_manifest_raw.get("friction") or 0.0),
            "texture_name": texture_name,
            "texture_builtin": texture_builtin,
            "texture_rgb1": (
                _validate_vector(ground_manifest_raw.get("texture_rgb1"), size=3, field_name="texture_rgb1")
                if ground_manifest_raw.get("texture_rgb1") is not None
                else None
            ),
            "texture_rgb2": (
                _validate_vector(ground_manifest_raw.get("texture_rgb2"), size=3, field_name="texture_rgb2")
                if ground_manifest_raw.get("texture_rgb2") is not None
                else None
            ),
            "texture_mark": texture_mark,
            "texture_markrgb": (
                _validate_vector(ground_manifest_raw.get("texture_markrgb"), size=3, field_name="texture_markrgb")
                if ground_manifest_raw.get("texture_markrgb") is not None
                else None
            ),
            "texture_size": (
                _validate_vector(ground_manifest_raw.get("texture_size"), size=2, field_name="texture_size")
                if ground_manifest_raw.get("texture_size") is not None
                else None
            ),
            "texrepeat": (
                _validate_vector(ground_manifest_raw.get("texrepeat"), size=2, field_name="texrepeat")
                if ground_manifest_raw.get("texrepeat") is not None
                else [1.0, 1.0]
            ),
            "texuniform": _validate_bool(
                ground_manifest_raw.get("texuniform", False),
                field_name="texuniform",
            ),
            "reflectance": float(ground_manifest_raw.get("reflectance") or 0.0),
            "material_rgba": (
                _validate_vector(ground_manifest_raw.get("material_rgba"), size=4, field_name="material_rgba")
                if ground_manifest_raw.get("material_rgba") is not None
                else None
            ),
        }

    light_manifest_raw = payload.get("light_manifest", [])
    if not isinstance(light_manifest_raw, list):
        raise ValueError("light_manifest must be a list when present")
    light_manifest: list[dict[str, Any]] = []
    for entry in light_manifest_raw:
        if not isinstance(entry, dict):
            raise ValueError("light_manifest entry must be an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("name is required for every light manifest entry")
        parent_body_name = entry.get("parent_body_name")
        if parent_body_name is not None:
            parent_body_name = str(parent_body_name)
        mode = entry.get("mode")
        if mode is not None:
            mode = str(mode)
        direction = entry.get("direction")
        if direction is not None:
            direction = _validate_vector(direction, size=3, field_name="direction")
        diffuse = entry.get("diffuse")
        if diffuse is not None:
            diffuse = _validate_vector(diffuse, size=3, field_name="diffuse")
        light_manifest.append(
            {
                "name": name,
                "parent_body_name": parent_body_name,
                "mode": mode,
                "position": _validate_vector(entry.get("position"), size=3, field_name="position"),
                "direction": direction,
                "diffuse": diffuse,
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
        geom_local_position = _validate_vector(
            entry.get("geom_local_position"),
            size=3,
            field_name="geom_local_position",
        )
        geom_local_quaternion = _validate_vector(
            entry.get("geom_local_quaternion"),
            size=4,
            field_name="geom_local_quaternion",
        )
        mesh_local_position = _validate_vector(
            entry.get("mesh_local_position"),
            size=3,
            field_name="mesh_local_position",
        )
        mesh_local_quaternion = _validate_vector(
            entry.get("mesh_local_quaternion"),
            size=4,
            field_name="mesh_local_quaternion",
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
                "geom_local_position": geom_local_position,
                "geom_local_quaternion": geom_local_quaternion,
                "mesh_local_position": mesh_local_position,
                "mesh_local_quaternion": mesh_local_quaternion,
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
        "ground_manifest": ground_manifest,
        "light_manifest": light_manifest,
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
    geom_poses_raw = payload.get("geom_poses")
    if not isinstance(geom_poses_raw, list):
        raise ValueError("geom_poses must be a list")
    geom_poses: list[dict[str, Any]] = []
    for entry in geom_poses_raw:
        if not isinstance(entry, dict):
            raise ValueError("geom pose entry must be an object")
        geom_name = entry.get("geom_name")
        if not isinstance(geom_name, str) or not geom_name:
            raise ValueError("geom_name is required for every geom pose")
        position = _validate_vector(entry.get("position"), size=3, field_name="position")
        rotation_matrix = _validate_vector(
            entry.get("rotation_matrix"),
            size=9,
            field_name="rotation_matrix",
        )
        geom_poses.append(
            {
                "geom_name": geom_name,
                "position": position,
                "rotation_matrix": rotation_matrix,
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
        "geom_poses": geom_poses,
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
        "geom_poses": [],
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
