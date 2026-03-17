import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_console_api_does_not_expose_legacy_roi_asset_routes(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    brain_asset_dir = tmp_path / "brain_assets"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    brain_asset_dir.mkdir()
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
                "neuropil_manifest": [
                    {
                        "neuropil": "AL",
                        "short_label": "AL",
                        "display_name": "Antennal Lobe",
                        "display_name_zh": "触角叶",
                        "group": "input-associated",
                        "description_zh": "正式显示的神经纤维区。",
                        "default_color": "#4ea8de",
                        "priority": 1,
                    }
                ],
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
        )
    )
    client = TestClient(app)

    route_paths = {route.path for route in app.routes}
    assert "/api/console/roi-assets" not in route_paths
    assert "/api/console/roi-mesh/{roi_id}" not in route_paths

    roi_assets_response = client.get("/api/console/roi-assets")
    assert roi_assets_response.status_code == 404

    roi_mesh_response = client.get("/api/console/roi-mesh/AL")
    assert roi_mesh_response.status_code == 404
