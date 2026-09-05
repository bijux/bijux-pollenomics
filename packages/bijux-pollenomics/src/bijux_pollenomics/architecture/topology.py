from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path

__all__ = [
    "PackageFacadePolicy",
    "RepositoryTopologyPolicy",
    "TopologyViolation",
    "UnitTestDomainPolicy",
    "assert_repository_topology",
    "audit_repository_topology",
    "repository_topology_policy",
]


@dataclass(frozen=True)
class PackageFacadePolicy:
    """Allowed direct modules for one deliberately narrow package facade."""

    package: str
    allowed_files: tuple[str, ...]


@dataclass(frozen=True)
class UnitTestDomainPolicy:
    """Explicit owner for a unit-test domain without a same-named package."""

    test_domain: str
    source_path: str


@dataclass(frozen=True)
class RepositoryTopologyPolicy:
    """Durable constraints that keep source and unit-test ownership legible."""

    maximum_direct_modules: int
    maximum_direct_test_modules: int
    forbidden_package_names: frozenset[str]
    source_root_files: tuple[str, ...]
    package_facades: tuple[PackageFacadePolicy, ...]
    unit_test_domains: tuple[UnitTestDomainPolicy, ...]


@dataclass(frozen=True, order=True)
class TopologyViolation:
    """One deterministic repository-topology policy failure."""

    code: str
    path: str
    detail: str

    def as_record(self) -> dict[str, str]:
        """Return a serialization-safe diagnostic record."""
        return {"code": self.code, "path": self.path, "detail": self.detail}


def repository_topology_policy() -> RepositoryTopologyPolicy:
    """Return the checked-in ownership and package-density policy."""
    return RepositoryTopologyPolicy(
        maximum_direct_modules=10,
        maximum_direct_test_modules=10,
        forbidden_package_names=frozenset(
            {
                "common",
                "foundation",
                "helpers",
                "misc",
                "pipeline",
                "shared",
                "temporary",
                "utils",
            }
        ),
        source_root_files=(
            "__init__.py",
            "__main__.py",
            "cli.py",
            "config.py",
            "publication_policy.py",
        ),
        package_facades=(
            PackageFacadePolicy("adna", ("__init__.py", "api.py")),
            PackageFacadePolicy("analysis", ("__init__.py",)),
            PackageFacadePolicy("collection", ("__init__.py", "api.py")),
        ),
        unit_test_domains=(UnitTestDomainPolicy("configuration", "config.py"),),
    )


def audit_repository_topology(
    source_root: Path,
    unit_test_root: Path,
    *,
    policy: RepositoryTopologyPolicy | None = None,
) -> tuple[TopologyViolation, ...]:
    """Audit package density, naming, facades, and unit-test ownership."""
    source = _existing_directory(source_root, "source root")
    tests = _existing_directory(unit_test_root, "unit-test root")
    active_policy = policy or repository_topology_policy()
    violations: list[TopologyViolation] = []

    source_directories = _python_directories(source)
    for directory in source_directories:
        relative = directory.relative_to(source)
        display_path = _display_path(relative)
        direct_modules = tuple(
            path
            for path in sorted(directory.glob("*.py"))
            if path.name != "__init__.py"
        )
        if relative.parts and not (directory / "__init__.py").is_file():
            violations.append(
                TopologyViolation(
                    "missing_package_marker",
                    display_path,
                    "a source directory containing Python modules must own __init__.py",
                )
            )
        if len(direct_modules) > active_policy.maximum_direct_modules:
            violations.append(
                TopologyViolation(
                    "crowded_package",
                    display_path,
                    (
                        f"{len(direct_modules)} direct modules exceed the "
                        f"limit of {active_policy.maximum_direct_modules}"
                    ),
                )
            )
        forbidden_parts = sorted(
            set(relative.parts) & active_policy.forbidden_package_names
        )
        if forbidden_parts:
            violations.append(
                TopologyViolation(
                    "ambiguous_package_name",
                    display_path,
                    "forbidden ownership name(s): " + ", ".join(forbidden_parts),
                )
            )

        initializer = directory / "__init__.py"
        if initializer.is_file() and _has_wildcard_import(initializer):
            violations.append(
                TopologyViolation(
                    "wildcard_package_export",
                    display_path,
                    "package initializers must export an explicit public surface",
                )
            )

    _audit_allowed_files(
        source,
        Path(),
        active_policy.source_root_files,
        "source_root_module_leak",
        violations,
    )
    for facade in active_policy.package_facades:
        _audit_allowed_files(
            source,
            Path(facade.package),
            facade.allowed_files,
            "facade_module_leak",
            violations,
        )
    _audit_relative_imports(source, violations)

    for test_path in sorted(tests.glob("test_*.py")):
        violations.append(
            TopologyViolation(
                "flat_unit_test",
                test_path.relative_to(tests).as_posix(),
                "unit tests must live under their production ownership domain",
            )
        )

    for directory in _test_directories(tests):
        relative = directory.relative_to(tests)
        direct_test_modules = tuple(sorted(directory.glob("test_*.py")))
        if not (directory / "__init__.py").is_file():
            violations.append(
                TopologyViolation(
                    "missing_test_package_marker",
                    relative.as_posix(),
                    "a unit-test directory must own __init__.py",
                )
            )
        if len(direct_test_modules) > active_policy.maximum_direct_test_modules:
            violations.append(
                TopologyViolation(
                    "crowded_test_package",
                    relative.as_posix(),
                    (
                        f"{len(direct_test_modules)} direct test modules exceed the "
                        f"limit of {active_policy.maximum_direct_test_modules}"
                    ),
                )
            )

    tested_domains = {
        path.relative_to(tests).parts[0]
        for path in tests.iterdir()
        if path.is_dir() and path.name != "__pycache__" and any(path.rglob("test_*.py"))
    }
    source_domains = {
        path.name
        for path in source.iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    }
    explicit_test_domains = {
        ownership.test_domain
        for ownership in active_policy.unit_test_domains
        if (source / ownership.source_path).exists()
    }
    for domain in sorted(tested_domains - source_domains - explicit_test_domains):
        violations.append(
            TopologyViolation(
                "unmirrored_unit_test_domain",
                domain,
                "top-level unit-test domains must mirror a production package",
            )
        )

    return tuple(sorted(set(violations)))


