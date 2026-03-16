import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_console_api_exposes_roi_asset_pack_and_mesh_routes(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    brain_asset_dir = tmp_path / "brain_assets"
    roi_asset_dir = tmp_path / "roi_assets"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    brain_asset_dir.mkdir()
    (roi_asset_dir / "roi_mesh").mkdir(parents=True)
    checkpoint_path.write_bytes(b"checkpoint")
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps(
            {
                "node_count": 139244,
                "edge_count": 15091494,
                "afferent_count": 19259,
                "intrinsic_count": 118496,
                "efferent_count": 1489,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 64,
                "steps_completed": 64,
                "terminated_early": False,
                "reward_mean": 1.0,
                "final_reward": 1.0,
                "mean_action_norm": 3.4,
                "forward_velocity_mean": 0.94,
                "forward_velocity_std": 0.57,
                "body_upright_mean": 0.98,
                "final_heading_delta": -108.53,
            }
        ),
        encoding="utf-8",
    )
    (brain_asset_dir / "brain_shell.glb").write_bytes(b"glb")
    (brain_asset_dir / "manifest.json").write_text(
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
                    "bbox_min": [0.0, 0.0, 0.0],
                    "bbox_max": [1.0, 1.0, 1.0],
                    "base_color": "#89a5ff",
                    "opacity": 0.18,
                },
                "roi_manifest": [
                    {
                        "roi_id": "AL",
                        "short_label": "AL",
                        "display_name": "Antennal Lobe",
                        "display_name_zh": "触角叶",
                        "group": "input-associated",
                        "description_zh": "V1 中作为气味输入相关脑区的代表。",
                        "default_color": "#4ea8de",
                        "priority": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (roi_asset_dir / "roi_manifest.json").write_text(
        json.dumps(
            [
                {
                    "roi_id": "AL",
                    "short_label": "AL",
                    "display_name": "Antennal Lobe",
                    "display_name_zh": "触角叶",
                    "group": "input-associated",
                    "description_zh": "V1 中作为气味输入相关脑区的代表。",
                    "default_color": "#4ea8de",
                    "priority": 1,
                }
            ]
        ),
        encoding="utf-8",
    )
    (roi_asset_dir / "node_roi_map.parquet").write_bytes(b"parquet")
    (roi_asset_dir / "roi_mesh" / "AL.glb").write_bytes(b"roi-glb")
    (roi_asset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "asset_id": "flywire_roi_pack_v1",
                "asset_version": "v1",
                "shell": {"render_asset_path": "brain_shell.glb", "render_format": "glb"},
                "roi_manifest_path": "roi_manifest.json",
                "node_roi_map_path": "node_roi_map.parquet",
                "roi_meshes": [
                    {"roi_id": "AL", "render_asset_path": "roi_mesh/AL.glb", "render_format": "glb"}
                ],
                "mapping_coverage": {"roi_mapped_nodes": 120000, "total_nodes": 139244},
            }
        ),
        encoding="utf-8",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=checkpoint_path,
            brain_asset_dir=brain_asset_dir,
            roi_asset_dir=roi_asset_dir,
        )
    )
    client = TestClient(app)

    roi_assets_response = client.get("/api/console/roi-assets")
    assert roi_assets_response.status_code == 200
    roi_assets_payload = roi_assets_response.json()
    assert roi_assets_payload["asset_id"] == "flywire_roi_pack_v1"
    assert roi_assets_payload["roi_meshes"][0]["asset_url"] == "/api/console/roi-mesh/AL"
    assert roi_assets_payload["mapping_coverage"] == {"roi_mapped_nodes": 120000, "total_nodes": 139244}

    roi_mesh_response = client.get("/api/console/roi-mesh/AL")
    assert roi_mesh_response.status_code == 200
    assert roi_mesh_response.headers["content-type"] == "model/gltf-binary"
    assert roi_mesh_response.content == b"roi-glb"
