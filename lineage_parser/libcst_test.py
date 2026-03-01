import ast
import libcst as cst
from libcst import metadata


SOURCE = """
import pandas as pd

def transform(df):
    data = df[df["col"] > 0]
    return data

df = pd.read_csv("important.csv")
data = transform(df)
data.to_csv("important2.csv", index=False)
"""


def _str_literal(node: cst.CSTNode):
    # LibCST represents string literals as SimpleString; .value includes quotes.
    if isinstance(node, cst.SimpleString):
        try:
            return ast.literal_eval(node.value)
        except Exception:
            return None
    return None


class LineageCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (
        metadata.ScopeProvider,
        metadata.PositionProvider,
    )

    def __init__(self):
        self.edges = []  # (src, dst, kind, location)
        self.fn_param = {}   # fn_name -> first_param_name
        self.fn_return = {}  # fn_name -> returned_name (only handles: return <Name>)

    def _scope_id(self, node: cst.CSTNode) -> str:
        scope = self.get_metadata(metadata.ScopeProvider, node)
        return f"{type(scope).__name__}@{id(scope)}"

    def _var(self, name_node: cst.Name) -> str:
        return f"var({self._scope_id(name_node)}::{name_node.value})"

    def _file(self, path: str) -> str:
        return f"file({path})"

    def _loc(self, node: cst.CSTNode) -> str:
        pos = self.get_metadata(metadata.PositionProvider, node)
        return f"{pos.start.line}:{pos.start.column}"

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        fn = node.name.value
        if node.params.params:
            p0 = node.params.params[0].name.value
            self.fn_param[fn] = p0

    def visit_Return(self, node: cst.Return) -> None:
        # Only record: return <Name>
        if isinstance(node.value, cst.Name):
            # Find nearest enclosing FunctionDef name by walking parents is more work;
            # for simplicity in this demo, we rely on "current function" not tracked.
            # So we record only if return is inside a function body we later match by name
            # using a crude heuristic in leave_FunctionDef below.
            pass

    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        fn = original_node.name.value
        returned = None
        for stmt in original_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for small in stmt.body:
                    if isinstance(small, cst.Return) and isinstance(small.value, cst.Name):
                        returned = small.value.value
        if returned:
            self.fn_return[fn] = returned

    def visit_Assign(self, node: cst.Assign) -> None:
        # Handle only simple: <Name> = <expr>
        if len(node.targets) != 1:
            return
        target = node.targets[0].target
        if not isinstance(target, cst.Name):
            return

        lhs = self._var(target)
        loc = self._loc(node)

        # Case A: df = pd.read_csv("important.csv")
        if isinstance(node.value, cst.Call) and isinstance(node.value.func, cst.Attribute):
            method = node.value.func.attr.value

            if method == "read_csv":
                if node.value.args:
                    path = _str_literal(node.value.args[0].value)
                    if path:
                        self.edges.append((self._file(path), lhs, "read_csv", loc))
                        return

            # Case B: data = transform(df)  (basic arg->param, return->lhs demo)
        if isinstance(node.value, cst.Call) and isinstance(node.value.func, cst.Name):
            fn = node.value.func.value
            if fn in self.fn_param and node.value.args:
                arg0 = node.value.args[0].value
                if isinstance(arg0, cst.Name):
                    arg_var = self._var(arg0)
                    param_name = self.fn_param[fn]
                    param_var = f"var({fn}::<param>::{param_name})"
                    self.edges.append((arg_var, param_var, "arg_to_param", loc))

                if fn in self.fn_return:
                    ret_name = self.fn_return[fn]
                    ret_var = f"var({fn}::<return>::{ret_name})"
                    self.edges.append((ret_var, lhs, "return_to_lhs", loc))
                return

        # Case C: x = y  (simple rename/alias)
        if isinstance(node.value, cst.Name):
            rhs = self._var(node.value)
            self.edges.append((rhs, lhs, "assign", loc))
            return
        
        if isinstance(node.value, cst.Subscript):
            src = node.value.value          # the df part of df[...]
            
        if isinstance(src, cst.Name):
            rhs = self._var(src)
            self.edges.append((rhs, lhs, "subscript_derive", loc))
            return

        # Also handle method calls that return a derived DataFrame: df2 = df.rename(...)
        if isinstance(node.value, cst.Call) and isinstance(node.value.func, cst.Attribute):
            receiver = node.value.func.value
            if isinstance(receiver, cst.Name):
                rhs = self._var(receiver)
                self.edges.append((rhs, lhs, "method_derive", loc))
                return


    def visit_Expr(self, node: cst.Expr) -> None:
        # Handle only: <Name>.to_csv("important2.csv")
        if not isinstance(node.value, cst.Call):
            return
        call = node.value
        if not isinstance(call.func, cst.Attribute):
            return
        if call.func.attr.value != "to_csv":
            return
        if not isinstance(call.func.value, cst.Name):
            return

        df_var = self._var(call.func.value)
        loc = self._loc(node)
        if call.args:
            path = _str_literal(call.args[0].value)
            if path:
                self.edges.append((df_var, self._file(path), "to_csv", loc))


def main():
    module = cst.parse_module(SOURCE)
    wrapper = metadata.MetadataWrapper(module)  # required to resolve metadata providers
    collector = LineageCollector()
    wrapper.visit(collector)

    print("=== Edges (src -> dst) ===")
    for src, dst, kind, loc in collector.edges:
        print(f"[{kind}] {src}  ->  {dst}   @ {loc}")


if __name__ == "__main__":
    main()
