from __future__ import annotations

import argparse
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = (
    ROOT / "apps" / "neural-console" / "public" / "mujoco-fly" / "flybody-official-walk"
)
ENTRY_XML = "walk_imitation.xml"
SCENE_VERSION = "flybody-walk-imitation-v1"

_export_with_assets = None


def _prepare_runtime_environment(environ: dict[str, str]) -> None:
    environ.setdefault("MUJOCO_GL", "off")

    cache_root = Path(tempfile.gettempdir()) / "fruitfly-export-cache"
    environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
    environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))


def _build_walk_imitation_environment():
    _prepare_runtime_environment(os.environ)
    try:
        from flybody.fly_envs import walk_imitation
    except ImportError as exc:  # pragma: no cover - exercised through runtime path
        raise RuntimeError("flybody runtime is unavailable") from exc

    return walk_imitation(ref_path=None)


def _ensure_export_with_assets():
    global _export_with_assets
    if _export_with_assets is None:
        try:
            from dm_control.mjcf import export_with_assets as export_with_assets_fn
        except ImportError as exc:  # pragma: no cover - exercised through runtime path
            raise RuntimeError("dm_control mjcf export_with_assets is unavailable") from exc
        _export_with_assets = export_with_assets_fn
    return _export_with_assets


def _initialize_environment(environment) -> None:
    environment.reset()


