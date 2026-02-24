import ast
import hashlib
from pathlib import Path
from typing import Optional, List
from lineage_parser.models import LineageEdge, LineageNode, ParseResult, ConfidenceLevel, EdgeStatus

# Table-producing and table-consuming patterns in pandas/sqlalchemy
READ_CALLS  = {"read_sql", "read_sql_query", "read_sql_table", "read_csv", "read_parquet"}
WRITE_CALLS = {"to_sql", "to_csv", "to_parquet"}


def _make_edge_id(source: str, target: str, filename: str) -> str:
    raw = f"{source}__{target}__{filename}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


class LineageVisitor(ast.NodeVisitor):
    """Walk a Python AST and extract source → target lineage edges."""

    def __init__(self, filename: str):
        self.filename = filename
        self.edges: list[LineageEdge] = []
        self.nodes: dict[str, LineageNode] = {}
        self._var_to_table: dict[str, str] = {}  # maps variable name → table name

    # ── Helpers ──────────────────────────────────────────────────

    def _register_node(self, name: str, node_type: str):
        if name not in self.nodes:
            self.nodes[name] = LineageNode(node_id=name, node_type=node_type)

    def _add_edge(self, source: str, target: str, snippet: str, lineno: int):
        self._register_node(source, "source")
        self._register_node(target, "intermediate")
        edge = LineageEdge(
            edge_id        = _make_edge_id(source, target, self.filename),
            source         = source,
            target         = target,
            transformation = snippet,
            source_file    = self.filename,
            line_number    = lineno,
            confidence     = ConfidenceLevel.HIGH,
            confidence_score = 0.9,
            status         = EdgeStatus.AI_SUGGESTED,
        )
        self.edges.append(edge)

    # ── Visitor methods ───────────────────────────────────────────

    def visit_Assign(self, node: ast.Assign):
        """Catch: df = pd.read_sql("table_name", engine)"""
        if isinstance(node.value, ast.Call):
            call = node.value
            func_name = self._get_func_name(call)

            if func_name in READ_CALLS:
                table_name = self._extract_string_arg(call, 0)
                if table_name and node.targets:
                    var_name = self._get_target_name(node.targets[0])
                    if var_name:
                        self._var_to_table[var_name] = table_name
                        self._register_node(table_name, "source")

        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr):
        """Catch: df.to_sql("target_table", engine)"""
        if isinstance(node.value, ast.Call):
            call = node.value
            func_name = self._get_func_name(call)

            if func_name in WRITE_CALLS:
                target_table = self._extract_string_arg(call, 0)
                # Find the variable being written (the object calling .to_sql)
                if isinstance(call.func, ast.Attribute):
                    obj_name = self._get_target_name(call.func.value)
                    source_table = self._var_to_table.get(obj_name, obj_name or "unknown")
                    if target_table and source_table:
                        snippet = ast.unparse(node)
                        self._add_edge(source_table, target_table, snippet, node.lineno)

        self.generic_visit(node)

    # ── Utility methods ───────────────────────────────────────────

    def _get_func_name(self, call: ast.Call) -> str:
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        if isinstance(call.func, ast.Name):
            return call.func.id
        return ""

    def _extract_string_arg(self, call: ast.Call, index: int) -> Optional[str]:
        if len(call.args) > index and isinstance(call.args[index], ast.Constant):
            return str(call.args[index].value)
        # Also check keyword args (e.g. name="table")
        for kw in call.keywords:
            if kw.arg in ("name", "sql", "table_name") and isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
        return None

    def _get_target_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def parse_python_file(filepath: str) -> ParseResult:
    """Parse a Python file and extract lineage edges."""
    path     = Path(filepath)
    errors   = []
    edges    = []
    nodes    = []

    try:
        source_code = path.read_text()
        tree        = ast.parse(source_code)
        visitor     = LineageVisitor(filename=path.name)
        visitor.visit(tree)
        edges = visitor.edges
        nodes = list(visitor.nodes.values())
    except SyntaxError as e:
        errors.append(f"SyntaxError in {filepath}: {e}")
    except Exception as e:
        errors.append(f"Unexpected error parsing {filepath}: {e}")

    return ParseResult(
        file_name   = path.name,
        file_type   = "python",
        edges       = edges,
        nodes       = nodes,
        parse_errors= errors,
    )
