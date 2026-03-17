import os
import json
from pathlib import Path
import time

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
    (brain_asset_dir / "AL.glb").write_bytes(b"al-glb")
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
                        "description_zh": "V1 中作为气味输入相关神经纤维区的代表。",
                        "default_color": "#4ea8de",
                        "priority": 1,
                        "render_asset_path": "AL.glb",
                        "render_format": "glb",
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
    assert brain_assets_payload["neuropil_manifest"][0]["neuropil"] == "AL"
    assert brain_assets_payload["neuropil_manifest"][0]["asset_url"] == "/api/console/brain-mesh/AL"

    brain_shell_response = client.get("/api/console/brain-shell")
    assert brain_shell_response.status_code == 200
    assert brain_shell_response.headers["content-type"] == "model/gltf-binary"
    assert brain_shell_response.content == b"glb"

    brain_mesh_response = client.get("/api/console/brain-mesh/AL")
    assert brain_mesh_response.status_code == 200
    assert brain_mesh_response.headers["content-type"] == "model/gltf-binary"
    assert brain_mesh_response.content == b"al-glb"

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


def test_console_api_brain_mesh_route_supports_relative_paths_and_fail_closed(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    brain_asset_dir = tmp_path / "brain_assets"
    roi_mesh_dir = tmp_path / "roi_meshes"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    brain_asset_dir.mkdir()
    roi_mesh_dir.mkdir()
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps({"node_count": 1, "edge_count": 0, "afferent_count": 0, "intrinsic_count": 1, "efferent_count": 0}),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps({"status": "ok", "task": "straight_walking", "steps_requested": 1, "steps_completed": 1}),
        encoding="utf-8",
    )
    (brain_asset_dir / "brain_shell.glb").write_bytes(b"shell-glb")
    (roi_mesh_dir / "AL.glb").write_bytes(b"al-relative-glb")
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
                    "vertex_count": 2,
                    "face_count": 1,
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
                        "description_zh": "V1 中作为气味输入相关神经纤维区的代表。",
                        "default_color": "#4ea8de",
                        "priority": 1,
                        "render_asset_path": "../roi_meshes/AL.glb",
                        "render_format": "glb",
                    },
                    {
                        "neuropil": "FB",
                        "short_label": "FB",
                        "display_name": "Fan-shaped Body",
                        "display_name_zh": "扇形体",
                        "group": "core-processing",
                        "description_zh": "V1 中作为中央复合体处理层展示。",
                        "default_color": "#f6bd60",
                        "priority": 2,
                        "render_asset_path": "../roi_meshes/FB.glb",
                        "render_format": "glb",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
            brain_asset_dir=brain_asset_dir,
        )
    )
    client = TestClient(app)

    relative_response = client.get("/api/console/brain-mesh/AL")
    assert relative_response.status_code == 200
    assert relative_response.content == b"al-relative-glb"

    missing_file_response = client.get("/api/console/brain-mesh/FB")
    assert missing_file_response.status_code == 404
    assert missing_file_response.json()["detail"] == "FB.glb not found"

    missing_entry_response = client.get("/api/console/brain-mesh/PB")
    assert missing_entry_response.status_code == 404
    assert missing_entry_response.json()["detail"] == "PB mesh not found"


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
    approved_group_ids = {"AL", "LH", "PB", "FB", "EB", "NO", "LAL", "GNG"}
    assert brain_payload["display_region_activity"]
    first_display = brain_payload["display_region_activity"][0]
    assert first_display["view_mode"] == "grouped-neuropil-v1"
    assert first_display["is_display_transform"] is True
    assert isinstance(first_display["member_neuropils"], list)
    assert first_display["group_neuropil_id"] in approved_group_ids
    assert timeline_payload["data_status"] == "recorded"
    assert timeline_payload["steps_completed"] == 4
    assert len(timeline_payload["events"]) >= 2
    assert timeline_payload["current_step"] == 4
    assert (eval_dir / "brain_view.json").exists()
    assert (eval_dir / "timeline.json").exists()


