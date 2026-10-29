"""Exercise only the HYDE detached-role seam; native capture admission stays separate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.land_use import (
    hyde_country,
)

PREFIX = "data/surface-reference/hyde-country-source-capture"
ROLES = frozenset(
    [
        "source-code/artifacts/science/hyde-country-source-custody/check_contracts.py",
        "source-code/artifacts/science/hyde-country-source-custody/common_runner.py",
        "source-code/artifacts/science/hyde-country-source-custody/contracts.py",
        "source-code/artifacts/science/hyde-country-source-custody/execute_source.py",
        "source-code/artifacts/science/hyde-country-source-custody/metadata.py",
        "source-code/artifacts/science/hyde-country-source-custody/observe.py",
        "source-code/artifacts/science/hyde-country-source-custody/prepare.py",
        "source-code/artifacts/science/hyde-country-source-custody/run.py",
        "source-code/artifacts/science/hyde-country-source-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/hyde_country_cropland.py",
    ]
)


def test_exact_eleven_roles_delegate_to_existing_capsule_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert hyde_country.DETACHED_SOURCE_MEMBERS == ROLES
    seen: list[tuple[Path, str, object]] = []

    def validated(repository: Path, prefix: str, expected: object) -> frozenset[str]:
        seen.append((repository, prefix, expected))
        return ROLES

    monkeypatch.setattr(hyde_country, "validate_capsule", validated)
    hyde_country._validate_source_transport(
        tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
    )
    assert len(seen) == 1
    assert seen[0][:2] == (tmp_path, PREFIX)
    assert seen[0][2] is hyde_country.EXPECTED_MEMBERS


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_missing_detached_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    monkeypatch.setattr(
        hyde_country, "validate_capsule", lambda *args: ROLES - {missing}
    )
    with pytest.raises(ReportRebuildError):
        hyde_country._validate_source_transport(
            tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
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
    monkeypatch.setattr(hyde_country, "validate_capsule", lambda *args: ROLES | {extra})
    with pytest.raises(ReportRebuildError):
        hyde_country._validate_source_transport(
            tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
        )


def test_same_count_wrong_role_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/artifacts/science/other_controller.py"}
    assert len(wrong) == 11
    monkeypatch.setattr(hyde_country, "validate_capsule", lambda *args: wrong)
    with pytest.raises(ReportRebuildError):
        hyde_country._validate_source_transport(
            tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
        )


def test_transport_identity_or_ancestry_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed transport source ancestry refusal")

    def refused(*args: object) -> frozenset[str]:
        raise refusal

    monkeypatch.setattr(hyde_country, "validate_capsule", refused)
    with pytest.raises(ReportRebuildError) as caught:
        hyde_country._validate_source_transport(
            tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
        )
    assert caught.value is refusal


def test_legacy_two_role_subset_is_not_complete_source_closure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy = frozenset(
        name
        for name in ROLES
        if name.startswith("source-code/packages/")
        or name == "source-code/configs/ci/report-ownership.json"
    )
    assert len(legacy) == 2
    monkeypatch.setattr(hyde_country, "validate_capsule", lambda *args: legacy)
    with pytest.raises(ReportRebuildError):
        hyde_country._validate_source_transport(
            tmp_path, PREFIX, hyde_country.EXPECTED_MEMBERS
        )
