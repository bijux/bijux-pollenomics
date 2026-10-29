"""Keep exact controller roles in a tiny constructed source catalogue."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_direct_pollen as subject,
)

PREFIX = "data/surface-reference/swedish-direct-pollen-source-capture"
EXTRAS = frozenset(
    [
        "original-source/controllers/check_contracts.py",
        "original-source/controllers/common_runner.py",
        "original-source/controllers/contracts.py",
        "original-source/controllers/execute_source.py",
        "original-source/controllers/independent.py",
        "original-source/controllers/observe.py",
        "original-source/controllers/prepare.py",
        "original-source/controllers/run.py",
        "original-source/controllers/runtime_contracts.py",
        "original-source/controllers/runtime_guarded_runner.py",
        "original-source/controllers/source_runtime.py",
    ]
)
ROLES = frozenset(
    [
        "original-source/controllers/check_contracts.py",
        "original-source/controllers/common_runner.py",
        "original-source/controllers/contracts.py",
        "original-source/controllers/execute_source.py",
        "original-source/controllers/independent.py",
        "original-source/controllers/observe.py",
        "original-source/controllers/prepare.py",
        "original-source/controllers/run.py",
        "original-source/controllers/runtime_contracts.py",
        "original-source/controllers/runtime_guarded_runner.py",
        "original-source/controllers/source_runtime.py",
        "original-source/source/configs/ci/report-ownership.json",
        "original-source/source/docs/report/regions/nordic/swedish-lake-transfer/reference/prediction-producer.py.txt",
        "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/reference/parallel-dataset-review-producer.py.txt",
        "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/reference/prediction-producer.py.txt",
        "original-source/source/packages/constructed_source.py",
    ]
)


def invoke(
    monkeypatch: pytest.MonkeyPatch, repository: Path, selected: frozenset[str]
) -> object:
    """Exercise only the role seam; complete transport authentication stays separate."""
    members: dict[str, Any] = {name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES}
    result = SimpleNamespace(detached=selected)
    monkeypatch.setattr(subject, "validated_descriptor", lambda *args: result)
    return subject.validate_capsule_members(repository, PREFIX, members)


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

    monkeypatch.setattr(subject, "validated_descriptor", refused)
    members: dict[str, Any] = {name: {"sha256": "a" * 64, "bytes": 0} for name in ROLES}
    with pytest.raises(ReportRebuildError) as caught:
        subject.validate_capsule_members(tmp_path, PREFIX, members)
    assert caught.value is refusal
