import json
from pathlib import Path
import pytest


def test_load_brain_asset_manifest_validates_shell_and_neuropil_contract(tmp_path: Path) -> None:
    from fruitfly.evaluation.brain_asset_manifest import load_brain_asset_manifest

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "asset_id": "flywire_brain_v141",
                "asset_version": "v141",
                "source": {
                    "provider": "flywire",
                    "cloudpath": "precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf",
                    "info_url": "https://storage.googleapis.com/flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf/info",
                    "mesh_segment_id": 1,
                },
                "shell": {
                    "render_asset_path": "brain_shell.glb",
                    "render_format": "glb",
                    "vertex_count": 8997,
                    "face_count": 18000,
                    "bbox_min": [213120.0, 77504.0, 760.0],
                    "bbox_max": [840512.0, 388160.0, 269560.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "neuropil_manifest": [
                    {
                        "neuropil": "MB",
                        "short_label": "MB",
                        "display_name": "Mushroom Body",
                        "display_name_zh": "蘑菇体",
                        "group": "core-processing",
                        "description_zh": "V1 中作为核心处理中间脑区展示。",
                        "default_color": "#f7b267",
                        "priority": 1,
                        "render_asset_path": "MB.glb",
                        "render_format": "glb",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = load_brain_asset_manifest(manifest_path)

    assert manifest["asset_id"] == "flywire_brain_v141"
    assert manifest["shell"]["render_asset_path"] == "brain_shell.glb"
    assert manifest["source"]["mesh_segment_id"] == 1
    assert manifest["neuropil_manifest"][0] == {
        "neuropil": "MB",
        "short_label": "MB",
        "display_name": "Mushroom Body",
        "display_name_zh": "蘑菇体",
        "group": "core-processing",
        "description_zh": "V1 中作为核心处理中间脑区展示。",
        "default_color": "#f7b267",
        "priority": 1,
        "render_asset_path": "MB.glb",
        "render_format": "glb",
    }


def test_build_default_neuropil_manifest_returns_representative_groups() -> None:
    from fruitfly.evaluation.brain_asset_manifest import build_default_neuropil_manifest

    neuropil_manifest = build_default_neuropil_manifest()

    assert len(neuropil_manifest) >= 6
    assert {entry["group"] for entry in neuropil_manifest} == {
        "input-associated",
        "core-processing",
        "output-associated",
    }
    assert neuropil_manifest[0]["neuropil"]


def test_load_brain_asset_manifest_validates_grouped_neuropil_mesh_contract(tmp_path: Path) -> None:
    from fruitfly.evaluation.brain_asset_manifest import load_brain_asset_manifest

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "asset_id": "flywire_brain_v141",
                "asset_version": "v141",
                "source": {
                    "provider": "flywire",
                    "cloudpath": "precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf",
                    "info_url": "https://storage.googleapis.com/flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf/info",
                    "mesh_segment_id": 1,
                },
                "shell": {
                    "render_asset_path": "brain_shell.glb",
                    "render_format": "glb",
                    "vertex_count": 8997,
                    "face_count": 18000,
                    "bbox_min": [213120.0, 77504.0, 760.0],
                    "bbox_max": [840512.0, 388160.0, 269560.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "neuropil_manifest": [
                    {
                        "neuropil": "AL",
                        "short_label": "AL",
                        "display_name": "Antennal Lobe",
                        "display_name_zh": "触角叶",
                        "group": "input-associated",
                        "description_zh": "V1 中作为气味输入相关神经纤维区的代表。",
                        "default_color": "#4ea8de",
                        "priority": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="brain asset neuropil entry missing keys"):
        load_brain_asset_manifest(manifest_path)


def test_checked_in_brain_asset_manifest_uses_neuropil_contract() -> None:
    manifest = json.loads(
        Path("outputs/ui-assets/flywire_brain_v141/manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["neuropil_manifest"]
    assert manifest["neuropil_manifest"][0]["neuropil"] == "AL"
    assert manifest["neuropil_manifest"][0]["render_asset_path"].endswith(".glb")
    assert manifest["neuropil_manifest"][0]["render_asset_path"].startswith(
        "../flywire_roi_meshes_v1/"
    )
