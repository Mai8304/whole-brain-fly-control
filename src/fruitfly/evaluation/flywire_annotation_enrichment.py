from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

ANNOTATION_ENRICHMENT_COLUMNS = [
    "source_id",
    "flow_role",
    "hemisphere",
]


def annotation_enrichment_filename(*, materialization: int | str) -> str:
    return f"annotation_enrichment_{materialization}.parquet"


def normalize_annotation_enrichment_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for record in records:
        if "root_id" not in record and "source_id" not in record:
            continue
        source_id = int(record.get("root_id", record.get("source_id")))
        normalized.append(
            {
                "source_id": source_id,
                "flow_role": str(record.get("flow") or record.get("flow_role") or "unknown"),
                "hemisphere": str(record.get("side") or record.get("hemisphere") or "unknown"),
            }
        )
    normalized.sort(key=lambda row: row["source_id"])
    return normalized


def write_annotation_enrichment(path: Path, rows: list[dict[str, Any]]) -> None:
    table = pa.table(
        {
            column: [row.get(column) for row in rows]
            for column in ANNOTATION_ENRICHMENT_COLUMNS
        }
    )
    pq.write_table(table, path)


def load_annotation_enrichment(path: Path) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    missing = set(ANNOTATION_ENRICHMENT_COLUMNS) - set(table.column_names)
    if missing:
        raise ValueError(f"annotation enrichment missing columns: {sorted(missing)}")
    rows = table.to_pylist()
    return [
        {
            "source_id": int(row["source_id"]),
            "flow_role": str(row["flow_role"] or "unknown"),
            "hemisphere": str(row["hemisphere"] or "unknown"),
        }
        for row in rows
    ]


def build_annotation_enrichment_manifest(
    *,
    output_dir: Path,
    dataset: str,
    materialization: int | str,
) -> dict[str, Any]:
    parquet_name = annotation_enrichment_filename(materialization=materialization)
    parquet_path = output_dir / parquet_name
    if not parquet_path.exists():
        raise ValueError(f"annotation enrichment parquet missing: {parquet_path}")
    row_count = pq.read_table(parquet_path, columns=["source_id"]).num_rows
    return {
        "dataset": str(dataset),
        "materialization": int(materialization) if isinstance(materialization, int) or str(materialization).isdigit() else str(materialization),
        "source": "FlyWire search_annotations enrichment snapshot",
        "files": {
            parquet_name: {
                "sha256": _sha256(parquet_path),
            }
        },
        "row_count": int(row_count),
    }


def write_annotation_enrichment_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
