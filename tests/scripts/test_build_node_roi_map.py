from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts import build_node_roi_map


def test_main_writes_default_output_and_prints_path(monkeypatch, tmp_path: Path, capsys) -> None:
    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 11, "node_idx": 0},
                {"source_id": 22, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )

    def fake_compile(**kwargs):
        return (
            [{"source_id": 11, "node_idx": 0, "roi_id": "AL"}],
            {"mapped_nodes": 1, "total_nodes": 2, "mapping_coverage": 0.5, "roi_counts": {"AL": 1}},
        )

    written: dict[str, object] = {}

    def fake_write(path: Path, rows):
        written["path"] = path
        written["rows"] = rows

    monkeypatch.setattr(build_node_roi_map, "compile_node_roi_map_rows", fake_compile)
    monkeypatch.setattr(build_node_roi_map, "write_node_roi_map", fake_write)

    exit_code = build_node_roi_map.main(["--compiled-graph-dir", str(compiled_graph_dir)])

    assert exit_code == 0
    assert written["path"] == compiled_graph_dir / "node_roi_map.parquet"
    assert written["rows"] == [{"source_id": 11, "node_idx": 0, "roi_id": "AL"}]
    assert capsys.readouterr().out.strip() == str(compiled_graph_dir / "node_roi_map.parquet")


def test_main_supports_json_and_limit(monkeypatch, tmp_path: Path, capsys) -> None:
    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 11, "node_idx": 0},
                {"source_id": 22, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )

    captured: dict[str, object] = {}

    def fake_compile(**kwargs):
        captured["kwargs"] = kwargs
        return (
            [{"source_id": 11, "node_idx": 0, "roi_id": "AL"}],
            {"mapped_nodes": 1, "total_nodes": 1, "mapping_coverage": 1.0, "roi_counts": {"AL": 1}},
        )

    monkeypatch.setattr(build_node_roi_map, "compile_node_roi_map_rows", fake_compile)
    monkeypatch.setattr(build_node_roi_map, "write_node_roi_map", lambda path, rows: None)

    exit_code = build_node_roi_map.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--limit-nodes",
            "1",
            "--materialization",
            "783",
            "--json",
        ]
    )

    assert exit_code == 0
    assert captured["kwargs"]["node_index_rows"] == [{"source_id": 11, "node_idx": 0}]
    assert captured["kwargs"]["materialization"] == 783
    payload = json.loads(capsys.readouterr().out)
    assert payload["mapped_nodes"] == 1
    assert payload["output_path"] == str(compiled_graph_dir / "node_roi_map.parquet")


def test_main_uses_cache_dir_with_resume(monkeypatch, tmp_path: Path, capsys) -> None:
    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 11, "node_idx": 0},
                {"source_id": 22, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(
        build_node_roi_map,
        "_compile_with_cache",
        lambda **kwargs: (
            [{"source_id": 11, "node_idx": 0, "roi_id": "AL"}],
            {"mapped_nodes": 1, "total_nodes": 2, "mapping_coverage": 0.5, "roi_counts": {"AL": 1}},
        ),
    )
    monkeypatch.setattr(build_node_roi_map, "write_node_roi_map", lambda path, rows: None)

    exit_code = build_node_roi_map.main(
        [
            "--compiled-graph-dir",
            str(compiled_graph_dir),
            "--cache-dir",
            str(cache_dir),
            "--resume",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mapped_nodes"] == 1
