from __future__ import annotations

from .types import CompiledGraph


def compile_snapshot(
    *,
    nodes: list[dict[str, object]],
    edges: list[dict[str, object]],
) -> CompiledGraph:
    active_nodes = [node for node in nodes if bool(node.get("is_active", False))]
    ordered_ids = [int(node["source_id"]) for node in active_nodes]
    node_index = {source_id: idx for idx, source_id in enumerate(ordered_ids)}

    active_edges = []
    for edge in edges:
        if not bool(edge.get("is_active", False)):
            continue
        pre_id = int(edge["pre_id"])
        post_id = int(edge["post_id"])
        if pre_id not in node_index or post_id not in node_index:
            continue
        active_edges.append((node_index[pre_id], node_index[post_id]))

    afferent_mask = [str(node["flow_role"]) == "afferent" for node in active_nodes]
    intrinsic_mask = [str(node["flow_role"]) == "intrinsic" for node in active_nodes]
    efferent_mask = [str(node["flow_role"]) == "efferent" for node in active_nodes]

    return CompiledGraph(
        node_index=node_index,
        edge_index=active_edges,
        afferent_mask=afferent_mask,
        intrinsic_mask=intrinsic_mask,
        efferent_mask=efferent_mask,
    )
