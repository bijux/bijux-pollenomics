"""Exercise only the svar detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry import (
    svar,
)

PREFIX = "data/surface-reference/svar-normalized-source-capture"
ROLES = frozenset(
    [
        "source-code/artifacts/science/svar-source-final-census/check_contracts.py",
        "source-code/artifacts/science/svar-source-final-census/common_runner.py",
        "source-code/artifacts/science/svar-source-final-census/contracts.py",
        "source-code/artifacts/science/svar-source-final-census/execute_source.py",
        "source-code/artifacts/science/svar-source-final-census/observe.py",
        "source-code/artifacts/science/svar-source-final-census/prepare.py",
        "source-code/artifacts/science/svar-source-final-census/run.py",
        "source-code/artifacts/science/svar-source-final-census/runtime.py",
        "source-code/artifacts/science/svar-source-final-census/source-correction.diff",
        "source-code/configs/ci/report-ownership.json",
        "source-code/docs/report/source-relations/svar/normalized-export/verify.py",
    ]
)


def test_exact_declared_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert svar.DETACHED_SOURCE_MEMBERS == ROLES
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(svar, "validate_capsule", validated)
    svar._validate_source_members(tmp_path, PREFIX)
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is svar.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(svar, "validate_capsule", lambda *args: ROLES - {missing})
    with pytest.raises(ReportRebuildError):
        svar._validate_source_members(tmp_path, PREFIX)


@pytest.mark.parametrize("extra", ["source-code/undeclared.py", "execution/plan.json"])
def test_extra_source_or_non_source_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    monkeypatch.setattr(svar, "validate_capsule", lambda *args: ROLES | {extra})
    with pytest.raises(ReportRebuildError):
        svar._validate_source_members(tmp_path, PREFIX)


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 11
    monkeypatch.setattr(svar, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        svar._validate_source_members(tmp_path, PREFIX)


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(svar, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        svar._validate_source_members(tmp_path, PREFIX)
    assert caught.value is refusal