def assert_repository_topology(
    source_root: Path,
    unit_test_root: Path,
    *,
    policy: RepositoryTopologyPolicy | None = None,
) -> None:
    """Raise with every deterministic topology failure when policy is violated."""
    violations = audit_repository_topology(
        source_root,
        unit_test_root,
        policy=policy,
    )
    if not violations:
        return
    details = "\n".join(
        f"- {violation.code}: {violation.path}: {violation.detail}"
        for violation in violations
    )
    raise ValueError(f"repository topology violations:\n{details}")


def _existing_directory(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"{label} is not a directory: {resolved}")
    return resolved


def _python_directories(root: Path) -> tuple[Path, ...]:
    return tuple(
        directory
        for directory in (root, *sorted(root.rglob("*")))
        if directory.is_dir()
        and "__pycache__" not in directory.parts
        and _contains_python_files(directory)
    )


def _test_directories(root: Path) -> tuple[Path, ...]:
    return tuple(
        directory
        for directory in sorted(root.rglob("*"))
        if directory.is_dir()
        and "__pycache__" not in directory.parts
        and any(
            "__pycache__" not in path.parts for path in directory.rglob("test_*.py")
        )
    )


def _contains_python_files(directory: Path) -> bool:
    return any("__pycache__" not in path.parts for path in directory.rglob("*.py"))


def _audit_allowed_files(
    source_root: Path,
    relative_package: Path,
    allowed_files: tuple[str, ...],
    code: str,
    violations: list[TopologyViolation],
) -> None:
    directory = source_root / relative_package
    display_path = _display_path(relative_package)
    if not directory.is_dir():
        violations.append(
            TopologyViolation(
                "missing_facade_package",
                display_path,
                "a topology-governed package is missing",
            )
        )
        return
    actual_files = {path.name for path in directory.glob("*.py")}
    unexpected = sorted(actual_files - set(allowed_files))
    if unexpected:
        violations.append(
            TopologyViolation(
                code,
                display_path,
                "unexpected direct module(s): " + ", ".join(unexpected),
            )
        )


def _has_wildcard_import(path: Path) -> bool:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    return any(
        isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
        for node in ast.walk(module)
    )


def _audit_relative_imports(
    source_root: Path,
    violations: list[TopologyViolation],
) -> None:
    module_paths = {
        _module_name(source_root, path): path
        for path in source_root.rglob("*.py")
        if "__pycache__" not in path.parts
    }
    for module_name, path in sorted(module_paths.items()):
        package_name = (
            module_name
            if path.name == "__init__.py"
            else module_name.rpartition(".")[0]
        )
        syntax_tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=path.as_posix(),
        )
        for node in ast.walk(syntax_tree):
            if (
                not isinstance(node, ast.ImportFrom)
                or not node.level
                or not node.module
            ):
                continue
            try:
                target = resolve_name("." * node.level + node.module, package_name)
            except ImportError:
                target = "." * node.level + node.module
            if target in module_paths:
                continue
            violations.append(
                TopologyViolation(
                    "unresolved_relative_import",
                    path.relative_to(source_root).as_posix(),
                    f"line {node.lineno} resolves to missing module {target}",
                )
            )


def _module_name(source_root: Path, path: Path) -> str:
    relative_parts = list(path.relative_to(source_root).with_suffix("").parts)
    if relative_parts[-1] == "__init__":
        relative_parts.pop()
    return ".".join((source_root.name, *relative_parts))


def _display_path(path: Path) -> str:
    return "." if not path.parts else path.as_posix()
