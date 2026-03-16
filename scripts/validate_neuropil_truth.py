from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

from fruitfly.evaluation.neuropil_truth_validation import validate_node_neuropil_occupancy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate node_neuropil_occupancy.parquet against official FlyWire 783 per-neuron neuropil counts."
    )
    parser.add_argument(
        "--raw-source-dir",
        type=Path,
        required=True,
        help="Directory containing official per_neuron_neuropil_count_*_783.feather files.",
    )
    parser.add_argument(
        "--occupancy-path",
        type=Path,
        required=True,
        help="Path to node_neuropil_occupancy.parquet.",
    )
    parser.add_argument(
        "--node-index-path",
        type=Path,
        default=None,
        help="Optional path to node_index.parquet. Defaults to <occupancy-dir>/node_index.parquet when present.",
    )
    parser.add_argument(
        "--proofread-root-ids-path",
        type=Path,
        default=None,
        help="Optional path to proofread_root_ids_783.npy. Defaults to <raw-source-dir>/proofread_root_ids_783.npy when present.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional validation JSON output path. Defaults to <occupancy-dir>/neuropil_truth_validation.json.",
    )
    parser.add_argument("--json", action="store_true", help="Print validation payload as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = args.output_path or (args.occupancy_path.parent / "neuropil_truth_validation.json")
    node_index_path = args.node_index_path or (args.occupancy_path.parent / "node_index.parquet")
    proofread_root_ids_path = args.proofread_root_ids_path or (args.raw_source_dir / "proofread_root_ids_783.npy")

    graph_source_ids = _load_graph_source_ids(node_index_path) if node_index_path.exists() else None
    proofread_root_ids = _load_proofread_root_ids(proofread_root_ids_path) if proofread_root_ids_path.exists() else None

    occupancy_rows = _iter_parquet_rows(
        args.occupancy_path,
        columns=["source_id", "neuropil", "pre_count", "post_count"],
    )
    official_pre_rows = _iter_feather_rows(
        args.raw_source_dir / "per_neuron_neuropil_count_pre_783.feather",
        columns=["pre_pt_root_id", "neuropil", "count"],
    )
    official_post_rows = _iter_feather_rows(
        args.raw_source_dir / "per_neuron_neuropil_count_post_783.feather",
        columns=["post_pt_root_id", "neuropil", "count"],
    )

    result = validate_node_neuropil_occupancy(
        occupancy_rows=occupancy_rows,
        official_pre_rows=official_pre_rows,
        official_post_rows=official_post_rows,
        graph_source_ids=graph_source_ids,
        proofread_root_ids=proofread_root_ids,
    )
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(result))
    else:
        print("validation_passed" if result["validation_passed"] else "validation_failed")
    return 0 if result["validation_passed"] else 1

def _load_graph_source_ids(path: Path) -> set[int]:
    table = pq.read_table(path, columns=["source_id"])
    return {int(value.as_py()) for value in table.column("source_id")}


def _load_proofread_root_ids(path: Path) -> set[int]:
    return {int(value) for value in np.load(path).tolist()}


def _iter_parquet_rows(path: Path, *, columns: list[str]) -> object:
    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(columns=columns):
        for row in batch.to_pylist():
            yield row


def _iter_feather_rows(path: Path, *, columns: list[str]) -> object:
    reader = ipc.RecordBatchFileReader(pa.memory_map(str(path), "r"))
    for batch_index in range(reader.num_record_batches):
        batch = reader.get_batch(batch_index).select(columns)
        for row in batch.to_pylist():
            yield row


if __name__ == "__main__":
    raise SystemExit(main())
