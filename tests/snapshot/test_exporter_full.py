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


def test_export_full_uses_proofread_roster_as_node_source(tmp_path: Path) -> None:
    import numpy as np
    import pyarrow as pa
    import pyarrow.feather as feather
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    proofread_root_ids_path = tmp_path / "proofread_root_ids_783.npy"
    np.save(proofread_root_ids_path, np.array([1, 2, 3], dtype=np.int64))
    proofread_connections_path = tmp_path / "proofread_connections_783.feather"
    feather.write_feather(
        pa.table(
            {
                "pre_pt_root_id": [1, 2],
                "post_pt_root_id": [2, 3],
                "neuropil": ["FB", "LAL_L"],
                "syn_count": [3, 5],
            }
        ),
        proofread_connections_path,
    )

    class FakeFlyWire:
        def __init__(self) -> None:
            self.annotation_materializations: list[object] = []
            self.connectivity_materializations: list[object] = []

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **kwargs):
            self.annotation_materializations.append(kwargs["materialization"])
            return [
                {"root_id": 1, "flow": "afferent", "side": "left"},
                {"root_id": 2, "flow": "efferent", "side": "right"},
            ]

        def get_connectivity(self, roots, **kwargs):
            self.connectivity_materializations.append(kwargs["materialization"])
            root_batch = list(roots)
            if root_batch == [1, 2]:
                return [{"pre": 1, "post": 2, "weight": 3}]
            if root_batch == [3]:
                return [{"pre": 2, "post": 3, "weight": 5}]
            return []

    client = FakeFlyWire()
    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id="proofread_roster_full",
            mode="full",
                batch_size=2,
                materialization=783,
                proofread_root_ids_path=proofread_root_ids_path,
                proofread_connections_path=proofread_connections_path,
                allow_live_annotation_fetch=True,
            ),
            output_root=tmp_path,
            flywire_client=client,
        )

    assert result.status == "ok"
    node_table = pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet")
    node_rows = sorted(node_table.to_pylist(), key=lambda row: row["source_id"])
    assert [row["source_id"] for row in node_rows] == [1, 2, 3]
    assert node_rows[0]["flow_role"] == "afferent"
    assert node_rows[1]["flow_role"] == "efferent"
    assert node_rows[2]["hemisphere"] == "unknown"
    assert node_rows[2]["flow_role"] == "unknown"

    manifest_text = (result.snapshot_dir / "manifest.yaml").read_text(encoding="utf-8")
    assert "flow_label_source: proofread_roster_plus_annotation_enrichment" in manifest_text
    assert client.annotation_materializations == [783]
    assert client.connectivity_materializations == []


def test_export_full_prefers_local_annotation_enrichment_over_live_fetch(tmp_path: Path) -> None:
    import numpy as np
    import pyarrow as pa
    import pyarrow.feather as feather
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    proofread_root_ids_path = tmp_path / "proofread_root_ids_783.npy"
    np.save(proofread_root_ids_path, np.array([1, 2, 3], dtype=np.int64))

    annotation_enrichment_path = tmp_path / "annotation_enrichment_783.parquet"
    pq.write_table(
        pa.table(
            {
                "source_id": [1, 2],
                "flow_role": ["afferent", "efferent"],
                "hemisphere": ["left", "right"],
            }
        ),
        annotation_enrichment_path,
    )
    proofread_connections_path = tmp_path / "proofread_connections_783.feather"
    feather.write_feather(
        pa.table(
            {
                "pre_pt_root_id": [1, 2],
                "post_pt_root_id": [2, 3],
                "neuropil": ["FB", "LAL_L"],
                "syn_count": [3, 5],
            }
        ),
        proofread_connections_path,
    )

    class FakeFlyWire:
        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            raise AssertionError("full export should not live-fetch annotations when a frozen enrichment file is provided")

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["materialization"] == 783
            root_batch = list(roots)
            if root_batch == [1, 2]:
                return [{"pre": 1, "post": 2, "weight": 3}]
            if root_batch == [3]:
                return [{"pre": 2, "post": 3, "weight": 5}]
            return []

    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id="proofread_roster_local_enrichment",
            mode="full",
                batch_size=2,
                materialization=783,
                proofread_root_ids_path=proofread_root_ids_path,
                annotation_enrichment_path=annotation_enrichment_path,
                proofread_connections_path=proofread_connections_path,
            ),
            output_root=tmp_path,
            flywire_client=FakeFlyWire(),
        )

    assert result.status == "ok"
    node_rows = sorted(
        pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet").to_pylist(),
        key=lambda row: row["source_id"],
    )
    assert [row["source_id"] for row in node_rows] == [1, 2, 3]
    assert node_rows[0]["flow_role"] == "afferent"
    assert node_rows[1]["flow_role"] == "efferent"
    assert node_rows[2]["flow_role"] == "unknown"


