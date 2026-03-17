import json
from pathlib import Path

from fastapi.testclient import TestClient
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def test_console_api_serves_realistic_read_only_payloads(tmp_path: Path) -> None:
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
    (eval_dir / "rollout.mp4").write_bytes(b"fake-video")
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
                        "roi_id": "MB",
                        "short_label": "MB",
                        "display_name": "Mushroom Body",
                        "display_name_zh": "蘑菇体",
                        "group": "core-processing",
                        "description_zh": "V1 中作为核心处理中间脑区展示。",
                        "default_color": "#f7b267",
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

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}

    session_response = client.get("/api/console/session")
    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert session_payload["mode"] == "Experiment"
    assert session_payload["task"] == "straight_walking"
    assert session_payload["action_provenance"]["direct_action_editing"] is False
    assert session_payload["action_provenance"]["joint_override"] is False

    pipeline_response = client.get("/api/console/pipeline")
    assert pipeline_response.status_code == 200
    pipeline_payload = pipeline_response.json()
    assert len(pipeline_payload["stages"]) == 6
    assert all(stage["status"] == "done" for stage in pipeline_payload["stages"])

    summary_response = client.get("/api/console/summary")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["reward_mean"] == 1.0
    assert summary_payload["video_url"] == "/api/console/video"

    brain_response = client.get("/api/console/brain-view")
    assert brain_response.status_code == 200
    brain_payload = brain_response.json()
    assert brain_payload["data_status"] == "unavailable"
    assert brain_payload["semantic_scope"] == "neuropil"
    assert brain_payload["view_mode"] == "grouped-neuropil-v1"
    assert brain_payload["mapping_mode"] == "node_neuropil_occupancy"
    assert brain_payload["activity_metric"] == "activity_mass"
    assert brain_payload["validation_passed"] is False
    assert brain_payload["graph_scope_validation_passed"] is False
    assert brain_payload["roster_alignment_passed"] is False
    assert brain_payload["shell"]["asset_id"] == "flywire_brain_v141"
    assert brain_payload["shell"]["asset_url"] == "/api/console/brain-shell"
    assert brain_payload["mapping_coverage"]["total_nodes"] == 139244
    assert brain_payload["mapping_coverage"]["neuropil_mapped_nodes"] == 0
    assert brain_payload["top_regions"] == []
    assert brain_payload["top_nodes"] == []
    assert brain_payload["formal_truth"]["validation_passed"] is False

    brain_assets_response = client.get("/api/console/brain-assets")
    assert brain_assets_response.status_code == 200
    brain_assets_payload = brain_assets_response.json()
    assert brain_assets_payload["asset_id"] == "flywire_brain_v141"
    assert brain_assets_payload["shell"]["asset_url"] == "/api/console/brain-shell"

    brain_shell_response = client.get("/api/console/brain-shell")
    assert brain_shell_response.status_code == 200
    assert brain_shell_response.headers["content-type"] == "model/gltf-binary"
    assert brain_shell_response.content == b"glb"

    timeline_response = client.get("/api/console/timeline")
    assert timeline_response.status_code == 200
    timeline_payload = timeline_response.json()
    assert timeline_payload["data_status"] == "unavailable"
    assert timeline_payload["current_step"] == 64
    assert timeline_payload["events"] == []

    video_response = client.get("/api/console/video")
    assert video_response.status_code == 200
    assert video_response.headers["content-type"] == "video/mp4"
    assert video_response.content == b"fake-video"


