from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path

__all__ = [
    "ImportCycle",
    "assert_acyclic_package_imports",
    "find_package_import_cycles",
]


@dataclass(frozen=True, order=True)
class ImportCycle:
    """One strongly connected set of eager package imports."""

    modules: tuple[str, ...]

    def as_record(self) -> dict[str, list[str]]:
        """Return a serialization-safe cycle record."""
        return {"modules": list(self.modules)}


def find_package_import_cycles(source_root: Path) -> tuple[ImportCycle, ...]:
    """Find cycles formed by imports executed during module initialization."""
    source = source_root.resolve()
    if not source.is_dir():
        raise ValueError(f"source root is not a directory: {source}")
    module_paths = {
        _module_name(source, path): path
        for path in source.rglob("*.py")
        if "__pycache__" not in path.parts
    }
    module_names = frozenset(module_paths)
    dependencies = {
        module_name: _eager_dependencies(
            path,
            module_name=module_name,
            module_names=module_names,
        )
        for module_name, path in module_paths.items()
    }
    components = _strongly_connected_components(dependencies)
    return tuple(
        ImportCycle(tuple(sorted(component)))
        for component in sorted(components, key=lambda value: tuple(sorted(value)))
        if len(component) > 1
    )


def assert_acyclic_package_imports(source_root: Path) -> None:
    """Raise with all initialization-time import cycles."""
    cycles = find_package_import_cycles(source_root)
    if not cycles:
        return
    detail = "\n".join("- " + " -> ".join(cycle.modules) for cycle in cycles)
    raise ValueError(f"eager package import cycles:\n{detail}")


def _eager_dependencies(
    path: Path,
    *,
    module_name: str,
    module_names: frozenset[str],
) -> frozenset[str]:
    syntax_tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=path.as_posix(),
    )
    package_name = (
        module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
    )
    dependencies: set[str] = set()
    for node in _module_initialization_imports(syntax_tree):
        for target in _import_targets(node, package_name=package_name):
            dependency = _owned_module(target, module_names)
            if dependency is not None and dependency != module_name:
                dependencies.add(dependency)
    return frozenset(dependencies)


def _module_initialization_imports(
    tree: ast.Module,
) -> tuple[ast.Import | ast.ImportFrom, ...]:
    imports: list[ast.Import | ast.ImportFrom] = []

    def inspect_statements(statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                imports.append(statement)
                continue
            if isinstance(statement, ast.If):
                if _is_type_checking_guard(statement.test):
                    continue
                inspect_statements(statement.body)
                inspect_statements(statement.orelse)
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                inspect_statements(statement.body)
                inspect_statements(statement.orelse)
                continue
            if isinstance(statement, (ast.Try, ast.TryStar)):
                inspect_statements(statement.body)
                for handler in statement.handlers:
                    inspect_statements(handler.body)
                inspect_statements(statement.orelse)
                inspect_statements(statement.finalbody)
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                inspect_statements(statement.body)
                continue
            if isinstance(statement, ast.Match):
                for case in statement.cases:
                    inspect_statements(case.body)

    inspect_statements(tree.body)
    return tuple(imports)


def _is_type_checking_guard(expression: ast.expr) -> bool:
    return (
        isinstance(expression, ast.Name)
        and expression.id == "TYPE_CHECKING"
        or isinstance(expression, ast.Attribute)
        and expression.attr == "TYPE_CHECKING"
    )


def _import_targets(
    node: ast.Import | ast.ImportFrom,
    *,
    package_name: str,
) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if node.level:
        try:
            base = resolve_name("." * node.level + (node.module or ""), package_name)
        except ImportError:
            return ()
    else:
        base = node.module or ""
    if node.module:
        return (base,)
    return tuple(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")


def _owned_module(target: str, module_names: frozenset[str]) -> str | None:
    candidate = target
    while candidate:
        if candidate in module_names:
            return candidate
        candidate = candidate.rpartition(".")[0]
    return None


def _strongly_connected_components(
    dependencies: dict[str, frozenset[str]],
) -> tuple[frozenset[str], ...]:
    indices: dict[str, int] = {}
    low_links: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    components: list[frozenset[str]] = []

    def visit(module: str) -> None:
        indices[module] = len(indices)
        low_links[module] = indices[module]
        stack.append(module)
        active.add(module)
        for dependency in sorted(dependencies[module]):
            if dependency not in indices:
                visit(dependency)
                low_links[module] = min(low_links[module], low_links[dependency])
            elif dependency in active:
                low_links[module] = min(low_links[module], indices[dependency])
        if low_links[module] != indices[module]:
            return
        component: set[str] = set()
        while stack:
            dependency = stack.pop()
            active.remove(dependency)
            component.add(dependency)
            if dependency == module:
                break
        components.append(frozenset(component))

    for module in sorted(dependencies):
        if module not in indices:
            visit(module)
    return tuple(components)


def _module_name(source_root: Path, path: Path) -> str:
    relative_parts = list(path.relative_to(source_root).with_suffix("").parts)
    if relative_parts[-1] == "__init__":
        relative_parts.pop()
    return ".".join((source_root.name, *relative_parts))
