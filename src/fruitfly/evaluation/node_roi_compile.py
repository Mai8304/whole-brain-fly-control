from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .roi_manifest import build_v1_roi_manifest

V1_TARGET_NEUROPILS = (
    "AL_L",
    "AL_R",
    "LH_L",
    "LH_R",
    "PB",
    "FB",
    "EB",
    "NO",
    "LAL_L",
    "LAL_R",
    "GNG",
)

V1_NEUROPIL_TO_ROI = {
    "AL_L": "AL",
    "AL_R": "AL",
    "LH_L": "LH",
    "LH_R": "LH",
    "PB": "PB",
    "FB": "FB",
    "EB": "EB",
    "NO": "NO",
    "LAL_L": "LAL",
    "LAL_R": "LAL",
    "GNG": "GNG",
}

V1_ROI_QUERY_GROUPS = {
    "AL": ("AL_L", "AL_R"),
    "LH": ("LH_L", "LH_R"),
    "PB": ("PB",),
    "FB": ("FB",),
    "EB": ("EB",),
    "NO": ("NO",),
    "LAL": ("LAL_L", "LAL_R"),
    "GNG": ("GNG",),
}


def build_v1_neuropil_to_roi_map() -> dict[str, str]:
    return dict(V1_NEUROPIL_TO_ROI)


def build_v1_roi_query_groups() -> dict[str, tuple[str, ...]]:
    return {roi_id: tuple(neuropils) for roi_id, neuropils in V1_ROI_QUERY_GROUPS.items()}