def test_console_api_rematerializes_stale_brain_view_contract(tmp_path: Path) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    )
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
    (eval_dir / "brain_view.json").write_text(
        json.dumps(
            {
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "legacy-roi-v1",
                "mapping_coverage": {"roi_mapped_nodes": 3, "total_nodes": 4},
                "region_activity": [],
                "top_regions": [],
                "top_nodes": [
                    {
                        "node_idx": 2,
                        "source_id": "30",
                        "activity_value": 0.9,
                        "flow_role": "efferent",
                        "roi_name": "FB",
                    }
                ],
                "afferent_activity": 0.4,
                "intrinsic_activity": 0.5,
                "efferent_activity": 0.6,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "timeline.json").write_text(
        json.dumps(
            {
                "data_status": "recorded",
                "steps_requested": 4,
                "steps_completed": 4,
                "current_step": 4,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [],
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

    brain_payload = client.get("/api/console/brain-view").json()

    assert brain_payload["view_mode"] == "grouped-neuropil-v1"
    assert brain_payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 3,
        "total_nodes": 4,
    }
    assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert brain_payload["artifact_origin"] == "initial-materialized"
    assert brain_payload["top_nodes"][0]["neuropil_memberships"] == [
        {
            "neuropil": "FB",
            "occupancy_fraction": 1.0,
            "synapse_count": 1,
        }
    ]
    stored_payload = json.loads((eval_dir / "brain_view.json").read_text(encoding="utf-8"))
    assert stored_payload["top_nodes"][0]["neuropil_memberships"] == [
        {
            "neuropil": "FB",
            "occupancy_fraction": 1.0,
            "synapse_count": 1,
        }
    ]
    assert stored_payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 3,
        "total_nodes": 4,
    }
    assert stored_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert stored_payload["artifact_origin"] == "initial-materialized"


def test_console_api_rematerializes_when_display_region_activity_missing(tmp_path: Path) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    )
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
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
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
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "reward_mean": 0.4,
                "final_reward": 0.8,
                "mean_action_norm": 1.0,
                "forward_velocity_mean": 0.2,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.9,
                "final_heading_delta": 0.0,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "snapshots": [
                    {
                        "step_id": 2,
                        "afferent_activity": 0.3,
                        "intrinsic_activity": 0.5,
                        "efferent_activity": 0.1,
                        "top_active_nodes": [{"node_idx": 1, "activity_value": 0.9, "flow_role": "intrinsic"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.2, 0.9], dtype=np.float32))

    brain_view_path = eval_dir / "brain_view.json"
    timeline_path = eval_dir / "timeline.json"
    brain_view_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "artifact_origin": "initial-materialized",
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "grouped-neuropil-v1",
                "mapping_mode": "node_neuropil_occupancy",
                "activity_metric": "activity_mass",
                "formal_truth": {
                    "validation_passed": True,
                    "graph_scope_validation_passed": True,
                    "roster_alignment_passed": True,
                },
                "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
                "region_activity": [
                    {
                        "neuropil_id": "AL_L",
                        "display_name": "AL",
                        "raw_activity_mass": 0.2,
                        "signed_activity": 0.2,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": True,
                    },
                    {
                        "neuropil_id": "FB",
                        "display_name": "FB",
                        "raw_activity_mass": 0.9,
                        "signed_activity": 0.9,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": False,
                    },
                ],
                "display_region_activity": None,
                "top_regions": [
                    {
                        "neuropil_id": "FB",
                        "display_name": "FB",
                        "raw_activity_mass": 0.9,
                        "signed_activity": 0.9,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": False,
                    }
                ],
                "top_nodes": [
                    {
                        "node_idx": 1,
                        "source_id": "20",
                        "activity_value": 0.9,
                        "flow_role": "intrinsic",
                        "display_group_hint": "FB",
                        "neuropil_memberships": [
                            {
                                "neuropil": "FB",
                                "occupancy_fraction": 1.0,
                                "synapse_count": 1,
                            }
                        ],
                    }
                ],
                "afferent_activity": 0.3,
                "intrinsic_activity": 0.5,
                "efferent_activity": 0.1,
            }
        ),
        encoding="utf-8",
    )
    timeline_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "steps_requested": 2,
                "steps_completed": 2,
                "current_step": 2,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [],
            }
        ),
        encoding="utf-8",
    )

    fresh_at = time.time()
    stale_at = fresh_at - 100
    for path in (
        eval_dir / "summary.json",
        eval_dir / "activity_trace.json",
        eval_dir / "final_node_activity.npy",
        compiled_dir / "node_index.parquet",
        compiled_dir / "node_neuropil_occupancy.parquet",
        compiled_dir / "neuropil_truth_validation.json",
    ):
        os.utime(path, (stale_at, stale_at))
    os.utime(brain_view_path, (fresh_at, fresh_at))
    os.utime(timeline_path, (fresh_at, fresh_at))

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    brain_payload = client.get("/api/console/brain-view").json()

    assert brain_payload["display_region_activity"]
    assert brain_payload["display_region_activity"][0]["group_neuropil_id"] in {"AL", "FB"}
    stored_payload = json.loads(brain_view_path.read_text(encoding="utf-8"))
    assert stored_payload["display_region_activity"]
    assert stored_payload["display_region_activity"][0]["view_mode"] == "grouped-neuropil-v1"


