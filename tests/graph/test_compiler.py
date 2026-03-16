def test_compiler_creates_contiguous_indices() -> None:
    from fruitfly.graph.compiler import compile_snapshot

    compiled = compile_snapshot(
        nodes=[
            {"source_id": 10, "flow_role": "afferent", "is_active": True},
            {"source_id": 20, "flow_role": "intrinsic", "is_active": True},
        ],
        edges=[{"pre_id": 10, "post_id": 20, "is_active": True}],
    )

    assert compiled.node_index == {10: 0, 20: 1}
