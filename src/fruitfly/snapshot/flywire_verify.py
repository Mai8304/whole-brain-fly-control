from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from dataclasses import dataclass
from typing import Any


DEFAULT_PUBLIC_COORDS = [[75350, 60162, 3162]]


@dataclass(slots=True)
class FlyWireVerificationResult:
    status: str
    dataset: str
    materialization_count: int
    latest_materialization: int | None
    query_points: int
    resolved_roots: int
    error_type: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "dataset": self.dataset,
            "materialization_count": self.materialization_count,
            "latest_materialization": self.latest_materialization,
            "query_points": self.query_points,
            "resolved_roots": self.resolved_roots,
        }
        if self.error_type is not None:
            payload["error_type"] = self.error_type
        if self.message is not None:
            payload["message"] = self.message
        return payload


def require_fafbseg() -> object:
    try:
        from fafbseg import flywire
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "fafbseg is not installed. Install the flywire extras before running FlyWire verification."
        ) from exc
    return flywire


def verify_flywire_readonly(
    *,
    flywire_client: object | None = None,
    coords: list[list[int]] | None = None,
    dataset: str = "public",
) -> FlyWireVerificationResult:
    query_coords = coords or DEFAULT_PUBLIC_COORDS

    try:
        client = flywire_client or require_fafbseg()
        _call_quietly(getattr(client, "set_default_dataset"), dataset)
        materializations = _call_quietly(getattr(client, "get_materialization_versions"))
        roots = _call_quietly(getattr(client, "locs_to_segments"), query_coords)
    except RuntimeError as exc:
        return FlyWireVerificationResult(
            status="failed",
            dataset=dataset,
            materialization_count=0,
            latest_materialization=None,
            query_points=len(query_coords),
            resolved_roots=0,
            error_type="dependency_error",
            message=str(exc),
        )
    except Exception as exc:
        return FlyWireVerificationResult(
            status="failed",
            dataset=dataset,
            materialization_count=0,
            latest_materialization=None,
            query_points=len(query_coords),
            resolved_roots=0,
            error_type=_classify_error(exc),
            message=str(exc),
        )

    materialization_versions = _extract_versions(materializations)
    resolved_count = _count_resolved_roots(roots)
    if resolved_count == 0:
        return FlyWireVerificationResult(
            status="failed",
            dataset=dataset,
            materialization_count=len(materialization_versions),
            latest_materialization=max(materialization_versions) if materialization_versions else None,
            query_points=len(query_coords),
            resolved_roots=0,
            error_type="empty_result",
            message="FlyWire returned no resolved root IDs for the provided coordinates.",
        )

    return FlyWireVerificationResult(
        status="ok",
        dataset=dataset,
        materialization_count=len(materialization_versions),
        latest_materialization=max(materialization_versions) if materialization_versions else None,
        query_points=len(query_coords),
        resolved_roots=resolved_count,
    )


def _extract_versions(materializations: Any) -> list[int]:
    if isinstance(materializations, list):
        return [int(item) for item in materializations]
    if isinstance(materializations, tuple):
        return [int(item) for item in materializations]
    if hasattr(materializations, "columns") and "version" in getattr(materializations, "columns"):
        versions = materializations["version"]
        return [int(item) for item in list(versions)]
    if hasattr(materializations, "tolist"):
        return [int(item) for item in materializations.tolist()]
    return []


def _count_resolved_roots(roots: Any) -> int:
    if hasattr(roots, "tolist"):
        values = roots.tolist()
    else:
        values = list(roots)
    return sum(1 for value in values if int(value) > 0)


def _classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "401" in message or "403" in message or "unauthorized" in message or "forbidden" in message:
        return "auth_error"
    if "timeout" in message or "connection" in message or "network" in message:
        return "network_error"
    return "query_error"


def _call_quietly(func: Any, *args: Any, **kwargs: Any) -> Any:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return func(*args, **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify read-only FlyWire access against the public dataset.")
    parser.add_argument("--dataset", default="public", help="FlyWire dataset name")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    result = verify_flywire_readonly(dataset=args.dataset)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for key, value in result.to_dict().items():
            print(f"{key}={value}")
    return _exit_code_for_result(result)


def _exit_code_for_result(result: FlyWireVerificationResult) -> int:
    if result.status == "ok":
        return 0
    if result.error_type == "dependency_error":
        return 1
    if result.error_type == "auth_error":
        return 2
    if result.error_type == "network_error":
        return 3
    if result.error_type == "empty_result":
        return 4
    return 5


if __name__ == "__main__":
    sys.exit(main())
