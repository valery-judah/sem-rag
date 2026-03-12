import ast
from pathlib import Path

PROJECT_ROOT = Path("src")


def resolve_import(module: str, level: int, current_file: str, names: list[str]) -> list[str]:
    paths = []

    if level > 0:
        current_dir = Path(current_file).parent
        for _ in range(level - 1):
            current_dir = current_dir.parent

        if module:
            base_path = current_dir / module.replace(".", "/")
        else:
            base_path = current_dir
    else:
        base_path = PROJECT_ROOT / module.replace(".", "/")

    # Check if base module is a file
    if base_path.with_suffix(".py").exists():
        paths.append(str(base_path.with_suffix(".py")))
    # Check if base module is a directory
    if (base_path / "__init__.py").exists():
        paths.append(str(base_path / "__init__.py"))

        # If it's a package, names could be submodules
        for name in names:
            sub_path = base_path / name
            if sub_path.with_suffix(".py").exists():
                paths.append(str(sub_path.with_suffix(".py")))
            if (sub_path / "__init__.py").exists():
                paths.append(str(sub_path / "__init__.py"))

    return paths


def get_imports(file_path: str):
    tree = ast.parse(Path(file_path).read_text())
    imported_files = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                paths = resolve_import(alias.name, 0, file_path, [])
                imported_files.extend(paths)
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            paths = resolve_import(node.module or "", node.level, file_path, names)
            imported_files.extend(paths)
    return imported_files


if __name__ == "__main__":
    print(get_imports("src/doc_forge/query/service.py"))