def test_console_api_rematerializes_when_display_region_activity_entry_is_invalid(tmp_path: Path) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    )
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
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
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
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "reward_mean": 0.4,
                "final_reward": 0.8,
                "mean_action_norm": 1.0,
                "forward_velocity_mean": 0.2,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.9,
                "final_heading_delta": 0.0,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "snapshots": [
                    {
                        "step_id": 2,
                        "afferent_activity": 0.3,
                        "intrinsic_activity": 0.5,
                        "efferent_activity": 0.1,
                        "top_active_nodes": [{"node_idx": 1, "activity_value": 0.9, "flow_role": "intrinsic"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.2, 0.9], dtype=np.float32))

    brain_view_path = eval_dir / "brain_view.json"
    timeline_path = eval_dir / "timeline.json"
    brain_view_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "artifact_origin": "initial-materialized",
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "grouped-neuropil-v1",
                "mapping_mode": "node_neuropil_occupancy",
                "activity_metric": "activity_mass",
                "formal_truth": {
                    "validation_passed": True,
                    "graph_scope_validation_passed": True,
                    "roster_alignment_passed": True,
                },
                "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
                "region_activity": [
                    {
                        "neuropil_id": "AL_L",
                        "display_name": "AL",
                        "raw_activity_mass": 0.2,
                        "signed_activity": 0.2,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": True,
                    },
                    {
                        "neuropil_id": "FB",
                        "display_name": "FB",
                        "raw_activity_mass": 0.9,
                        "signed_activity": 0.9,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": False,
                    },
                ],
                "display_region_activity": [
                    {
                        "group_neuropil_id": "ME",
                        "raw_activity_mass": "0.9",
                        "signed_activity": 0.9,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "member_neuropils": ["FB"],
                        "view_mode": "grouped-neuropil-v1",
                        "is_display_transform": True,
                    }
                ],
                "top_regions": [
                    {
                        "neuropil_id": "FB",
                        "display_name": "FB",
                        "raw_activity_mass": 0.9,
                        "signed_activity": 0.9,
                        "covered_weight_sum": 1.0,
                        "node_count": 1,
                        "is_display_grouped": False,
                    }
                ],
                "top_nodes": [
                    {
                        "node_idx": 1,
                        "source_id": "20",
                        "activity_value": 0.9,
                        "flow_role": "intrinsic",
                        "display_group_hint": "FB",
                        "neuropil_memberships": [
                            {
                                "neuropil": "FB",
                                "occupancy_fraction": 1.0,
                                "synapse_count": 1,
                            }
                        ],
                    }
                ],
                "afferent_activity": 0.3,
                "intrinsic_activity": 0.5,
                "efferent_activity": 0.1,
            }
        ),
        encoding="utf-8",
    )
    timeline_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "steps_requested": 2,
                "steps_completed": 2,
                "current_step": 2,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [],
            }
        ),
        encoding="utf-8",
    )

    fresh_at = time.time()
    stale_at = fresh_at - 100
    for path in (
        eval_dir / "summary.json",
        eval_dir / "activity_trace.json",
        eval_dir / "final_node_activity.npy",
        compiled_dir / "node_index.parquet",
        compiled_dir / "node_neuropil_occupancy.parquet",
        compiled_dir / "neuropil_truth_validation.json",
    ):
        os.utime(path, (stale_at, stale_at))
    os.utime(brain_view_path, (fresh_at, fresh_at))
    os.utime(timeline_path, (fresh_at, fresh_at))

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    brain_payload = client.get("/api/console/brain-view").json()

    assert brain_payload["display_region_activity"]
    assert {entry["group_neuropil_id"] for entry in brain_payload["display_region_activity"]} == {
        "AL",
        "FB",
    }
    stored_payload = json.loads(brain_view_path.read_text(encoding="utf-8"))
    assert {entry["group_neuropil_id"] for entry in stored_payload["display_region_activity"]} == {
        "AL",
        "FB",
    }
    assert all(isinstance(entry["raw_activity_mass"], float) for entry in stored_payload["display_region_activity"])


