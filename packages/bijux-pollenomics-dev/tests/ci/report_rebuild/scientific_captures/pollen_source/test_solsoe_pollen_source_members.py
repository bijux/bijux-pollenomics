"""Exercise only the solsoe pollen detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    solsoe_pollen,
)

PREFIX = "data/countries/denmark/solsoe-primary-pollen-source-capture"
ROLES = frozenset(
    [
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/check_contract.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/common_runner.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/contracts.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/execute_source.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/observe.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/prepare.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/run.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py",
    ]
)


def test_exact_declared_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert solsoe_pollen.EXPECTED_MEMBERS.keys() >= ROLES
    assert len(ROLES) == 10
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(solsoe_pollen, "validate_capsule", validated)
    solsoe_pollen._validate_source_transport(
        tmp_path, PREFIX, solsoe_pollen.EXPECTED_MEMBERS
    )
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is solsoe_pollen.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(
        solsoe_pollen, "validate_capsule", lambda *args: ROLES - {missing}
    )
    with pytest.raises(ReportRebuildError):
        solsoe_pollen._validate_source_transport(
            tmp_path, PREFIX, solsoe_pollen.EXPECTED_MEMBERS
        )


@pytest.mark.parametrize(
    "extra",
    [
        "source-code/undeclared.py",
        "execution/plan.json",
        "source-code/configs/ci/unqualified-ownership.json",
    ],
)
def test_extra_source_or_non_source_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    monkeypatch.setattr(
        solsoe_pollen, "validate_capsule", lambda *args: ROLES | {extra}
    )
    with pytest.raises(ReportRebuildError):
        solsoe_pollen._validate_source_transport(
            tmp_path, PREFIX, solsoe_pollen.EXPECTED_MEMBERS
        )


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 10
    monkeypatch.setattr(solsoe_pollen, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        solsoe_pollen._validate_source_transport(
            tmp_path, PREFIX, solsoe_pollen.EXPECTED_MEMBERS
        )


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(solsoe_pollen, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        solsoe_pollen._validate_source_transport(
            tmp_path, PREFIX, solsoe_pollen.EXPECTED_MEMBERS
        )
    assert caught.value is refusal
