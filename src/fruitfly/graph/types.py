from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CompiledGraph:
    node_index: dict[int, int]
    edge_index: list[tuple[int, int]]
    afferent_mask: list[bool]
    intrinsic_mask: list[bool]
    efferent_mask: list[bool]
    manifest: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    graph_stats: dict[str, Any] | None = None
