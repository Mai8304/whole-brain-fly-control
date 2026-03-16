from __future__ import annotations

import argparse
import contextlib
from collections.abc import Sequence
from dataclasses import dataclass
import io
import json
from pathlib import Path
import time
import sys
from typing import Any

import yaml

from .flywire_verify import DEFAULT_PUBLIC_COORDS, require_fafbseg


DEFAULT_SNAPSHOT_ROOT = Path("data/connectome/snapshots")
NORMALIZED_NODE_COLUMNS = [
    "source_id",
    "dataset_version",
    "hemisphere",
    "flow_role",
    "is_active",
]
NORMALIZED_EDGE_COLUMNS = [
    "pre_id",
    "post_id",
    "synapse_count",
    "is_directed",
    "is_active",
]
NORMALIZED_PARTITION_COLUMNS = [
    "source_id",
    "flow_role",
    "partition_version",
]


@dataclass(slots=True)
class SnapshotExportRequest:
    snapshot_id: str
    dataset: str = "public"
    mode: str = "dry-run"
    resume: bool = False
    seed_root_id: int | None = None
    max_hops: int = 2
    max_nodes: int = 5000
    batch_size: int = 256
    seed_strategy: str = "readonly_coords"


@dataclass(slots=True)
class SnapshotExportResult:
    snapshot_dir: Path
    seed_root_id: int
    node_count: int
    edge_count: int
    status: str


def build_snapshot_paths(snapshot_id: str, *, output_root: Path = DEFAULT_SNAPSHOT_ROOT) -> dict[str, Path]:
    snapshot_dir = output_root / snapshot_id
    return {
        "snapshot_dir": snapshot_dir,
        "raw_dir": snapshot_dir / "raw",
        "normalized_dir": snapshot_dir / "normalized",
        "connectivity_batch_dir": snapshot_dir / "raw" / "connectivity_batches",
        "state_path": snapshot_dir / "state.json",
    }


def export_snapshot(
    *,
    request: SnapshotExportRequest,
    output_root: Path = DEFAULT_SNAPSHOT_ROOT,
    flywire_client: object | None = None,
    seed_root_id: int | None = None,
) -> SnapshotExportResult:
    if request.mode == "dry-run":
        return export_snapshot_dry_run(
            request=request,
            output_root=output_root,
            flywire_client=flywire_client,
            seed_root_id=seed_root_id,
        )
    if request.mode == "full":
        return export_snapshot_full(
            request=request,
            output_root=output_root,
            flywire_client=flywire_client,
        )
    raise ValueError(f"Unsupported snapshot export mode: {request.mode}")


def resolve_seed_root_id(
    *,
    flywire_client: object | None = None,
    seed_root_id: int | None = None,
    coords: list[list[int]] | None = None,
) -> int:
    if seed_root_id is not None:
        return int(seed_root_id)

    client = flywire_client or require_fafbseg()
    roots = getattr(client, "locs_to_segments")(coords or DEFAULT_PUBLIC_COORDS)
    values = roots.tolist() if hasattr(roots, "tolist") else list(roots)
    for value in values:
        root_id = int(value)
        if root_id > 0:
            return root_id
    raise ValueError("Could not resolve a non-zero FlyWire root ID from the provided coordinates.")


