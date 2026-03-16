from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

from fruitfly.evaluation.node_neuropil_occupancy import (
    aggregate_node_neuropil_occupancy_rows_from_batches,
    write_node_neuropil_occupancy,
)

DEFAULT_SYNTH_BATCH_SIZE = 500_000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build node_neuropil_occupancy.parquet from formal synapse_neuropil_assignment truth."
    )
    parser.add_argument(
        "--compiled-graph-dir",
        type=Path,
        required=True,
        help="Directory containing node_index.parquet and, by default, synapse_neuropil_assignment.parquet.",
    )
    parser.add_argument(
        "--synapse-assignment-path",
        type=Path,
        default=None,
        help="Optional explicit path to synapse_neuropil_assignment.parquet.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional explicit output path. Defaults to <compiled-graph-dir>/node_neuropil_occupancy.parquet.",
    )
    parser.add_argument("--json", action="store_true", help="Print the build summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    node_index_path = args.compiled_graph_dir / "node_index.parquet"
    synapse_assignment_path = args.synapse_assignment_path or (args.compiled_graph_dir / "synapse_neuropil_assignment.parquet")
    output_path = args.output_path or (args.compiled_graph_dir / "node_neuropil_occupancy.parquet")

    node_index_rows = pq.read_table(node_index_path).to_pylist()
    synapse_assignment_file = pq.ParquetFile(synapse_assignment_path)
    occupancy_rows = aggregate_node_neuropil_occupancy_rows_from_batches(
        synapse_assignment_batches=synapse_assignment_file.iter_batches(
            batch_size=DEFAULT_SYNTH_BATCH_SIZE,
            columns=["root_id", "direction", "neuropil", "materialization", "dataset"],
        ),
        node_index_rows=node_index_rows,
    )
    write_node_neuropil_occupancy(output_path, occupancy_rows)

    summary = {
        "total_nodes": len({int(row["source_id"]) for row in occupancy_rows}),
        "occupancy_rows": len(occupancy_rows),
        "output_path": str(output_path),
    }
    if args.json:
        print(json.dumps(summary))
    else:
        print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
