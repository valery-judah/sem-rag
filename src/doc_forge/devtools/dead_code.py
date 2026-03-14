from __future__ import annotations

import argparse
import ast
import sys
from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

BucketName = Literal[
    "api_reachable",
    "repo_entrypoint_only",
    "test_only",
    "unreferenced",
]

DEFAULT_API_ROOTS = (Path("src/doc_forge/app/api.py"),)
DEFAULT_REPO_ENTRYPOINT_ROOTS = (
    Path("src/doc_forge/runtime.py"),
    Path("src/doc_forge/lifecycle/worker.py"),
    Path("src/doc_forge/devtools/secret_scan.py"),
)
BUCKET_ORDER: tuple[BucketName, ...] = (
    "api_reachable",
    "repo_entrypoint_only",
    "test_only",
    "unreferenced",
)


@dataclass(frozen=True)
class ResolvedTarget:
    kind: Literal["class", "module"]
    value: str


@dataclass(frozen=True)
class ClassTarget:
    symbol: str


@dataclass(frozen=True)
class ModuleTarget:
    module_name: str


@dataclass(frozen=True)
class ExportTarget:
    module_name: str
    export_name: str


BindingTarget = ClassTarget | ModuleTarget | ExportTarget


@dataclass(frozen=True)
class ClassDefinition:
    symbol: str
    module_name: str
    class_name: str
    path: Path


@dataclass(frozen=True)
class ClassFinding:
    symbol: str
    class_name: str
    path: Path
    bucket: BucketName
    via_root: str | None


@dataclass(frozen=True)
class AnalysisResult:
    findings_by_bucket: dict[BucketName, tuple[ClassFinding, ...]]


@dataclass
class ModuleInfo:
    name: str
    path: Path
    is_package: bool
    tree: ast.Module
    class_definitions: dict[str, ClassDefinition] = field(default_factory=lambda: {})
    top_level_bindings: dict[str, set[BindingTarget]] = field(default_factory=lambda: {})
    local_imports: set[str] = field(default_factory=lambda: set())


@dataclass(frozen=True)
class RootGroup:
    name: str
    roots: tuple[Path, ...]


