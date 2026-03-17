from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from fruitfly.evaluation.inspector_trace import dump_replay_trace
from fruitfly.evaluation.runtime_activity_artifacts import RUNTIME_ACTIVITY_ARTIFACT_VERSION
from fruitfly.ui import ConsoleApiConfig, create_console_api


def test_console_api_exposes_replay_seek_and_step_synchronized_payloads(tmp_path: Path) -> None:
    import fruitfly.ui.console_api as console_api_module

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    checkpoint_path.write_bytes(b"checkpoint")
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
                {"source_id": 10, "node_idx": 0, "neuropil": "AL_L", "occupancy_fraction": 1.0},
                {"source_id": 20, "node_idx": 1, "neuropil": "LH_R", "occupancy_fraction": 1.0},
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
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_requested": 3,
            "steps_completed": 3,
        },
        state_arrays={
            "step_id": np.asarray([1, 2, 3], dtype=np.int64),
            "reward": np.asarray([0.1, 0.2, 0.3], dtype=np.float64),
            "forward_velocity": np.asarray([0.4, 0.5, 0.6], dtype=np.float64),
            "body_upright": np.asarray([0.8, 0.9, 1.0], dtype=np.float64),
            "terminated": np.asarray([False, False, True], dtype=bool),
            "qpos": np.zeros((3, 2), dtype=np.float64),
            "qvel": np.zeros((3, 2), dtype=np.float64),
            "ctrl": np.zeros((3, 2), dtype=np.float64),
            "sim_time": np.asarray([0.1, 0.2, 0.3], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1, 2, 3], dtype=np.int64),
            "node_activity": np.asarray(
                [
                    [0.1, 0.2],
                    [0.3, 0.4],
                    [0.5, 0.6],
                ],
                dtype=np.float32,
            ),
            "afferent_activity": np.asarray([0.1, 0.3, 0.5], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.2, 0.4, 0.6], dtype=np.float32),
            "efferent_activity": np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
        },
        events=[
            {"step_id": 1, "event_type": "rollout_started", "label": "Recorded rollout start"},
            {"step_id": 3, "event_type": "rollout_completed", "label": "Recorded rollout complete"},
        ],
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 3,
                "steps_completed": 3,
                "reward_mean": 0.2,
            }
        ),
        encoding="utf-8",
    )

    class FakeResidentClient:
        def render_frame(self, *, step: int, camera: str, width: int, height: int) -> bytes:
            assert step == 2
            assert camera == "top"
            assert width == 320
            assert height == 240
            return b"fake-jpeg"

        def close(self) -> None:
            return None

    console_api_module._create_replay_frame_client = lambda *, config: FakeResidentClient()

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=checkpoint_path,
        )
    )

    with TestClient(app) as client:
        session_response = client.get("/api/console/replay/session")
        assert session_response.status_code == 200
        assert session_response.json()["current_step"] == 1

        seek_response = client.post("/api/console/replay/seek", json={"step": 2})
        assert seek_response.status_code == 200
        assert seek_response.json()["current_step"] == 2

        brain_response = client.get("/api/console/replay/brain-view")
        summary_response = client.get("/api/console/replay/summary")
        timeline_response = client.get("/api/console/replay/timeline")

        assert brain_response.status_code == 200
        assert summary_response.status_code == 200
        assert timeline_response.status_code == 200
        assert brain_response.json()["step_id"] == 2
        assert summary_response.json()["step_id"] == 2
        assert timeline_response.json()["current_step"] == 2

        camera_response = client.post("/api/console/replay/camera", json={"camera": "top"})
        assert camera_response.status_code == 200
        assert camera_response.json()["camera"] == "top"

        frame_response = client.get("/api/console/replay/frame?width=320&height=240")
        assert frame_response.status_code == 200
        assert frame_response.headers["content-type"] == "image/jpeg"
        assert frame_response.content == b"fake-jpeg"

        brain_payload = brain_response.json()
        assert brain_payload["step_id"] == 2
        assert brain_payload["semantic_scope"] == "neuropil"
        assert brain_payload["mapping_mode"] == "node_neuropil_occupancy"
        assert brain_payload["activity_metric"] == "activity_mass"
        assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
        assert brain_payload["artifact_origin"] == "replay-live-step"
        assert brain_payload["validation_passed"] is True
        assert brain_payload["graph_scope_validation_passed"] is True
        assert brain_payload["roster_alignment_passed"] is True
        assert brain_payload["mapping_coverage"] == {
            "neuropil_mapped_nodes": 2,
            "total_nodes": 2,
        }
        assert brain_payload["top_nodes"] == []
        assert summary_response.json()["step_id"] == 2
        assert timeline_response.json()["current_step"] == 2

        control_response = client.post("/api/console/replay/control", json={"action": "play"})
        assert control_response.status_code == 200
        assert control_response.json()["status"] == "playing"


