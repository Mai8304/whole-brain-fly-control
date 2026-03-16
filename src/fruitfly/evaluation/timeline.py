from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_shared_timeline_payload(
    *,
    steps_requested: int,
    steps_completed: int,
    current_step: int,
    events: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "steps_requested": int(steps_requested),
        "steps_completed": int(steps_completed),
        "current_step": int(current_step),
        "brain_view_ref": "step_id",
        "body_view_ref": "step_id",
        "events": [
            {
                "step_id": int(event["step_id"]),
                "event_type": str(event["event_type"]),
                "label": str(event["label"]),
            }
            for event in events
        ],
    }
