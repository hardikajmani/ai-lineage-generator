"""
Quick smoke test — run from the lineage-ai/ root:
    python test_parsers.py
"""
import sys, json
sys.path.insert(0, ".")

from lineage_parser.ast_parser import parse_python_file
from lineage_parser.sql_parser import parse_sql_file

print("=" * 60)
print("Testing ingest_transactions.py")
print("=" * 60)
result = parse_python_file("corpus/ingest_transactions.py")
print(f"Nodes  : {[n.node_id for n in result.nodes]}")
print(f"Edges  : {len(result.edges)}")
for e in result.edges:
    print(f"  {e.source} ──► {e.target}  [{e.confidence}] line {e.line_number}")
print(f"Errors : {result.parse_errors}")

print()
print("=" * 60)
print("Testing compute_fees.py")
print("=" * 60)
result2 = parse_python_file("corpus/compute_fees.py")
print(f"Nodes  : {[n.node_id for n in result2.nodes]}")
print(f"Edges  : {len(result2.edges)}")
for e in result2.edges:
    print(f"  {e.source} ──► {e.target}  [{e.confidence}] line {e.line_number}")

print()
print("=" * 60)
print("Testing generate_report.sql")
print("=" * 60)
result3 = parse_sql_file("corpus/generate_report.sql")
print(f"Nodes  : {[n.node_id for n in result3.nodes]}")
print(f"Edges  : {len(result3.edges)}")
for e in result3.edges:
    print(f"  {e.source} ──► {e.target}  [{e.confidence}]  file={e.source_file}")
print(f"Errors : {result3.parse_errors}")

print()
print("=" * 60)
print("Testing airflow_dag.py")
print("=" * 60)
result4 = parse_python_file("corpus/airflow_dag.py")
print(f"Nodes  : {[n.node_id for n in result4.nodes]}")
print(f"Edges  : {len(result4.edges)}")
for e in result4.edges:
    print(f"  {e.source} ──► {e.target}  [{e.confidence}] line {e.line_number}")
print(f"Errors : {result4.parse_errors}")
