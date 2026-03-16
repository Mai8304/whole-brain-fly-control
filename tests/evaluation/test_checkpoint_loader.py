from pathlib import Path


def test_load_checkpoint_bundle_reconstructs_model(tmp_path: Path) -> None:
    import torch

    from fruitfly.graph import CompiledGraph, save_compiled_graph
    from fruitfly.evaluation.checkpoint_loader import load_checkpoint_bundle
    from fruitfly.models import WholeBrainRateModel

    compiled_dir = tmp_path / "compiled"
    save_compiled_graph(
        graph=CompiledGraph(
            node_index={10: 0, 20: 1, 30: 2},
            edge_index=[(0, 1), (1, 2)],
            afferent_mask=[True, False, False],
            intrinsic_mask=[False, True, False],
            efferent_mask=[False, False, True],
        ),
        compiled_dir=compiled_dir,
        snapshot_id="test_snapshot",
    )

    model = WholeBrainRateModel(
        num_nodes=3,
        hidden_dim=4,
        action_dim=2,
        afferent_indices=[0],
        efferent_indices=[2],
        edge_index=[(0, 1), (1, 2)],
    )
    dummy_input = torch.zeros((1, 5), dtype=torch.float32)
    dummy_state = model.initial_state(batch_size=1)
    with torch.no_grad():
        model(dummy_input, dummy_state)

    checkpoint_path = tmp_path / "epoch_0001.pt"
    torch.save({"epoch": 1, "model": model.state_dict(), "optimizer": {}}, checkpoint_path)

    bundle = load_checkpoint_bundle(
        checkpoint_path=checkpoint_path,
        compiled_graph_dir=compiled_dir,
    )

    state = bundle.model.initial_state(batch_size=1)
    mean, _, _ = bundle.model(dummy_input, state)

    assert bundle.hidden_dim == 4
    assert bundle.action_dim == 2
    assert bundle.input_dim == 5
    assert tuple(mean.shape) == (1, 2)
