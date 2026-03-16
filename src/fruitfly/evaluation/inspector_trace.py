from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ReplayTracePayload:
    session: dict[str, Any]
    state_arrays: dict[str, np.ndarray]
    neural_arrays: dict[str, np.ndarray]
    events: list[dict[str, Any]]


def dump_replay_trace(
    *,
    output_dir: Path,
    session: dict[str, Any],
    state_arrays: dict[str, np.ndarray],
    neural_arrays: dict[str, np.ndarray],
    events: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "session.json").write_text(
        json.dumps(session, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    np.savez_compressed(output_dir / "state_traces.npz", **state_arrays)
    np.savez_compressed(output_dir / "neural_traces.npz", **neural_arrays)

    events_path = output_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")


def load_replay_trace(output_dir: Path) -> ReplayTracePayload:
    session = json.loads((output_dir / "session.json").read_text(encoding="utf-8"))
    state_arrays = _load_npz(output_dir / "state_traces.npz")
    neural_arrays = _load_npz(output_dir / "neural_traces.npz")
    events = [
        json.loads(line)
        for line in (output_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return ReplayTracePayload(
        session=session,
        state_arrays=state_arrays,
        neural_arrays=neural_arrays,
        events=events,
    )


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        return {str(key): payload[key] for key in payload.files}
