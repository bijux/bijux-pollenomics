"""Architecture constraints for release-evidence policy ownership."""

from __future__ import annotations

from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT


_POLICY_ROOT = (
    REPOSITORY_ROOT
    / "packages/bijux-pollenomics/src/bijux_pollenomics/provenance/release_evidence/policy"
)


def test_policy_is_an_intent_owned_package() -> None:
    assert _POLICY_ROOT.is_dir()
    assert not _POLICY_ROOT.with_suffix(".py").exists()
    assert {path.name for path in _python_files()} == {
        "__init__.py",
        "artifacts.py",
        "contracts.py",
        "embedded.py",
        "reconciliation.py",
    }


def test_policy_modules_remain_bounded() -> None:
    line_counts = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in _python_files()
    }

    assert max(line_counts.values()) <= 220, line_counts


def _python_files() -> tuple[Path, ...]:
    return tuple(sorted(_POLICY_ROOT.glob("*.py")))
