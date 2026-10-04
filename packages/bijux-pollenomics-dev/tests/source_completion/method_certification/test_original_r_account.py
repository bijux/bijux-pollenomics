"""Retained original R source custody and one-report publication remain separate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.lra_validation import reference_replay
from bijux_pollenomics_dev.source_completion.method_certification import (
    original_r_account as m,
)


def _account() -> dict[str, Any]:
    """Make a synthetic already-computed account, without executing numerical work."""
    return {
        "schema_version": "retained-r-python-replay.1",
        "status": "passed",
        "fresh_R_executed": False,
        "original_R_executed": True,
        "original_source_commit": m.ORIGINAL_SOURCE,
        "original_certificate_sha256": reference_replay.CERTIFICATE_SHA256,
        "release_certificate": False,
        "current_inputs_sha256": {"source.py": "a" * 64},
        "attempted_cases": 66,
        "evaluated_cases": 48,
        "passed_cases": 48,
        "failed_cases": 0,
        "refused_cases": 18,
        "cases": [
            {
                "profile": profile,
                "id": str(i),
                "status": "passed",
                "name": str(i),
                "api": "synthetic",
                "mode": "synthetic",
                "semantics": "synthetic",
            }
            for profile, n in [
                ("source-compatible-core", 25),
                ("source-domains-and-corrected-forward", 23),
            ]
            for i in range(n)
        ],
        "current_core_cases_without_retained_R": [
            {
                "name": str(i),
                "api": "synthetic",
                "reason": "no_result_in_original_R_bundle",
            }
            for i in range(18)
        ],
    }


def _route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, Any]]:
    repository = tmp_path / "repository"
    parent = repository / "artifacts/evidence/producer-output"
    parent.mkdir(parents=True)
    output = parent / "source-products"
    report = _account()
    monkeypatch.setattr(
        m, "_snapshot", lambda r: ((), report["current_inputs_sha256"], "fixed")
    )
    expected = _account()
    returned = [
        (row["profile"], row["id"], row["name"], row["api"], row["mode"])
        if row["profile"] == "source-compatible-core"
        else (row["profile"], row["id"], row["semantics"])
        for row in expected["cases"]
    ]
    missing = [
        (row["name"], row["api"], row["reason"])
        for row in expected["current_core_cases_without_retained_R"]
    ]
    monkeypatch.setattr(m, "_populations", lambda r, h: (returned, missing))

    def replay(root: Path, bundle: Path, comparison: Path) -> dict[str, Any]:
        assert root == repository and bundle == repository / m.BUNDLE
        comparison.mkdir()
        (comparison / "inputs").mkdir()
        (comparison / "inputs/input.csv").write_text("value\n0.25\n")
        (comparison / "report.json").write_text(json.dumps(report) + "\n")
        return report

    monkeypatch.setattr(reference_replay, "replay", replay)
    return repository, output, report


def test_complete_producer_stage_retained_outside_single_owner_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    result = m.publish(repository, output)
    assert result == report == json.loads((output / "report.json").read_text())
    assert list(output.iterdir()) == [output / "report.json"]
    assert {
        str(path.relative_to(output.parent))
        for path in output.parent.rglob("*")
        if path.is_file()
    } == {"source-products/report.json"}
    stages = list(output.parent.parent.glob(".source-products.original-r-account-*"))
    assert len(stages) == 1
    assert (stages[0] / "comparison/inputs/input.csv").read_text() == "value\n0.25\n"
    assert json.loads((stages[0] / "comparison/report.json").read_text()) == report


@pytest.mark.parametrize(
    "field,value",
    [
        ("fresh_R_executed", True),
        ("release_certificate", True),
        ("original_certificate_sha256", "0" * 64),
        ("original_source_commit", "0" * 40),
        ("refused_cases", 0),
        ("passed_cases", 66),
        ("evaluated_cases", 66),
        ("attempted_cases", True),
        ("status", "failed"),
        ("current_inputs_sha256", {}),
    ],
)
def test_changed_scope_cannot_publish_a_synthetic_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    fixed_hashes = dict(report["current_inputs_sha256"])
    monkeypatch.setattr(m, "_snapshot", lambda r: ((), fixed_hashes, "fixed"))
    report[field] = value
    with pytest.raises(ValueError, match="scope or actual comparison differs"):
        m.publish(repository, output)
    assert not output.exists()


@pytest.mark.parametrize("mutation", ["reference", "source", "writer"])
def test_source_and_reference_changes_refuse_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    original: tuple[object, ...] = ((), report["current_inputs_sha256"], "fixed")
    changed = list(original)
    changed[{"reference": 0, "source": 1, "writer": 2}[mutation]] = "changed"
    values = iter([original, tuple(changed)])
    monkeypatch.setattr(m, "_snapshot", lambda r: next(values))
    with pytest.raises(ValueError, match="source or retained reference changed"):
        m.publish(repository, output)
    assert not output.exists()
    assert list(
        output.parent.parent.glob(
            ".source-products.original-r-account-*/comparison/report.json"
        )
    )


@pytest.mark.parametrize("kind", ["existing", "alias", "outside"])
def test_unsafe_output_refuses_before_any_producer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    repository, output, _ = _route(tmp_path, monkeypatch)
    calls: list[object] = []
    monkeypatch.setattr(reference_replay, "replay", lambda *args: calls.append(args))
    if kind == "existing":
        output.mkdir()
    elif kind == "alias":
        output.symlink_to(output.parent, target_is_directory=True)
    else:
        output = tmp_path / "outside"
    with pytest.raises(ReportRebuildError, match="configured owner output"):
        m.publish(repository, output)
    assert calls == []


def test_changed_returned_and_physical_stage_reports_refuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    original = reference_replay.replay

    def replay(root: Path, bundle: Path, comparison: Path) -> dict[str, Any]:
        value = original(root, bundle, comparison)
        substituted = copy.deepcopy(value)
        substituted["passed_cases"] = 47
        (comparison / "report.json").write_text(json.dumps(substituted))
        return value

    monkeypatch.setattr(reference_replay, "replay", replay)
    with pytest.raises(ValueError, match="producer report differs"):
        m.publish(repository, output)
    assert not output.exists() and report["passed_cases"] == 48


def test_competing_destination_keeps_its_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    count = 0

    def snapshot(root: Path) -> tuple[object, ...]:
        nonlocal count
        count += 1
        if count == 2:
            output.mkdir()
            (output / "report.json").write_text("competitor\n")
        return (), report["current_inputs_sha256"], "fixed"

    monkeypatch.setattr(m, "_snapshot", snapshot)
    with pytest.raises(FileExistsError):
        m.publish(repository, output)
    assert (output / "report.json").read_text() == "competitor\n"


@pytest.mark.parametrize(
    "mutation",
    [
        "core-id",
        "domain-id",
        "core-name",
        "core-api",
        "core-mode",
        "domain-semantics",
        "duplicate-core",
        "duplicate-domain",
        "missing-name",
        "missing-api",
        "duplicate-missing",
    ],
)
def test_exact_returned_and_unavailable_population_cannot_be_substituted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repository, output, report = _route(tmp_path, monkeypatch)
    if mutation.startswith("duplicate-"):
        if mutation == "duplicate-missing":
            report["current_core_cases_without_retained_R"][1] = copy.deepcopy(
                report["current_core_cases_without_retained_R"][0]
            )
        else:
            start = 25 if mutation == "duplicate-domain" else 0
            report["cases"][start + 1] = copy.deepcopy(report["cases"][start])
    elif mutation.startswith("missing-"):
        report["current_core_cases_without_retained_R"][0][
            mutation.split("-", 1)[1]
        ] = "substitution"
    else:
        kind, field = mutation.split("-", 1)
        report["cases"][25 if kind == "domain" else 0][field] = "substitution"
    with pytest.raises(
        ValueError, match="population differs|scope or actual comparison differs"
    ):
        m.publish(repository, output)
    assert not output.exists()