def _build_manifest(output_dir: Path, *, environment) -> dict[str, object]:
    entry_xml_path = output_dir / ENTRY_XML
    (
        body_manifest,
        geom_manifest,
        camera_presets,
        camera_manifest,
        ground_manifest,
        light_manifest,
    ) = _build_scene_manifests(entry_xml_path, physics=getattr(environment, "physics", None))
    _materialize_compiled_mesh_assets(
        output_dir=output_dir,
        geom_manifest=geom_manifest,
        physics=getattr(environment, "physics", None),
    )
    exported_files = sorted(
        str(path.relative_to(output_dir))
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    return {
        "entry_xml": ENTRY_XML,
        "scene_version": SCENE_VERSION,
        "asset_count": len(exported_files),
        "files": exported_files,
        "camera_presets": camera_presets,
        "camera_manifest": camera_manifest,
        "ground_manifest": ground_manifest,
        "light_manifest": light_manifest,
        "body_manifest": body_manifest,
        "geom_manifest": geom_manifest,
        "output_dir": str(output_dir),
    }


def _build_scene_manifests(
    entry_xml_path: Path,
    *,
    physics=None,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[str],
    list[dict[str, object]],
    dict[str, object] | None,
    list[dict[str, object]],
]:
    root = ET.parse(entry_xml_path).getroot()
    defaults_by_class = _build_defaults_by_class(root)
    material_specs_by_name = _build_material_specs_by_name(root)
    texture_specs_by_name = _build_texture_specs_by_name(root)
    mesh_file_by_name = {
        str(mesh.get("name")): {
            "file": str(mesh.get("file")),
            "scale": _resolve_mesh_scale(mesh, defaults_by_class),
        }
        for mesh in root.findall("./asset/mesh")
        if mesh.get("name") and mesh.get("file")
    }
    camera_manifest = _build_camera_manifest(root)
    camera_presets = [entry["preset"] for entry in camera_manifest]
    ground_manifest = _build_ground_manifest(
        root,
        material_specs_by_name=material_specs_by_name,
        texture_specs_by_name=texture_specs_by_name,
    )
    light_manifest = _build_light_manifest(root)

    body_manifest: list[dict[str, object]] = []
    geom_manifest: list[dict[str, object]] = []
    worldbody = root.find("worldbody")
    if worldbody is None:
        return (
            body_manifest,
            geom_manifest,
            camera_presets,
            camera_manifest,
            ground_manifest,
            light_manifest,
        )

    for body in worldbody.findall("body"):
        _collect_body_and_geom_manifests(
            body,
            parent_body_name=None,
            inherited_childclass=None,
            body_manifest=body_manifest,
            geom_manifest=geom_manifest,
            mesh_file_by_name=mesh_file_by_name,
            defaults_by_class=defaults_by_class,
            material_specs_by_name=material_specs_by_name,
        )
    return (
        body_manifest,
        geom_manifest,
        camera_presets,
        camera_manifest,
        ground_manifest,
        light_manifest,
    )


def _collect_body_and_geom_manifests(
    body: ET.Element,
    *,
    parent_body_name: str | None,
    inherited_childclass: str | None,
    body_manifest: list[dict[str, object]],
    geom_manifest: list[dict[str, object]],
    mesh_file_by_name: dict[str, dict[str, object]],
    defaults_by_class: dict[str, dict[str, object]],
    material_specs_by_name: dict[str, dict[str, object]],
) -> None:
    body_name = body.get("name")
    effective_parent = parent_body_name
    effective_childclass = body.get("childclass") or inherited_childclass
    geom_names: list[str] = []

    if body_name:
        body_manifest.append(
            {
                "body_name": body_name,
                "parent_body_name": parent_body_name,
                "renderable": False,
                "geom_names": geom_names,
            }
        )
        effective_parent = body_name

    for index, geom in enumerate(body.findall("geom")):
        mesh_name = geom.get("mesh")
        if not mesh_name:
            continue
        mesh_entry = mesh_file_by_name.get(mesh_name)
        if mesh_entry is None:
            continue
        geom_name = geom.get("name") or _synthetic_geom_name(body_name, mesh_name, index)
        geom_defaults = _resolve_geom_defaults(
            geom=geom,
            inherited_childclass=effective_childclass,
            defaults_by_class=defaults_by_class,
        )
        material_name = _resolve_geom_material_name(geom=geom, geom_defaults=geom_defaults)
        material_spec = material_specs_by_name.get(material_name or "")
        geom_manifest.append(
            {
                "geom_name": geom_name,
                "body_name": body_name,
                "mesh_asset_path": str(mesh_entry["file"]),
                "mesh_scale": [float(value) for value in mesh_entry["scale"]],
                "source_mesh_asset_path": str(mesh_entry["file"]),
                "source_mesh_scale": [float(value) for value in mesh_entry["scale"]],
                "geom_local_position": _vector_attr(geom.get("pos"), size=3, default=[0.0, 0.0, 0.0]),
                "geom_local_quaternion": _vector_attr(
                    geom.get("quat"),
                    size=4,
                    default=[1.0, 0.0, 0.0, 0.0],
                ),
                "mesh_local_position": [0.0, 0.0, 0.0],
                "mesh_local_quaternion": [1.0, 0.0, 0.0, 0.0],
                "source_mesh_local_position": [0.0, 0.0, 0.0],
                "source_mesh_local_quaternion": [1.0, 0.0, 0.0, 0.0],
                "material_name": material_name,
                "material_rgba": material_spec.get("rgba") if material_spec else None,
                "material_specular": material_spec.get("specular") if material_spec else None,
                "material_shininess": material_spec.get("shininess") if material_spec else None,
            }
        )
        geom_names.append(geom_name)

    if body_name and geom_names:
        body_manifest[-1]["renderable"] = True

    for child in body.findall("body"):
        _collect_body_and_geom_manifests(
            child,
            parent_body_name=effective_parent,
            inherited_childclass=effective_childclass,
            body_manifest=body_manifest,
            geom_manifest=geom_manifest,
            mesh_file_by_name=mesh_file_by_name,
            defaults_by_class=defaults_by_class,
            material_specs_by_name=material_specs_by_name,
        )


def _materialize_compiled_mesh_assets(
    *,
    output_dir: Path,
    geom_manifest: list[dict[str, object]],
    physics,
) -> None:
    if physics is None or not hasattr(physics, "model"):
        return

    model = physics.model
    geom_dataid = np.asarray(model.geom_dataid)
    mesh_count = int(getattr(model, "nmesh", len(getattr(model, "mesh_pos", []))))
    compiled_dir = output_dir / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    baked_mesh_paths: dict[int, str] = {}

    for entry in geom_manifest:
        geom_name = entry.get("geom_name")
        if not isinstance(geom_name, str) or not geom_name:
            continue
        try:
            geom_id = model.name2id(geom_name, "geom")
        except Exception:
            continue
        mesh_id = int(geom_dataid[geom_id])
        if mesh_id < 0 or mesh_id >= mesh_count:
            continue
        asset_path = baked_mesh_paths.get(mesh_id)
        if asset_path is None:
            asset_path = _write_compiled_mesh_asset(
                output_dir=output_dir,
                model=model,
                mesh_id=mesh_id,
            )
            baked_mesh_paths[mesh_id] = asset_path
        entry["mesh_asset_path"] = asset_path
        entry["mesh_scale"] = [1.0, 1.0, 1.0]
        # model.mesh_vert already stores the compiled mesh in geom-local space.
        # Re-applying model.mesh_pos / model.mesh_quat here explodes limbs and
        # wings in downstream renderers.
        entry["mesh_local_position"] = [0.0, 0.0, 0.0]
        entry["mesh_local_quaternion"] = [1.0, 0.0, 0.0, 0.0]
def _write_compiled_mesh_asset(
    *,
    output_dir: Path,
    model,
    mesh_id: int,
) -> str:
    vert_start = int(model.mesh_vertadr[mesh_id])
    vert_count = int(model.mesh_vertnum[mesh_id])
    face_start = int(model.mesh_faceadr[mesh_id])
    face_count = int(model.mesh_facenum[mesh_id])
    normal_start = int(model.mesh_normaladr[mesh_id])
    normal_count = int(model.mesh_normalnum[mesh_id])
    texcoord_start = int(model.mesh_texcoordadr[mesh_id])
    texcoord_count = int(model.mesh_texcoordnum[mesh_id])

    vertices = np.asarray(model.mesh_vert[vert_start : vert_start + vert_count], dtype=np.float64).copy()
    normals = np.asarray(
        model.mesh_normal[normal_start : normal_start + normal_count],
        dtype=np.float64,
    ).copy()
    texcoords = np.asarray(
        model.mesh_texcoord[texcoord_start : texcoord_start + texcoord_count],
        dtype=np.float64,
    ).copy()
    faces = np.asarray(model.mesh_face[face_start : face_start + face_count], dtype=np.int32).copy()

    if normals.size:
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        lengths[lengths == 0] = 1.0
        normals = normals / lengths

    relative_path = Path("compiled") / f"mesh-{mesh_id}.obj"
    mesh_path = output_dir / relative_path
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    with mesh_path.open("w", encoding="utf-8") as handle:
        for vertex in vertices:
            handle.write(f"v {vertex[0]:.12g} {vertex[1]:.12g} {vertex[2]:.12g}\n")
        if texcoords.size and texcoord_count == vert_count:
            for texcoord in texcoords:
                handle.write(f"vt {texcoord[0]:.12g} {texcoord[1]:.12g}\n")
        if normals.size and normal_count == vert_count:
            for normal in normals:
                handle.write(f"vn {normal[0]:.12g} {normal[1]:.12g} {normal[2]:.12g}\n")
        for face in faces:
            indices = [int(index) + 1 for index in face.tolist()]
            if texcoord_count == vert_count and normal_count == vert_count:
                handle.write(
                    "f "
                    + " ".join(f"{index}/{index}/{index}" for index in indices)
                    + "\n"
                )
            elif normal_count == vert_count:
                handle.write("f " + " ".join(f"{index}//{index}" for index in indices) + "\n")
            else:
                handle.write("f " + " ".join(str(index) for index in indices) + "\n")
    return relative_path.as_posix()

def _vector_attr(raw: str | None, *, size: int, default: list[float]) -> list[float]:
    if raw is None:
        return list(default)
    values = [float(part) for part in raw.split()]
    if len(values) != size:
        raise ValueError(f"expected {size} values, got {len(values)} from {raw!r}")
    return values


def _synthetic_geom_name(body_name: str | None, mesh_name: str, index: int) -> str:
    body_prefix = body_name or "world"
    return f"{body_prefix}#mesh-{mesh_name}-{index}"


def _build_defaults_by_class(root: ET.Element) -> dict[str, dict[str, object]]:
    defaults_root = root.find("default")
    if defaults_root is None:
        return {}

    defaults: dict[str, dict[str, object]] = {}
    for child in defaults_root.findall("default"):
        _collect_defaults(child, parent_defaults={}, output=defaults)
    return defaults


def _collect_defaults(
    default_element: ET.Element,
    *,
    parent_defaults: dict[str, object],
    output: dict[str, dict[str, object]],
) -> None:
    resolved_defaults = dict(parent_defaults)
    mesh_element = default_element.find("mesh")
    if mesh_element is not None and mesh_element.get("scale"):
        resolved_defaults["scale"] = _vector_attr(
            mesh_element.get("scale"),
            size=3,
            default=[1.0, 1.0, 1.0],
        )
    geom_element = default_element.find("geom")
    if geom_element is not None:
        if geom_element.get("material"):
            resolved_defaults["material"] = str(geom_element.get("material"))
        if geom_element.get("rgba"):
            resolved_defaults["rgba"] = _vector_attr(
                geom_element.get("rgba"),
                size=4,
                default=[1.0, 1.0, 1.0, 1.0],
            )

    class_name = default_element.get("class")
    if class_name:
        output[class_name] = dict(resolved_defaults)

    for child in default_element.findall("default"):
        _collect_defaults(child, parent_defaults=resolved_defaults, output=output)


def _resolve_mesh_scale(
    mesh_element: ET.Element,
    defaults_by_class: dict[str, dict[str, object]],
) -> list[float]:
    raw_scale = mesh_element.get("scale")
    if raw_scale:
        return _vector_attr(raw_scale, size=3, default=[1.0, 1.0, 1.0])

    class_name = mesh_element.get("class")
    if class_name and class_name in defaults_by_class:
        class_defaults = defaults_by_class[class_name]
        if "scale" in class_defaults:
            return list(class_defaults["scale"])

    return [1.0, 1.0, 1.0]


def _build_material_specs_by_name(root: ET.Element) -> dict[str, dict[str, object]]:
    material_specs: dict[str, dict[str, object]] = {}
    for material in root.findall("./asset/material"):
        material_name = material.get("name")
        if not material_name:
            continue
        material_specs[str(material_name)] = {
            "rgba": _vector_attr(material.get("rgba"), size=4, default=[1.0, 1.0, 1.0, 1.0]),
            "specular": float(material.get("specular") or 0.0),
            "shininess": float(material.get("shininess") or 0.0),
        }
    return material_specs


def _build_texture_specs_by_name(root: ET.Element) -> dict[str, dict[str, object]]:
    texture_specs: dict[str, dict[str, object]] = {}
    for texture in root.findall("./asset/texture"):
        texture_name = texture.get("name")
        if not texture_name:
            continue
        texture_specs[str(texture_name)] = {
            "builtin": texture.get("builtin"),
            "rgb1": (
                _vector_attr(texture.get("rgb1"), size=3, default=[1.0, 1.0, 1.0])
                if texture.get("rgb1")
                else None
            ),
            "rgb2": (
                _vector_attr(texture.get("rgb2"), size=3, default=[0.0, 0.0, 0.0])
                if texture.get("rgb2")
                else None
            ),
            "mark": texture.get("mark"),
            "markrgb": (
                _vector_attr(texture.get("markrgb"), size=3, default=[1.0, 1.0, 1.0])
                if texture.get("markrgb")
                else None
            ),
            "width": int(texture.get("width")) if texture.get("width") else None,
            "height": int(texture.get("height")) if texture.get("height") else None,
        }
    return texture_specs


def _resolve_geom_defaults(
    *,
    geom: ET.Element,
    inherited_childclass: str | None,
    defaults_by_class: dict[str, dict[str, object]],
) -> dict[str, object]:
    geom_class = geom.get("class") or inherited_childclass
    if not geom_class:
        return {}
    defaults = defaults_by_class.get(geom_class)
    if not defaults:
        return {}
    return dict(defaults)


def _resolve_geom_material_name(*, geom: ET.Element, geom_defaults: dict[str, object]) -> str | None:
    if geom.get("material"):
        return str(geom.get("material"))
    material = geom_defaults.get("material")
    if material is None:
        return None
    return str(material)


def _build_camera_manifest(root: ET.Element) -> list[dict[str, object]]:
    parent_map = _build_parent_map(root)
    camera_manifest: list[dict[str, object]] = []
    for preset, camera_name in (
        ("track", "walker/track1"),
        ("side", "walker/side"),
        ("back", "walker/back"),
        ("top", "top_camera"),
    ):
        camera = next(
            (candidate for candidate in root.iter("camera") if candidate.get("name") == camera_name),
            None,
        )
        if camera is None:
            continue
        parent_body_name = _nearest_parent_body_name(camera, parent_map)
        camera_manifest.append(
            {
                "preset": preset,
                "camera_name": camera_name,
                "parent_body_name": parent_body_name,
                "mode": camera.get("mode"),
                "position": _vector_attr(camera.get("pos"), size=3, default=[0.0, 0.0, 0.0]),
                "quaternion": (
                    _vector_attr(camera.get("quat"), size=4, default=[1.0, 0.0, 0.0, 0.0])
                    if camera.get("quat")
                    else None
                ),
                "xyaxes": (
                    _vector_attr(camera.get("xyaxes"), size=6, default=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
                    if camera.get("xyaxes")
                    else None
                ),
                "fovy": float(camera.get("fovy")) if camera.get("fovy") else None,
            }
        )
    return camera_manifest


def _build_ground_manifest(
    root: ET.Element,
    *,
    material_specs_by_name: dict[str, dict[str, object]],
    texture_specs_by_name: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    ground_geom = next((geom for geom in root.iter("geom") if geom.get("name") == "groundplane"), None)
    if ground_geom is None:
        return None

    material_name = ground_geom.get("material")
    material = next(
        (
            candidate
            for candidate in root.findall("./asset/material")
            if candidate.get("name") == material_name
        ),
        None,
    )
    texture_name = material.get("texture") if material is not None else None
    texture_spec = texture_specs_by_name.get(texture_name or "")

    return {
        "geom_name": "groundplane",
        "size": _vector_attr(ground_geom.get("size"), size=3, default=[1.0, 1.0, 0.1]),
        "material_name": material_name,
        "friction": float(ground_geom.get("friction") or 0.0),
        "texture_name": texture_name,
        "texture_builtin": texture_spec.get("builtin") if texture_spec else None,
        "texture_rgb1": texture_spec.get("rgb1") if texture_spec else None,
        "texture_rgb2": texture_spec.get("rgb2") if texture_spec else None,
        "texture_mark": texture_spec.get("mark") if texture_spec else None,
        "texture_markrgb": texture_spec.get("markrgb") if texture_spec else None,
        "texture_size": (
            [float(texture_spec["width"]), float(texture_spec["height"])]
            if texture_spec and texture_spec.get("width") is not None and texture_spec.get("height") is not None
            else None
        ),
        "texrepeat": (
            _vector_attr(material.get("texrepeat"), size=2, default=[1.0, 1.0])
            if material is not None and material.get("texrepeat")
            else [1.0, 1.0]
        ),
        "texuniform": (
            str(material.get("texuniform")).lower() == "true"
            if material is not None and material.get("texuniform") is not None
            else False
        ),
        "reflectance": float(material.get("reflectance") or 0.0) if material is not None else 0.0,
        "material_rgba": (
            material_specs_by_name.get(material_name or "", {}).get("rgba")
            if material_name
            else None
        ),
    }


def _build_light_manifest(root: ET.Element) -> list[dict[str, object]]:
    parent_map = _build_parent_map(root)
    lights: list[dict[str, object]] = []
    for light in root.iter("light"):
        name = light.get("name")
        if not name:
            continue
        parent_body_name = _nearest_parent_body_name(light, parent_map)
        lights.append(
            {
                "name": name,
                "parent_body_name": parent_body_name,
                "mode": light.get("mode"),
                "position": _vector_attr(light.get("pos"), size=3, default=[0.0, 0.0, 0.0]),
                "direction": (
                    _vector_attr(light.get("dir"), size=3, default=[0.0, 0.0, -1.0])
                    if light.get("dir")
                    else None
                ),
                "diffuse": (
                    _vector_attr(light.get("diffuse"), size=3, default=[1.0, 1.0, 1.0])
                    if light.get("diffuse")
                    else None
                ),
            }
        )
    return lights


def _build_parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _nearest_parent_body_name(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> str | None:
    parent = parent_map.get(element)
    while parent is not None:
        if parent.tag == "body" and parent.get("name"):
            return str(parent.get("name"))
        parent = parent_map.get(parent)
    return None


def export_official_walk_scene(output_dir: Path) -> dict[str, object]:
    environment = _build_walk_imitation_environment()
    _initialize_environment(environment)

    output_dir.mkdir(parents=True, exist_ok=True)
    exporter = _ensure_export_with_assets()
    exporter(environment.task.root_entity.mjcf_model, output_dir, ENTRY_XML)

    manifest = _build_manifest(output_dir, environment=environment)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write the exported official walk scene bundle.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the export manifest as JSON.",
    )
    args = parser.parse_args(argv)

    manifest = export_official_walk_scene(args.output_dir)

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"Exported official walk scene to {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