def test_console_api_reuses_one_resident_replay_frame_client(tmp_path: Path, monkeypatch) -> None:
    import fruitfly.ui.console_api as console_api_module

    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    checkpoint_path = tmp_path / "epoch_0001.pt"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    checkpoint_path.write_bytes(b"checkpoint")
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
                {"source_id": 10, "node_idx": 0, "neuropil": "AL_L", "occupancy_fraction": 1.0},
                {"source_id": 20, "node_idx": 1, "neuropil": "LH_R", "occupancy_fraction": 1.0},
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_requested": 3,
            "steps_completed": 3,
        },
        state_arrays={
            "step_id": np.asarray([1, 2, 3], dtype=np.int64),
            "reward": np.asarray([0.1, 0.2, 0.3], dtype=np.float64),
            "forward_velocity": np.asarray([0.4, 0.5, 0.6], dtype=np.float64),
            "body_upright": np.asarray([0.8, 0.9, 1.0], dtype=np.float64),
            "terminated": np.asarray([False, False, True], dtype=bool),
            "qpos": np.zeros((3, 2), dtype=np.float64),
            "qvel": np.zeros((3, 2), dtype=np.float64),
            "ctrl": np.zeros((3, 2), dtype=np.float64),
            "sim_time": np.asarray([0.1, 0.2, 0.3], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1, 2, 3], dtype=np.int64),
            "node_activity": np.asarray(
                [
                    [0.1, 0.2],
                    [0.3, 0.4],
                    [0.5, 0.6],
                ],
                dtype=np.float32,
            ),
            "afferent_activity": np.asarray([0.1, 0.3, 0.5], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.2, 0.4, 0.6], dtype=np.float32),
            "efferent_activity": np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
        },
        events=[],
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 3,
                "steps_completed": 3,
                "reward_mean": 0.2,
            }
        ),
        encoding="utf-8",
    )

    created_clients: list[FakeResidentClient] = []

    class FakeResidentClient:
        def __init__(self) -> None:
            self.calls: list[tuple[int, str, int, int]] = []
            self.closed = False

        def render_frame(self, *, step: int, camera: str, width: int, height: int) -> bytes:
            self.calls.append((step, camera, width, height))
            return f"frame:{step}:{camera}:{width}:{height}".encode("utf-8")

        def close(self) -> None:
            self.closed = True

    def fake_create_replay_frame_client(*, config):
        client = FakeResidentClient()
        created_clients.append(client)
        return client

    monkeypatch.setattr(
        console_api_module,
        "_create_replay_frame_client",
        fake_create_replay_frame_client,
        raising=False,
    )
    monkeypatch.setattr(console_api_module, "_resolve_replay_renderer_python", lambda config: None)

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=checkpoint_path,
        )
    )

    with TestClient(app) as client:
        first_frame_response = client.get("/api/console/replay/frame?width=320&height=240")
        assert first_frame_response.status_code == 200
        assert first_frame_response.content == b"frame:1:follow:320:240"

        seek_response = client.post("/api/console/replay/seek", json={"step": 2})
        assert seek_response.status_code == 200

        camera_response = client.post("/api/console/replay/camera", json={"camera": "top"})
        assert camera_response.status_code == 200

        second_frame_response = client.get("/api/console/replay/frame?width=640&height=360")
        assert second_frame_response.status_code == 200
        assert second_frame_response.content == b"frame:2:top:640:360"

    assert len(created_clients) == 1
    assert created_clients[0].calls == [
        (1, "follow", 320, 240),
        (2, "top", 640, 360),
    ]
    assert created_clients[0].closed is True


def test_console_api_returns_404_when_replay_artifacts_are_missing(tmp_path: Path) -> None:
    compiled_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"

    compiled_dir.mkdir()
    eval_dir.mkdir()
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps(
            {"node_count": 2, "edge_count": 1, "afferent_count": 1, "intrinsic_count": 1, "efferent_count": 0}
        ),
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
                {"source_id": 10, "node_idx": 0, "neuropil": "AL_L", "occupancy_fraction": 1.0},
                {"source_id": 20, "node_idx": 1, "neuropil": "LH_R", "occupancy_fraction": 1.0},
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=compiled_dir,
            eval_dir=eval_dir,
            checkpoint_path=None,
        )
    )
    client = TestClient(app)

    response = client.get("/api/console/replay/session")
    assert response.status_code == 404
    assert response.json()["detail"] == "Replay inspector artifacts are unavailable"


def test_console_api_replay_brain_view_returns_unavailable_when_validation_is_missing(tmp_path: Path) -> None:
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
                    "materialization": 783,
                    "dataset": "public",
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                },
            ]
        ),
        compiled_dir / "node_neuropil_occupancy.parquet",
    )
    dump_replay_trace(
        output_dir=eval_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_requested": 1,
            "steps_completed": 1,
        },
        state_arrays={
            "step_id": np.asarray([1], dtype=np.int64),
            "reward": np.asarray([0.1], dtype=np.float64),
            "forward_velocity": np.asarray([0.4], dtype=np.float64),
            "body_upright": np.asarray([0.8], dtype=np.float64),
            "terminated": np.asarray([True], dtype=bool),
            "qpos": np.zeros((1, 2), dtype=np.float64),
            "qvel": np.zeros((1, 2), dtype=np.float64),
            "ctrl": np.zeros((1, 2), dtype=np.float64),
            "sim_time": np.asarray([0.1], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([1], dtype=np.int64),
            "node_activity": np.asarray([[0.2, 0.4]], dtype=np.float32),
            "afferent_activity": np.asarray([0.2], dtype=np.float32),
            "intrinsic_activity": np.asarray([0.4], dtype=np.float32),
            "efferent_activity": np.asarray([0.0], dtype=np.float32),
        },
        events=[],
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 1,
                "steps_completed": 1,
                "reward_mean": 0.1,
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

    payload = client.get("/api/console/replay/brain-view").json()

    assert payload["data_status"] == "unavailable"
    assert payload["mapping_mode"] == "node_neuropil_occupancy"
    assert payload["validation_passed"] is False
    assert payload["graph_scope_validation_passed"] is False
    assert payload["mapping_coverage"] == {
        "neuropil_mapped_nodes": 2,
        "total_nodes": 2,
    }
    assert payload["region_activity"] == []
    assert payload["top_nodes"] == []
