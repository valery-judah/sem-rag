import ast
import os
from pathlib import Path


def find_logs(d):
    for root, _, files in os.walk(d):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            try:
                content = path.read_text()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                        if node.func.attr in ("info", "warning", "error", "exception", "debug"):
                            msg = None
                            if (
                                node.args
                                and isinstance(node.args[0], ast.Constant)
                                and isinstance(node.args[0].value, str)
                            ):
                                msg = node.args[0].value
                            else:
                                for kw in node.keywords:
                                    if (
                                        kw.arg == "event"
                                        and isinstance(kw.value, ast.Constant)
                                        and isinstance(kw.value.value, str)
                                    ):
                                        msg = kw.value.value
                            if msg:
                                parts = msg.split(".")
                                if len(parts) < 3 or " " in msg:
                                    print(f"{path}:{node.lineno}: {msg}")
            except Exception:
                pass


find_logs("src")
find_logs("e2e")
find_logs("tests")
