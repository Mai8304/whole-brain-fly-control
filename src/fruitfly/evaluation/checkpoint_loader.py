from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from fruitfly.graph import load_compiled_graph_runtime
from fruitfly.models import WholeBrainRateModel


@dataclass(slots=True)
class LoadedCheckpointBundle:
    model: WholeBrainRateModel
    compiled_graph: dict[str, object]
    checkpoint_path: Path
    hidden_dim: int
    action_dim: int
    input_dim: int
    device: torch.device


def load_checkpoint_bundle(
    *,
    checkpoint_path: Path,
    compiled_graph_dir: Path,
    device: torch.device | str = "cpu",
) -> LoadedCheckpointBundle:
    resolved_device = torch.device(device)
    payload = torch.load(checkpoint_path, map_location=resolved_device)
    state_dict = payload["model"]

    hidden_dim = int(state_dict["message_projector.weight"].shape[0])
    action_dim = int(state_dict["mean_head.weight"].shape[0])
    input_dim = int(state_dict["input_projector.weight"].shape[1])

    compiled_graph = load_compiled_graph_runtime(compiled_graph_dir)
    afferent_mask = compiled_graph["afferent_mask"]
    efferent_mask = compiled_graph["efferent_mask"]
    edge_index = compiled_graph["edge_index"]
    num_nodes = int(compiled_graph["node_count"])

    model = WholeBrainRateModel(
        num_nodes=num_nodes,
        hidden_dim=hidden_dim,
        action_dim=action_dim,
        afferent_indices=torch.nonzero(afferent_mask, as_tuple=False).flatten().tolist(),
        efferent_indices=torch.nonzero(efferent_mask, as_tuple=False).flatten().tolist(),
        edge_index=edge_index,
    )
    _initialize_lazy_layers(model=model, input_dim=input_dim, device=resolved_device)
    model.load_state_dict(state_dict)
    model.to(resolved_device)
    model.eval()

    return LoadedCheckpointBundle(
        model=model,
        compiled_graph=compiled_graph,
        checkpoint_path=checkpoint_path,
        hidden_dim=hidden_dim,
        action_dim=action_dim,
        input_dim=input_dim,
        device=resolved_device,
    )


def _initialize_lazy_layers(
    *,
    model: WholeBrainRateModel,
    input_dim: int,
    device: torch.device,
) -> None:
    dummy_input = torch.zeros((1, input_dim), dtype=torch.float32, device=device)
    dummy_state = model.initial_state(batch_size=1, device=device)
    with torch.no_grad():
        model(dummy_input, dummy_state)
