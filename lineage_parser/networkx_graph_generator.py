import json
import networkx as nx
from lineage_parser.models import LineageGraph

# 1. Define the Entity Resolution Map
# This maps the fragmented LLM variations to a single, canonical ID
ENTITY_RESOLUTION_MAP = {
    # Transactions Table
    "transactions": "table:transactions",
    "source_transactions_table": "table:transactions",
    "table_warehouse_transactions": "table:transactions",
    
    # Accounts Table
    "accounts": "table:accounts",
    "source_accounts_table": "table:accounts",
    "table_warehouse_accounts": "table:accounts",
    
    # Fees Table
    "sink_fees_table": "table:fees",
    "fees": "table:fees",
    "table_warehouse_fees": "table:fees",
    
    # Client Summary Table
    "client_summary": "table:client_summary",
    "table_warehouse_client_summary": "table:client_summary",
    
    # Standardize the raw file
    "data/raw_transactions.csv": "file:raw_transactions.csv",
    "file_raw_transactions_csv": "file:raw_transactions.csv"
}

def resolve_id(original_id: str) -> str:
    """Returns the canonical ID if it exists in the map, otherwise returns the original."""
    return ENTITY_RESOLUTION_MAP.get(original_id, original_id)

def resolve_entities(graph: LineageGraph) -> LineageGraph:
    """Applies Entity Resolution to stitch the fragmented graph together."""
    resolved_nodes_dict = {}
    
    # 1. Resolve Nodes
    for node in graph.nodes:
        new_id = resolve_id(node.node_id)
        if new_id not in resolved_nodes_dict:
            # Create a copy with the new canonical ID
            resolved_node = node.model_copy(update={"node_id": new_id})
            resolved_nodes_dict[new_id] = resolved_node
        else:
            # If we already have this node, preserve the best description
            if node.description and not resolved_nodes_dict[new_id].description:
                resolved_nodes_dict[new_id].description = node.description

    # 2. Resolve Edges
    resolved_edges_dict = {}
    for edge in graph.edges:
        new_source = resolve_id(edge.source)
        new_target = resolve_id(edge.target)
        
        # Prevent self-loops if source and target resolved to the same entity
        if new_source == new_target:
            continue
            
        # Regenerate edge ID based on new resolved source/targets
        new_edge_id = f"{new_source}__{new_target}__{edge.source_file}"
        
        if new_edge_id not in resolved_edges_dict:
            resolved_edge = edge.model_copy(update={
                "edge_id": new_edge_id,
                "source": new_source,
                "target": new_target
            })
            resolved_edges_dict[new_edge_id] = resolved_edge
            
    return LineageGraph(
        nodes=list(resolved_nodes_dict.values()),
        edges=list(resolved_edges_dict.values())
    )


def build_networkx_graph(graph: LineageGraph) -> nx.DiGraph:
    """Converts the Pydantic LineageGraph into a NetworkX DiGraph for traversal."""
    G = nx.DiGraph()
    
    # Use dot notation (.nodes) instead of bracket notation (["nodes"])
    for node in graph.nodes:
        # .model_dump() converts the Pydantic node back to a dict for NetworkX attributes
        G.add_node(node.node_id, **node.model_dump())
        
    for edge in graph.edges:
        G.add_edge(edge.source, edge.target, **edge.model_dump())
        
    return G

def print_end_to_end_paths(G: nx.DiGraph, source_node: str, target_node: str):
    """Utility to prove the graph is stitched by finding paths from raw file to final report."""
    print(f"\n--- Tracing Lineage: {source_node} -> {target_node} ---")
    try:
        paths = list(nx.all_simple_paths(G, source=source_node, target=target_node))
        if not paths:
            print("No continuous path found. The graph is still broken.")
            return
            
        for i, path in enumerate(paths, 1):
            print(f"\nPath {i}:")
            print(" -> \n".join(path))
    except nx.NetworkXNoPath:
        print("No continuous path found.")