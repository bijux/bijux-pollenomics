"""Keep exact controller roles in a tiny constructed source catalogue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.land_use import (
    openland_members as subject,
)

PREFIX = "data/surface-reference/openland-member-source-capture"
EXTRAS = frozenset(
    [
        "source-code/artifacts/science/openland-member-telemetry-custody/check_contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/common_runner.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/execute_source.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/metadata.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/observe.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/prepare.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/run.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/runtime_contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/runtime_guarded_runner.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/source_runtime.py",
    ]
)
ROLES = frozenset(
    [
        "historical-source/open-land-authority.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/check_contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/common_runner.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/execute_source.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/metadata.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/observe.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/prepare.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/run.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/runtime_contracts.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/runtime_guarded_runner.py",
        "source-code/artifacts/science/openland-member-telemetry-custody/source_runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/packages/constructed_source.py",
    ]
)


def invoke(
    monkeypatch: pytest.MonkeyPatch, repository: Path, selected: frozenset[str]
) -> None:
    """Exercise only the role seam; complete transport authentication stays separate."""
    members: dict[str, Any] = {name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES}
    result = selected
    monkeypatch.setattr(subject, "validate_capsule", lambda *args: result)
    subject._validate_source_transport(repository, PREFIX, members)


def test_exact_roles_include_previously_omitted_controllers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert EXTRAS == subject.ADDITIONAL_DETACHED_SOURCE_MEMBERS
    invoke(monkeypatch, tmp_path, ROLES)


@pytest.mark.parametrize("missing", sorted(ROLES))
def test_each_source_or_controller_role_is_required(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: str
) -> None:
    with pytest.raises((ReportRebuildError, ValueError)):
        invoke(monkeypatch, tmp_path, ROLES - {missing})


@pytest.mark.parametrize(
    "extra", ["source-code/undeclared.py", "publication/non-source.json"]
)
def test_unknown_source_or_publication_role_cannot_replace_a_controller(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str
) -> None:
    with pytest.raises((ReportRebuildError, ValueError)):
        invoke(monkeypatch, tmp_path, ROLES | {extra})


def test_equal_population_wrong_role_still_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = ROLES - {min(ROLES)} | {"source-code/other-controller.py"}
    assert len(wrong) == len(ROLES)
    with pytest.raises((ReportRebuildError, ValueError)):
        invoke(monkeypatch, tmp_path, wrong)


def test_existing_transport_failure_is_not_rescued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    refusal = ReportRebuildError("constructed source ancestry or raw identity failure")

    def refused(*args: object) -> object:
        raise refusal

    monkeypatch.setattr(subject, "validate_capsule", refused)
    members: dict[str, Any] = {name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES}
    with pytest.raises(ReportRebuildError) as caught:
        subject._validate_source_transport(tmp_path, PREFIX, members)
    assert caught.value is refusal
