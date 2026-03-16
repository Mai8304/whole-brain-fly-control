from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq


def _load_validate_neuropil_truth_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "validate_neuropil_truth.py"
    spec = importlib.util.spec_from_file_location("validate_neuropil_truth", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_validates_node_neuropil_occupancy_against_official_counts(tmp_path: Path, capsys) -> None:
    validate_neuropil_truth = _load_validate_neuropil_truth_module()

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
        pa.Table.from_pylist([{"pre_pt_root_id": 11, "neuropil": "FB", "count": 2}]),
        raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
    )
    feather.write_feather(
        pa.Table.from_pylist([{"post_pt_root_id": 11, "neuropil": "FB", "count": 1}]),
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
    validate_neuropil_truth = _load_validate_neuropil_truth_module()

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
        pa.Table.from_pylist([{"pre_pt_root_id": 11, "neuropil": "FB", "count": 3}]),
        raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
    )
    feather.write_feather(
        pa.Table.from_pylist([{"post_pt_root_id": 11, "neuropil": "FB", "count": 0}]),
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


def test_main_uses_graph_scope_and_reports_proofread_alignment(tmp_path: Path, capsys) -> None:
    validate_neuropil_truth = _load_validate_neuropil_truth_module()

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    occupancy_path = compiled_graph_dir / "node_neuropil_occupancy.parquet"
    node_index_path = compiled_graph_dir / "node_index.parquet"
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
    pq.write_table(pa.Table.from_pylist([{"source_id": 11, "node_idx": 0}]), node_index_path)

    raw_source_dir = tmp_path / "raw"
    raw_source_dir.mkdir()
    feather.write_feather(
        pa.Table.from_pylist(
            [
                {"pre_pt_root_id": 11, "neuropil": "FB", "count": 2},
                {"pre_pt_root_id": 22, "neuropil": "GNG", "count": 4},
            ]
        ),
        raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
    )
    feather.write_feather(
        pa.Table.from_pylist(
            [
                {"post_pt_root_id": 11, "neuropil": "FB", "count": 1},
                {"post_pt_root_id": 22, "neuropil": "GNG", "count": 7},
            ]
        ),
        raw_source_dir / "per_neuron_neuropil_count_post_783.feather",
    )
    np.save(raw_source_dir / "proofread_root_ids_783.npy", np.array([11, 22], dtype=np.int64))

    exit_code = validate_neuropil_truth.main(
        [
            "--raw-source-dir",
            str(raw_source_dir),
            "--occupancy-path",
            str(occupancy_path),
            "--node-index-path",
            str(node_index_path),
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["validation_passed"] is True
    assert payload["validation_scope"] == "graph_source_ids"
    assert payload["roster_alignment"]["proofread_only_root_count"] == 1
    assert payload["roster_alignment"]["alignment_passed"] is False