def test_brain_view_artifact_current_check_fails_closed_for_malformed_payloads() -> None:
    from fruitfly.ui.console_api import _brain_view_artifact_is_current

    assert _brain_view_artifact_is_current(
        {
            "artifact_contract_version": "invalid",
            "semantic_scope": "neuropil",
            "view_mode": "grouped-neuropil-v1",
            "mapping_mode": "node_neuropil_occupancy",
            "activity_metric": "activity_mass",
            "artifact_origin": "initial-materialized",
            "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
            "formal_truth": {
                "validation_passed": True,
                "graph_scope_validation_passed": True,
                "roster_alignment_passed": True,
            },
            "top_nodes": [],
        }
    ) is False
    assert _brain_view_artifact_is_current(
        {
            "artifact_contract_version": 1,
            "semantic_scope": "neuropil",
            "view_mode": "grouped-neuropil-v1",
            "mapping_mode": "node_neuropil_occupancy",
            "activity_metric": "activity_mass",
            "artifact_origin": "initial-materialized",
            "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
            "formal_truth": {
                "validation_passed": True,
                "graph_scope_validation_passed": True,
                "roster_alignment_passed": True,
            },
            "region_activity": [],
            "display_region_activity": None,
            "top_regions": [],
            "top_nodes": [],
        }
    ) is False
    assert _brain_view_artifact_is_current(
        {
            "artifact_contract_version": 1,
            "semantic_scope": "neuropil",
            "view_mode": "grouped-neuropil-v1",
            "mapping_mode": "node_neuropil_occupancy",
            "activity_metric": "activity_mass",
            "artifact_origin": "initial-materialized",
            "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
            "formal_truth": {
                "validation_passed": True,
                "graph_scope_validation_passed": True,
                "roster_alignment_passed": True,
            },
            "region_activity": [],
            "display_region_activity": [
                {
                    "group_neuropil_id": "ME",
                    "raw_activity_mass": "0.9",
                    "signed_activity": 0.9,
                    "covered_weight_sum": 1.0,
                    "node_count": 1,
                    "member_neuropils": ["FB"],
                    "view_mode": "grouped-neuropil-v1",
                    "is_display_transform": True,
                }
            ],
            "top_regions": [],
            "top_nodes": [],
        }
    ) is False
    assert _brain_view_artifact_is_current(
        {
            "artifact_contract_version": 1,
            "semantic_scope": "neuropil",
            "view_mode": "grouped-neuropil-v1",
            "mapping_mode": "node_neuropil_occupancy",
            "activity_metric": "activity_mass",
            "artifact_origin": "initial-materialized",
            "mapping_coverage": {"neuropil_mapped_nodes": 2, "total_nodes": 2},
            "formal_truth": {
                "validation_passed": True,
                "graph_scope_validation_passed": True,
                "roster_alignment_passed": True,
            },
            "top_nodes": ["broken"],
        }
    ) is False


def test_timeline_artifact_current_check_rejects_incomplete_payload() -> None:
    from fruitfly.ui.console_api import _timeline_artifact_is_current

    assert _timeline_artifact_is_current(
        {
            "artifact_contract_version": 1,
        }
    ) is False


def test_console_api_rematerializes_when_final_node_activity_is_newer(tmp_path: Path) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    )
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
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
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
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "reward_mean": 0.4,
                "final_reward": 0.8,
                "mean_action_norm": 1.0,
                "forward_velocity_mean": 0.2,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.9,
                "final_heading_delta": 0.0,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "snapshots": [
                    {
                        "step_id": 1,
                        "afferent_activity": 0.1,
                        "intrinsic_activity": 0.2,
                        "efferent_activity": 0.0,
                        "top_active_nodes": [{"node_idx": 0, "activity_value": 0.4, "flow_role": "afferent"}],
                    },
                    {
                        "step_id": 2,
                        "afferent_activity": 0.3,
                        "intrinsic_activity": 0.5,
                        "efferent_activity": 0.1,
                        "top_active_nodes": [{"node_idx": 1, "activity_value": 0.9, "flow_role": "intrinsic"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.2, 0.9], dtype=np.float32))

    brain_view_path = eval_dir / "brain_view.json"
    timeline_path = eval_dir / "timeline.json"
    brain_view_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "grouped-neuropil-v1",
                "mapping_mode": "node_neuropil_occupancy",
                "activity_metric": "activity_mass",
                "formal_truth": {
                    "validation_passed": True,
                    "graph_scope_validation_passed": True,
                    "roster_alignment_passed": True,
                },
                "mapping_coverage": {"neuropil_mapped_nodes": 999, "total_nodes": 2},
                "region_activity": [],
                "top_regions": [],
                "top_nodes": [],
                "afferent_activity": 9.9,
                "intrinsic_activity": 9.9,
                "efferent_activity": 9.9,
            }
        ),
        encoding="utf-8",
    )
    timeline_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "steps_requested": 2,
                "steps_completed": 2,
                "current_step": 2,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [],
            }
        ),
        encoding="utf-8",
    )

    stale_at = time.time() - 100
    fresh_at = time.time()
    os.utime(brain_view_path, (stale_at, stale_at))
    os.utime(timeline_path, (stale_at, stale_at))
    os.utime(eval_dir / "final_node_activity.npy", (fresh_at, fresh_at))

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

    assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert brain_payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 2,
        "total_nodes": 2,
    }
    assert brain_payload["intrinsic_activity"] == 0.5
    assert brain_payload["top_nodes"][0]["source_id"] == "20"
    assert timeline_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert timeline_payload["steps_completed"] == 2
    assert timeline_payload["current_step"] == 2


