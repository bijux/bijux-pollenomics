"""Keep exact controller roles in a tiny constructed source catalogue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.neotoma_lake import (
    members as subject,
)

PREFIX = "data/source-custody/neotoma/lakeparameters"
EXTRAS = frozenset(
    [
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_controls.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_tools.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/common_runner.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/controller-budget-delta.diff",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_projection.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_reader.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/lake_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/observe.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/prepare.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/projection_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/run.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/runtime_contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_admission.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_entry.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_inputs.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_runtime.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_tools.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/install.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/observe.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/pip_entry.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/prepare.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run_account_qualification.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/transport.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_tools.py",
        "source/artifacts/science/source-runtime-native-observation-custody/contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/observe.py",
        "source/artifacts/science/source-runtime-native-observation-custody/prepare.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run_account_qualification.py",
    ]
)
ROLES = frozenset(
    [
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_controls.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_tools.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/common_runner.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/controller-budget-delta.diff",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_projection.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_reader.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/lake_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/observe.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/prepare.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/projection_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/run.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/runtime_contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_admission.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_entry.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_inputs.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_runtime.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_tools.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/install.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/observe.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/pip_entry.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/prepare.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run_account_qualification.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/transport.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_tools.py",
        "source/artifacts/science/source-runtime-native-observation-custody/contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/observe.py",
        "source/artifacts/science/source-runtime-native-observation-custody/prepare.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run_account_qualification.py",
        "source/configs/ci/report-ownership.json",
        "source/docs/report/source-relations/neotoma/lakeparameters/verify.py",
        "source/packages/constructed_source.py",
    ]
)


def invoke(
    monkeypatch: pytest.MonkeyPatch, repository: Path, selected: frozenset[str]
) -> None:
    """Exercise only the role seam; complete transport authentication stays separate."""
    members: dict[str, Any] = {name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES}
    result = selected
    monkeypatch.setattr(subject, "validate_capsule", lambda *args: result)
    subject.validate_members(repository, repository / PREFIX, members)


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
        subject.validate_members(tmp_path, tmp_path / PREFIX, members)
    assert caught.value is refusal


@pytest.mark.parametrize(
    "foreign",
    ["source/configs/ci/unknown.json", "source/docs/unreviewed.py"],
)
def test_declared_foreign_control_or_document_is_not_admitted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, foreign: str
) -> None:
    """Reject foreign roles even when both member and detached catalogues declare them."""
    members: dict[str, Any] = {
        name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES | {foreign}
    }
    selected = frozenset(members)
    monkeypatch.setattr(subject, "validate_capsule", lambda *args: selected)
    with pytest.raises((ReportRebuildError, ValueError)):
        subject.validate_members(tmp_path, tmp_path / PREFIX, members)
