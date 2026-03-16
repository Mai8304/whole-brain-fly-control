from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from fruitfly.evaluation.brain_asset_manifest import (
    DEFAULT_FLYWIRE_BRAIN_CLOUDPATH,
    build_brain_asset_manifest,
    write_brain_asset_manifest,
)

DEFAULT_OUTPUT_DIR = Path("outputs/ui-assets/flywire_brain_v141")


def import_flywire_brain_mesh_asset(
    *,
    output_dir: Path,
    cloudpath: str = DEFAULT_FLYWIRE_BRAIN_CLOUDPATH,
    mesh_segment_id: int = 1,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    info_url = cloudpath_to_info_url(cloudpath)
    source_info = fetch_source_info(info_url)
    (output_dir / "source_info.json").write_text(json.dumps(source_info, indent=2), encoding="utf-8")

    mesh = fetch_shell_mesh(cloudpath=cloudpath, mesh_segment_id=mesh_segment_id)
    shell_path = output_dir / "brain_shell.glb"
    export_shell_glb(mesh=mesh, output_path=shell_path)

    manifest = build_brain_asset_manifest(
        asset_id="flywire_brain_v141",
        asset_version="v141",
        source={
            "provider": "flywire",
            "cloudpath": cloudpath,
            "info_url": info_url,
            "mesh_segment_id": mesh_segment_id,
        },
        shell={
            "render_asset_path": shell_path.name,
            "render_format": "glb",
            "vertex_count": int(mesh.vertices.shape[0]),
            "face_count": int(mesh.faces.shape[0]),
            "bbox_min": [float(value) for value in mesh.vertices.min(axis=0)],
            "bbox_max": [float(value) for value in mesh.vertices.max(axis=0)],
            "base_color": "#89a5ff",
            "opacity": 0.18,
        },
    )
    write_brain_asset_manifest(output_dir / "manifest.json", manifest)
    return manifest


def cloudpath_to_info_url(cloudpath: str) -> str:
    prefix = "precomputed://gs://"
    if not cloudpath.startswith(prefix):
        raise ValueError(f"unsupported FlyWire cloudpath: {cloudpath}")
    bucket_and_path = cloudpath[len(prefix) :]
    bucket, object_path = bucket_and_path.split("/", 1)
    return f"https://storage.googleapis.com/{bucket}/{object_path}/info"


def fetch_source_info(info_url: str) -> dict[str, Any]:
    with urlopen(info_url, timeout=30) as response:  # noqa: S310
        return json.load(response)


def fetch_shell_mesh(*, cloudpath: str, mesh_segment_id: int):
    try:
        from cloudvolume import CloudVolume
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "cloudvolume is not installed. Run FlyWire brain-mesh import from the dedicated .venv-flywire environment."
        ) from exc

    volume = CloudVolume(cloudpath, progress=False, use_https=True)
    return volume.mesh.get(mesh_segment_id)


def export_shell_glb(*, mesh, output_path: Path) -> None:
    try:
        import trimesh
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "trimesh is not installed. Run FlyWire brain-mesh import from the dedicated .venv-flywire environment."
        ) from exc

    render_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    render_mesh.export(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import FlyWire brain mesh assets for the neural console.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where manifest.json, source_info.json, and brain_shell.glb are written.",
    )
    parser.add_argument(
        "--cloudpath",
        default=DEFAULT_FLYWIRE_BRAIN_CLOUDPATH,
        help="FlyWire precomputed cloudpath for the whole-brain shell asset.",
    )
    parser.add_argument(
        "--mesh-segment-id",
        type=int,
        default=1,
        help="Segment ID to fetch from the FlyWire whole-brain shell asset.",
    )
    parser.add_argument("--json", action="store_true", help="Print the imported manifest as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = import_flywire_brain_mesh_asset(
        output_dir=args.output_dir,
        cloudpath=args.cloudpath,
        mesh_segment_id=args.mesh_segment_id,
    )
    if args.json:
        print(json.dumps(manifest))
    else:
        print(args.output_dir / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
