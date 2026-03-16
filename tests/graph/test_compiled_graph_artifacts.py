from pathlib import Path


def test_save_compiled_graph_writes_required_files(tmp_path: Path) -> None:
    from fruitfly.graph import COMPILED_GRAPH_FILES, CompiledGraph, save_compiled_graph

    compiled_dir = tmp_path / "compiled"
    graph = CompiledGraph(
        node_index={10: 0, 20: 1},
        edge_index=[(0, 1)],
        afferent_mask=[True, False],
        intrinsic_mask=[False, False],
        efferent_mask=[False, True],
    )

    save_compiled_graph(
        graph=graph,
        compiled_dir=compiled_dir,
        snapshot_id="test_snapshot",
    )

    assert COMPILED_GRAPH_FILES.issubset({path.name for path in compiled_dir.iterdir()})
