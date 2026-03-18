from __future__ import annotations

import argparse
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

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


def _build_manifest(output_dir: Path) -> dict[str, object]:
    entry_xml_path = output_dir / ENTRY_XML
    body_manifest, geom_manifest, camera_presets = _build_scene_manifests(entry_xml_path)
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
        "body_manifest": body_manifest,
        "geom_manifest": geom_manifest,
        "output_dir": str(output_dir),
    }


def _build_scene_manifests(entry_xml_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    root = ET.parse(entry_xml_path).getroot()
    mesh_defaults_by_class = _build_mesh_defaults_by_class(root)
    mesh_file_by_name = {
        str(mesh.get("name")): {
            "file": str(mesh.get("file")),
            "scale": _resolve_mesh_scale(mesh, mesh_defaults_by_class),
        }
        for mesh in root.findall("./asset/mesh")
        if mesh.get("name") and mesh.get("file")
    }
    available_camera_ids = {
        str(camera.get("name"))
        for camera in root.iter("camera")
        if camera.get("name")
    }
    camera_presets = [
        preset
        for preset, camera_id in (
            ("track", "walker/track1"),
            ("side", "walker/side"),
            ("back", "walker/back"),
            ("top", "top_camera"),
        )
        if camera_id in available_camera_ids
    ]

    body_manifest: list[dict[str, object]] = []
    geom_manifest: list[dict[str, object]] = []
    worldbody = root.find("worldbody")
    if worldbody is None:
        return body_manifest, geom_manifest, camera_presets

    for body in worldbody.findall("body"):
        _collect_body_and_geom_manifests(
            body,
            parent_body_name=None,
            body_manifest=body_manifest,
            geom_manifest=geom_manifest,
            mesh_file_by_name=mesh_file_by_name,
        )
    return body_manifest, geom_manifest, camera_presets


def _collect_body_and_geom_manifests(
    body: ET.Element,
    *,
    parent_body_name: str | None,
    body_manifest: list[dict[str, object]],
    geom_manifest: list[dict[str, object]],
    mesh_file_by_name: dict[str, dict[str, object]],
) -> None:
    body_name = body.get("name")
    effective_parent = parent_body_name
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
        geom_manifest.append(
            {
                "geom_name": geom_name,
                "body_name": body_name,
                "mesh_asset_path": str(mesh_entry["file"]),
                "mesh_scale": [float(value) for value in mesh_entry["scale"]],
                "local_position": _vector_attr(geom.get("pos"), size=3, default=[0.0, 0.0, 0.0]),
                "local_quaternion": _vector_attr(geom.get("quat"), size=4, default=[1.0, 0.0, 0.0, 0.0]),
            }
        )
        geom_names.append(geom_name)

    if body_name and geom_names:
        body_manifest[-1]["renderable"] = True

    for child in body.findall("body"):
        _collect_body_and_geom_manifests(
            child,
            parent_body_name=effective_parent,
            body_manifest=body_manifest,
            geom_manifest=geom_manifest,
            mesh_file_by_name=mesh_file_by_name,
        )


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


def _build_mesh_defaults_by_class(root: ET.Element) -> dict[str, dict[str, list[float]]]:
    defaults_root = root.find("default")
    if defaults_root is None:
        return {}

    mesh_defaults: dict[str, dict[str, list[float]]] = {}
    for child in defaults_root.findall("default"):
        _collect_mesh_defaults(child, parent_defaults={}, output=mesh_defaults)
    return mesh_defaults


def _collect_mesh_defaults(
    default_element: ET.Element,
    *,
    parent_defaults: dict[str, list[float]],
    output: dict[str, dict[str, list[float]]],
) -> None:
    resolved_defaults = dict(parent_defaults)
    mesh_element = default_element.find("mesh")
    if mesh_element is not None and mesh_element.get("scale"):
        resolved_defaults["scale"] = _vector_attr(
            mesh_element.get("scale"),
            size=3,
            default=[1.0, 1.0, 1.0],
        )

    class_name = default_element.get("class")
    if class_name:
        output[class_name] = dict(resolved_defaults)

    for child in default_element.findall("default"):
        _collect_mesh_defaults(child, parent_defaults=resolved_defaults, output=output)


def _resolve_mesh_scale(
    mesh_element: ET.Element,
    mesh_defaults_by_class: dict[str, dict[str, list[float]]],
) -> list[float]:
    raw_scale = mesh_element.get("scale")
    if raw_scale:
        return _vector_attr(raw_scale, size=3, default=[1.0, 1.0, 1.0])

    class_name = mesh_element.get("class")
    if class_name and class_name in mesh_defaults_by_class:
        class_defaults = mesh_defaults_by_class[class_name]
        if "scale" in class_defaults:
            return list(class_defaults["scale"])

    return [1.0, 1.0, 1.0]


def export_official_walk_scene(output_dir: Path) -> dict[str, object]:
    environment = _build_walk_imitation_environment()
    _initialize_environment(environment)

    output_dir.mkdir(parents=True, exist_ok=True)
    exporter = _ensure_export_with_assets()
    exporter(environment.task.root_entity.mjcf_model, output_dir, ENTRY_XML)

    manifest = _build_manifest(output_dir)
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
