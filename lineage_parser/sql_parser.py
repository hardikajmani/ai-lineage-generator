import hashlib
from typing import List
import sqlglot
import sqlglot.expressions as exp
from pathlib import Path
from lineage_parser.models import LineageEdge, LineageNode, ParseResult, ConfidenceLevel, EdgeStatus


def _make_edge_id(source: str, target: str, filename: str) -> str:
    raw = f"{source}__{target}__{filename}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _register_node(nodes: dict, name: str, node_type: str):
    if name not in nodes:
        nodes[name] = LineageNode(node_id=name, node_type=node_type)


def parse_sql_file(filepath: str) -> ParseResult:
    path   = Path(filepath)
    errors: List[str] = []
    edges:  List[LineageEdge] = []
    nodes:  dict = {}
    try:
        sql_text   = path.read_text()
        statements = sqlglot.parse(sql_text, dialect="postgres")
        for stmt in statements:
            if stmt is None:
                continue
            insert_target = None
            if isinstance(stmt, exp.Insert):
                tbl = stmt.find(exp.Table)
                if tbl:
                    insert_target = tbl.name
                    _register_node(nodes, insert_target, "output")
            source_tables = []
            for table in stmt.find_all(exp.Table):
                name = table.name
                if name and name != insert_target:
                    source_tables.append(name)
                    _register_node(nodes, name, "source")
            snippet = sql_text[:300].replace("\n", " ").strip()
            if insert_target and source_tables:
                for source in set(source_tables):
                    edges.append(LineageEdge(
                        edge_id          = _make_edge_id(source, insert_target, path.name),
                        source           = source,
                        target           = insert_target,
                        transformation   = snippet,
                        source_file      = path.name,
                        confidence       = ConfidenceLevel.HIGH,
                        confidence_score = 0.92,
                        status           = EdgeStatus.AI_SUGGESTED,
                    ))
            elif not insert_target and source_tables:
                for source in set(source_tables):
                    _register_node(nodes, "query_result", "intermediate")
                    edges.append(LineageEdge(
                        edge_id          = _make_edge_id(source, "query_result", path.name),
                        source           = source,
                        target           = "query_result",
                        transformation   = snippet,
                        source_file      = path.name,
                        confidence       = ConfidenceLevel.MEDIUM,
                        confidence_score = 0.7,
                        status           = EdgeStatus.AI_SUGGESTED,
                    ))
    except Exception as e:
        errors.append(f"Error: {e}")
    return ParseResult(file_name=path.name, file_type="sql",
                       edges=edges, nodes=list(nodes.values()), parse_errors=errors)