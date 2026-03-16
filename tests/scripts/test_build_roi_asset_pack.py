import json
from pathlib import Path

import pytest


def test_build_roi_asset_pack_cli_writes_pack_layout(tmp_path: Path) -> None:
    from scripts import build_roi_asset_pack

    shell_asset_dir = tmp_path / "shell_asset"
    shell_asset_dir.mkdir(parents=True, exist_ok=True)
    (shell_asset_dir / "brain_shell.glb").write_bytes(b"glb")
    (shell_asset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "asset_id": "flywire_brain_v141",
                "asset_version": "v141",
                "source": {
                    "provider": "flywire",
                    "cloudpath": "precomputed://gs://example",
                    "info_url": "https://example/info",
                    "mesh_segment_id": 1,
                },
                "shell": {
                    "render_asset_path": "brain_shell.glb",
                    "render_format": "glb",
                    "vertex_count": 1,
                    "face_count": 1,
                    "bbox_min": [0.0, 0.0, 0.0],
                    "bbox_max": [1.0, 1.0, 1.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "roi_manifest": [],
            }
        ),
        encoding="utf-8",
    )

    node_roi_map_path = tmp_path / "node_roi_map.parquet"
    node_roi_map_path.write_bytes(b"parquet")
    output_dir = tmp_path / "roi_pack"

    exit_code = build_roi_asset_pack.main(
        [
            "--shell-asset-dir",
            str(shell_asset_dir),
            "--node-roi-map-path",
            str(node_roi_map_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "roi_manifest.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "roi_mesh" / "AL.glb").exists()

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["shell"]["render_asset_path"] == "brain_shell.glb"
    assert manifest["roi_manifest_path"] == "roi_manifest.json"
    assert manifest["node_roi_map_path"] == "node_roi_map.parquet"
    assert manifest["roi_meshes"][0]["render_asset_path"].startswith("roi_mesh/")


def test_build_roi_asset_pack_cli_copies_real_roi_meshes_when_mesh_dir_is_provided(
    tmp_path: Path,
) -> None:
    from scripts import build_roi_asset_pack

    shell_asset_dir = tmp_path / "shell_asset"
    shell_asset_dir.mkdir(parents=True, exist_ok=True)
    (shell_asset_dir / "brain_shell.glb").write_bytes(b"shell-glb")
    (shell_asset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "asset_id": "flywire_brain_v141",
                "asset_version": "v141",
                "source": {
                    "provider": "flywire",
                    "cloudpath": "precomputed://gs://example",
                    "info_url": "https://example/info",
                    "mesh_segment_id": 1,
                },
                "shell": {
                    "render_asset_path": "brain_shell.glb",
                    "render_format": "glb",
                    "vertex_count": 1,
                    "face_count": 1,
                    "bbox_min": [0.0, 0.0, 0.0],
                    "bbox_max": [1.0, 1.0, 1.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "roi_manifest": [],
            }
        ),
        encoding="utf-8",
    )
    roi_mesh_dir = tmp_path / "real_roi_meshes"
    roi_mesh_dir.mkdir(parents=True, exist_ok=True)
    for roi_id in ["AL", "LH", "PB", "FB", "EB", "NO", "LAL", "GNG"]:
        (roi_mesh_dir / f"{roi_id}.glb").write_bytes(f"real-{roi_id}".encode("utf-8"))

    node_roi_map_path = tmp_path / "node_roi_map.parquet"
    node_roi_map_path.write_bytes(b"parquet")
    output_dir = tmp_path / "roi_pack"

    exit_code = build_roi_asset_pack.main(
        [
            "--shell-asset-dir",
            str(shell_asset_dir),
            "--node-roi-map-path",
            str(node_roi_map_path),
            "--roi-mesh-dir",
            str(roi_mesh_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "roi_mesh" / "AL.glb").read_bytes() == b"real-AL"
    assert (output_dir / "roi_mesh" / "GNG.glb").read_bytes() == b"real-GNG"


def test_build_roi_asset_pack_rejects_incomplete_roi_mesh_dir(tmp_path: Path) -> None:
    from scripts.build_roi_asset_pack import build_roi_asset_pack

    shell_asset_dir = tmp_path / "shell_asset"
    shell_asset_dir.mkdir(parents=True, exist_ok=True)
    (shell_asset_dir / "brain_shell.glb").write_bytes(b"shell-glb")
    (shell_asset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "asset_id": "flywire_brain_v141",
                "asset_version": "v141",
                "source": {
                    "provider": "flywire",
                    "cloudpath": "precomputed://gs://example",
                    "info_url": "https://example/info",
                    "mesh_segment_id": 1,
                },
                "shell": {
                    "render_asset_path": "brain_shell.glb",
                    "render_format": "glb",
                    "vertex_count": 1,
                    "face_count": 1,
                    "bbox_min": [0.0, 0.0, 0.0],
                    "bbox_max": [1.0, 1.0, 1.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "roi_manifest": [],
            }
        ),
        encoding="utf-8",
    )
    roi_mesh_dir = tmp_path / "real_roi_meshes"
    roi_mesh_dir.mkdir(parents=True, exist_ok=True)
    (roi_mesh_dir / "AL.glb").write_bytes(b"real-AL")
    node_roi_map_path = tmp_path / "node_roi_map.parquet"
    node_roi_map_path.write_bytes(b"parquet")

    with pytest.raises(ValueError, match="missing ROI mesh files"):
        build_roi_asset_pack(
            shell_asset_dir=shell_asset_dir,
            node_roi_map_path=node_roi_map_path,
            output_dir=tmp_path / "roi_pack",
            roi_mesh_dir=roi_mesh_dir,
        )
