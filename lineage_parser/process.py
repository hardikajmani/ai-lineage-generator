from pathlib import Path
from lineage_parser.ast_parser import parse_python_file
from lineage_parser.sql_parser import parse_sql_file
from lineage_parser.models import LineageGraph
from  lineage_parser.llm_parser import enrich_lineage_with_ai

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

# To run it:
final_lineage = process_corpus("./corpus")
print(final_lineage.model_dump_json(indent=2))