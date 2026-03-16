from __future__ import annotations

import json
from pathlib import Path


def test_export_full_writes_normalized_snapshot_from_annotations(tmp_path: Path) -> None:
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    class FakeFlyWire:
        def __init__(self) -> None:
            self.dataset = None

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            return [
                {"root_id": 1, "flow": "afferent", "side": "left"},
                {"root_id": 2, "flow": "intrinsic", "side": "center"},
                {"root_id": 3, "flow": "efferent", "side": "right"},
            ]

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["dataset"] == "public"
            if list(roots) == [1, 2]:
                return [
                    {"pre": 1, "post": 2, "weight": 3},
                    {"pre": 2, "post": 3, "weight": 5},
                ]
            if list(roots) == [3]:
                return [
                    {"pre": 2, "post": 3, "weight": 5},
                ]
            return []

    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id="full_test",
            mode="full",
            batch_size=2,
        ),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
    )

    assert result.status == "ok"
    manifest = json.loads((result.snapshot_dir / "state.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["completed_batches"] == 2

    node_table = pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet")
    edge_table = pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet")

    assert node_table.num_rows == 3
    assert edge_table.num_rows == 2


def test_export_full_resume_skips_completed_batches(tmp_path: Path) -> None:
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot, build_snapshot_paths

    class FakeFlyWire:
        def __init__(self) -> None:
            self.calls: list[list[int]] = []

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            return [
                {"root_id": 1, "flow": "afferent", "side": "left"},
                {"root_id": 2, "flow": "intrinsic", "side": "center"},
                {"root_id": 3, "flow": "efferent", "side": "right"},
                {"root_id": 4, "flow": "efferent", "side": "right"},
            ]

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["dataset"] == "public"
            root_batch = list(roots)
            self.calls.append(root_batch)
            if root_batch == [3, 4]:
                return [{"pre": 3, "post": 4, "weight": 7}]
            return []

    snapshot_id = "resume_test"
    paths = build_snapshot_paths(snapshot_id, output_root=tmp_path)
    raw_dir = paths["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = raw_dir / "connectivity_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "batch_00000.jsonl").write_text(
        json.dumps({"pre_id": 1, "post_id": 2, "synapse_count": 3, "is_directed": True, "is_active": True}) + "\n",
        encoding="utf-8",
    )
    (paths["snapshot_dir"] / "state.json").write_text(
        json.dumps({"status": "running", "completed_batches": 1, "total_batches": 2}, indent=2),
        encoding="utf-8",
    )

    client = FakeFlyWire()
    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id=snapshot_id,
            mode="full",
            batch_size=2,
            resume=True,
        ),
        output_root=tmp_path,
        flywire_client=client,
    )

    assert result.status == "ok"
    assert client.calls == [[3, 4]]

    edge_table = pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet")
    assert edge_table.num_rows == 2


def test_export_full_resume_uses_local_nodes_without_refetching_annotations(tmp_path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import (
        NORMALIZED_NODE_COLUMNS,
        NORMALIZED_PARTITION_COLUMNS,
        SnapshotExportRequest,
        export_snapshot,
        build_snapshot_paths,
    )

    class FakeFlyWire:
        def __init__(self) -> None:
            self.calls: list[list[int]] = []

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            raise AssertionError("resume should not refetch annotations when local normalized nodes already exist")

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["dataset"] == "public"
            root_batch = list(roots)
            self.calls.append(root_batch)
            if root_batch == [3, 4]:
                return [{"pre": 3, "post": 4, "weight": 7}]
            return []

    snapshot_id = "resume_local_nodes"
    paths = build_snapshot_paths(snapshot_id, output_root=tmp_path)
    raw_dir = paths["raw_dir"]
    normalized_dir = paths["normalized_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = raw_dir / "connectivity_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)

    pa.table(
        {
            column: values
            for column, values in {
                "source_id": [1, 2, 3, 4],
                "dataset_version": ["public", "public", "public", "public"],
                "hemisphere": ["left", "center", "right", "right"],
                "flow_role": ["afferent", "intrinsic", "efferent", "efferent"],
                "is_active": [True, True, True, True],
            }.items()
        }
    )
    pq.write_table(
        pa.table(
            {
                column: values
                for column, values in {
                    "source_id": [1, 2, 3, 4],
                    "dataset_version": ["public", "public", "public", "public"],
                    "hemisphere": ["left", "center", "right", "right"],
                    "flow_role": ["afferent", "intrinsic", "efferent", "efferent"],
                    "is_active": [True, True, True, True],
                }.items()
            }
        ),
        normalized_dir / "nodes.parquet",
    )
    pq.write_table(
        pa.table(
            {
                column: values
                for column, values in {
                    "source_id": [1, 2, 3, 4],
                    "flow_role": ["afferent", "intrinsic", "efferent", "efferent"],
                    "partition_version": [snapshot_id, snapshot_id, snapshot_id, snapshot_id],
                }.items()
            }
        ),
        normalized_dir / "partitions.parquet",
    )
    (batch_dir / "batch_00000.jsonl").write_text(
        json.dumps({"pre_id": 1, "post_id": 2, "synapse_count": 3, "is_directed": True, "is_active": True}) + "\n",
        encoding="utf-8",
    )
    (paths["snapshot_dir"] / "state.json").write_text(
        json.dumps({"status": "paused", "completed_batches": 1, "total_batches": 2}, indent=2),
        encoding="utf-8",
    )

    client = FakeFlyWire()
    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id=snapshot_id,
            mode="full",
            batch_size=2,
            resume=True,
        ),
        output_root=tmp_path,
        flywire_client=client,
    )

    assert result.status == "ok"
    assert client.calls == [[3, 4]]


def test_export_full_retries_transient_connectivity_failure(tmp_path: Path) -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    class FakeFlyWire:
        def __init__(self) -> None:
            self.calls = 0

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            return [
                {"root_id": 1, "flow": "afferent", "side": "left"},
                {"root_id": 2, "flow": "efferent", "side": "right"},
            ]

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["dataset"] == "public"
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("503 Server Error: Service Temporarily Unavailable")
            return [{"pre": 1, "post": 2, "weight": 3}]

    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id="retry_test",
            mode="full",
            batch_size=2,
        ),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
    )

    assert result.status == "ok"
