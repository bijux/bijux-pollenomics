from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.architecture import (
    assert_repository_topology,
    audit_repository_topology,
    repository_topology_policy,
)
from tests.support.repository import REPOSITORY_ROOT

_SOURCE_ROOT = REPOSITORY_ROOT / "packages/bijux-pollenomics/src/bijux_pollenomics"
_UNIT_TEST_ROOT = REPOSITORY_ROOT / "packages/bijux-pollenomics/tests/unit"


def test_repository_source_and_unit_test_trees_satisfy_topology_policy() -> None:
    assert audit_repository_topology(_SOURCE_ROOT, _UNIT_TEST_ROOT) == ()
    assert_repository_topology(_SOURCE_ROOT, _UNIT_TEST_ROOT)


def test_topology_policy_keeps_public_facades_narrow_and_packages_bounded() -> None:
    policy = repository_topology_policy()

    assert policy.maximum_direct_modules == 10
    assert policy.maximum_direct_test_modules == 10
    assert policy.maximum_source_module_lines == 680
    assert policy.maximum_unit_test_module_lines == 610
    assert policy.forbidden_package_names == {
        "common",
        "foundation",
        "helpers",
        "misc",
        "pipeline",
        "shared",
        "temporary",
        "utils",
    }
    assert {
        facade.package: facade.allowed_files for facade in policy.package_facades
    } == {
        "adna": ("__init__.py", "api.py"),
        "analysis": ("__init__.py",),
        "collection": ("__init__.py", "api.py"),
    }
    assert {
        ownership.test_domain: ownership.source_path
        for ownership in policy.unit_test_domains
    } == {"configuration": "config.py"}


def test_topology_audit_reports_all_structural_failure_classes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    tests = tmp_path / "unit"
    _write(source / "__init__.py", "")
    _write(source / "leaked.py", "")
    _write(source / "adna/__init__.py", "")
    _write(source / "adna/unowned.py", "")
    _write(source / "adna/broken.py", "from ..missing.owner import thing\n")
    _write(source / "analysis/__init__.py", "")
    _write(source / "collection/__init__.py", "")
    _write(source / "shared/__init__.py", "")
    _write(source / "unmarked/behavior.py", "")
    _write(source / "wild/__init__.py", "from sibling import *\n")
    _write(source / "oversized/__init__.py", "\n" * 681)
    for index in range(11):
        _write(source / f"crowded/behavior_{index}.py", "")
    _write(tests / "test_flat.py", "")
    _write(tests / "orphan/test_behavior.py", "")
    _write(tests / "adna/__init__.py", "")
    _write(tests / "adna/crowded/__init__.py", "")
    _write(tests / "adna/oversized/test_behavior.py", "\n" * 611)
    for index in range(11):
        _write(tests / f"adna/crowded/test_behavior_{index}.py", "")

    violations = audit_repository_topology(source, tests)

    assert {violation.code for violation in violations} == {
        "ambiguous_package_name",
        "crowded_package",
        "crowded_test_package",
        "facade_module_leak",
        "flat_unit_test",
        "missing_package_marker",
        "missing_test_package_marker",
        "oversized_source_module",
        "oversized_unit_test_module",
        "source_root_module_leak",
        "unmirrored_unit_test_domain",
        "unresolved_relative_import",
        "wildcard_package_export",
    }
    with pytest.raises(ValueError, match="repository topology violations"):
        assert_repository_topology(source, tests)


def test_topology_audit_requires_existing_roots(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source root is not a directory"):
        audit_repository_topology(tmp_path / "missing-source", tmp_path)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
