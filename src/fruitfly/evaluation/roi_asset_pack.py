from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REQUIRED_TOP_LEVEL_KEYS = {
    "asset_id",
    "asset_version",
    "shell",
    "roi_manifest_path",
    "node_roi_map_path",
    "roi_meshes",
    "mapping_coverage",
}
_REQUIRED_SHELL_KEYS = {"render_asset_path", "render_format"}
_REQUIRED_ROI_MESH_KEYS = {"roi_id", "render_asset_path", "render_format"}
_REQUIRED_MAPPING_COVERAGE_KEYS = {"roi_mapped_nodes", "total_nodes"}


def build_roi_asset_pack_manifest(
    *,
    asset_id: str,
    asset_version: str,
    shell: dict[str, Any],
    roi_manifest_path: str,
    node_roi_map_path: str,
    roi_meshes: list[dict[str, Any]],
    mapping_coverage: dict[str, int],
) -> dict[str, Any]:
    manifest = {
        "asset_id": str(asset_id),
        "asset_version": str(asset_version),
        "shell": {
            "render_asset_path": str(shell["render_asset_path"]),
            "render_format": str(shell["render_format"]),
        },
        "roi_manifest_path": str(roi_manifest_path),
        "node_roi_map_path": str(node_roi_map_path),
        "roi_meshes": [
            {
                "roi_id": str(entry["roi_id"]),
                "render_asset_path": str(entry["render_asset_path"]),
                "render_format": str(entry["render_format"]),
            }
            for entry in roi_meshes
        ],
        "mapping_coverage": {
            "roi_mapped_nodes": int(mapping_coverage["roi_mapped_nodes"]),
            "total_nodes": int(mapping_coverage["total_nodes"]),
        },
    }
    _validate_roi_asset_pack_manifest(manifest)
    return manifest


def write_roi_asset_pack_manifest(path: Path, manifest: dict[str, Any]) -> None:
    _validate_roi_asset_pack_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_roi_asset_pack_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _validate_roi_asset_pack_manifest(manifest)
    return manifest


def _validate_roi_asset_pack_manifest(manifest: dict[str, Any]) -> None:
    missing_top_level = _REQUIRED_TOP_LEVEL_KEYS - set(manifest)
    if missing_top_level:
        raise ValueError(f"roi asset pack missing keys: {sorted(missing_top_level)}")

    missing_shell = _REQUIRED_SHELL_KEYS - set(manifest["shell"])
    if missing_shell:
        raise ValueError(f"roi asset pack shell missing keys: {sorted(missing_shell)}")

    roi_meshes = manifest["roi_meshes"]
    if not isinstance(roi_meshes, list) or not roi_meshes:
        raise ValueError("roi asset pack roi_meshes must be a non-empty list")
    for entry in roi_meshes:
        missing_roi_mesh = _REQUIRED_ROI_MESH_KEYS - set(entry)
        if missing_roi_mesh:
            raise ValueError(f"roi asset pack roi_mesh entry missing keys: {sorted(missing_roi_mesh)}")

    missing_mapping = _REQUIRED_MAPPING_COVERAGE_KEYS - set(manifest["mapping_coverage"])
    if missing_mapping:
        raise ValueError(
            f"roi asset pack mapping_coverage missing keys: {sorted(missing_mapping)}"
        )
