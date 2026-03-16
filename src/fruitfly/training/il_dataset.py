from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fruitfly.utils import Array1D


def write_il_dataset(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


class ILDataset:
    def __init__(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as handle:
            self._records = [json.loads(line) for line in handle if line.strip()]

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, index: int) -> dict[str, Array1D]:
        record = self._records[index]
        sample: dict[str, Any] = {
            "observation": Array1D(float(value) for value in record["observation"]),
            "command": Array1D(float(value) for value in record["command"]),
            "expert_mean": Array1D(float(value) for value in record["expert_mean"]),
            "expert_log_std": Array1D(float(value) for value in record["expert_log_std"]),
        }
        if "episode_id" in record:
            sample["episode_id"] = int(record["episode_id"])
        if "step_id" in record:
            sample["step_id"] = int(record["step_id"])
        if "task" in record:
            sample["task"] = str(record["task"])
        return sample
