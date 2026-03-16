from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.evaluation.flywire_annotation_enrichment import (
    annotation_enrichment_filename,
    build_annotation_enrichment_manifest,
    normalize_annotation_enrichment_records,
    write_annotation_enrichment,
    write_annotation_enrichment_manifest,
)
from fruitfly.snapshot.exporter import _call_quietly, _list_records


def freeze_annotation_enrichment(
    *,
    output_dir: Path,
    dataset: str,
    materialization: int | str,
    flywire_client: object,
) -> dict[str, object]:
    if not hasattr(flywire_client, "search_annotations"):
        raise RuntimeError("FlyWire annotation enrichment freeze requires search_annotations(...).")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_records = _call_quietly(
        getattr(flywire_client, "search_annotations"),
        None,
        materialization=materialization,
        verbose=False,
        regex=False,
        dataset=dataset,
    )
    rows = normalize_annotation_enrichment_records(_list_records(raw_records))
    parquet_path = output_dir / annotation_enrichment_filename(materialization=materialization)
    write_annotation_enrichment(parquet_path, rows)
    manifest = build_annotation_enrichment_manifest(
        output_dir=output_dir,
        dataset=dataset,
        materialization=materialization,
    )
    write_annotation_enrichment_manifest(output_dir / "manifest.json", manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze FlyWire annotation enrichment into a local derived-source directory."
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Destination directory for annotation enrichment parquet and manifest.")
    parser.add_argument("--dataset", default="public", help="FlyWire dataset name.")
    parser.add_argument("--materialization", default="783", help="FlyWire materialization version.")
    parser.add_argument("--json", action="store_true", help="Print the manifest as JSON.")
    return parser


def main(argv: list[str] | None = None, *, flywire_client: object | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        materialization: int | str = int(args.materialization)
    except ValueError:
        materialization = args.materialization

    client = flywire_client
    if client is None:
        from fafbseg import flywire as client  # type: ignore[assignment]

    manifest = freeze_annotation_enrichment(
        output_dir=args.output_dir,
        dataset=args.dataset,
        materialization=materialization,
        flywire_client=client,
    )
    if args.json:
        print(json.dumps(manifest))
    else:
        print(args.output_dir / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
