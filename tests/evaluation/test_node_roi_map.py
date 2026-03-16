from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


def test_load_node_roi_map_requires_source_id_node_idx_and_roi_id(tmp_path: Path) -> None:
    from fruitfly.evaluation.node_roi_map import load_node_roi_map

    path = tmp_path / "node_roi_map.parquet"
    table = pa.table(
        {
            "source_id": [1],
            "roi_id": ["AL"],
        }
    )
    pq.write_table(table, path)

    with pytest.raises(ValueError, match="missing columns"):
        load_node_roi_map(path)


def test_load_node_roi_map_rejects_unknown_roi_ids(tmp_path: Path) -> None:
    from fruitfly.evaluation.node_roi_map import load_node_roi_map

    path = tmp_path / "node_roi_map.parquet"
    table = pa.table(
        {
            "source_id": [1],
            "node_idx": [0],
            "roi_id": ["UNKNOWN"],
        }
    )
    pq.write_table(table, path)

    with pytest.raises(ValueError, match="unknown roi_id"):
        load_node_roi_map(path)


def test_load_node_roi_map_returns_typed_rows(tmp_path: Path) -> None:
    from fruitfly.evaluation.node_roi_map import load_node_roi_map

    path = tmp_path / "node_roi_map.parquet"
    table = pa.table(
        {
            "source_id": [1, 2],
            "node_idx": [0, 1],
            "roi_id": ["AL", "FB"],
        }
    )
    pq.write_table(table, path)

    rows = load_node_roi_map(path)

    assert rows == [
        {"source_id": 1, "node_idx": 0, "roi_id": "AL"},
        {"source_id": 2, "node_idx": 1, "roi_id": "FB"},
    ]


def test_load_node_roi_map_allows_null_roi_ids(tmp_path: Path) -> None:
    from fruitfly.evaluation.node_roi_map import load_node_roi_map

    path = tmp_path / "node_roi_map.parquet"
    table = pa.table(
        {
            "source_id": [1, 2],
            "node_idx": [0, 1],
            "roi_id": ["AL", None],
        }
    )
    pq.write_table(table, path)

    rows = load_node_roi_map(path)

    assert rows == [
        {"source_id": 1, "node_idx": 0, "roi_id": "AL"},
        {"source_id": 2, "node_idx": 1, "roi_id": None},
    ]