@dataclass
class ProjectIndex:
    project_root: Path
    modules_by_name: dict[str, ModuleInfo]
    modules_by_path: dict[Path, ModuleInfo]
    class_definitions: dict[str, ClassDefinition]
    _export_cache: dict[tuple[str, str], frozenset[ResolvedTarget]] = field(default_factory=lambda: {})
    _reference_cache: dict[str, frozenset[str]] = field(default_factory=lambda: {})
    _closure_cache: dict[str, frozenset[str]] = field(default_factory=lambda: {})

    def resolve_export(self, module_name: str, export_name: str) -> frozenset[ResolvedTarget]:
        key = (module_name, export_name)
        cached = self._export_cache.get(key)
        if cached is not None:
            return cached

        cached = self._resolve_export(module_name, export_name, seen=set())
        self._export_cache[key] = cached
        return cached

    def _resolve_export(
        self,
        module_name: str,
        export_name: str,
        *,
        seen: set[tuple[str, str]],
    ) -> frozenset[ResolvedTarget]:
        key = (module_name, export_name)
        if key in seen:
            return frozenset()
        seen.add(key)

        module = self.modules_by_name.get(module_name)
        if module is None:
            return frozenset()

        if export_name in module.class_definitions:
            return frozenset(
                {
                    ResolvedTarget(
                        kind="class",
                        value=module.class_definitions[export_name].symbol,
                    )
                }
            )

        resolved: set[ResolvedTarget] = set()
        for target in module.top_level_bindings.get(export_name, set()):
            resolved.update(self._resolve_binding_target(target, seen=seen))

        return frozenset(resolved)

    def _resolve_binding_target(
        self,
        target: BindingTarget,
        *,
        seen: set[tuple[str, str]],
    ) -> frozenset[ResolvedTarget]:
        if isinstance(target, ClassTarget):
            return frozenset({ResolvedTarget(kind="class", value=target.symbol)})
        if isinstance(target, ModuleTarget):
            if target.module_name in self.modules_by_name:
                return frozenset({ResolvedTarget(kind="module", value=target.module_name)})
            return frozenset()
        return self._resolve_export(target.module_name, target.export_name, seen=seen)

    def resolve_name_targets(self, module_name: str, name: str) -> frozenset[ResolvedTarget]:
        module = self.modules_by_name[module_name]
        resolved: set[ResolvedTarget] = set()

        class_definition = module.class_definitions.get(name)
        if class_definition is not None:
            resolved.add(ResolvedTarget(kind="class", value=class_definition.symbol))

        for target in module.top_level_bindings.get(name, set()):
            resolved.update(self._resolve_binding_target(target, seen=set()))

        return frozenset(resolved)

    def resolve_chain(self, module_name: str, chain: Sequence[str]) -> frozenset[str]:
        if not chain:
            return frozenset()

        current_targets = set(self.resolve_name_targets(module_name, chain[0]))
        if not current_targets:
            return frozenset()

        class_symbols: set[str] = set()
        for index, attribute_name in enumerate(chain[1:], start=1):
            next_targets: set[ResolvedTarget] = set()
            for target in current_targets:
                if target.kind == "class":
                    class_symbols.add(target.value)
                    continue

                submodule_name = f"{target.value}.{attribute_name}"
                if submodule_name in self.modules_by_name:
                    next_targets.add(ResolvedTarget(kind="module", value=submodule_name))
                    continue

                exported = self.resolve_export(target.value, attribute_name)
                if exported:
                    next_targets.update(exported)
                    continue

                if index == len(chain) - 1:
                    continue

            current_targets = next_targets
            if not current_targets:
                break

        for target in current_targets:
            if target.kind == "class":
                class_symbols.add(target.value)

        return frozenset(class_symbols)

    def referenced_classes(self, module_name: str) -> frozenset[str]:
        cached = self._reference_cache.get(module_name)
        if cached is not None:
            return cached

        module = self.modules_by_name[module_name]
        referenced: set[str] = set()
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Name):
                referenced.update(
                    target.value
                    for target in self.resolve_name_targets(module_name, node.id)
                    if target.kind == "class"
                )
            elif isinstance(node, ast.Attribute):
                chain = _attribute_chain(node)
                if chain is not None:
                    referenced.update(self.resolve_chain(module_name, chain))

        cached = frozenset(referenced)
        self._reference_cache[module_name] = cached
        return cached

    def transitive_module_closure(self, root_module_name: str) -> frozenset[str]:
        cached = self._closure_cache.get(root_module_name)
        if cached is not None:
            return cached

        if root_module_name not in self.modules_by_name:
            new_cached: frozenset[str] = frozenset()
            self._closure_cache[root_module_name] = new_cached
            return new_cached

        visited: set[str] = set()
        queue: deque[str] = deque([root_module_name])
        while queue:
            module_name = queue.popleft()
            if module_name in visited:
                continue
            visited.add(module_name)
            module = self.modules_by_name[module_name]
            for imported_module in sorted(module.local_imports):
                if imported_module in self.modules_by_name and imported_module not in visited:
                    queue.append(imported_module)

        cached = frozenset(visited)
        self._closure_cache[root_module_name] = cached
        return cached


def build_project_index(project_root: Path) -> ProjectIndex:
    project_root = project_root.resolve()
    modules_by_name: dict[str, ModuleInfo] = {}
    modules_by_path: dict[Path, ModuleInfo] = {}
    class_definitions: dict[str, ClassDefinition] = {}

    for root_dir in _iter_existing_dirs(project_root / "src", project_root / "tests"):
        for path in sorted(root_dir.rglob("*.py")):
            module_name = _module_name_for_path(path=path, root_dir=root_dir)
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            module = ModuleInfo(
                name=module_name,
                path=path.resolve(),
                is_package=path.name == "__init__.py",
                tree=tree,
            )
            modules_by_name[module_name] = module
            modules_by_path[module.path] = module

    index = ProjectIndex(
        project_root=project_root,
        modules_by_name=modules_by_name,
        modules_by_path=modules_by_path,
        class_definitions=class_definitions,
    )

    for module in index.modules_by_name.values():
        module.class_definitions = _collect_class_definitions(module)
        class_definitions.update(
            {definition.symbol: definition for definition in module.class_definitions.values()}
        )
        module.top_level_bindings = _collect_top_level_bindings(module, index)
        module.local_imports = _collect_local_imports(module, index)

    return index


