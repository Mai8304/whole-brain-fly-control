def test_export_dry_run_writes_normalized_tables(tmp_path) -> None:
    import pyarrow.parquet as pq

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run
    from fruitfly.snapshot.schema import validate_edges_columns, validate_nodes_columns

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {
                        "source_id": 1,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "intrinsic",
                        "is_active": True,
                    },
                ],
                "edges": [],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "intrinsic"},
                ],
            }

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="normalized_test"),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )

    node_columns = set(pq.read_table(result.snapshot_dir / "normalized" / "nodes.parquet").column_names)
    edge_columns = set(pq.read_table(result.snapshot_dir / "normalized" / "edges.parquet").column_names)

    assert validate_nodes_columns(node_columns)
    assert validate_edges_columns(edge_columns)
