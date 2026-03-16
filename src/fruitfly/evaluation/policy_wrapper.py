from __future__ import annotations

import math
from typing import Any

import torch

from fruitfly.adapters.flybody_export import adapt_straight_walking_inputs
from fruitfly.evaluation.checkpoint_loader import LoadedCheckpointBundle
from fruitfly.evaluation.neural_activity import summarize_neural_activity


class ClosedLoopPolicyWrapper:
    def __init__(self, *, bundle: LoadedCheckpointBundle) -> None:
        self.bundle = bundle
        self.model = bundle.model
        self.device = bundle.device
        self._state: torch.Tensor | None = None

    def reset(self) -> None:
        self._state = None

    def act(self, observation: Any) -> list[float]:
        obs_values, command_values = adapt_straight_walking_inputs(observation)
        model_input = obs_values + command_values
        if len(model_input) != self.bundle.input_dim:
            raise ValueError(
                f"Model input dimension mismatch: expected {self.bundle.input_dim}, got {len(model_input)}"
            )

        if self._state is None:
            self._state = self.model.initial_state(batch_size=1, device=self.device)

        input_tensor = torch.tensor([model_input], dtype=torch.float32, device=self.device)
        with torch.no_grad():
            mean, _, next_state = self.model(input_tensor, self._state)
        self._state = next_state.detach()
        return [float(value) for value in mean[0].detach().cpu().tolist()]

    def activity_snapshot(self, *, top_k: int = 20) -> dict[str, Any]:
        if self._state is None:
            return {
                "afferent_activity": 0.0,
                "intrinsic_activity": 0.0,
                "efferent_activity": 0.0,
                "top_active_nodes": [],
            }
        compiled_graph = self.bundle.compiled_graph
        return summarize_neural_activity(
            state=self._state.detach(),
            afferent_mask=compiled_graph["afferent_mask"],
            intrinsic_mask=compiled_graph["intrinsic_mask"],
            efferent_mask=compiled_graph["efferent_mask"],
            top_k=top_k,
        )

    @staticmethod
    def action_norm(action: list[float]) -> float:
        return math.sqrt(sum(float(value) * float(value) for value in action))
