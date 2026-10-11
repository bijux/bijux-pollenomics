from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.architecture import (
    assert_acyclic_package_imports,
    find_package_import_cycles,
)
from tests.support.repository import REPOSITORY_ROOT

_SOURCE_ROOTS = (
    "packages/bijux-pollenomics/src/bijux_pollenomics",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra",
)


@pytest.mark.parametrize("relative_source", _SOURCE_ROOTS)
def test_runtime_package_has_no_initialization_time_import_cycles(
    relative_source: str,
) -> None:
    source = REPOSITORY_ROOT / relative_source
    assert find_package_import_cycles(source) == ()
    assert_acyclic_package_imports(source)


def test_dependency_audit_reports_eager_cycles_but_not_deferred_imports(
    tmp_path: Path,
) -> None:
    source = tmp_path / "owned_package"
    _write(source / "__init__.py", "")
    _write(source / "first.py", "from . import second\n")
    _write(
        source / "second.py",
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from . import typing_only\n"
        "from . import first\n"
        "def load_deferred():\n"
        "    from . import deferred\n",
    )
    _write(source / "typing_only.py", "from . import second\n")
    _write(source / "deferred.py", "from . import second\n")

    cycles = find_package_import_cycles(source)

    assert [cycle.modules for cycle in cycles] == [
        ("owned_package.first", "owned_package.second")
    ]
    with pytest.raises(ValueError, match="eager package import cycles"):
        assert_acyclic_package_imports(source)


def test_dependency_audit_requires_an_existing_source_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source root is not a directory"):
        find_package_import_cycles(tmp_path / "missing")


@pytest.mark.parametrize(
    "import_statement",
    (
        "from ._build_version import version",
        "from owned_package._build_version import version",
        "import owned_package._build_version",
        "from .missing.intermediate import version",
    ),
)
def test_missing_explicit_module_does_not_become_root_dependency(
    tmp_path: Path,
    import_statement: str,
) -> None:
    source = tmp_path / "owned_package"
    _write(source / "__init__.py", "from .version import version\n")
    _write(
        source / "version.py",
        f"try:\n    {import_statement}\nexcept ImportError:\n    version = 'unknown'\n",
    )
    assert find_package_import_cycles(source) == ()


@pytest.mark.parametrize(
    "import_statement", ("from . import version", "from owned_package import version")
)
def test_actual_root_attribute_keeps_its_eager_cycle(
    tmp_path: Path,
    import_statement: str,
) -> None:
    source = tmp_path / "owned_package"
    _write(source / "__init__.py", "version = '1'\nfrom . import consumer\n")
    _write(source / "consumer.py", f"{import_statement}\n")
    assert [cycle.modules for cycle in find_package_import_cycles(source)] == [
        ("owned_package", "owned_package.consumer")
    ]


@pytest.mark.parametrize("generated_cycle", (False, True))
def test_installed_generated_module_resolves_to_its_actual_module(
    tmp_path: Path,
    generated_cycle: bool,
) -> None:
    source = tmp_path / "owned_package"
    _write(source / "__init__.py", "from .version import version\n")
    _write(source / "version.py", "from ._build_version import version\n")
    _write(
        source / "_build_version.py",
        "from .version import version\n" if generated_cycle else "version = '1'\n",
    )
    expected = (
        [("owned_package._build_version", "owned_package.version")]
        if generated_cycle
        else []
    )
    assert [cycle.modules for cycle in find_package_import_cycles(source)] == expected


def test_explicit_package_attribute_is_not_redirected_to_a_same_named_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "owned_package"
    _write(source / "__init__.py", "version = '1'\nfrom . import consumer\n")
    _write(source / "consumer.py", "from owned_package import version\n")
    _write(source / "version.py", "unrelated = 'a child with the same name'\n")
    assert [cycle.modules for cycle in find_package_import_cycles(source)] == [
        ("owned_package", "owned_package.consumer")
    ]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
