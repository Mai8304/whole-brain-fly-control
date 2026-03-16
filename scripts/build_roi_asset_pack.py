from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from fruitfly.evaluation.roi_asset_pack import (
    build_roi_asset_pack_manifest,
    write_roi_asset_pack_manifest,
)
from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

DEFAULT_OUTPUT_DIR = Path("outputs/ui-assets/flywire_roi_pack_v1")


def build_roi_asset_pack(
    *,
    shell_asset_dir: Path,
    node_roi_map_path: Path,
    output_dir: Path,
    roi_mesh_dir: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_roi_mesh_dir = output_dir / "roi_mesh"
    output_roi_mesh_dir.mkdir(parents=True, exist_ok=True)

    shell_manifest = json.loads((shell_asset_dir / "manifest.json").read_text(encoding="utf-8"))
    shell_asset_path = shell_asset_dir / shell_manifest["shell"]["render_asset_path"]
    shell_output_path = output_dir / shell_asset_path.name
    shutil.copyfile(shell_asset_path, shell_output_path)

    roi_manifest = build_v1_roi_manifest()
    (output_dir / "roi_manifest.json").write_text(json.dumps(roi_manifest, indent=2), encoding="utf-8")

    node_roi_map_output_path = output_dir / node_roi_map_path.name
    shutil.copyfile(node_roi_map_path, node_roi_map_output_path)

    roi_meshes: list[dict[str, str]] = []
    source_roi_meshes = _resolve_roi_mesh_sources(roi_manifest=roi_manifest, roi_mesh_dir=roi_mesh_dir)
    for entry in roi_manifest:
        roi_mesh_path = output_roi_mesh_dir / f'{entry["roi_id"]}.glb'
        source_path = source_roi_meshes.get(str(entry["roi_id"]))
        if source_path is None:
            roi_mesh_path.write_bytes(b"glb")
        else:
            shutil.copyfile(source_path, roi_mesh_path)
        roi_meshes.append(
            {
                "roi_id": str(entry["roi_id"]),
                "render_asset_path": str(roi_mesh_path.relative_to(output_dir)),
                "render_format": "glb",
            }
        )

    manifest = build_roi_asset_pack_manifest(
        asset_id="flywire_roi_pack_v1",
        asset_version="v1",
        shell={
            "render_asset_path": shell_output_path.name,
            "render_format": str(shell_manifest["shell"]["render_format"]),
        },
        roi_manifest_path="roi_manifest.json",
        node_roi_map_path=node_roi_map_output_path.name,
        roi_meshes=roi_meshes,
        mapping_coverage={
            "roi_mapped_nodes": 0,
            "total_nodes": 0,
        },
    )
    write_roi_asset_pack_manifest(output_dir / "manifest.json", manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a representative ROI asset pack for the neural console.")
    parser.add_argument(
        "--shell-asset-dir",
        type=Path,
        required=True,
        help="Directory containing an existing FlyWire brain shell manifest and brain_shell.glb.",
    )
    parser.add_argument(
        "--node-roi-map-path",
        type=Path,
        required=True,
        help="Path to the compiled node_roi_map.parquet file to copy into the asset pack.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the ROI asset-pack files are written.",
    )
    parser.add_argument(
        "--roi-mesh-dir",
        type=Path,
        default=None,
        help="Optional directory containing real <ROI_ID>.glb files for the V1 ROI set.",
    )
    parser.add_argument("--json", action="store_true", help="Print the built ROI asset-pack manifest as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build_roi_asset_pack(
        shell_asset_dir=args.shell_asset_dir,
        node_roi_map_path=args.node_roi_map_path,
        output_dir=args.output_dir,
        roi_mesh_dir=args.roi_mesh_dir,
    )
    if args.json:
        print(json.dumps(manifest))
    else:
        print(args.output_dir / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
def _resolve_roi_mesh_sources(
    *,
    roi_manifest: list[dict[str, Any]],
    roi_mesh_dir: Path | None,
) -> dict[str, Path]:
    if roi_mesh_dir is None:
        return {}

    source_paths: dict[str, Path] = {}
    missing_roi_ids: list[str] = []
    for entry in roi_manifest:
        roi_id = str(entry["roi_id"])
        mesh_path = roi_mesh_dir / f"{roi_id}.glb"
        if not mesh_path.exists():
            missing_roi_ids.append(roi_id)
            continue
        source_paths[roi_id] = mesh_path

    if missing_roi_ids:
        raise ValueError(f"missing ROI mesh files: {', '.join(missing_roi_ids)}")

    return source_paths
