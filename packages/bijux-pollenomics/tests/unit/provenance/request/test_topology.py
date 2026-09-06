"""Architectural boundaries for request derivation responsibilities."""

from __future__ import annotations

from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT

_REQUEST_ROOT = (
    REPOSITORY_ROOT
    / "packages/bijux-pollenomics/src/bijux_pollenomics/provenance/request"
)


def test_request_implementation_is_an_intent_owned_package() -> None:
    assert _REQUEST_ROOT.is_dir()
    assert not _REQUEST_ROOT.with_suffix(".py").exists()
    assert {path.relative_to(_REQUEST_ROOT).as_posix() for path in _python_files()} == {
        "__init__.py",
        "artifacts.py",
        "blockers.py",
        "gates.py",
        "identity.py",
        "reconciliation/__init__.py",
        "reconciliation/chronology.py",
        "reconciliation/classification.py",
        "reconciliation/country.py",
        "reconciliation/json_object.py",
        "reconciliation/model.py",
        "reconciliation/propagation.py",
        "reconciliation/records.py",
        "reconciliation/service.py",
    }


def test_request_modules_remain_bounded() -> None:
    line_counts = {
        path.relative_to(_REQUEST_ROOT).as_posix(): len(
            path.read_text(encoding="utf-8").splitlines()
        )
        for path in _python_files()
    }

    assert max(line_counts.values()) <= 160, line_counts


def _python_files() -> tuple[Path, ...]:
    return tuple(sorted(_REQUEST_ROOT.rglob("*.py")))
