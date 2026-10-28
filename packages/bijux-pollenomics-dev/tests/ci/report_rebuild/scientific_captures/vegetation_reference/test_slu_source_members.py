"""Exercise only the SLU detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.vegetation_reference import (
    slu_guide,
)

PREFIX = "data/validation/slu-calibration-guide-source-capture"
CONTROLLER = (
    "source-code/artifacts/science/current-report-custody/run_account_qualification.py"
)
HELPERS = (
    "acquire.py",
    "check_contracts.py",
    "contracts.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "runtime_custody.py",
)
ROLES = frozenset(
    {
        CONTROLLER,
        *(
            "source-code/artifacts/science/official-slu-guide-native-alias-custody/"
            + name
            for name in HELPERS
        ),
    }
)


def test_exact_eight_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert slu_guide.DETACHED_SOURCE_MEMBERS == ROLES
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(slu_guide, "validate_capsule", validated)
    slu_guide._validate_source_members(tmp_path, PREFIX)
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is slu_guide.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(slu_guide, "validate_capsule", lambda *args: ROLES - {missing})
    with pytest.raises(ReportRebuildError):
        slu_guide._validate_source_members(tmp_path, PREFIX)


@pytest.mark.parametrize("extra", ["source-code/undeclared.py", "execution/plan.json"])
def test_extra_source_or_non_source_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    monkeypatch.setattr(slu_guide, "validate_capsule", lambda *args: ROLES | {extra})
    with pytest.raises(ReportRebuildError):
        slu_guide._validate_source_members(tmp_path, PREFIX)


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {CONTROLLER} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 8
    monkeypatch.setattr(slu_guide, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        slu_guide._validate_source_members(tmp_path, PREFIX)


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(slu_guide, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        slu_guide._validate_source_members(tmp_path, PREFIX)
    assert caught.value is refusal
