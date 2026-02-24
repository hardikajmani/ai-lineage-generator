import hashlib
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
    """Parse a SQL file and extract source → target lineage edges using sqlglot."""
    path   = Path(filepath)
    errors = []
    edges  = []
    nodes  = {}

    try:
        sql_text   = path.read_text()
        statements = sqlglot.parse(sql_text, dialect="ansi")

        for stmt in statements:
            if stmt is None:
                continue

            # ── Find INSERT INTO target ──────────────────────────
            insert_target = None
            if isinstance(stmt, exp.Insert):
                insert_target = stmt.find(exp.Table)
                if insert_target:
                    insert_target = insert_target.name
                    _register_node(nodes, insert_target, "output")

            # ── Find all FROM / JOIN sources ─────────────────────
            source_tables = []
            for table in stmt.find_all(exp.Table):
                name = table.name
                if name and name != insert_target:
                    source_tables.append(name)
                    _register_node(nodes, name, "source")

            # ── Build edges: each source → target ─────────────────
            if insert_target and source_tables:
                # De-duplicate sources
                for source in set(source_tables):
                    snippet = sql_text[:300].replace("\n", " ").strip()
                    edge = LineageEdge(
                        edge_id          = _make_edge_id(source, insert_target, path.name),
                        source           = source,
                        target           = insert_target,
                        transformation   = snippet,
                        source_file      = path.name,
                        line_number      = None,
                        confidence       = ConfidenceLevel.HIGH,
                        confidence_score = 0.92,
                        status           = EdgeStatus.AI_SUGGESTED,
                    )
                    edges.append(edge)

            # ── Handle plain SELECT (no INSERT) ───────────────────
            elif not insert_target and source_tables:
                for source in set(source_tables):
                    _register_node(nodes, source, "source")
                    _register_node(nodes, "query_result", "intermediate")
                    snippet = sql_text[:300].replace("\n", " ").strip()
                    edge = LineageEdge(
                        edge_id          = _make_edge_id(source, "query_result", path.name),
                        source           = source,
                        target           = "query_result",
                        transformation   = snippet,
                        source_file      = path.name,
                        confidence       = ConfidenceLevel.MEDIUM,
                        confidence_score = 0.7,
                        status           = EdgeStatus.AI_SUGGESTED,
                    )
                    edges.append(edge)

    except Exception as e:
        errors.append(f"Error parsing SQL in {filepath}: {e}")

    return ParseResult(
        file_name    = path.name,
        file_type    = "sql",
        edges        = edges,
        nodes        = list(nodes.values()),
        parse_errors = errors,
    )
