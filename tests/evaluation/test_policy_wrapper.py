def test_closed_loop_policy_wrapper_preserves_hidden_state_across_steps() -> None:
    import torch

    from fruitfly.graph import CompiledGraph, save_compiled_graph
    from fruitfly.evaluation.checkpoint_loader import load_checkpoint_bundle
    from fruitfly.evaluation.policy_wrapper import ClosedLoopPolicyWrapper
    from fruitfly.models import WholeBrainRateModel

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        compiled_dir = base / "compiled"
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
        dummy_input = torch.zeros((1, 14), dtype=torch.float32)
        dummy_state = model.initial_state(batch_size=1)
        with torch.no_grad():
            model(dummy_input, dummy_state)

        checkpoint_path = base / "epoch_0001.pt"
        torch.save({"epoch": 1, "model": model.state_dict(), "optimizer": {}}, checkpoint_path)

        bundle = load_checkpoint_bundle(
            checkpoint_path=checkpoint_path,
            compiled_graph_dir=compiled_dir,
        )
        wrapper = ClosedLoopPolicyWrapper(bundle=bundle)

        observation = {
            "walker/accelerometer": [1.0, 1.0, 1.0],
            "walker/world_zaxis": [0.0, 0.0, 1.0],
            "walker/ref_displacement": [[0.1, 0.0, 0.0], [0.2, 0.0, 0.0]],
        }

        action_1 = wrapper.act(observation)
        state_after_first = wrapper._state.clone()
        action_2 = wrapper.act(observation)

        assert len(action_1) == 2
        assert len(action_2) == 2
        assert wrapper._state is not None
        assert not torch.equal(state_after_first, wrapper._state)


def test_closed_loop_policy_wrapper_exposes_activity_snapshot() -> None:
    import torch

    from fruitfly.graph import CompiledGraph, save_compiled_graph
    from fruitfly.evaluation.checkpoint_loader import load_checkpoint_bundle
    from fruitfly.evaluation.policy_wrapper import ClosedLoopPolicyWrapper
    from fruitfly.models import WholeBrainRateModel

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        compiled_dir = base / "compiled"
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
        dummy_input = torch.zeros((1, 14), dtype=torch.float32)
        dummy_state = model.initial_state(batch_size=1)
        with torch.no_grad():
            model(dummy_input, dummy_state)

        checkpoint_path = base / "epoch_0001.pt"
        torch.save({"epoch": 1, "model": model.state_dict(), "optimizer": {}}, checkpoint_path)

        bundle = load_checkpoint_bundle(
            checkpoint_path=checkpoint_path,
            compiled_graph_dir=compiled_dir,
        )
        wrapper = ClosedLoopPolicyWrapper(bundle=bundle)

        observation = {
            "walker/accelerometer": [1.0, 1.0, 1.0],
            "walker/world_zaxis": [0.0, 0.0, 1.0],
            "walker/ref_displacement": [[0.1, 0.0, 0.0], [0.2, 0.0, 0.0]],
        }

        wrapper.act(observation)
        snapshot = wrapper.activity_snapshot(top_k=2)

        assert set(snapshot) == {
            "afferent_activity",
            "intrinsic_activity",
            "efferent_activity",
            "top_active_nodes",
        }
        assert len(snapshot["top_active_nodes"]) == 2
