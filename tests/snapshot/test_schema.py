def test_validate_normalized_snapshot_tables() -> None:
    from fruitfly.snapshot.schema import validate_nodes_columns

    columns = {"source_id", "dataset_version", "hemisphere", "flow_role", "is_active"}
    assert validate_nodes_columns(columns)