def test_console_api_rematerializes_when_neuropil_truth_is_newer(tmp_path: Path) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        RUNTIME_ACTIVITY_ARTIFACT_VERSION,
    )
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps({"node_count": 2, "edge_count": 1, "afferent_count": 1, "intrinsic_count": 1, "efferent_count": 0}),
        encoding="utf-8",
    )
    node_index_path = compiled_dir / "node_index.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
                {"source_id": 20, "node_idx": 1},
            ]
        ),
        node_index_path,
    )
    occupancy_path = compiled_dir / "node_neuropil_occupancy.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
            ]
        ),
        occupancy_path,
    )
    validation_path = compiled_dir / "neuropil_truth_validation.json"
    validation_path.write_text(
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
    summary_path = eval_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "reward_mean": 0.4,
                "final_reward": 0.8,
                "mean_action_norm": 1.0,
                "forward_velocity_mean": 0.2,
                "forward_velocity_std": 0.1,
                "body_upright_mean": 0.9,
                "final_heading_delta": 0.0,
            }
        ),
        encoding="utf-8",
    )
    trace_path = eval_dir / "activity_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
                "snapshots": [
                    {
                        "step_id": 2,
                        "afferent_activity": 0.3,
                        "intrinsic_activity": 0.5,
                        "efferent_activity": 0.1,
                        "top_active_nodes": [{"node_idx": 1, "activity_value": 0.9, "flow_role": "intrinsic"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    final_node_activity_path = eval_dir / "final_node_activity.npy"
    np.save(final_node_activity_path, np.asarray([0.2, 0.9], dtype=np.float32))

    brain_view_path = eval_dir / "brain_view.json"
    timeline_path = eval_dir / "timeline.json"
    brain_view_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "semantic_scope": "neuropil",
                "view_mode": "grouped-neuropil-v1",
                "mapping_mode": "node_neuropil_occupancy",
                "activity_metric": "activity_mass",
                "formal_truth": {
                    "validation_passed": True,
                    "graph_scope_validation_passed": True,
                    "roster_alignment_passed": True,
                },
                "mapping_coverage": {"neuropil_mapped_nodes": 999, "total_nodes": 2},
                "region_activity": [],
                "top_regions": [],
                "top_nodes": [],
                "afferent_activity": 9.9,
                "intrinsic_activity": 9.9,
                "efferent_activity": 9.9,
            }
        ),
        encoding="utf-8",
    )
    timeline_path.write_text(
        json.dumps(
            {
                "artifact_contract_version": RUNTIME_ACTIVITY_ARTIFACT_VERSION,
                "data_status": "recorded",
                "steps_requested": 2,
                "steps_completed": 2,
                "current_step": 2,
                "brain_view_ref": "step_id",
                "body_view_ref": "step_id",
                "events": [],
            }
        ),
        encoding="utf-8",
    )

    stale_at = time.time() - 100
    fresh_at = time.time()
    for path in (
        brain_view_path,
        timeline_path,
        trace_path,
        final_node_activity_path,
        summary_path,
        validation_path,
        node_index_path,
    ):
        os.utime(path, (stale_at, stale_at))
    os.utime(occupancy_path, (fresh_at, fresh_at))

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

    assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert brain_payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 2,
        "total_nodes": 2,
    }
    assert brain_payload["intrinsic_activity"] == 0.5
    assert brain_payload["top_nodes"][0]["source_id"] == "20"
    assert timeline_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert timeline_payload["steps_completed"] == 2
    assert timeline_payload["current_step"] == 2


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
