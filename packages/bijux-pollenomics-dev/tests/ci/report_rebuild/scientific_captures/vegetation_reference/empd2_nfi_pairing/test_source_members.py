"""Keep exact controller roles in a tiny constructed source catalogue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.vegetation_reference.empd2_nfi_pairing import (
    capsule as subject,
)

PREFIX = "data/validation/empd2-nfi-pairing-source-capture"
EXTRAS = frozenset(
    [
        "control/check_contracts.py",
        "control/common_runner.py",
        "control/contracts.py",
        "control/execute_source.py",
        "control/metadata.py",
        "control/observe.py",
        "control/preflight/qualify_source.py",
        "control/preflight/source_style.py",
        "control/prepare.py",
        "control/run.py",
        "control/runtime_contracts.py",
        "control/runtime_guarded_runner.py",
        "control/source_runtime.py",
        "timeout-observation/control/check_contracts.py",
        "timeout-observation/control/common_runner.py",
        "timeout-observation/control/contracts.py",
        "timeout-observation/control/execute_source.py",
        "timeout-observation/control/metadata.py",
        "timeout-observation/control/observe.py",
        "timeout-observation/control/prepare.py",
        "timeout-observation/control/run.py",
        "timeout-observation/control/runtime_contracts.py",
        "timeout-observation/control/runtime_guarded_runner.py",
        "timeout-observation/control/source_runtime.py",
    ]
)
ROLES = frozenset(
    [
        "control/check_contracts.py",
        "control/common_runner.py",
        "control/contracts.py",
        "control/execute_source.py",
        "control/metadata.py",
        "control/observe.py",
        "control/preflight/qualify_source.py",
        "control/preflight/source_style.py",
        "control/prepare.py",
        "control/run.py",
        "control/runtime_contracts.py",
        "control/runtime_guarded_runner.py",
        "control/source_runtime.py",
        "source/packages/constructed_source.py",
        "timeout-observation/control/check_contracts.py",
        "timeout-observation/control/common_runner.py",
        "timeout-observation/control/contracts.py",
        "timeout-observation/control/execute_source.py",
        "timeout-observation/control/metadata.py",
        "timeout-observation/control/observe.py",
        "timeout-observation/control/prepare.py",
        "timeout-observation/control/run.py",
        "timeout-observation/control/runtime_contracts.py",
        "timeout-observation/control/runtime_guarded_runner.py",
        "timeout-observation/control/source_runtime.py",
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
