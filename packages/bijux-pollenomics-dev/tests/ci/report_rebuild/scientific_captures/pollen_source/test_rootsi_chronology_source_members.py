"""Exercise only the rootsi chronology detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    rootsi_chronology,
)

PREFIX = "data/surface-reference/rootsi-chronology-source-capture"
ROLES = frozenset(
    [
        "source-code/artifacts/science/rootsi-controller-import-custody/cache_contract.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/check_contracts.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/common_runner.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/contracts.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/execute_source.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/independent.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/observe.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/prepare.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/run.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/runtime.py",
        "source-code/artifacts/science/rootsi-controller-import-custody/source-prefix.diff",
        "source-code/configs/ci/report-ownership.json",
        "source-code/docs/report/source-relations/landclim/neotoma-chronology-witness/replay.py",
        "source-code/docs/report/source-relations/landclim/workbook-chronology/replay.py",
    ]
)


def test_exact_declared_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert rootsi_chronology.DETACHED_SOURCE_MEMBERS == ROLES
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(rootsi_chronology, "validate_capsule", validated)
    rootsi_chronology._validate_source_members(tmp_path, PREFIX)
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is rootsi_chronology.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(
        rootsi_chronology, "validate_capsule", lambda *args: ROLES - {missing}
    )
    with pytest.raises(ReportRebuildError):
        rootsi_chronology._validate_source_members(tmp_path, PREFIX)


@pytest.mark.parametrize("extra", ["source-code/undeclared.py", "execution/plan.json"])
def test_extra_source_or_non_source_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    monkeypatch.setattr(
        rootsi_chronology, "validate_capsule", lambda *args: ROLES | {extra}
    )
    with pytest.raises(ReportRebuildError):
        rootsi_chronology._validate_source_members(tmp_path, PREFIX)


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 14
    monkeypatch.setattr(rootsi_chronology, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        rootsi_chronology._validate_source_members(tmp_path, PREFIX)


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(rootsi_chronology, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        rootsi_chronology._validate_source_members(tmp_path, PREFIX)
    assert caught.value is refusal
