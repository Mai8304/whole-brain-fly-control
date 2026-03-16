from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def test_main_builds_node_neuropil_occupancy(tmp_path: Path, capsys) -> None:
    from scripts import build_node_neuropil_occupancy

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 11, "node_idx": 0},
                {"source_id": 22, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )

    synapse_assignment_path = compiled_graph_dir / "synapse_neuropil_assignment.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"synapse_id": 1, "root_id": 11, "direction": "pre", "neuropil": "FB", "materialization": 783, "dataset": "public"},
                {"synapse_id": 2, "root_id": 11, "direction": "post", "neuropil": "FB", "materialization": 783, "dataset": "public"},
                {"synapse_id": 3, "root_id": 11, "direction": "pre", "neuropil": "LAL", "materialization": 783, "dataset": "public"},
                {"synapse_id": 4, "root_id": 22, "direction": "post", "neuropil": "GNG", "materialization": 783, "dataset": "public"},
            ]
        ),
        synapse_assignment_path,
    )

    output_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    exit_code = build_node_neuropil_occupancy.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--synapse-assignment-path",
            str(synapse_assignment_path),
            "--output-path",
            str(output_path),
            "--json",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_nodes"] == 2
    assert payload["occupancy_rows"] == 3
    assert payload["output_path"] == str(output_path)


def test_main_defaults_to_compiled_graph_artifact_paths(tmp_path: Path) -> None:
    from scripts import build_node_neuropil_occupancy

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist([{"source_id": 11, "node_idx": 0}]),
        compiled_graph_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"synapse_id": 1, "root_id": 11, "direction": "pre", "neuropil": "FB", "materialization": 783, "dataset": "public"},
            ]
        ),
        compiled_graph_dir / "synapse_neuropil_assignment.parquet",
    )

    exit_code = build_node_neuropil_occupancy.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
        ]
    )

    assert exit_code == 0
    assert (compiled_graph_dir / "node_neuropil_occupancy.parquet").exists()


def test_main_streams_synapse_assignment_batches(tmp_path: Path) -> None:
    from scripts import build_node_neuropil_occupancy

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    node_index_path = compiled_graph_dir / "node_index.parquet"
    synapse_assignment_path = compiled_graph_dir / "synapse_neuropil_assignment.parquet"
    output_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"

    pq.write_table(
        pa.Table.from_pylist([{"source_id": 11, "node_idx": 0}]),
        node_index_path,
    )
    synapse_assignment_path.write_bytes(b"stub")

    original_read_table = build_node_neuropil_occupancy.pq.read_table

    def fake_read_table(path, *args, **kwargs):
        if Path(path) == synapse_assignment_path:
            raise AssertionError("synapse assignment should be streamed via ParquetFile.iter_batches")
        return original_read_table(path, *args, **kwargs)

    class FakeParquetFile:
        def __init__(self, path):
            assert Path(path) == synapse_assignment_path

        def iter_batches(self, batch_size=None, columns=None):
            assert columns == ["root_id", "direction", "neuropil", "materialization", "dataset"]
            yield pa.RecordBatch.from_pylist(
                [
                    {
                        "root_id": 11,
                        "direction": "pre",
                        "neuropil": "FB",
                        "materialization": 783,
                        "dataset": "public",
                    },
                    {
                        "root_id": 11,
                        "direction": "post",
                        "neuropil": "FB",
                        "materialization": 783,
                        "dataset": "public",
                    },
                ]
            )

    monkeypatch = __import__("pytest").MonkeyPatch()
    monkeypatch.setattr(build_node_neuropil_occupancy.pq, "read_table", fake_read_table)
    monkeypatch.setattr(build_node_neuropil_occupancy.pq, "ParquetFile", FakeParquetFile)
    try:
        exit_code = build_node_neuropil_occupancy.main(
            [
                "--compiled-graph-dir",
                str(compiled_graph_dir),
                "--output-path",
                str(output_path),
            ]
        )
    finally:
        monkeypatch.undo()

    assert exit_code == 0
    table = pq.read_table(output_path)
    assert table.to_pylist() == [
        {
            "source_id": 11,
            "node_idx": 0,
            "neuropil": "FB",
            "pre_count": 1,
            "post_count": 1,
            "synapse_count": 2,
            "occupancy_fraction": 1.0,
            "materialization": 783,
            "dataset": "public",
        }
    ]
