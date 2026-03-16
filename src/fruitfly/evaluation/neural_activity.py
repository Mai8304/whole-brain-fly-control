from __future__ import annotations

from typing import Any

import torch
from torch import Tensor


def summarize_neural_activity(
    *,
    state: Tensor,
    afferent_mask: Tensor,
    intrinsic_mask: Tensor,
    efferent_mask: Tensor,
    top_k: int = 20,
) -> dict[str, Any]:
    if state.ndim != 3:
        raise ValueError("state must have shape [batch, num_nodes, hidden_dim]")
    if state.shape[0] < 1:
        raise ValueError("state must contain at least one batch element")

    node_activity = state[0].abs().mean(dim=-1)
    afferent_mask = afferent_mask.to(device=node_activity.device, dtype=torch.bool)
    intrinsic_mask = intrinsic_mask.to(device=node_activity.device, dtype=torch.bool)
    efferent_mask = efferent_mask.to(device=node_activity.device, dtype=torch.bool)

    top_k = max(0, min(int(top_k), int(node_activity.numel())))
    if top_k > 0:
        top_values, top_indices = torch.topk(node_activity, k=top_k)
        top_active_nodes = [
            {
                "node_idx": int(node_idx),
                "activity_value": float(value),
                "flow_role": _flow_role_for_index(
                    node_idx=int(node_idx),
                    afferent_mask=afferent_mask,
                    intrinsic_mask=intrinsic_mask,
                    efferent_mask=efferent_mask,
                ),
            }
            for value, node_idx in zip(top_values.tolist(), top_indices.tolist(), strict=True)
        ]
    else:
        top_active_nodes = []

    return {
        "afferent_activity": _masked_mean(node_activity, afferent_mask),
        "intrinsic_activity": _masked_mean(node_activity, intrinsic_mask),
        "efferent_activity": _masked_mean(node_activity, efferent_mask),
        "top_active_nodes": top_active_nodes,
    }


def _masked_mean(values: Tensor, mask: Tensor) -> float:
    selected = values[mask]
    if selected.numel() == 0:
        return 0.0
    return float(selected.mean().item())


def _flow_role_for_index(
    *,
    node_idx: int,
    afferent_mask: Tensor,
    intrinsic_mask: Tensor,
    efferent_mask: Tensor,
) -> str:
    if bool(afferent_mask[node_idx].item()):
        return "afferent"
    if bool(efferent_mask[node_idx].item()):
        return "efferent"
    if bool(intrinsic_mask[node_idx].item()):
        return "intrinsic"
    return "unlabeled"