def test_console_api_prefers_recorded_brain_and_timeline_payloads(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    checkpoint_path.write_bytes(b"checkpoint")
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps({"node_count": 100, "edge_count": 200, "afferent_count": 10, "intrinsic_count": 80, "efferent_count": 10}),
        encoding="utf-8",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 4,
                    "materialization": 783,
                    "dataset": "public",
                }
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {
                    "alignment_passed": False,
                    "graph_only_root_count": 1,
                    "proofread_only_root_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 8,
                "steps_completed": 8,
                "terminated_early": False,
                "reward_mean": 1.0,
                "final_reward": 1.0,
                "mean_action_norm": 1.2,
                "forward_velocity_mean": 0.2,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.95,
                "final_heading_delta": -2.0,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "brain_view.json").write_text(
        json.dumps(
            {
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "grouped-neuropil-v1",
                "mapping_mode": "node_neuropil_occupancy",
                "activity_metric": "activity_mass",
                "formal_truth": {
                    "validation_passed": True,
                    "graph_scope_validation_passed": True,
                    "roster_alignment_passed": False,
                },
                "mapping_coverage": {"neuropil_mapped_nodes": 50, "total_nodes": 100},
                "region_activity": [],
                "top_regions": [],
                "top_nodes": [],
                "afferent_activity": 0.1,
                "intrinsic_activity": 0.2,
                "efferent_activity": 0.3,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "timeline.json").write_text(
        json.dumps(
            {
                "data_status": "recorded",
                "steps_requested": 8,
                "steps_completed": 8,
                "current_step": 5,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [{"step_id": 3, "event_type": "recorded", "label": "captured"}],
            }
        ),
        encoding="utf-8",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=checkpoint_path,
        )
    )
    client = TestClient(app)

    brain_payload = client.get("/api/console/brain-view").json()
    timeline_payload = client.get("/api/console/timeline").json()

    assert brain_payload["data_status"] == "recorded"
    assert brain_payload["mapping_coverage"]["neuropil_mapped_nodes"] == 50
    assert brain_payload["mapping_mode"] == "node_neuropil_occupancy"
    assert brain_payload["validation_passed"] is True
    assert brain_payload["graph_scope_validation_passed"] is True
    assert brain_payload["roster_alignment_passed"] is False
    assert brain_payload["materialization"] == 783
    assert brain_payload["dataset"] == "public"
    assert timeline_payload["data_status"] == "recorded"


def test_console_api_materializes_recorded_brain_and_timeline_from_activity_trace(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps({"node_count": 4, "edge_count": 3, "afferent_count": 1, "intrinsic_count": 2, "efferent_count": 1}),
        encoding="utf-8",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
                {"source_id": 20, "node_idx": 1},
                {"source_id": 30, "node_idx": 2},
                {"source_id": 40, "node_idx": 3},
            ]
        ),
        compiled_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "pre_count": 1,
                    "post_count": 0,
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "AL_R",
                    "pre_count": 1,
                    "post_count": 0,
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 30,
                    "node_idx": 2,
                    "neuropil": "FB",
                    "pre_count": 1,
                    "post_count": 0,
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {
                    "alignment_passed": True,
                    "graph_only_root_count": 0,
                    "proofread_only_root_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 4,
                "steps_completed": 4,
                "terminated_early": False,
                "reward_mean": 1.0,
                "final_reward": 1.0,
                "mean_action_norm": 1.2,
                "forward_velocity_mean": 0.3,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.95,
                "final_heading_delta": 0.2,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "task": "straight_walking",
                "steps_requested": 4,
                "steps_completed": 4,
                "terminated_early": False,
                "snapshots": [
                    {
                        "step_id": 1,
                        "afferent_activity": 0.1,
                        "intrinsic_activity": 0.2,
                        "efferent_activity": 0.3,
                        "top_active_nodes": [{"node_idx": 1, "activity_value": 0.6, "flow_role": "intrinsic"}],
                    },
                    {
                        "step_id": 4,
                        "afferent_activity": 0.4,
                        "intrinsic_activity": 0.5,
                        "efferent_activity": 0.6,
                        "top_active_nodes": [{"node_idx": 2, "activity_value": 0.9, "flow_role": "efferent"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.2, 0.6, 0.9, 0.1], dtype=np.float32))

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    brain_payload = client.get("/api/console/brain-view").json()
    timeline_payload = client.get("/api/console/timeline").json()

    assert brain_payload["data_status"] == "recorded"
    assert brain_payload["semantic_scope"] == "neuropil"
    assert brain_payload["mapping_mode"] == "node_neuropil_occupancy"
    assert brain_payload["activity_metric"] == "activity_mass"
    assert brain_payload["validation_passed"] is True
    assert brain_payload["graph_scope_validation_passed"] is True
    assert brain_payload["roster_alignment_passed"] is True
    assert brain_payload["materialization"] == 783
    assert brain_payload["dataset"] == "public"
    assert brain_payload["top_regions"][0]["neuropil_id"] == "FB"
    assert brain_payload["top_nodes"][0]["source_id"] == "30"
    assert brain_payload["top_nodes"][0]["display_group_hint"] == "FB"
    assert brain_payload["top_nodes"][0]["neuropil_memberships"] == [
        {
            "neuropil": "FB",
            "occupancy_fraction": 1.0,
            "synapse_count": 1,
        }
    ]
    assert timeline_payload["data_status"] == "recorded"
    assert timeline_payload["steps_completed"] == 4
    assert len(timeline_payload["events"]) >= 2
    assert timeline_payload["current_step"] == 4
    assert (eval_dir / "brain_view.json").exists()
    assert (eval_dir / "timeline.json").exists()


def test_console_api_surfaces_graph_scoped_formal_truth_state(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    checkpoint_path.write_bytes(b"checkpoint")
    (compiled_dir / "graph_stats.json").write_text(json.dumps({"node_count": 139244}), encoding="utf-8")
    pq.write_table(
        pa.Table.from_pylist([{"source_id": 11, "neuropil": "FB", "pre_count": 1, "post_count": 1}]),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {
                    "alignment_passed": False,
                    "graph_only_root_count": 15,
                    "proofread_only_root_count": 26,
                },
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 1,
                "steps_completed": 1,
                "terminated_early": False,
                "reward_mean": 1.0,
                "final_reward": 1.0,
                "mean_action_norm": 1.0,
                "forward_velocity_mean": 0.0,
                "forward_velocity_std": 0.0,
                "body_upright_mean": 1.0,
                "final_heading_delta": 0.0,
            }
        ),
        encoding="utf-8",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=checkpoint_path,
        )
    )
    client = TestClient(app)

    brain_payload = client.get("/api/console/brain-view").json()
    assert brain_payload["formal_truth"]["validation_passed"] is True
    assert brain_payload["graph_scope_validation_passed"] is True
    assert brain_payload["validation_passed"] is True
    assert brain_payload["formal_truth"]["validation_scope"] == "graph_source_ids"
    assert brain_payload["formal_truth"]["roster_alignment_passed"] is False
    assert brain_payload["roster_alignment_passed"] is False
    assert brain_payload["formal_truth"]["graph_only_root_count"] == 15
    assert brain_payload["formal_truth"]["proofread_only_root_count"] == 26
    assert "proofread roster alignment differs" in brain_payload["formal_truth"]["reason"]


