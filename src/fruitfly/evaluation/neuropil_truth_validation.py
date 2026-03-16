from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def validate_node_neuropil_occupancy(
    *,
    occupancy_rows: Iterable[dict[str, Any]],
    official_pre_rows: Iterable[dict[str, Any]],
    official_post_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    derived_pre = _derived_counts_by_key(occupancy_rows, count_field="pre_count")
    derived_post = _derived_counts_by_key(occupancy_rows, count_field="post_count")
    official_pre = _official_counts_by_key(official_pre_rows)
    official_post = _official_counts_by_key(official_post_rows)

    pre_mismatches = _build_mismatches(direction="pre", expected=official_pre, actual=derived_pre)
    post_mismatches = _build_mismatches(direction="post", expected=official_post, actual=derived_post)
    mismatches = pre_mismatches + post_mismatches

    return {
        "validation_passed": not mismatches,
        "pre_mismatch_count": len(pre_mismatches),
        "post_mismatch_count": len(post_mismatches),
        "example_mismatches": mismatches[:10],
    }


def _derived_counts_by_key(rows: Iterable[dict[str, Any]], *, count_field: str) -> dict[tuple[int, str], int]:
    counts: dict[tuple[int, str], int] = {}
    for row in rows:
        key = (int(row["source_id"]), str(row["neuropil"]))
        counts[key] = int(row[count_field])
    return counts


def _official_counts_by_key(rows: Iterable[dict[str, Any]]) -> dict[tuple[int, str], int]:
    counts: dict[tuple[int, str], int] = {}
    for row in rows:
        key = (int(row["root_id"]), str(row["neuropil"]))
        counts[key] = int(row["count"])
    return counts


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