def analyze_project(
    project_root: Path,
    *,
    api_roots: Sequence[Path] | None = None,
    repo_entrypoint_roots: Sequence[Path] | None = None,
    test_roots: Sequence[Path] | None = None,
) -> AnalysisResult:
    index = build_project_index(project_root)
    groups = _root_groups(
        project_root=project_root,
        api_roots=api_roots,
        repo_entrypoint_roots=repo_entrypoint_roots,
        test_roots=test_roots,
    )

    references_by_root: dict[str, frozenset[str]] = {}
    for group in groups:
        for root in group.roots:
            module = index.modules_by_path.get((project_root / root).resolve())
            if module is None:
                continue
            referenced: set[str] = set()
            for module_name in index.transitive_module_closure(module.name):
                referenced.update(index.referenced_classes(module_name))
            references_by_root[root.as_posix()] = frozenset(referenced)

    findings_by_bucket: dict[BucketName, list[ClassFinding]] = {
        bucket: [] for bucket in BUCKET_ORDER
    }
    for symbol, definition in sorted(
        index.class_definitions.items(),
        key=lambda item: (item[1].path.as_posix(), item[1].class_name),
    ):
        if not definition.path.is_relative_to((project_root / "src").resolve()):
            continue

        bucket, via_root = _classify_symbol(
            symbol=symbol,
            groups=groups,
            references_by_root=references_by_root,
        )
        findings_by_bucket[bucket].append(
            ClassFinding(
                symbol=symbol,
                class_name=definition.class_name,
                path=definition.path,
                bucket=bucket,
                via_root=via_root,
            )
        )

    return AnalysisResult(
        findings_by_bucket={bucket: tuple(findings_by_bucket[bucket]) for bucket in BUCKET_ORDER}
    )


def render_text_report(result: AnalysisResult, *, project_root: Path) -> str:
    lines = [f"API-rooted dead-class analysis for {project_root.resolve()}"]
    for bucket in BUCKET_ORDER:
        findings = result.findings_by_bucket[bucket]
        lines.append("")
        lines.append(f"[{bucket}] {len(findings)}")
        for finding in findings:
            relative_path = finding.path.relative_to(project_root.resolve()).as_posix()
            via_text = " via none" if finding.via_root is None else f" via {finding.via_root}"
            lines.append(f"- {relative_path}: {finding.class_name}{via_text}")
    return "\n".join(lines)


def _classify_symbol(
    *,
    symbol: str,
    groups: Sequence[RootGroup],
    references_by_root: dict[str, frozenset[str]],
) -> tuple[BucketName, str | None]:
    for group in groups:
        for root in group.roots:
            root_key = root.as_posix()
            if symbol in references_by_root.get(root_key, frozenset()):
                if group.name == "api_reachable":
                    return "api_reachable", root_key
                if group.name == "repo_entrypoint_only":
                    return "repo_entrypoint_only", root_key
                return "test_only", root_key
    return "unreferenced", None


def _root_groups(
    *,
    project_root: Path,
    api_roots: Sequence[Path] | None,
    repo_entrypoint_roots: Sequence[Path] | None,
    test_roots: Sequence[Path] | None,
) -> tuple[RootGroup, ...]:
    normalized_test_roots = tuple(
        _normalize_relative_path(project_root, path)
        for path in (
            test_roots if test_roots is not None else sorted((project_root / "tests").rglob("*.py"))
        )
    )
    return (
        RootGroup(
            name="api_reachable",
            roots=tuple(
                _normalize_relative_path(project_root, path)
                for path in (api_roots or DEFAULT_API_ROOTS)
            ),
        ),
        RootGroup(
            name="repo_entrypoint_only",
            roots=tuple(
                _normalize_relative_path(project_root, path)
                for path in (repo_entrypoint_roots or DEFAULT_REPO_ENTRYPOINT_ROOTS)
            ),
        ),
        RootGroup(name="test_only", roots=normalized_test_roots),
    )


