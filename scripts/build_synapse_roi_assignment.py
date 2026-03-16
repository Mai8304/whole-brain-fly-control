from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from fruitfly.evaluation.flywire_neuropil_raw import (
    FLYWIRE_783_DATASET,
    FLYWIRE_783_RELEASE_VERSION,
)
from fruitfly.evaluation.synapse_neuropil_assignment import (
    SYNAPSE_NEUROPIL_ASSIGNMENT_SCHEMA,
    compile_synapse_assignment_rows,
    rows_to_synapse_assignment_table,
    write_synapse_assignment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile synapse_neuropil_assignment.parquet from the FlyWire 783 official synapse release."
    )
    parser.add_argument(
        "--compiled-graph-dir",
        type=Path,
        required=True,
        help="Directory containing node_index.parquet from the compiled full-brain graph.",
    )
    parser.add_argument(
        "--raw-source-dir",
        type=Path,
        required=True,
        help="Directory containing flywire_synapses_783.feather from the frozen FlyWire 783 raw source layer.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="Batch cache directory used for resumable synapse-neuropil assignment compile.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Destination parquet path. Defaults to <compiled-graph-dir>/synapse_neuropil_assignment.parquet.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Number of query roots per batch.",
    )
    parser.add_argument(
        "--limit-nodes",
        type=int,
        default=None,
        help="Optional smoke limit for the number of nodes to compile.",
    )
    parser.add_argument(
        "--dataset",
        default=FLYWIRE_783_DATASET,
        help="Dataset label written into the formal truth rows.",
    )
    parser.add_argument(
        "--materialization",
        default=FLYWIRE_783_RELEASE_VERSION,
        help="Materialization label written into the formal truth rows.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing batch cache files from --cache-dir when available.",
    )
    parser.add_argument("--json", action="store_true", help="Print the final summary as JSON.")
    return parser


def load_release_synapse_rows(*, raw_source_dir: Path, query_ids: set[int]) -> list[dict[str, object]]:
    synapse_path = raw_source_dir / "flywire_synapses_783.feather"
    if not synapse_path.exists():
        raise ValueError(f"missing required FlyWire synapse release file: {synapse_path}")
    if not query_ids:
        return []

    dataset = ds.dataset(synapse_path, format="ipc")
    query_values = pa.array(sorted(query_ids), type=pa.int64())
    filter_expr = ds.field("pre_pt_root_id").isin(query_values) | ds.field("post_pt_root_id").isin(query_values)
    table = dataset.to_table(
        columns=["id", "pre_pt_root_id", "post_pt_root_id", "neuropil"],
        filter=filter_expr,
    )
    return table.to_pylist()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = args.output_path or (args.compiled_graph_dir / "synapse_neuropil_assignment.parquet")
    node_index_path = args.compiled_graph_dir / "node_index.parquet"

    node_index_rows = pq.read_table(node_index_path).to_pylist()
    if args.limit_nodes is not None:
        node_index_rows = node_index_rows[: args.limit_nodes]

    summary = _compile_with_cache(
        node_index_rows=node_index_rows,
        raw_source_dir=args.raw_source_dir,
        cache_dir=args.cache_dir,
        batch_size=args.batch_size,
        dataset=str(args.dataset),
        materialization=args.materialization,
        resume=bool(args.resume),
        output_path=output_path,
    )

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
    raw_source_dir: Path,
    cache_dir: Path,
    batch_size: int,
    dataset: str,
    materialization: str,
    resume: bool,
    output_path: Path,
) -> dict[str, object]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    total_nodes = len(node_index_rows)
    total_rows = 0
    completed_batches = 0
    batch_cache_paths: list[Path] = []

    for batch_index, batch_rows in enumerate(_batched(node_index_rows, batch_size)):
        cache_json_path = cache_dir / f"batch_{batch_index:05d}.json"
        cache_parquet_path = cache_dir / f"batch_{batch_index:05d}.parquet"
        if resume and cache_json_path.exists():
            cached_payload = json.loads(cache_json_path.read_text(encoding="utf-8"))
            if cache_parquet_path.exists():
                payload = cached_payload
            elif isinstance(cached_payload, dict) and "rows" in cached_payload:
                write_synapse_assignment(cache_parquet_path, rows=cached_payload["rows"])
                payload = cached_payload
            else:
                query_ids = {int(row["source_id"]) for row in batch_rows}
                synapse_rows = load_release_synapse_rows(raw_source_dir=raw_source_dir, query_ids=query_ids)
                compiled_rows = compile_synapse_assignment_rows(
                    synapse_rows=synapse_rows,
                    query_ids=query_ids,
                    materialization=materialization,
                    dataset=dataset,
                )
                payload = {
                    "rows": compiled_rows,
                    "summary": {
                        "batch_index": batch_index,
                        "total_nodes": len(batch_rows),
                        "total_rows": len(compiled_rows),
                    },
                }
                write_synapse_assignment(cache_parquet_path, rows=compiled_rows)
                cache_json_path.write_text(json.dumps(payload["summary"]), encoding="utf-8")
        else:
            query_ids = {int(row["source_id"]) for row in batch_rows}
            synapse_rows = load_release_synapse_rows(raw_source_dir=raw_source_dir, query_ids=query_ids)
            compiled_rows = compile_synapse_assignment_rows(
                synapse_rows=synapse_rows,
                query_ids=query_ids,
                materialization=materialization,
                dataset=dataset,
            )
            payload = {
                "rows": compiled_rows,
                "summary": {
                    "batch_index": batch_index,
                    "total_nodes": len(batch_rows),
                    "total_rows": len(compiled_rows),
                },
            }
            write_synapse_assignment(cache_parquet_path, rows=compiled_rows)
            cache_json_path.write_text(json.dumps(payload["summary"]), encoding="utf-8")

        if cache_parquet_path.exists():
            batch_cache_paths.append(cache_parquet_path)
        total_rows += int(payload["summary"]["total_rows"] if "summary" in payload else payload["total_rows"])
        completed_batches += 1

    _merge_batch_parquet_files(batch_cache_paths=batch_cache_paths, output_path=output_path)

    summary = {
        "total_nodes": total_nodes,
        "total_rows": total_rows,
        "completed_batches": completed_batches,
        "dataset": dataset,
        "materialization": materialization,
        "cache_dir": str(cache_dir),
    }
    return summary


def _batched(values: list[dict[str, object]], batch_size: int):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for index in range(0, len(values), batch_size):
        yield values[index : index + batch_size]


def _merge_batch_parquet_files(*, batch_cache_paths: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not batch_cache_paths:
        pq.write_table(rows_to_synapse_assignment_table([]), output_path)
        return

    with pq.ParquetWriter(output_path, SYNAPSE_NEUROPIL_ASSIGNMENT_SCHEMA) as writer:
        for batch_cache_path in batch_cache_paths:
            writer.write_table(pq.read_table(batch_cache_path))


if __name__ == "__main__":
    raise SystemExit(main())