def export_snapshot_dry_run(
    *,
    request: SnapshotExportRequest,
    output_root: Path = DEFAULT_SNAPSHOT_ROOT,
    flywire_client: object | None = None,
    seed_root_id: int | None = None,
) -> SnapshotExportResult:
    paths = build_snapshot_paths(request.snapshot_id, output_root=output_root)
    snapshot_dir = paths["snapshot_dir"]
    raw_dir = paths["raw_dir"]
    normalized_dir = paths["normalized_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    resolved_seed = resolve_seed_root_id(
        flywire_client=flywire_client,
        seed_root_id=seed_root_id or request.seed_root_id,
    )
    neighborhood = _get_neighborhood(
        flywire_client=flywire_client,
        dataset=request.dataset,
        seed_root_id=resolved_seed,
        max_hops=request.max_hops,
        max_nodes=request.max_nodes,
    )
    nodes = _list_records(neighborhood.get("nodes"))
    edges = _list_records(neighborhood.get("edges"))
    flow_labels = _list_records(neighborhood.get("flow_labels"))
    normalized_nodes = _normalize_nodes(
        nodes=nodes,
        flow_labels=flow_labels,
        dataset_version=request.dataset,
    )
    normalized_edges = _normalize_edges(edges)
    normalized_partitions = _normalize_partitions(
        nodes=normalized_nodes,
        flow_labels=flow_labels,
        partition_version=request.snapshot_id,
    )
    stats = _build_stats(
        nodes=normalized_nodes,
        edges=normalized_edges,
        partitions=normalized_partitions,
    )
    metadata = dict(neighborhood.get("metadata") or {})

    _write_manifest(
        snapshot_dir / "manifest.yaml",
        request=request,
        seed_root_id=resolved_seed,
        node_count=len(nodes),
        edge_count=len(edges),
        flow_label_source=str(metadata.get("flow_label_source", "provided")),
    )
    _write_parquet(raw_dir / "nodes.parquet", nodes)
    _write_parquet(raw_dir / "edges.parquet", edges)
    _write_parquet(raw_dir / "flow_labels.parquet", flow_labels)
    _write_parquet(
        normalized_dir / "nodes.parquet",
        normalized_nodes,
        columns=NORMALIZED_NODE_COLUMNS,
    )
    _write_parquet(
        normalized_dir / "edges.parquet",
        normalized_edges,
        columns=NORMALIZED_EDGE_COLUMNS,
    )
    _write_parquet(
        normalized_dir / "partitions.parquet",
        normalized_partitions,
        columns=NORMALIZED_PARTITION_COLUMNS,
    )
    _write_json(normalized_dir / "stats.json", stats)

    return SnapshotExportResult(
        snapshot_dir=snapshot_dir,
        seed_root_id=resolved_seed,
        node_count=len(nodes),
        edge_count=len(edges),
        status="ok",
    )


