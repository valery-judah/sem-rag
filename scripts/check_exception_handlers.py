import ast
import sys
from pathlib import Path


def check_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return False

    # Check if FastAPI is instantiated
    has_fastapi = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "FastAPI":
                has_fastapi = True
                break
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "FastAPI":
                has_fastapi = True
                break

    if not has_fastapi:
        return True

    # If FastAPI is instantiated, look for the exception handler
    has_handler = False
    returns_correctly = False

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_exception_handler = False
            for decorator in node.decorator_list:
                # We are looking for @app.exception_handler(Exception)
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "exception_handler":
                        # Check if it's handling Exception
                        for arg in decorator.args:
                            if isinstance(arg, ast.Name) and arg.id == "Exception":
                                is_exception_handler = True
                                break

            if is_exception_handler:
                has_handler = True
                # Now check if it returns ErrorResponse or uses .model_dump()
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        # Look for ErrorResponse in the return value
                        for ret_child in ast.walk(child):
                            if isinstance(ret_child, ast.Name) and ret_child.id == "ErrorResponse":
                                returns_correctly = True
                                break
                            elif (
                                isinstance(ret_child, ast.Attribute)
                                and ret_child.attr == "model_dump"
                            ):
                                pass
                if returns_correctly:
                    break

    if not has_handler:
        print(
            f"FAIL: {filepath} instantiates FastAPI but is missing "
            "an @app.exception_handler(Exception) decorator.",
            file=sys.stderr,
        )
        return False

    if not returns_correctly:
        print(
            f"FAIL: {filepath} has an exception handler, "
            "but does not seem to return an ErrorResponse.",
            file=sys.stderr,
        )
        return False

    return True


def main() -> int:
    src_dir = Path("src")
    if not src_dir.exists():
        print("src directory not found.", file=sys.stderr)
        return 1

    success = True
    for filepath in src_dir.rglob("*.py"):
        if not check_file(filepath):
            success = False

    if success:
        print("All FastAPI instances have correct exception handlers.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
