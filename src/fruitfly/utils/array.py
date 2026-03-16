from __future__ import annotations


class Array1D(list[float]):
    @property
    def shape(self) -> tuple[int]:
        return (len(self),)
