from __future__ import annotations

from collections.abc import Collection, Iterable
from typing import Any


def validate_node_neuropil_occupancy(
    *,
    occupancy_rows: Iterable[dict[str, Any]],
    official_pre_rows: Iterable[dict[str, Any]],
    official_post_rows: Iterable[dict[str, Any]],
    graph_source_ids: Collection[int] | None = None,
    proofread_root_ids: Collection[int] | None = None,
) -> dict[str, Any]:
    graph_source_id_set = _normalize_source_id_set(graph_source_ids)
    proofread_root_id_set = _normalize_source_id_set(proofread_root_ids)
    derived_pre, derived_post, occupancy_source_ids = _derived_counts_by_key(
        occupancy_rows,
        allowed_root_ids=graph_source_id_set,
    )
    official_pre, official_pre_root_ids = _official_counts_by_key(
        official_pre_rows,
        preferred_root_id_field="pre_pt_root_id",
        allowed_root_ids=graph_source_id_set,
    )
    official_post, official_post_root_ids = _official_counts_by_key(
        official_post_rows,
        preferred_root_id_field="post_pt_root_id",
        allowed_root_ids=graph_source_id_set,
    )

    pre_mismatches = _build_mismatches(direction="pre", expected=official_pre, actual=derived_pre)
    post_mismatches = _build_mismatches(direction="post", expected=official_post, actual=derived_post)
    mismatches = pre_mismatches + post_mismatches
    effective_graph_source_ids = graph_source_id_set or occupancy_source_ids

    return {
        "validation_passed": not mismatches,
        "graph_scope_validation_passed": not mismatches,
        "validation_scope": "graph_source_ids" if graph_source_id_set is not None else "occupancy_rows",
        "pre_mismatch_count": len(pre_mismatches),
        "post_mismatch_count": len(post_mismatches),
        "example_mismatches": mismatches[:10],
        "scope": {
            "graph_node_count": len(effective_graph_source_ids),
            "occupancy_node_count": len(occupancy_source_ids),
            "official_pre_graph_overlap_count": len(official_pre_root_ids),
            "official_post_graph_overlap_count": len(official_post_root_ids),
        },
        "roster_alignment": _build_roster_alignment(
            graph_source_ids=effective_graph_source_ids,
            proofread_root_ids=proofread_root_id_set,
        ),
    }


def _derived_counts_by_key(
    rows: Iterable[dict[str, Any]],
    *,
    allowed_root_ids: set[int] | None,
) -> tuple[dict[tuple[int, str], int], dict[tuple[int, str], int], set[int]]:
    pre_counts: dict[tuple[int, str], int] = {}
    post_counts: dict[tuple[int, str], int] = {}
    source_ids: set[int] = set()
    for row in rows:
        source_id = int(row["source_id"])
        if allowed_root_ids is not None and source_id not in allowed_root_ids:
            continue
        source_ids.add(source_id)
        key = (source_id, str(row["neuropil"]))
        pre_counts[key] = int(row["pre_count"])
        post_counts[key] = int(row["post_count"])
    return pre_counts, post_counts, source_ids


def _official_counts_by_key(
    rows: Iterable[dict[str, Any]],
    *,
    preferred_root_id_field: str,
    allowed_root_ids: set[int] | None,
) -> tuple[dict[tuple[int, str], int], set[int]]:
    counts: dict[tuple[int, str], int] = {}
    root_ids: set[int] = set()
    for row in rows:
        root_id_field = preferred_root_id_field if preferred_root_id_field in row else "root_id"
        root_id = int(row[root_id_field])
        if allowed_root_ids is not None and root_id not in allowed_root_ids:
            continue
        root_ids.add(root_id)
        key = (root_id, str(row["neuropil"]))
        counts[key] = int(row["count"])
    return counts, root_ids


def _build_mismatches(
    *,
    direction: str,
    expected: dict[tuple[int, str], int],
    actual: dict[tuple[int, str], int],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for key in sorted(set(expected) | set(actual)):
        expected_count = expected.get(key, 0)
        actual_count = actual.get(key, 0)
        if expected_count == actual_count:
            continue
        root_id, neuropil = key
        mismatches.append(
            {
                "direction": direction,
                "root_id": root_id,
                "neuropil": neuropil,
                "expected_count": expected_count,
                "actual_count": actual_count,
            }
        )
    return mismatches


def _build_roster_alignment(
    *,
    graph_source_ids: set[int],
    proofread_root_ids: set[int] | None,
) -> dict[str, Any]:
    if proofread_root_ids is None:
        return {
            "proofread_root_count": None,
            "graph_in_proofread_count": None,
            "graph_only_root_count": None,
            "proofread_only_root_count": None,
            "alignment_passed": None,
            "example_graph_only_roots": [],
            "example_proofread_only_roots": [],
        }

    graph_only = sorted(graph_source_ids - proofread_root_ids)
    proofread_only = sorted(proofread_root_ids - graph_source_ids)
    return {
        "proofread_root_count": len(proofread_root_ids),
        "graph_in_proofread_count": len(graph_source_ids & proofread_root_ids),
        "graph_only_root_count": len(graph_only),
        "proofread_only_root_count": len(proofread_only),
        "alignment_passed": not graph_only and not proofread_only,
        "example_graph_only_roots": graph_only[:10],
        "example_proofread_only_roots": proofread_only[:10],
    }


def _normalize_source_id_set(values: Collection[int] | None) -> set[int] | None:
    if values is None:
        return None
    return {int(value) for value in values}
