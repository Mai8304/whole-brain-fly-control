from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import torch

from fruitfly.graph import load_compiled_graph_tensors
from fruitfly.models import WholeBrainRateModel
from fruitfly.training import ILDataset, ILTrainingConfig, OfflineILTrainer


def _parse_index_list(value: str) -> list[int]:
    if not value:
        return []
    return [int(item) for item in value.split(",") if item]


def _load_edges(path: Path | None) -> list[tuple[int, int]]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [tuple(pair) for pair in payload]


def _resolve_graph_inputs(args: argparse.Namespace) -> dict[str, object]:
    if args.compiled_graph_dir is not None:
        compiled = load_compiled_graph_tensors(args.compiled_graph_dir)
        afferent_mask = compiled["afferent_mask"]
        efferent_mask = compiled["efferent_mask"]
        return {
            "num_nodes": int(len(compiled["node_index"])),
            "edge_index": compiled["edge_index"],
            "afferent_indices": torch.nonzero(afferent_mask, as_tuple=False).flatten().tolist(),
            "efferent_indices": torch.nonzero(efferent_mask, as_tuple=False).flatten().tolist(),
        }

    if args.num_nodes is None:
        raise ValueError("Either --compiled-graph-dir or --num-nodes must be provided.")

    return {
        "num_nodes": int(args.num_nodes),
        "edge_index": _load_edges(args.edge_json),
        "afferent_indices": _parse_index_list(args.afferent_indices),
        "efferent_indices": _parse_index_list(args.efferent_indices),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an IL-only walking controller.")
    parser.add_argument("--dataset", type=Path, required=True, help="Path to the IL dataset")
    parser.add_argument("--output-dir", type=Path, required=True, help="Training output directory")
    parser.add_argument("--compiled-graph-dir", type=Path, default=None, help="Compiled graph artifact directory")
    parser.add_argument("--num-nodes", type=int, default=None, help="Number of graph nodes")
    parser.add_argument("--hidden-dim", type=int, default=32, help="Hidden state width")
    parser.add_argument("--action-dim", type=int, default=59, help="Action dimension")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
        help="Optimizer learning rate",
    )
    parser.add_argument(
        "--afferent-indices",
        default="",
        help="Comma-separated afferent node indices",
    )
    parser.add_argument(
        "--efferent-indices",
        default="",
        help="Comma-separated efferent node indices",
    )
    parser.add_argument(
        "--edge-json",
        type=Path,
        default=None,
        help="Optional JSON file containing [[src, dst], ...] edges",
    )
    args = parser.parse_args()
    graph_inputs = _resolve_graph_inputs(args)

    model = WholeBrainRateModel(
        num_nodes=graph_inputs["num_nodes"],
        hidden_dim=args.hidden_dim,
        action_dim=args.action_dim,
        afferent_indices=graph_inputs["afferent_indices"],
        efferent_indices=graph_inputs["efferent_indices"],
        edge_index=graph_inputs["edge_index"],
    )
    trainer = OfflineILTrainer(
        model=model,
        dataset=ILDataset(args.dataset),
        output_dir=args.output_dir,
        config=ILTrainingConfig(
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
        ),
    )
    metrics = trainer.train()
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
