from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.feather as feather
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
    occupancy_rows = pq.read_table(args.occupancy_path).to_pylist()
    official_pre_rows = feather.read_table(args.raw_source_dir / "per_neuron_neuropil_count_pre_783.feather").to_pylist()
    official_post_rows = feather.read_table(args.raw_source_dir / "per_neuron_neuropil_count_post_783.feather").to_pylist()

    result = validate_node_neuropil_occupancy(
        occupancy_rows=occupancy_rows,
        official_pre_rows=official_pre_rows,
        official_post_rows=official_post_rows,
    )
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(result))
    else:
        print("validation_passed" if result["validation_passed"] else "validation_failed")
    return 0 if result["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