def compile_node_roi_map_rows(
    *,
    node_index_rows: list[dict[str, Any]],
    synapse_count_fetcher: Callable[..., Any] | None = None,
    batch_size: int = 64,
    dataset: str = "public",
    materialization: str | int = "latest",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if synapse_count_fetcher is None:
        from fafbseg import flywire

        synapse_count_fetcher = flywire.get_synapse_counts

    manifest = build_v1_roi_manifest()
    roi_priority = {str(entry["roi_id"]): int(entry["priority"]) for entry in manifest}
    node_idx_by_source_id = {int(row["source_id"]): int(row["node_idx"]) for row in node_index_rows}
    source_ids = list(node_idx_by_source_id)

    compiled_rows: list[dict[str, Any]] = []
    roi_counts = {str(entry["roi_id"]): 0 for entry in manifest}

    for root_batch in _batched(source_ids, batch_size):
        batch_rows, batch_summary = compile_node_roi_map_batch_rows(
            node_index_rows=[{"source_id": source_id, "node_idx": node_idx_by_source_id[source_id]} for source_id in root_batch],
            synapse_count_fetcher=synapse_count_fetcher,
            dataset=dataset,
            materialization=materialization,
        )
        compiled_rows.extend(batch_rows)
        for roi_id, count in batch_summary["roi_counts"].items():
            roi_counts[roi_id] += int(count)

    mapped_nodes = sum(1 for row in compiled_rows if row["roi_id"] is not None)
    summary = {
        "total_nodes": len(source_ids),
        "mapped_nodes": mapped_nodes,
        "mapping_coverage": (mapped_nodes / len(source_ids)) if source_ids else 0.0,
        "roi_counts": roi_counts,
        "target_neuropils": list(V1_TARGET_NEUROPILS),
        "target_rois": list(build_v1_roi_query_groups()),
        "materialization": materialization,
        "dataset": dataset,
        "mapping_source": "fafbseg.flywire.get_synapse_counts(by_neuropil=True)",
    }
    return compiled_rows, summary


def compile_node_roi_map_batch_rows(
    *,
    node_index_rows: list[dict[str, Any]],
    synapse_count_fetcher: Callable[..., Any] | None = None,
    dataset: str = "public",
    materialization: str | int = "latest",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if synapse_count_fetcher is None:
        from fafbseg import flywire

        synapse_count_fetcher = flywire.get_synapse_counts

    manifest = build_v1_roi_manifest()
    roi_priority = {str(entry["roi_id"]): int(entry["priority"]) for entry in manifest}
    node_idx_by_source_id = {int(row["source_id"]): int(row["node_idx"]) for row in node_index_rows}
    query_ids = set(node_idx_by_source_id)
    weights_by_root = _accumulate_synapse_count_weights(
        synapse_count_fetcher=synapse_count_fetcher,
        query_ids=query_ids,
        roi_priority=roi_priority,
        dataset=dataset,
        materialization=materialization,
    )

    roi_counts = {str(entry["roi_id"]): 0 for entry in manifest}
    compiled_rows: list[dict[str, Any]] = []
    for source_id in sorted(query_ids, key=lambda value: node_idx_by_source_id[int(value)]):
        roi_weights = weights_by_root.get(int(source_id))
        roi_id = _select_dominant_roi(roi_weights=roi_weights, roi_priority=roi_priority)
        compiled_rows.append(
            {
                "source_id": int(source_id),
                "node_idx": int(node_idx_by_source_id[int(source_id)]),
                "roi_id": roi_id,
            }
        )
        if roi_id is not None:
            roi_counts[roi_id] += 1

    mapped_nodes = sum(1 for row in compiled_rows if row["roi_id"] is not None)
    summary = {
        "total_nodes": len(query_ids),
        "mapped_nodes": mapped_nodes,
        "mapping_coverage": (mapped_nodes / len(query_ids)) if query_ids else 0.0,
        "roi_counts": roi_counts,
        "target_neuropils": list(V1_TARGET_NEUROPILS),
        "target_rois": list(build_v1_roi_query_groups()),
        "materialization": materialization,
        "dataset": dataset,
        "mapping_source": "fafbseg.flywire.get_synapse_counts(by_neuropil=True)",
    }
    return compiled_rows, summary


def write_node_roi_map(path: Path, rows: list[dict[str, Any]]) -> None:
    table = pa.table(
        {
            "source_id": [int(row["source_id"]) for row in rows],
            "node_idx": [int(row["node_idx"]) for row in rows],
            "roi_id": [None if row["roi_id"] is None else str(row["roi_id"]) for row in rows],
        },
        schema=pa.schema(
            [
                pa.field("source_id", pa.int64(), nullable=False),
                pa.field("node_idx", pa.int64(), nullable=False),
                pa.field("roi_id", pa.string(), nullable=True),
            ]
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _accumulate_synapse_count_weights(
    *,
    synapse_count_fetcher: Callable[..., Any],
    query_ids: set[int],
    roi_priority: dict[str, int],
    dataset: str,
    materialization: str | int,
) -> dict[int, dict[str, int]]:
    weights_by_root: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    synapse_counts = synapse_count_fetcher(
        list(query_ids),
        by_neuropil=True,
        filtered=True,
        materialization=materialization,
        dataset=dataset,
        progress=False,
        batch_size=max(1, len(query_ids)),
    )
    for row in _coerce_synapse_count_rows(synapse_counts):
        source_id = int(row["id"])
        if source_id not in query_ids:
            continue
        roi_id = V1_NEUROPIL_TO_ROI.get(str(row["neuropil"]))
        if roi_id is None:
            continue
        weight = int(row.get("pre") or 0) + int(row.get("post") or 0)
        if weight <= 0:
            continue
        weights_by_root[source_id][roi_id] += weight

    # Materialize plain dicts for deterministic downstream behavior.
    return {
        int(source_id): {
            roi_id: int(weight)
            for roi_id, weight in sorted(
                roi_weights.items(),
                key=lambda item: (-item[1], roi_priority.get(item[0], 999), item[0]),
            )
        }
        for source_id, roi_weights in weights_by_root.items()
    }


def _select_dominant_roi(
    *,
    roi_weights: dict[str, int] | None,
    roi_priority: dict[str, int],
) -> str | None:
    if not roi_weights:
        return None

    ranked = sorted(
        roi_weights.items(),
        key=lambda item: (-item[1], roi_priority.get(item[0], 999), item[0]),
    )
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def _coerce_synapse_count_rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if hasattr(value, "reset_index") and hasattr(value, "to_dict"):
        return list(value.reset_index().to_dict(orient="records"))
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, Iterable):
        return [dict(item) for item in value]
    raise TypeError(f"unsupported synapse-count payload: {type(value)!r}")


def _batched(values: list[int], batch_size: int) -> Iterable[list[int]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for index in range(0, len(values), batch_size):
        yield values[index : index + batch_size]