def test_export_full_requires_frozen_annotation_enrichment_for_proofread_scope(tmp_path: Path) -> None:
    import numpy as np
    import pytest

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    proofread_root_ids_path = tmp_path / "proofread_root_ids_783.npy"
    np.save(proofread_root_ids_path, np.array([1, 2, 3], dtype=np.int64))

    class FakeFlyWire:
        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            raise AssertionError("full export should refuse live annotation fetch by default")

        def get_connectivity(self, roots, **kwargs):
            return []

    with pytest.raises(RuntimeError, match="annotation enrichment"):
        export_snapshot(
            request=SnapshotExportRequest(
                snapshot_id="proofread_roster_missing_enrichment",
                mode="full",
                batch_size=2,
                materialization=783,
                proofread_root_ids_path=proofread_root_ids_path,
            ),
            output_root=tmp_path,
            flywire_client=FakeFlyWire(),
        )


def test_export_full_uses_offline_proofread_connections_for_edges(tmp_path: Path) -> None:
    import numpy as np
    import pyarrow as pa
    import pyarrow.feather as feather
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot

    proofread_root_ids_path = tmp_path / "proofread_root_ids_783.npy"
    np.save(proofread_root_ids_path, np.array([1, 2, 3], dtype=np.int64))

    annotation_enrichment_path = tmp_path / "annotation_enrichment_783.parquet"
    pq.write_table(
        pa.table(
            {
                "source_id": [1, 2, 3],
                "flow_role": ["afferent", "intrinsic", "efferent"],
                "hemisphere": ["left", "center", "right"],
            }
        ),
        annotation_enrichment_path,
    )

    proofread_connections_path = tmp_path / "proofread_connections_783.feather"
    feather.write_feather(
        pa.table(
            {
                "pre_pt_root_id": [1, 1, 2, 9],
                "post_pt_root_id": [2, 2, 3, 1],
                "neuropil": ["FB", "EB", "LAL_L", "FB"],
                "syn_count": [3, 5, 7, 11],
            }
        ),
        proofread_connections_path,
    )

    class FakeFlyWire:
        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def search_annotations(self, *_args, **_kwargs):
            raise AssertionError("offline proofread connection export should not live-fetch annotations")

        def get_connectivity(self, *_args, **_kwargs):
            raise AssertionError("offline proofread connection export should not call get_connectivity")

    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id="proofread_connections_full",
            mode="full",
            batch_size=2,
            materialization=783,
            proofread_root_ids_path=proofread_root_ids_path,
            annotation_enrichment_path=annotation_enrichment_path,
            proofread_connections_path=proofread_connections_path,
        ),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
    )

    assert result.status == "ok"
    edge_rows = sorted(
        pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet").to_pylist(),
        key=lambda row: (row["pre_id"], row["post_id"]),
    )
    assert edge_rows == [
        {"pre_id": 1, "post_id": 2, "synapse_count": 8, "is_directed": True, "is_active": True},
        {"pre_id": 2, "post_id": 3, "synapse_count": 7, "is_directed": True, "is_active": True},
    ]
    manifest_text = (result.snapshot_dir / "manifest.yaml").read_text(encoding="utf-8")
    assert "edge_source: proofread_connections_783.feather" in manifest_text
