import ast
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from lineage_parser.models import LineageEdge, LineageNode, ParseResult, ConfidenceLevel, EdgeStatus

READ_CALLS  = {"read_sql", "read_sql_query", "read_sql_table", "read_csv", "read_parquet"}
WRITE_CALLS = {"to_sql", "to_csv", "to_parquet"}


def _make_edge_id(source: str, target: str, filename: str) -> str:
    raw = f"{source}__{target}__{filename}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


class LineageVisitor(ast.NodeVisitor):
    """
    Two-pass AST walker.
    Pass 1: build a global var_to_table map across ALL functions in the file.
    Pass 2: find all to_sql writes and resolve source using the global map.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.edges: List[LineageEdge] = []
        self.nodes: Dict[str, LineageNode] = {}

        # Global map: variable name → table name (across all scopes)
        self._var_to_table: Dict[str, str] = {}

        # Track function signatures: param name → what was passed at call site
        # e.g. write_transactions(clean, engine) → param "df" maps to caller var "clean"
        self._func_params: Dict[str, Dict[str, str]] = {}  # func_name → {param: caller_var}
        self._func_calls: List[ast.Call] = []

    # ── Node registration ─────────────────────────────────────────

    def _register_node(self, name: str, node_type: str):
        if name not in self.nodes:
            self.nodes[name] = LineageNode(node_id=name, node_type=node_type)

    def _add_edge(self, source: str, target: str, snippet: str, lineno: int,
                  confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
                  confidence_score: float = 0.9):
        self._register_node(source, "source")
        self._register_node(target, "intermediate")
        self.edges.append(LineageEdge(
            edge_id          = _make_edge_id(source, target, self.filename),
            source           = source,
            target           = target,
            transformation   = snippet,
            source_file      = self.filename,
            line_number      = lineno,
            confidence       = confidence,
            confidence_score = confidence_score,
            status           = EdgeStatus.AI_SUGGESTED,
        ))

    # ── Pass 1: collect all read_sql assignments globally ─────────

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            func_name = self._get_func_name(node.value)
            if func_name in READ_CALLS:
                table_name = self._extract_string_arg(node.value, 0)
                if table_name and node.targets:
                    var_name = self._get_assign_target_name(node.targets[0])
                    if var_name:
                        self._var_to_table[var_name] = table_name
                        self._register_node(table_name, "source")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Collect function param names and map them to positional argument names
        used at call sites discovered later. Also walk the function body
        to find inner read/write calls.
        """
        self._func_params[node.name] = {
            arg.arg: idx for idx, arg in enumerate(node.args.args)
        }
        self.generic_visit(node)

    # ── Pass 1b: collect all call sites globally ──────────────────

    def visit_Call(self, node: ast.Call):
        """Record every function call so we can resolve param→table mappings."""
        func_name = self._get_func_name(node)
        if func_name and func_name not in READ_CALLS and func_name not in WRITE_CALLS:
            # Map positional args at call site to param names in function def
            if func_name in self._func_params:
                param_map = self._func_params[func_name]
                for param_name, idx in param_map.items():
                    if idx < len(node.args):
                        caller_var = self._get_assign_target_name(node.args[idx])
                        if caller_var and caller_var in self._var_to_table:
                            # param "df" inside the function = caller_var "clean" = table "transactions"
                            self._var_to_table[param_name] = self._var_to_table[caller_var]
        self.generic_visit(node)

    # ── Pass 2: find to_sql writes and resolve source ─────────────

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call):
            call = node.value
            func_name = self._get_func_name(call)
            if func_name in WRITE_CALLS:
                target_table = self._extract_string_arg(call, 0)
                if isinstance(call.func, ast.Attribute):
                    obj_name = self._get_assign_target_name(call.func.value)
                    # Resolve: obj_name could be "df" (param) → look up in global map
                    resolved_source = self._var_to_table.get(obj_name)

                    if resolved_source and target_table:
                        snippet = ast.unparse(node)
                        self._add_edge(resolved_source, target_table, snippet, node.lineno)
                    elif obj_name and target_table:
                        # Fallback: use obj_name as-is but flag as MEDIUM confidence
                        snippet = ast.unparse(node)
                        self._add_edge(
                            obj_name, target_table, snippet, node.lineno,
                            confidence=ConfidenceLevel.MEDIUM,
                            confidence_score=0.6
                        )
        self.generic_visit(node)

    # ── Utilities ─────────────────────────────────────────────────

    def _get_func_name(self, call: ast.Call) -> str:
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        if isinstance(call.func, ast.Name):
            return call.func.id
        return ""

    def _extract_string_arg(self, call: ast.Call, index: int) -> Optional[str]:
        if len(call.args) > index and isinstance(call.args[index], ast.Constant):
            return str(call.args[index].value)
        for kw in call.keywords:
            if kw.arg in ("name", "sql", "table_name") and isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
        return None

    def _get_assign_target_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def parse_python_file(filepath: str) -> ParseResult:
    path   = Path(filepath)
    errors: List[str] = []
    edges:  List[LineageEdge] = []
    nodes:  List[LineageNode] = []
    try:
        tree    = ast.parse(path.read_text())
        visitor = LineageVisitor(filename=path.name)
        visitor.visit(tree)
        edges = visitor.edges
        nodes = list(visitor.nodes.values())
    except SyntaxError as e:
        errors.append(f"SyntaxError: {e}")
    except Exception as e:
        errors.append(f"Error: {e}")
    return ParseResult(file_name=path.name, file_type="python",
                       edges=edges, nodes=nodes, parse_errors=errors)