def _normalize_relative_path(project_root: Path, path: Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path.resolve().relative_to(project_root.resolve())
    return path


def _iter_existing_dirs(*paths: Path) -> Iterable[Path]:
    for path in paths:
        if path.exists():
            yield path


def _module_name_for_path(*, path: Path, root_dir: Path) -> str:
    relative = path.relative_to(root_dir)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    if root_dir.name == "tests":
        return ".".join(("tests", *parts)) if parts else "tests"
    return ".".join(parts)


def _collect_class_definitions(module: ModuleInfo) -> dict[str, ClassDefinition]:
    definitions: dict[str, ClassDefinition] = {}
    for node in module.tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        symbol = f"{module.name}.{node.name}"
        definitions[node.name] = ClassDefinition(
            symbol=symbol,
            module_name=module.name,
            class_name=node.name,
            path=module.path,
        )
    return definitions


def _collect_top_level_bindings(
    module: ModuleInfo,
    index: ProjectIndex,
) -> dict[str, set[BindingTarget]]:
    bindings: dict[str, set[BindingTarget]] = {}
    for class_name, definition in module.class_definitions.items():
        bindings.setdefault(class_name, set()).add(ClassTarget(symbol=definition.symbol))

    for node in module.tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_name, target = _binding_for_import(alias, index)
                if bound_name is None or target is None:
                    continue
                bindings.setdefault(bound_name, set()).add(target)
        elif isinstance(node, ast.ImportFrom):
            resolved_module = _resolve_imported_module_name(
                current_module=module.name,
                current_is_package=module.is_package,
                module_name=node.module,
                level=node.level,
            )
            if resolved_module is None:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound_name, target = _binding_for_from_import(
                    resolved_module=resolved_module,
                    alias=alias,
                    index=index,
                )
                if bound_name is None or target is None:
                    continue
                bindings.setdefault(bound_name, set()).add(target)

    return bindings


def _binding_for_import(
    alias: ast.alias,
    index: ProjectIndex,
) -> tuple[str | None, BindingTarget | None]:
    imported_name = alias.name
    if "." in imported_name and alias.asname is None:
        package_name = imported_name.split(".", maxsplit=1)[0]
        if package_name in index.modules_by_name:
            return package_name, ModuleTarget(module_name=package_name)
        return None, None

    if imported_name in index.modules_by_name:
        return alias.asname or imported_name, ModuleTarget(module_name=imported_name)

    return None, None


def _binding_for_from_import(
    *,
    resolved_module: str,
    alias: ast.alias,
    index: ProjectIndex,
) -> tuple[str | None, BindingTarget | None]:
    submodule_name = f"{resolved_module}.{alias.name}"
    bound_name = alias.asname or alias.name
    if submodule_name in index.modules_by_name:
        return bound_name, ModuleTarget(module_name=submodule_name)
    if resolved_module in index.modules_by_name:
        return bound_name, ExportTarget(module_name=resolved_module, export_name=alias.name)
    return None, None


def _collect_local_imports(module: ModuleInfo, index: ProjectIndex) -> set[str]:
    imported_modules: set[str] = set()
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in index.modules_by_name:
                    imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved_module = _resolve_imported_module_name(
                current_module=module.name,
                current_is_package=module.is_package,
                module_name=node.module,
                level=node.level,
            )
            if resolved_module is None:
                continue
            if resolved_module in index.modules_by_name:
                imported_modules.add(resolved_module)
            for alias in node.names:
                if alias.name == "*":
                    continue
                submodule_name = f"{resolved_module}.{alias.name}"
                if submodule_name in index.modules_by_name:
                    imported_modules.add(submodule_name)
    return imported_modules


def _resolve_imported_module_name(
    *,
    current_module: str,
    current_is_package: bool,
    module_name: str | None,
    level: int,
) -> str | None:
    if level == 0:
        return module_name

    current_parts = current_module.split(".")
    if not current_is_package:
        current_parts = current_parts[:-1]

    if level - 1 > len(current_parts):
        return None
    base_parts = current_parts[: len(current_parts) - (level - 1)]
    if module_name:
        base_parts.extend(module_name.split("."))
    return ".".join(part for part in base_parts if part)


def _attribute_chain(node: ast.Attribute) -> tuple[str, ...] | None:
    parts: list[str] = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    parts.reverse()
    return tuple(parts)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify classes unreachable from API roots.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root to analyze.",
    )
    parser.add_argument(
        "--roots",
        choices=("api",),
        default="api",
        help="Primary live root set for dead-class analysis.",
    )
    parser.add_argument(
        "--report",
        choices=("classified",),
        default="classified",
        help="Report format to render.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    project_root = Path(args.project_root).resolve()
    result = analyze_project(project_root)
    print(render_text_report(result, project_root=project_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
