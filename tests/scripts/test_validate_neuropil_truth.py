from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq


def test_main_validates_node_neuropil_occupancy_against_official_counts(tmp_path: Path, capsys) -> None:
    from scripts import validate_neuropil_truth

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    occupancy_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 11,
                    "node_idx": 0,
                    "neuropil": "FB",
                    "pre_count": 2,
                    "post_count": 1,
                    "synapse_count": 3,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                }
            ]
        ),
        occupancy_path,
    )

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    feather.write_feather(
        pa.Table.from_pylist([{"root_id": 11, "neuropil": "FB", "count": 2}]),
        raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
    )
    feather.write_feather(
        pa.Table.from_pylist([{"root_id": 11, "neuropil": "FB", "count": 1}]),
        raw_source_dir / "per_neuron_neuropil_count_post_783.feather",
    )

    exit_code = validate_neuropil_truth.main(
        [
            "--raw-source-dir",
            str(raw_source_dir),
            "--occupancy-path",
            str(occupancy_path),
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["validation_passed"] is True
    assert payload["pre_mismatch_count"] == 0
    assert payload["post_mismatch_count"] == 0
    written_payload = json.loads((compiled_graph_dir / "neuropil_truth_validation.json").read_text(encoding="utf-8"))
    assert written_payload["validation_passed"] is True


def test_main_returns_nonzero_when_validation_fails(tmp_path: Path) -> None:
    from scripts import validate_neuropil_truth

    occupancy_path = tmp_path / "node_neuropil_occupancy.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 11,
                    "node_idx": 0,
                    "neuropil": "FB",
                    "pre_count": 1,
                    "post_count": 0,
                    "synapse_count": 1,
                    "occupancy_fraction": 1.0,
                    "materialization": 783,
                    "dataset": "public",
                }
            ]
        ),
        occupancy_path,
    )

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    feather.write_feather(
        pa.Table.from_pylist([{"root_id": 11, "neuropil": "FB", "count": 3}]),
        raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
    )
    feather.write_feather(
        pa.Table.from_pylist([{"root_id": 11, "neuropil": "FB", "count": 0}]),
        raw_source_dir / "per_neuron_neuropil_count_post_783.feather",
    )

    exit_code = validate_neuropil_truth.main(
        [
            "--raw-source-dir",
            str(raw_source_dir),
            "--occupancy-path",
            str(occupancy_path),
        ]
    )

    assert exit_code == 1
    written_payload = json.loads((tmp_path / "neuropil_truth_validation.json").read_text(encoding="utf-8"))
    assert written_payload["validation_passed"] is False
