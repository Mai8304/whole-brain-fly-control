from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pyarrow.parquet as pq


def _load_freeze_annotation_enrichment_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "freeze_flywire_annotation_enrichment.py"
    spec = importlib.util.spec_from_file_location("freeze_flywire_annotation_enrichment", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_freeze_annotation_enrichment_writes_parquet_and_manifest(tmp_path: Path) -> None:
    freeze_flywire_annotation_enrichment = _load_freeze_annotation_enrichment_module()

    class FakeFlyWire:
        def search_annotations(self, *_args, **kwargs):
            assert kwargs["materialization"] == 783
            assert kwargs["dataset"] == "public"
            return [
                {"root_id": 1, "flow": "afferent", "side": "left"},
                {"root_id": 2, "flow": "efferent", "side": "right"},
            ]

    output_dir = tmp_path / "annotation_enrichment_release"
    manifest = freeze_flywire_annotation_enrichment.freeze_annotation_enrichment(
        output_dir=output_dir,
        dataset="public",
        materialization=783,
        flywire_client=FakeFlyWire(),
    )

    parquet_path = output_dir / "annotation_enrichment_783.parquet"
    manifest_path = output_dir / "manifest.json"

    assert parquet_path.exists()
    assert manifest_path.exists()
    assert manifest["dataset"] == "public"
    assert manifest["materialization"] == 783
    assert manifest["row_count"] == 2

    rows = sorted(pq.read_table(parquet_path).to_pylist(), key=lambda row: row["source_id"])
    assert rows == [
        {"source_id": 1, "flow_role": "afferent", "hemisphere": "left"},
        {"source_id": 2, "flow_role": "efferent", "hemisphere": "right"},
    ]
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["files"]["annotation_enrichment_783.parquet"]["sha256"]


def test_freeze_annotation_enrichment_cli_prints_manifest_path(tmp_path: Path, capsys) -> None:
    freeze_flywire_annotation_enrichment = _load_freeze_annotation_enrichment_module()

    class FakeFlyWire:
        def search_annotations(self, *_args, **kwargs):
            return [{"root_id": 1, "flow": "afferent", "side": "left"}]

    output_dir = tmp_path / "annotation_enrichment_release"
    exit_code = freeze_flywire_annotation_enrichment.main(
        [
            "--output-dir",
            str(output_dir),
            "--dataset",
            "public",
            "--materialization",
            "783",
        ],
        flywire_client=FakeFlyWire(),
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(output_dir / "manifest.json")
    assert (output_dir / "annotation_enrichment_783.parquet").exists()
