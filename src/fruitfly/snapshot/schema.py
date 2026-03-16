from __future__ import annotations


REQUIRED_NODE_COLUMNS = {
    "source_id",
    "dataset_version",
    "hemisphere",
    "flow_role",
    "is_active",
}

REQUIRED_EDGE_COLUMNS = {
    "pre_id",
    "post_id",
    "synapse_count",
    "is_directed",
    "is_active",
}

REQUIRED_PARTITION_COLUMNS = {
    "source_id",
    "flow_role",
    "partition_version",
}


def _validate_columns(columns: set[str], required: set[str], table_name: str) -> bool:
    missing = required - columns
    if missing:
        raise ValueError(f"Missing {table_name} columns: {sorted(missing)}")
    return True


def validate_nodes_columns(columns: set[str]) -> bool:
    return _validate_columns(columns, REQUIRED_NODE_COLUMNS, "node")


def validate_edges_columns(columns: set[str]) -> bool:
    return _validate_columns(columns, REQUIRED_EDGE_COLUMNS, "edge")


def validate_partitions_columns(columns: set[str]) -> bool:
    return _validate_columns(columns, REQUIRED_PARTITION_COLUMNS, "partition")
