from __future__ import annotations

from collections.abc import Mapping, Sequence

from fruitfly.utils import Array1D


SECTION_ORDER = ("proprio", "mechanosensation", "vision", "command")


def adapt_observation(observation: Mapping[str, Sequence[float]]) -> Array1D:
    flattened: list[float] = []
    for key in SECTION_ORDER:
        flattened.extend(float(value) for value in observation.get(key, []))
    return Array1D(flattened)
