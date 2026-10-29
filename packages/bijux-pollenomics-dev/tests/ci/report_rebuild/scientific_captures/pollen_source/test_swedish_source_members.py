"""Exercise only the Swedish cohort detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_cohort,
)

PREFIX = "data/surface-reference/swedish-cohort-source-capture"
ROLES = frozenset(
    [
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/check_contracts.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/common_runner.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/contracts.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/custody.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/execute_source.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/metadata.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/observe.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/formatted-common-construction.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/prepare.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/run.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/runtime.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/source-observer.diff",
        "source-code/artifacts/science/swedish-cohort-source-custody/check_contracts.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/common_runner.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/contracts.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/execute_source.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/metadata.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/observe.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/preflight/check_tools.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/prepare.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/run.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py",
    ]
)


def test_exact_twenty_four_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert swedish_cohort.DETACHED_SOURCE_MEMBERS == ROLES
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(swedish_cohort, "validate_capsule", validated)
    swedish_cohort._validate_source_members(tmp_path, PREFIX)
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is swedish_cohort.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(
        swedish_cohort, "validate_capsule", lambda *args: ROLES - {missing}
    )
    with pytest.raises(ReportRebuildError):
        swedish_cohort._validate_source_members(tmp_path, PREFIX)


@pytest.mark.parametrize("extra", ["source-code/undeclared.py", "execution/plan.json"])
def test_extra_source_or_non_source_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    monkeypatch.setattr(
        swedish_cohort, "validate_capsule", lambda *args: ROLES | {extra}
    )
    with pytest.raises(ReportRebuildError):
        swedish_cohort._validate_source_members(tmp_path, PREFIX)


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 24
    monkeypatch.setattr(swedish_cohort, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        swedish_cohort._validate_source_members(tmp_path, PREFIX)


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(swedish_cohort, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        swedish_cohort._validate_source_members(tmp_path, PREFIX)
    assert caught.value is refusal
