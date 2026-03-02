from pathlib import Path
from lineage_parser.ast_parser import parse_python_file
from lineage_parser.sql_parser import parse_sql_file
from lineage_parser.models import LineageGraph
from lineage_parser.llm_parser import enrich_lineage_with_ai
from lineage_parser.networkx_graph_generator import build_networkx_graph, print_end_to_end_paths, resolve_entities

def process_corpus(corpus_dir: str) -> LineageGraph:
    corpus_path = Path(corpus_dir)
    
    # We will accumulate all enriched nodes and edges here
    master_graph = LineageGraph(nodes=[], edges=[])
    
    for filepath in corpus_path.iterdir():
        if not filepath.is_file() or filepath.name == "__init__.py":
            continue
            
        print(f"Processing {filepath.name}...")
        raw_code = filepath.read_text()
        
        # 1. Deterministic Parsing Layer
        if filepath.suffix == ".py":
            static_facts = parse_python_file(str(filepath))
        elif filepath.suffix == ".sql":
            static_facts = parse_sql_file(str(filepath))
        else:
            continue
            
        # 2. AI Reasoning Layer
        print(f"  -> Sending {filepath.name} facts to AI Agent...")
        enriched_graph = enrich_lineage_with_ai(raw_code, static_facts)
        
        # 3. Merge into Master Graph
        master_graph.nodes.extend(enriched_graph.nodes)
        master_graph.edges.extend(enriched_graph.edges)
        
    return deduplicate_graph(master_graph)

def deduplicate_graph(graph: LineageGraph) -> LineageGraph:
    """Utility to remove duplicate nodes across different files."""
    unique_nodes = {node.node_id: node for node in graph.nodes}
    unique_edges = {edge.edge_id: edge for edge in graph.edges}
    return LineageGraph(
        nodes=list(unique_nodes.values()), 
        edges=list(unique_edges.values())
    )

def get_or_generate_raw_lineage(corpus_dir: str, cache_file: str = "raw_lineage_cache.json") -> LineageGraph:
    """
    Checks if a cached version of the AI output exists. 
    If yes, loads it. If no, runs the AI pipeline and saves the result.
    """
    cache_path = Path(corpus_dir) / cache_file
    
    if cache_path.exists():
        print(f"⚡ Found cached AI data at '{cache_file}'. Skipping API calls...")
        # Read the JSON and instantly validate it back into our Pydantic model
        return LineageGraph.model_validate_json(cache_path.read_text())
    
    print(f"No cache found at '{cache_file}'. Calling LLM API to generate new lineage...")
    raw_lineage = process_corpus(corpus_dir)
    
    # Save the raw lineage to cache so we don't have to call the AI next time
    cache_path.write_text(raw_lineage.model_dump_json(indent=2))
    print(f"✅ Saved raw AI lineage cache to '{cache_file}'")
    
    return raw_lineage

# To run it:
if __name__ == "__main__":
    print("Starting AI Lineage Generation...\n")
    
    # 1. Process corpus and get raw fragmented graph (Uses Cache if available!)
    RAW_CACHE_FILE = "raw_lineage_cache.json"
    raw_lineage = get_or_generate_raw_lineage("./corpus", RAW_CACHE_FILE)
    
    print(f"\nRaw Graph: {len(raw_lineage.nodes)} nodes, {len(raw_lineage.edges)} edges.")
    
    # 2. Apply Entity Resolution to stitch it together
    stitched_lineage = resolve_entities(raw_lineage)
    print(f"Stitched Graph: {len(stitched_lineage.nodes)} nodes, {len(stitched_lineage.edges)} edges.")
    
    # 3. Save to JSON for the React Flow UI
    output_file = "stitched_lineage.json"
    with open(output_file, "w") as f:
        f.write(stitched_lineage.model_dump_json(indent=2))
    print(f"✅ Successfully saved stitched graph for UI to '{output_file}'")
    
    # 4. Build NetworkX to verify end-to-end paths
    nx_graph = build_networkx_graph(stitched_lineage)
    print_end_to_end_paths(
        nx_graph, 
        source_node="file:raw_transactions.csv", 
        target_node="table:client_summary"
    )