def export_snapshot_full(
    *,
    request: SnapshotExportRequest,
    output_root: Path = DEFAULT_SNAPSHOT_ROOT,
    flywire_client: object | None = None,
) -> SnapshotExportResult:
    paths = build_snapshot_paths(request.snapshot_id, output_root=output_root)
    snapshot_dir = paths["snapshot_dir"]
    raw_dir = paths["raw_dir"]
    normalized_dir = paths["normalized_dir"]
    connectivity_batch_dir = paths["connectivity_batch_dir"]
    state_path = paths["state_path"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    connectivity_batch_dir.mkdir(parents=True, exist_ok=True)

    client = flywire_client or require_fafbseg()
    if hasattr(client, "set_default_dataset"):
        _call_quietly(getattr(client, "set_default_dataset"), request.dataset)

    normalized_nodes, normalized_partitions, flow_labels = _load_or_initialize_full_metadata(
        request=request,
        snapshot_dir=snapshot_dir,
        raw_dir=raw_dir,
        normalized_dir=normalized_dir,
        flywire_client=client,
    )

    root_ids = [int(node["source_id"]) for node in normalized_nodes]
    total_batches = max(1, (len(root_ids) + request.batch_size - 1) // request.batch_size)
    state = _load_export_state(
        state_path,
        total_batches=total_batches,
        resume=request.resume,
    )
    completed_batches = int(state.get("completed_batches", 0))

    for batch_index, root_batch in enumerate(_batched(root_ids, request.batch_size)):
        if batch_index < completed_batches:
            continue
        connectivity = _get_connectivity_with_retry(
            flywire_client=client,
            root_batch=root_batch,
            dataset=request.dataset,
        )
        edges = _normalize_connectivity_records(_list_records(connectivity))
        _write_batch_jsonl(connectivity_batch_dir / f"batch_{batch_index:05d}.jsonl", edges)
        _write_export_state(
            state_path,
            {
                "status": "running",
                "mode": request.mode,
                "completed_batches": batch_index + 1,
                "total_batches": total_batches,
            },
        )

    normalized_edges = _aggregate_batch_edges(
        connectivity_batch_dir=connectivity_batch_dir,
        valid_node_ids={int(node["source_id"]) for node in normalized_nodes},
    )
    stats = _build_stats(
        nodes=normalized_nodes,
        edges=normalized_edges,
        partitions=normalized_partitions,
    )
    _write_manifest(
        snapshot_dir / "manifest.yaml",
        request=request,
        seed_root_id=0,
        node_count=len(normalized_nodes),
        edge_count=len(normalized_edges),
        flow_label_source="annotation_table",
    )
    _write_parquet(raw_dir / "nodes.parquet", normalized_nodes)
    _write_parquet(raw_dir / "edges.parquet", normalized_edges)
    _write_parquet(raw_dir / "flow_labels.parquet", flow_labels)
    _write_parquet(
        normalized_dir / "nodes.parquet",
        normalized_nodes,
        columns=NORMALIZED_NODE_COLUMNS,
    )
    _write_parquet(
        normalized_dir / "edges.parquet",
        normalized_edges,
        columns=NORMALIZED_EDGE_COLUMNS,
    )
    _write_parquet(
        normalized_dir / "partitions.parquet",
        normalized_partitions,
        columns=NORMALIZED_PARTITION_COLUMNS,
    )
    _write_json(normalized_dir / "stats.json", stats)
    _write_export_state(
        state_path,
        {
            "status": "complete",
            "mode": request.mode,
            "completed_batches": total_batches,
            "total_batches": total_batches,
        },
    )
    return SnapshotExportResult(
        snapshot_dir=snapshot_dir,
        seed_root_id=0,
        node_count=len(normalized_nodes),
        edge_count=len(normalized_edges),
        status="ok",
    )


def _get_neighborhood(
    *,
    flywire_client: object | None,
    dataset: str,
    seed_root_id: int,
    max_hops: int,
    max_nodes: int,
) -> dict[str, Any]:
    client = flywire_client or require_fafbseg()
    if hasattr(client, "set_default_dataset"):
        _call_quietly(getattr(client, "set_default_dataset"), dataset)
    if not hasattr(client, "get_neighborhood"):
        if hasattr(client, "get_connectivity"):
            return _build_neighborhood_from_connectivity(
                flywire_client=client,
                dataset=dataset,
                seed_root_id=seed_root_id,
                max_hops=max_hops,
                max_nodes=max_nodes,
            )
        raise RuntimeError(
            "FlyWire dry-run export currently requires a provider with get_neighborhood(...) or get_connectivity(...)."
        )
    return _call_quietly(getattr(client, "get_neighborhood"), seed_root_id, max_hops, max_nodes)


def _load_or_initialize_full_metadata(
    *,
    request: SnapshotExportRequest,
    snapshot_dir: Path,
    raw_dir: Path,
    normalized_dir: Path,
    flywire_client: object,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_path = normalized_dir / "nodes.parquet"
    partitions_path = normalized_dir / "partitions.parquet"
    flow_labels_path = raw_dir / "flow_labels.parquet"
    raw_nodes_path = raw_dir / "nodes.parquet"

    if request.resume and nodes_path.exists() and partitions_path.exists():
        normalized_nodes = _read_parquet_records(nodes_path)
        normalized_partitions = _read_parquet_records(partitions_path)
        if flow_labels_path.exists():
            flow_labels = _read_parquet_records(flow_labels_path)
        else:
            flow_labels = [
                {"source_id": int(node["source_id"]), "flow_role": str(node["flow_role"])}
                for node in normalized_nodes
            ]
        return normalized_nodes, normalized_partitions, flow_labels

    annotations = _load_full_annotations(
        flywire_client=flywire_client,
        dataset=request.dataset,
    )
    if not annotations:
        raise RuntimeError("Full snapshot export returned no annotations.")
    normalized_nodes = _normalize_annotation_nodes(annotations, dataset_version=request.dataset)
    normalized_partitions = _normalize_annotation_partitions(
        annotations,
        partition_version=request.snapshot_id,
    )
    flow_labels = [
        {"source_id": int(node["source_id"]), "flow_role": str(node["flow_role"])}
        for node in normalized_nodes
    ]
    _write_parquet(raw_nodes_path, normalized_nodes)
    _write_parquet(flow_labels_path, flow_labels)
    _write_parquet(
        nodes_path,
        normalized_nodes,
        columns=NORMALIZED_NODE_COLUMNS,
    )
    _write_parquet(
        partitions_path,
        normalized_partitions,
        columns=NORMALIZED_PARTITION_COLUMNS,
    )
    return normalized_nodes, normalized_partitions, flow_labels


def _read_parquet_records(path: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return _list_records(pq.read_table(path))


def _get_connectivity_with_retry(
    *,
    flywire_client: object,
    root_batch: list[int],
    dataset: str,
    attempts: int = 5,
    initial_delay_seconds: float = 2.0,
) -> Any:
    delay = initial_delay_seconds
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _call_quietly(
                getattr(flywire_client, "get_connectivity"),
                root_batch,
                upstream=True,
                downstream=True,
                progress=False,
                dataset=dataset,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= attempts or not _is_retryable_connectivity_error(exc):
                raise
            time.sleep(delay)
            delay *= 2
    if last_error is not None:
        raise last_error
    raise RuntimeError("Connectivity retry loop exited unexpectedly.")


def _is_retryable_connectivity_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retry_markers = (
        "503",
        "service temporarily unavailable",
        "timeout",
        "connection reset",
        "connection aborted",
        "temporarily unavailable",
    )
    return any(marker in message for marker in retry_markers)


def _load_full_annotations(
    *,
    flywire_client: object,
    dataset: str,
) -> list[dict[str, Any]]:
    if not hasattr(flywire_client, "search_annotations"):
        raise RuntimeError("FlyWire full export requires search_annotations(...).")
    annotations = _call_quietly(
        getattr(flywire_client, "search_annotations"),
        None,
        materialization="latest",
        verbose=False,
        regex=False,
        dataset=dataset,
    )
    records = _list_records(annotations)
    normalized: list[dict[str, Any]] = []
    for record in records:
        if "root_id" not in record:
            continue
        normalized.append(
            {
                "source_id": int(record["root_id"]),
                "flow_role": str(record.get("flow") or "intrinsic"),
                "hemisphere": str(record.get("side") or record.get("hemisphere") or "unknown"),
            }
        )
    return normalized


def _normalize_annotation_nodes(
    annotations: list[dict[str, Any]],
    *,
    dataset_version: str,
) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(record["source_id"]),
            "dataset_version": dataset_version,
            "hemisphere": str(record.get("hemisphere") or "unknown"),
            "flow_role": str(record.get("flow_role") or "intrinsic"),
            "is_active": True,
        }
        for record in annotations
    ]


def _normalize_annotation_partitions(
    annotations: list[dict[str, Any]],
    *,
    partition_version: str,
) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(record["source_id"]),
            "flow_role": str(record.get("flow_role") or "intrinsic"),
            "partition_version": partition_version,
        }
        for record in annotations
    ]


def _normalize_connectivity_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        pre_id = record.get("pre_id", record.get("pre"))
        post_id = record.get("post_id", record.get("post"))
        if pre_id is None or post_id is None:
            continue
        normalized.append(
            {
                "pre_id": int(pre_id),
                "post_id": int(post_id),
                "synapse_count": int(record.get("synapse_count", record.get("weight", 1))),
                "is_directed": bool(record.get("is_directed", True)),
                "is_active": bool(record.get("is_active", True)),
            }
        )
    return normalized


def _batched(values: list[int], batch_size: int) -> list[list[int]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def _load_export_state(path: Path, *, total_batches: int, resume: bool) -> dict[str, Any]:
    if resume and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"status": "pending", "completed_batches": 0, "total_batches": total_batches}


def _write_export_state(path: Path, payload: dict[str, Any]) -> None:
    _write_json(path, payload)


def _write_batch_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _aggregate_batch_edges(
    *,
    connectivity_batch_dir: Path,
    valid_node_ids: set[int],
) -> list[dict[str, Any]]:
    edge_weights: dict[tuple[int, int], int] = {}
    for batch_file in sorted(connectivity_batch_dir.glob("batch_*.jsonl")):
        for line in batch_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            pre_id = int(record["pre_id"])
            post_id = int(record["post_id"])
            if pre_id not in valid_node_ids or post_id not in valid_node_ids:
                continue
            key = (pre_id, post_id)
            edge_weights[key] = edge_weights.get(key, 0) + int(record.get("synapse_count", 1))
    return [
        {
            "pre_id": pre_id,
            "post_id": post_id,
            "synapse_count": weight,
            "is_directed": True,
            "is_active": True,
        }
        for (pre_id, post_id), weight in sorted(edge_weights.items())
    ]


def _write_manifest(
    path: Path,
    *,
    request: SnapshotExportRequest,
    seed_root_id: int,
    node_count: int,
    edge_count: int,
    flow_label_source: str,
) -> None:
    payload = {
        "snapshot_id": request.snapshot_id,
        "dataset": request.dataset,
        "seed_strategy": request.seed_strategy,
        "seed_root_id": seed_root_id,
        "max_hops": request.max_hops,
        "max_nodes": request.max_nodes,
        "node_count": node_count,
        "edge_count": edge_count,
        "flow_label_source": flow_label_source,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_parquet(
    path: Path,
    records: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if columns is None:
        table = pa.Table.from_pylist(records)
    else:
        column_data = {
            column: [record.get(column) for record in records]
            for column in columns
        }
        table = pa.table(column_data)
    pq.write_table(table, path)


def _list_records(records: Any) -> list[dict[str, Any]]:
    if records is None:
        return []
    if isinstance(records, list):
        return [dict(item) for item in records]
    if isinstance(records, Sequence):
        return [dict(item) for item in list(records)]
    if hasattr(records, "to_dict"):
        return [dict(item) for item in records.to_dict(orient="records")]
    if hasattr(records, "to_pylist"):
        return [dict(item) for item in records.to_pylist()]
    raise TypeError("Unsupported record collection type for snapshot export.")


def _normalize_nodes(
    *,
    nodes: list[dict[str, Any]],
    flow_labels: list[dict[str, Any]],
    dataset_version: str,
) -> list[dict[str, Any]]:
    flow_by_id = {
        int(label["source_id"]): str(label["flow_role"])
        for label in flow_labels
        if "source_id" in label and "flow_role" in label
    }
    normalized = []
    for node in nodes:
        source_id = int(node["source_id"])
        normalized.append(
            {
                "source_id": source_id,
                "dataset_version": str(node.get("dataset_version") or dataset_version),
                "hemisphere": str(node.get("hemisphere") or "unknown"),
                "flow_role": str(node.get("flow_role") or flow_by_id.get(source_id, "intrinsic")),
                "is_active": bool(node.get("is_active", True)),
            }
        )
    return normalized


def _normalize_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for edge in edges:
        normalized.append(
            {
                "pre_id": int(edge["pre_id"]),
                "post_id": int(edge["post_id"]),
                "synapse_count": int(edge.get("synapse_count", 1)),
                "is_directed": bool(edge.get("is_directed", True)),
                "is_active": bool(edge.get("is_active", True)),
            }
        )
    return normalized


def _normalize_partitions(
    *,
    nodes: list[dict[str, Any]],
    flow_labels: list[dict[str, Any]],
    partition_version: str,
) -> list[dict[str, Any]]:
    flow_by_id = {
        int(label["source_id"]): str(label["flow_role"])
        for label in flow_labels
        if "source_id" in label and "flow_role" in label
    }
    partitions = []
    for node in nodes:
        source_id = int(node["source_id"])
        partitions.append(
            {
                "source_id": source_id,
                "flow_role": str(flow_by_id.get(source_id, node["flow_role"])),
                "partition_version": partition_version,
            }
        )
    return partitions


def _build_stats(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
) -> dict[str, Any]:
    flow_counts = {"afferent": 0, "intrinsic": 0, "efferent": 0}
    active_nodes = 0
    active_edges = 0
    for node in nodes:
        if bool(node["is_active"]):
            active_nodes += 1
        flow_role = str(node["flow_role"])
        if flow_role in flow_counts:
            flow_counts[flow_role] += 1
    for edge in edges:
        if bool(edge["is_active"]):
            active_edges += 1
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "active_node_count": active_nodes,
        "active_edge_count": active_edges,
        "partition_count": len(partitions),
        "flow_role_counts": flow_counts,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_neighborhood_from_connectivity(
    *,
    flywire_client: object,
    dataset: str,
    seed_root_id: int,
    max_hops: int,
    max_nodes: int,
) -> dict[str, Any]:
    visited = [int(seed_root_id)]
    visited_set = {int(seed_root_id)}
    frontier = [int(seed_root_id)]
    edge_weights: dict[tuple[int, int], int] = {}

    for _ in range(max_hops):
        if not frontier or len(visited) >= max_nodes:
            break
        connectivity = _call_quietly(
            getattr(flywire_client, "get_connectivity"),
            frontier,
            upstream=True,
            downstream=True,
            progress=False,
            dataset=dataset,
        )
        records = _list_records(connectivity)
        candidate_ids: set[int] = set()
        for record in records:
            pre_id = int(record["pre"])
            post_id = int(record["post"])
            weight = int(record.get("weight", 1))
            edge_weights[(pre_id, post_id)] = edge_weights.get((pre_id, post_id), 0) + weight
            candidate_ids.add(pre_id)
            candidate_ids.add(post_id)

        remaining_budget = max_nodes - len(visited)
        if remaining_budget <= 0:
            break
        next_frontier = sorted(candidate_ids - visited_set)[:remaining_budget]
        visited.extend(next_frontier)
        visited_set.update(next_frontier)
        frontier = next_frontier

    edges = [
        {
            "pre_id": pre_id,
            "post_id": post_id,
            "synapse_count": weight,
            "is_directed": True,
            "is_active": True,
        }
        for (pre_id, post_id), weight in sorted(edge_weights.items())
        if pre_id in visited_set and post_id in visited_set
    ]
    flow_labels = _infer_flow_labels(node_ids=visited, edges=edges)
    flow_map = {item["source_id"]: item["flow_role"] for item in flow_labels}
    nodes = [
        {
            "source_id": source_id,
            "dataset_version": dataset,
            "hemisphere": "unknown",
            "flow_role": flow_map[source_id],
            "is_active": True,
        }
        for source_id in visited
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "flow_labels": flow_labels,
        "metadata": {"flow_label_source": "local_degree_heuristic"},
    }


def _infer_flow_labels(
    *,
    node_ids: list[int],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    indegree = {source_id: 0 for source_id in node_ids}
    outdegree = {source_id: 0 for source_id in node_ids}
    for edge in edges:
        pre_id = int(edge["pre_id"])
        post_id = int(edge["post_id"])
        if pre_id in outdegree:
            outdegree[pre_id] += 1
        if post_id in indegree:
            indegree[post_id] += 1

    labels = []
    for source_id in node_ids:
        if indegree[source_id] == 0 and outdegree[source_id] > 0:
            flow_role = "afferent"
        elif outdegree[source_id] == 0 and indegree[source_id] > 0:
            flow_role = "efferent"
        else:
            flow_role = "intrinsic"
        labels.append({"source_id": source_id, "flow_role": flow_role})
    return labels


def load_normalized_snapshot(snapshot_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import pyarrow.parquet as pq

    normalized_dir = snapshot_dir / "normalized"
    nodes = _list_records(pq.read_table(normalized_dir / "nodes.parquet"))
    edges = _list_records(pq.read_table(normalized_dir / "edges.parquet"))
    return nodes, edges


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a FlyWire snapshot.")
    parser.add_argument("--snapshot-id", required=True, help="Snapshot directory name")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_SNAPSHOT_ROOT, help="Snapshot output root")
    parser.add_argument("--dataset", default="public", help="FlyWire dataset name")
    parser.add_argument("--mode", choices=("dry-run", "full"), default="dry-run", help="Snapshot export mode")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted full export")
    parser.add_argument("--seed-root-id", type=int, default=None, help="Optional explicit seed root ID")
    parser.add_argument("--max-hops", type=int, default=2, help="Neighborhood hop limit")
    parser.add_argument("--max-nodes", type=int, default=5000, help="Neighborhood node budget")
    parser.add_argument("--batch-size", type=int, default=256, help="Connectivity query batch size for full export")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    result = export_snapshot(
        request=SnapshotExportRequest(
            snapshot_id=args.snapshot_id,
            dataset=args.dataset,
            mode=args.mode,
            resume=args.resume,
            seed_root_id=args.seed_root_id,
            max_hops=args.max_hops,
            max_nodes=args.max_nodes,
            batch_size=args.batch_size,
        ),
        output_root=args.output_root,
    )
    payload = {
        "status": result.status,
        "snapshot_dir": str(result.snapshot_dir),
        "seed_root_id": result.seed_root_id,
        "node_count": result.node_count,
        "edge_count": result.edge_count,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}={value}")
    return 0


def _call_quietly(func: Any, *args: Any, **kwargs: Any) -> Any:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return func(*args, **kwargs)


if __name__ == "__main__":
    sys.exit(main())
