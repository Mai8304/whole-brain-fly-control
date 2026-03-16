import json
from pathlib import Path

import pytest


def test_load_roi_asset_pack_requires_core_fields(tmp_path: Path) -> None:
    from fruitfly.evaluation.roi_asset_pack import load_roi_asset_pack_manifest

    manifest_path = tmp_path / "roi_asset_pack.json"
    manifest_path.write_text(
        json.dumps(
            {
                "asset_id": "roi_pack_v1",
                "asset_version": "v1",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing keys"):
        load_roi_asset_pack_manifest(manifest_path)


def test_build_roi_asset_pack_manifest_registers_roi_meshes_and_mapping_summary() -> None:
    from fruitfly.evaluation.roi_asset_pack import build_roi_asset_pack_manifest

    manifest = build_roi_asset_pack_manifest(
        asset_id="roi_pack_v1",
        asset_version="v1",
        shell={
            "render_asset_path": "brain_shell.glb",
            "render_format": "glb",
        },
        roi_manifest_path="roi_manifest.json",
        node_roi_map_path="node_roi_map.parquet",
        roi_meshes=[
            {"roi_id": "AL", "render_asset_path": "roi_mesh/AL.glb", "render_format": "glb"},
            {"roi_id": "FB", "render_asset_path": "roi_mesh/FB.glb", "render_format": "glb"},
        ],
        mapping_coverage={"roi_mapped_nodes": 120000, "total_nodes": 139244},
    )

    assert manifest["shell"]["render_asset_path"] == "brain_shell.glb"
    assert manifest["roi_manifest_path"] == "roi_manifest.json"
    assert manifest["node_roi_map_path"] == "node_roi_map.parquet"
    assert manifest["roi_meshes"] == [
        {"roi_id": "AL", "render_asset_path": "roi_mesh/AL.glb", "render_format": "glb"},
        {"roi_id": "FB", "render_asset_path": "roi_mesh/FB.glb", "render_format": "glb"},
    ]
    assert manifest["mapping_coverage"] == {"roi_mapped_nodes": 120000, "total_nodes": 139244}


def test_write_and_load_roi_asset_pack_manifest_round_trip(tmp_path: Path) -> None:
    from fruitfly.evaluation.roi_asset_pack import (
        build_roi_asset_pack_manifest,
        load_roi_asset_pack_manifest,
        write_roi_asset_pack_manifest,
    )

    manifest = build_roi_asset_pack_manifest(
        asset_id="roi_pack_v1",
        asset_version="v1",
        shell={
            "render_asset_path": "brain_shell.glb",
            "render_format": "glb",
        },
        roi_manifest_path="roi_manifest.json",
        node_roi_map_path="node_roi_map.parquet",
        roi_meshes=[
            {"roi_id": "AL", "render_asset_path": "roi_mesh/AL.glb", "render_format": "glb"},
        ],
        mapping_coverage={"roi_mapped_nodes": 120000, "total_nodes": 139244},
    )
    manifest_path = tmp_path / "roi_asset_pack.json"

    write_roi_asset_pack_manifest(manifest_path, manifest)
    loaded = load_roi_asset_pack_manifest(manifest_path)

    assert loaded == manifest
