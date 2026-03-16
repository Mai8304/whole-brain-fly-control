from pathlib import Path


def test_save_and_load_compiled_graph_round_trip(tmp_path: Path) -> None:
    from fruitfly.graph import CompiledGraph, load_compiled_graph, save_compiled_graph

    graph = CompiledGraph(
        node_index={10: 0, 20: 1},
        edge_index=[(0, 1)],
        afferent_mask=[True, False],
        intrinsic_mask=[False, False],
        efferent_mask=[False, True],
    )

    compiled_dir = tmp_path / "compiled"
    save_compiled_graph(
        graph=graph,
        compiled_dir=compiled_dir,
        snapshot_id="test_snapshot",
    )
    loaded = load_compiled_graph(compiled_dir)

    assert loaded.node_index == graph.node_index
    assert loaded.edge_index == graph.edge_index
    assert loaded.afferent_mask == graph.afferent_mask
    assert loaded.intrinsic_mask == graph.intrinsic_mask
    assert loaded.efferent_mask == graph.efferent_mask
    assert loaded.manifest is not None
    assert loaded.config is not None
    assert loaded.graph_stats is not None
