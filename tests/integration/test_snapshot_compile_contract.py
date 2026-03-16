from pathlib import Path


def test_exported_normalized_snapshot_compiles(tmp_path: Path) -> None:
    from fruitfly.graph.compiler import compile_snapshot
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run, load_normalized_snapshot

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {
                        "source_id": 1,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "afferent",
                        "is_active": True,
                    },
                    {
                        "source_id": 2,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "intrinsic",
                        "is_active": True,
                    },
                    {
                        "source_id": 3,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "efferent",
                        "is_active": True,
                    },
                ],
                "edges": [
                    {"pre_id": 1, "post_id": 2, "synapse_count": 2, "is_active": True},
                    {"pre_id": 2, "post_id": 3, "synapse_count": 4, "is_active": True},
                ],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "afferent"},
                    {"source_id": 2, "flow_role": "intrinsic"},
                    {"source_id": 3, "flow_role": "efferent"},
                ],
            }

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="compile_contract"),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )
    nodes, edges = load_normalized_snapshot(result.snapshot_dir)
    compiled = compile_snapshot(nodes=nodes, edges=edges)

    assert compiled.node_index == {1: 0, 2: 1, 3: 2}
    assert compiled.edge_index == [(0, 1), (1, 2)]
    assert compiled.afferent_mask == [True, False, False]
    assert compiled.intrinsic_mask == [False, True, False]
    assert compiled.efferent_mask == [False, False, True]
