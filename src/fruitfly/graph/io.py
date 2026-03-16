from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import torch

from .types import CompiledGraph


COMPILED_GRAPH_FILES = {
    "manifest.json",
    "config.json",
    "node_index.parquet",
    "edge_index.pt",
    "io_masks.pt",
    "graph_stats.json",
}


def save_compiled_graph(
    *,
    graph: CompiledGraph,
    compiled_dir: Path,
    snapshot_id: str,
    config: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    compiled_dir.mkdir(parents=True, exist_ok=True)

    resolved_config = {
        "format_version": 1,
        "active_filtering": True,
        "edge_dedup": False,
        "ordering": "active_source_id_order",
    }
    if config:
        resolved_config.update(config)

    resolved_manifest = {
        "snapshot_id": snapshot_id,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "compiled_graph",
    }
    if manifest:
        resolved_manifest.update(manifest)

    node_rows = [
        {"source_id": int(source_id), "node_idx": int(node_idx)}
        for source_id, node_idx in sorted(graph.node_index.items(), key=lambda item: item[1])
    ]
    node_table = pa.Table.from_pylist(node_rows, schema=pa.schema([("source_id", pa.int64()), ("node_idx", pa.int32())]))
    pq.write_table(node_table, compiled_dir / "node_index.parquet")

    edge_tensor = _edge_tensor_from_pairs(graph.edge_index)
    torch.save(edge_tensor, compiled_dir / "edge_index.pt")

    io_masks = {
        "afferent_mask": torch.tensor(graph.afferent_mask, dtype=torch.bool),
        "intrinsic_mask": torch.tensor(graph.intrinsic_mask, dtype=torch.bool),
        "efferent_mask": torch.tensor(graph.efferent_mask, dtype=torch.bool),
    }
    torch.save(io_masks, compiled_dir / "io_masks.pt")

    graph_stats = {
        "node_count": len(graph.node_index),
        "edge_count": len(graph.edge_index),
        "afferent_count": sum(graph.afferent_mask),
        "intrinsic_count": sum(graph.intrinsic_mask),
        "efferent_count": sum(graph.efferent_mask),
    }
    if graph.graph_stats:
        graph_stats.update(graph.graph_stats)

    (compiled_dir / "manifest.json").write_text(
        json.dumps(resolved_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (compiled_dir / "config.json").write_text(
        json.dumps(resolved_config, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (compiled_dir / "graph_stats.json").write_text(
        json.dumps(graph_stats, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_compiled_graph(compiled_dir: Path) -> CompiledGraph:
    import pyarrow.parquet as pq

    table = pq.read_table(compiled_dir / "node_index.parquet")
    source_ids = table.column("source_id").to_pylist()
    node_indices = table.column("node_idx").to_pylist()
    node_index = {int(source_id): int(node_idx) for source_id, node_idx in zip(source_ids, node_indices, strict=True)}

    edge_tensor = torch.load(compiled_dir / "edge_index.pt", map_location="cpu")
    edge_index = _edge_pairs_from_tensor(edge_tensor)

    io_masks = torch.load(compiled_dir / "io_masks.pt", map_location="cpu")
    manifest = json.loads((compiled_dir / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((compiled_dir / "config.json").read_text(encoding="utf-8"))
    graph_stats = json.loads((compiled_dir / "graph_stats.json").read_text(encoding="utf-8"))

    return CompiledGraph(
        node_index=node_index,
        edge_index=edge_index,
        afferent_mask=_mask_to_list(io_masks["afferent_mask"]),
        intrinsic_mask=_mask_to_list(io_masks["intrinsic_mask"]),
        efferent_mask=_mask_to_list(io_masks["efferent_mask"]),
        manifest=manifest,
        config=config,
        graph_stats=graph_stats,
    )


def load_compiled_graph_tensors(compiled_dir: Path) -> dict[str, Any]:
    import pyarrow.parquet as pq

    table = pq.read_table(compiled_dir / "node_index.parquet")
    source_ids = table.column("source_id").to_pylist()
    node_indices = table.column("node_idx").to_pylist()
    node_index = {int(source_id): int(node_idx) for source_id, node_idx in zip(source_ids, node_indices, strict=True)}

    io_masks = torch.load(compiled_dir / "io_masks.pt", map_location="cpu")
    edge_index = torch.load(compiled_dir / "edge_index.pt", map_location="cpu")

    return {
        "node_index": node_index,
        "edge_index": edge_index,
        "afferent_mask": io_masks["afferent_mask"].to(dtype=torch.bool),
        "intrinsic_mask": io_masks["intrinsic_mask"].to(dtype=torch.bool),
        "efferent_mask": io_masks["efferent_mask"].to(dtype=torch.bool),
        "manifest": json.loads((compiled_dir / "manifest.json").read_text(encoding="utf-8")),
        "config": json.loads((compiled_dir / "config.json").read_text(encoding="utf-8")),
        "graph_stats": json.loads((compiled_dir / "graph_stats.json").read_text(encoding="utf-8")),
    }


def load_compiled_graph_runtime(compiled_dir: Path) -> dict[str, Any]:
    io_masks = torch.load(compiled_dir / "io_masks.pt", map_location="cpu")
    edge_index = torch.load(compiled_dir / "edge_index.pt", map_location="cpu")
    manifest = json.loads((compiled_dir / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((compiled_dir / "config.json").read_text(encoding="utf-8"))
    graph_stats = json.loads((compiled_dir / "graph_stats.json").read_text(encoding="utf-8"))
    return {
        "edge_index": edge_index,
        "afferent_mask": io_masks["afferent_mask"].to(dtype=torch.bool),
        "intrinsic_mask": io_masks["intrinsic_mask"].to(dtype=torch.bool),
        "efferent_mask": io_masks["efferent_mask"].to(dtype=torch.bool),
        "manifest": manifest,
        "config": config,
        "graph_stats": graph_stats,
        "node_count": int(graph_stats["node_count"]),
    }


def _edge_tensor_from_pairs(edge_index: list[tuple[int, int]]) -> torch.Tensor:
    if not edge_index:
        return torch.empty((2, 0), dtype=torch.long)
    src = [int(source) for source, _ in edge_index]
    dst = [int(target) for _, target in edge_index]
    return torch.tensor([src, dst], dtype=torch.long)


def _edge_pairs_from_tensor(edge_index: torch.Tensor) -> list[tuple[int, int]]:
    if edge_index.numel() == 0:
        return []
    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError("edge_index.pt must contain a [2, E] tensor")
    src = edge_index[0].tolist()
    dst = edge_index[1].tolist()
    return [(int(source), int(target)) for source, target in zip(src, dst, strict=True)]


def _mask_to_list(mask: torch.Tensor) -> list[bool]:
    return [bool(value) for value in mask.tolist()]
