from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq


def test_main_builds_cached_batches_and_final_parquet(monkeypatch, tmp_path: Path, capsys) -> None:
    from scripts import build_synapse_roi_assignment

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

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    (raw_source_dir / "flywire_synapses_783.feather").write_bytes(b"stub")

    def fake_load_release_synapse_rows(*, raw_source_dir: Path, query_ids: set[int]):
        assert raw_source_dir.name == "raw"
        assert query_ids == {11, 22}
        return [
            {"id": 101, "pre_pt_root_id": 11, "post_pt_root_id": 22, "neuropil": "FB"},
        ]

    monkeypatch.setattr(build_synapse_roi_assignment, "load_release_synapse_rows", fake_load_release_synapse_rows)

    output_path = compiled_graph_dir / "synapse_neuropil_assignment.parquet"
    cache_dir = compiled_graph_dir / "synapse_batches"
    exit_code = build_synapse_roi_assignment.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--raw-source-dir",
            str(raw_source_dir),
            "--cache-dir",
            str(cache_dir),
            "--output-path",
            str(output_path),
            "--batch-size",
            "2",
            "--json",
        ]
    )

    assert exit_code == 0
    assert (cache_dir / "batch_00000.json").exists()
    assert output_path.exists()
    payload = json.loads(capsys.readouterr().out)
    assert payload["completed_batches"] == 1
    assert payload["total_rows"] == 2


def test_main_resumes_from_existing_batch_cache(monkeypatch, tmp_path: Path) -> None:
    from scripts import build_synapse_roi_assignment

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist([{"source_id": 11, "node_idx": 0}]),
        compiled_graph_dir / "node_index.parquet",
    )

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    (raw_source_dir / "flywire_synapses_783.feather").write_bytes(b"stub")

    cache_dir = compiled_graph_dir / "synapse_batches"
    cache_dir.mkdir()
    (cache_dir / "batch_00000.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "synapse_id": 101,
                        "root_id": 11,
                        "direction": "pre",
                        "neuropil": "FB",
                        "materialization": 783,
                        "dataset": "public",
                    }
                ],
                "summary": {"batch_index": 0, "total_nodes": 1, "total_rows": 1},
            }
        ),
        encoding="utf-8",
    )

    def fail_if_called(**kwargs):
        raise AssertionError("release loader should not be called when resuming cached batch")

    monkeypatch.setattr(build_synapse_roi_assignment, "load_release_synapse_rows", fail_if_called)

    output_path = compiled_graph_dir / "synapse_neuropil_assignment.parquet"
    exit_code = build_synapse_roi_assignment.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--raw-source-dir",
            str(raw_source_dir),
            "--cache-dir",
            str(cache_dir),
            "--output-path",
            str(output_path),
            "--batch-size",
            "1",
            "--resume",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()


def test_main_writes_batch_parquet_cache_and_streams_final_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from scripts import build_synapse_roi_assignment

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 11, "node_idx": 0},
                {"source_id": 22, "node_idx": 1},
                {"source_id": 33, "node_idx": 2},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    (raw_source_dir / "flywire_synapses_783.feather").write_bytes(b"stub")

    def fake_load_release_synapse_rows(*, raw_source_dir: Path, query_ids: set[int]):
        rows = []
        for query_id in sorted(query_ids):
            rows.append(
                {
                    "id": query_id * 10,
                    "pre_pt_root_id": query_id,
                    "post_pt_root_id": query_id + 1000,
                    "neuropil": "FB",
                }
            )
        return rows

    monkeypatch.setattr(build_synapse_roi_assignment, "load_release_synapse_rows", fake_load_release_synapse_rows)

    output_path = compiled_graph_dir / "synapse_neuropil_assignment.parquet"
    cache_dir = compiled_graph_dir / "synapse_batches"
    exit_code = build_synapse_roi_assignment.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--raw-source-dir",
            str(raw_source_dir),
            "--cache-dir",
            str(cache_dir),
            "--output-path",
            str(output_path),
            "--batch-size",
            "1",
        ]
    )

    assert exit_code == 0
    assert (cache_dir / "batch_00000.parquet").exists()
    assert (cache_dir / "batch_00001.parquet").exists()
    assert (cache_dir / "batch_00002.parquet").exists()

    rows = pq.read_table(output_path).to_pylist()
    assert rows == [
        {
            "synapse_id": 110,
            "root_id": 11,
            "direction": "pre",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        },
        {
            "synapse_id": 220,
            "root_id": 22,
            "direction": "pre",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        },
        {
            "synapse_id": 330,
            "root_id": 33,
            "direction": "pre",
            "neuropil": "FB",
            "materialization": 783,
            "dataset": "public",
        },
    ]


def test_load_release_synapse_rows_filters_official_feather_rows(tmp_path: Path) -> None:
    from scripts.build_synapse_roi_assignment import load_release_synapse_rows

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    feather.write_feather(
        pa.Table.from_pylist(
            [
                {"id": 101, "pre_pt_root_id": 11, "post_pt_root_id": 22, "neuropil": "FB"},
                {"id": 202, "pre_pt_root_id": 33, "post_pt_root_id": 44, "neuropil": "LAL"},
            ]
        ),
        raw_source_dir / "flywire_synapses_783.feather",
    )

    rows = load_release_synapse_rows(raw_source_dir=raw_source_dir, query_ids={11, 44})

    assert rows == [
        {"id": 101, "pre_pt_root_id": 11, "post_pt_root_id": 22, "neuropil": "FB"},
        {"id": 202, "pre_pt_root_id": 33, "post_pt_root_id": 44, "neuropil": "LAL"},
    ]
