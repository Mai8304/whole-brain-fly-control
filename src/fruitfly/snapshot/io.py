from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Manifest must deserialize to a mapping: {manifest_path}")
    return data
