from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

from fruitfly.evaluation.node_roi_compile import (
    compile_node_roi_map_batch_rows,
    compile_node_roi_map_rows,
    write_node_roi_map,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a node_roi_map.parquet for the V1 ROI set using FlyWire synapse-count evidence by neuropil."
    )
    parser.add_argument(
        "--compiled-graph-dir",
        type=Path,
        required=True,
        help="Directory containing node_index.parquet from a compiled full-brain graph.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Where node_roi_map.parquet is written. Defaults to <compiled-graph-dir>/node_roi_map.parquet.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Number of root IDs to query per batch.",
    )
    parser.add_argument(
        "--limit-nodes",
        type=int,
        default=None,
        help="Optional smoke limit for the number of nodes to compile.",
    )
    parser.add_argument(
        "--dataset",
        default="public",
        help="FlyWire dataset passed to fafbseg.flywire.get_synapse_counts.",
    )
    parser.add_argument(
        "--materialization",
        default="latest",
        help='Materialization passed to fafbseg.flywire.get_synapse_counts, e.g. "latest" or an integer.',
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional batch-cache directory for slow FlyWire synapse-count queries.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing batch-cache files from --cache-dir when available.",
    )
    parser.add_argument("--json", action="store_true", help="Print the compile summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    node_index_path = args.compiled_graph_dir / "node_index.parquet"
    output_path = args.output_path or (args.compiled_graph_dir / "node_roi_map.parquet")

    node_index_rows = pq.read_table(node_index_path).to_pylist()
    if args.limit_nodes is not None:
        node_index_rows = node_index_rows[: args.limit_nodes]

    materialization: str | int = args.materialization
    if isinstance(materialization, str) and materialization.isdigit():
        materialization = int(materialization)

    if args.cache_dir is None:
        rows, summary = compile_node_roi_map_rows(
            node_index_rows=node_index_rows,
            batch_size=args.batch_size,
            dataset=str(args.dataset),
            materialization=materialization,
        )
    else:
        rows, summary = _compile_with_cache(
            node_index_rows=node_index_rows,
            cache_dir=args.cache_dir,
            batch_size=args.batch_size,
            dataset=str(args.dataset),
            materialization=materialization,
            resume=bool(args.resume),
        )
    write_node_roi_map(output_path, rows)

    summary_payload = dict(summary)
    summary_payload["output_path"] = str(output_path)
    if args.json:
        print(json.dumps(summary_payload))
    else:
        print(output_path)
    return 0


def _compile_with_cache(
    *,
    node_index_rows: list[dict[str, object]],
    cache_dir: Path,
    batch_size: int,
    dataset: str,
    materialization: str | int,
    resume: bool,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    aggregated_rows: list[dict[str, object]] = []
    roi_counts: dict[str, int] | None = None
    total_nodes = len(node_index_rows)
    mapped_nodes = 0
    completed_batches = 0

    for batch_index, batch_rows in enumerate(_batched(node_index_rows, batch_size)):
        cache_path = cache_dir / f"batch_{batch_index:05d}.json"
        if resume and cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            compiled_rows, batch_summary = compile_node_roi_map_batch_rows(
                node_index_rows=batch_rows,
                dataset=dataset,
                materialization=materialization,
            )
            payload = {"rows": compiled_rows, "summary": batch_summary}
            cache_path.write_text(json.dumps(payload), encoding="utf-8")

        aggregated_rows.extend(payload["rows"])
        mapped_nodes += int(payload["summary"]["mapped_nodes"])
        batch_counts = payload["summary"]["roi_counts"]
        if roi_counts is None:
            roi_counts = {str(key): int(value) for key, value in batch_counts.items()}
        else:
            for roi_id, value in batch_counts.items():
                roi_counts[str(roi_id)] += int(value)
        completed_batches += 1

    roi_counts = roi_counts or {}
    summary = {
        "total_nodes": total_nodes,
        "mapped_nodes": mapped_nodes,
        "mapping_coverage": (mapped_nodes / total_nodes) if total_nodes else 0.0,
        "roi_counts": roi_counts,
        "materialization": materialization,
        "dataset": dataset,
        "cache_dir": str(cache_dir),
        "completed_batches": completed_batches,
    }
    return sorted(aggregated_rows, key=lambda row: int(row["node_idx"])), summary


def _batched(values: list[dict[str, object]], batch_size: int):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for index in range(0, len(values), batch_size):
        yield values[index : index + batch_size]


if __name__ == "__main__":
    raise SystemExit(main())
