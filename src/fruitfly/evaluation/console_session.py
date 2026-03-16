from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class ConsoleSession:
    mode: str
    checkpoint: str
    task: str
    applied_state: dict[str, Any]
    pending_state: dict[str, Any]
    pending_changes: bool
    intervention_log: list[dict[str, Any]]
    action_provenance: dict[str, bool]

    @classmethod
    def create(
        cls,
        *,
        mode: str,
        checkpoint: str,
        task: str,
        environment_physics: dict[str, Any],
        sensory_inputs: dict[str, Any],
    ) -> "ConsoleSession":
        applied_state = {
            "environment_physics": dict(environment_physics),
            "sensory_inputs": dict(sensory_inputs),
        }
        return cls(
            mode=mode,
            checkpoint=checkpoint,
            task=task,
            applied_state=applied_state,
            pending_state=applied_state,
            pending_changes=False,
            intervention_log=[],
            action_provenance={
                "direct_action_editing": False,
                "joint_override": False,
            },
        )

    def stage_changes(
        self,
        *,
        environment_physics: dict[str, Any] | None = None,
        sensory_inputs: dict[str, Any] | None = None,
    ) -> "ConsoleSession":
        pending_state = {
            "environment_physics": dict(
                environment_physics if environment_physics is not None else self.applied_state["environment_physics"]
            ),
            "sensory_inputs": dict(sensory_inputs if sensory_inputs is not None else self.applied_state["sensory_inputs"]),
        }
        pending_changes = pending_state != self.applied_state
        return replace(
            self,
            pending_state=pending_state,
            pending_changes=pending_changes,
        )

    def apply_pending(self) -> "ConsoleSession":
        changed_fields = [
            field_name
            for field_name, value in self.pending_state.items()
            if value != self.applied_state.get(field_name)
        ]
        intervention_log = list(self.intervention_log)
        if changed_fields:
            intervention_log.append(
                {
                    "changed_fields": changed_fields,
                    "type": "applied_pending_changes",
                }
            )
        return replace(
            self,
            applied_state=self.pending_state,
            pending_changes=False,
            intervention_log=intervention_log,
        )
