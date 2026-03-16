from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .roi_manifest import REQUIRED_ROI_MANIFEST_KEYS, build_v1_roi_manifest

DEFAULT_FLYWIRE_BRAIN_CLOUDPATH = (
    "precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf"
)

_REQUIRED_SOURCE_KEYS = {"provider", "cloudpath", "info_url", "mesh_segment_id"}
_REQUIRED_SHELL_KEYS = {
    "render_asset_path",
    "render_format",
    "vertex_count",
    "face_count",
    "bbox_min",
    "bbox_max",
    "base_color",
    "opacity",
}
def build_default_roi_manifest() -> list[dict[str, Any]]:
    return build_v1_roi_manifest()


def build_brain_asset_manifest(
    *,
    asset_id: str,
    asset_version: str,
    source: dict[str, Any],
    shell: dict[str, Any],
    roi_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = {
        "asset_id": str(asset_id),
        "asset_version": str(asset_version),
        "source": {
            "provider": str(source["provider"]),
            "cloudpath": str(source["cloudpath"]),
            "info_url": str(source["info_url"]),
            "mesh_segment_id": int(source["mesh_segment_id"]),
        },
        "shell": {
            "render_asset_path": str(shell["render_asset_path"]),
            "render_format": str(shell["render_format"]),
            "vertex_count": int(shell["vertex_count"]),
            "face_count": int(shell["face_count"]),
            "bbox_min": [float(value) for value in shell["bbox_min"]],
            "bbox_max": [float(value) for value in shell["bbox_max"]],
            "base_color": str(shell["base_color"]),
            "opacity": float(shell["opacity"]),
        },
        "roi_manifest": list(roi_manifest or build_default_roi_manifest()),
    }
    _validate_brain_asset_manifest(manifest)
    return manifest


def write_brain_asset_manifest(path: Path, manifest: dict[str, Any]) -> None:
    _validate_brain_asset_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_brain_asset_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _validate_brain_asset_manifest(manifest)
    return manifest


def with_runtime_asset_urls(
    manifest: dict[str, Any],
    *,
    shell_asset_url: str | None = None,
) -> dict[str, Any]:
    payload = json.loads(json.dumps(manifest))
    if shell_asset_url is not None:
        payload.setdefault("shell", {})
        payload["shell"]["asset_url"] = shell_asset_url
    return payload


def _validate_brain_asset_manifest(manifest: dict[str, Any]) -> None:
    missing_top_level = {"asset_id", "asset_version", "source", "shell", "roi_manifest"} - set(
        manifest
    )
    if missing_top_level:
        raise ValueError(f"brain asset manifest missing keys: {sorted(missing_top_level)}")

    missing_source = _REQUIRED_SOURCE_KEYS - set(manifest["source"])
    if missing_source:
        raise ValueError(f"brain asset source missing keys: {sorted(missing_source)}")

    missing_shell = _REQUIRED_SHELL_KEYS - set(manifest["shell"])
    if missing_shell:
        raise ValueError(f"brain asset shell missing keys: {sorted(missing_shell)}")

    roi_manifest = manifest["roi_manifest"]
    if not isinstance(roi_manifest, list) or not roi_manifest:
        raise ValueError("brain asset manifest roi_manifest must be a non-empty list")
    for entry in roi_manifest:
        missing_roi_keys = REQUIRED_ROI_MANIFEST_KEYS - set(entry)
        if missing_roi_keys:
            raise ValueError(f"brain asset roi entry missing keys: {sorted(missing_roi_keys)}")
