from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.architecture import (
    assert_acyclic_package_imports,
    find_package_import_cycles,
)

from tests.support.repository import REPOSITORY_ROOT

_SOURCE_ROOT = REPOSITORY_ROOT / "packages/bijux-pollenomics/src/bijux_pollenomics"


def test_runtime_package_has_no_initialization_time_import_cycles() -> None:
    assert find_package_import_cycles(_SOURCE_ROOT) == ()
    assert_acyclic_package_imports(_SOURCE_ROOT)


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


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