def test_console_api_returns_unavailable_summary_when_eval_artifacts_are_missing(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    checkpoint_path.write_bytes(b"checkpoint")
    (compiled_dir / "graph_stats.json").write_text(json.dumps({"node_count": 139255}), encoding="utf-8")
    pq.write_table(
        pa.Table.from_pylist([{"source_id": 11, "neuropil": "FB", "pre_count": 1, "post_count": 1}]),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {
                    "alignment_passed": True,
                    "graph_only_root_count": 0,
                    "proofread_only_root_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    session_payload = client.get("/api/console/session").json()
    assert session_payload["checkpoint"] == "unavailable"

    summary_payload = client.get("/api/console/summary").json()
    assert summary_payload["data_status"] == "unavailable"
    assert summary_payload["status"] == "unavailable"
    assert summary_payload["video_url"] is None

    timeline_payload = client.get("/api/console/timeline").json()
    assert timeline_payload["data_status"] == "unavailable"
    assert timeline_payload["steps_requested"] == 0
    assert timeline_payload["steps_completed"] == 0

    brain_payload = client.get("/api/console/brain-view").json()
    assert brain_payload["formal_truth"]["validation_passed"] is True
    assert brain_payload["formal_truth"]["roster_alignment_passed"] is True
    assert brain_payload["validation_passed"] is True
    assert brain_payload["graph_scope_validation_passed"] is True
    assert brain_payload["roster_alignment_passed"] is True


def test_console_api_returns_unavailable_brain_view_when_validation_is_missing(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps({"node_count": 2, "edge_count": 1, "afferent_count": 1, "intrinsic_count": 1, "efferent_count": 0}),
        encoding="utf-8",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
                {"source_id": 20, "node_idx": 1},
            ]
        ),
        compiled_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 3,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 4,
                    "materialization": 783,
                    "dataset": "public",
                },
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "steps_requested": 2,
                "steps_completed": 2,
                "snapshots": [
                    {
                        "step_id": 2,
                        "afferent_activity": 0.1,
                        "intrinsic_activity": 0.2,
                        "efferent_activity": 0.3,
                        "top_active_nodes": [
                            {"node_idx": 0, "activity_value": 0.5, "flow_role": "afferent"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.5, 0.2], dtype=np.float32))

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    payload = client.get("/api/console/brain-view").json()

    assert payload["data_status"] == "unavailable"
    assert payload["validation_passed"] is False
    assert payload["graph_scope_validation_passed"] is False
    assert payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 2,
        "total_nodes": 2,
    }
    assert payload["region_activity"] == []
    assert payload["top_regions"] == []
    assert payload["top_nodes"] == []
    assert not (eval_dir / "brain_view.json").exists()
