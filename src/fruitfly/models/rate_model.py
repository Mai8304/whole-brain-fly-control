from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import Tensor, nn


class WholeBrainRateModel(nn.Module):
    def __init__(
        self,
        *,
        num_nodes: int,
        hidden_dim: int,
        action_dim: int,
        afferent_indices: Sequence[int] | None = None,
        efferent_indices: Sequence[int] | None = None,
        edge_index: Sequence[tuple[int, int]] | None = None,
    ) -> None:
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.action_dim = action_dim

        self.input_projector = nn.LazyLinear(hidden_dim)
        self.message_projector = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.update_gate = nn.Linear(hidden_dim * 2, hidden_dim)
        self.update_candidate = nn.Linear(hidden_dim * 2, hidden_dim)
        self.decoder = nn.Linear(hidden_dim, hidden_dim)
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std_head = nn.Linear(hidden_dim, action_dim)

        afferent = list(afferent_indices or [])
        efferent = list(efferent_indices or [])
        if isinstance(edge_index, torch.Tensor):
            if edge_index.ndim != 2 or edge_index.shape[0] != 2:
                raise ValueError("edge_index tensor must have shape [2, E]")
            src_tensor = edge_index[0].to(dtype=torch.long)
            dst_tensor = edge_index[1].to(dtype=torch.long)
        else:
            edges = list(edge_index or [])
            src_tensor = torch.tensor([source for source, _ in edges], dtype=torch.long)
            dst_tensor = torch.tensor([target for _, target in edges], dtype=torch.long)

        self.register_buffer(
            "afferent_indices",
            torch.tensor(afferent, dtype=torch.long),
            persistent=False,
        )
        self.register_buffer(
            "efferent_indices",
            torch.tensor(efferent, dtype=torch.long),
            persistent=False,
        )
        self.register_buffer(
            "src_index",
            src_tensor,
            persistent=False,
        )
        self.register_buffer(
            "dst_index",
            dst_tensor,
            persistent=False,
        )

    def initial_state(self, *, batch_size: int, device: torch.device | None = None) -> Tensor:
        return torch.zeros(batch_size, self.num_nodes, self.hidden_dim, device=device)

    def forward(self, obs: Tensor, state: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        injected = self._inject_inputs(obs, state)
        messages = self._propagate(state)
        combined = messages + injected

        gate_input = torch.cat([state, combined], dim=-1)
        update_gate = torch.sigmoid(self.update_gate(gate_input))
        candidate = torch.tanh(self.update_candidate(gate_input))
        next_state = (1.0 - update_gate) * state + update_gate * candidate

        readout = self._readout(next_state)
        decoded = torch.tanh(self.decoder(readout))
        mean = self.mean_head(decoded)
        log_std = self.log_std_head(decoded).clamp(min=-5.0, max=2.0)
        return mean, log_std, next_state

    def _inject_inputs(self, obs: Tensor, state: Tensor) -> Tensor:
        projected = self.input_projector(obs)
        injected = torch.zeros_like(state)
        if self.afferent_indices.numel() == 0:
            injected[:] = projected.unsqueeze(1)
            return injected
        injected[:, self.afferent_indices, :] = projected.unsqueeze(1)
        return injected

    def _propagate(self, state: Tensor) -> Tensor:
        messages = torch.zeros_like(state)
        if self.src_index.numel() == 0:
            return messages

        source_state = self.message_projector(state[:, self.src_index, :])
        batch_size = state.shape[0]
        offsets = (
            torch.arange(batch_size, device=state.device, dtype=torch.long).unsqueeze(1)
            * self.num_nodes
        )
        flat_target = (self.dst_index.unsqueeze(0) + offsets).reshape(-1)
        flat_messages = messages.reshape(batch_size * self.num_nodes, self.hidden_dim)
        flat_messages.index_add_(0, flat_target, source_state.reshape(-1, self.hidden_dim))
        return flat_messages.view_as(messages)

    def _readout(self, state: Tensor) -> Tensor:
        if self.efferent_indices.numel() == 0:
            return state.mean(dim=1)
        return state[:, self.efferent_indices, :].mean(dim=1)
