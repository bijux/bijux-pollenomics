"""Six-bin batch completeness controls before any actual artifact observation."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
from typing import Any

import pytest

from .materialization import NAMES
from .scalar import METHODS
from .verification import (
    PRODUCTION_PATHS,
    PROTOCOL,
    artifact_pin,
    closed_batch,
    verify_production_revision,
)


def batch_fixture() -> dict[str, Any]:
    bins: list[dict[str, Any]] = [
        {
            "bin": name,
            "folds": [{"fold_id": fold} for fold in ("a", "b", "c")],
            "method_dispositions": [
                {"fold_id": fold, "method": method, "status": "predicted"}
                for fold in ("a", "b", "c")
                for method in METHODS
            ],
        }
        for name in NAMES
    ]
    dispositions = [
        {"bin": row["bin"], **item}
        for row in bins
        for item in row["method_dispositions"]
    ]
    return {
        "schema_version": "krageholm-regional-coupled-batch.v1",
        "operation": "prepare",
        "source_commit": "synthetic",
        "protocol": {"path": "prospective protocol"},
        "all_bins_accounted": True,
        "requested_folds": 18,
        "requested_method_dispositions": 54,
        "scientific_acceptance": "not_evaluated",
        "exposure": "prior_exposed_development",
        "bins": bins,
        "method_dispositions": dispositions,
        "status_counts": {"predicted": 54},
    }


def test_exact_six_bins18_folds54_dispositions_close() -> None:
    closed_batch(
        batch_fixture(), "prepare", "synthetic", {"path": "prospective protocol"}
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_bin",
        "duplicate_bin",
        "incomplete",
        "missing_fold",
        "duplicate_method",
        "status_count",
        "source_commit",
        "scientific_admission",
    ],
)
def test_incomplete_or_misrepresented_fixed_population_refuses(corruption: str) -> None:
    value = deepcopy(batch_fixture())
    if corruption == "missing_bin":
        value["bins"].pop()
    elif corruption == "duplicate_bin":
        value["bins"][1]["bin"] = value["bins"][0]["bin"]
    elif corruption == "incomplete":
        value["all_bins_accounted"] = False
    elif corruption == "missing_fold":
        value["bins"][0]["folds"].pop()
    elif corruption == "duplicate_method":
        value["bins"][0]["method_dispositions"][1] = value["bins"][0][
            "method_dispositions"
        ][0]
    elif corruption == "status_count":
        value["status_counts"]["predicted"] = 53
    elif corruption == "source_commit":
        value["source_commit"] = "another"
    else:
        value["scientific_acceptance"] = "accepted"
    with pytest.raises(ValueError):
        closed_batch(value, "prepare", "synthetic", {"path": "prospective protocol"})


def test_relative_artifact_pin_preserves_serialized_locator_and_byte_identity(
    tmp_path: Path,
) -> None:
    owner = tmp_path / "artifacts/study"
    path = owner / "predictions/batch.json"
    path.parent.mkdir(parents=True)
    body = b'{"source_commit":"original"}'
    path.write_bytes(body)
    pin = {
        "path": "artifacts/study/predictions/batch.json",
        "sha256": sha256(body).hexdigest(),
    }
    original = deepcopy(pin)
    assert artifact_pin(tmp_path, pin, owner) == (
        path,
        body,
        {"source_commit": "original"},
    )
    assert pin == original


def git_stub(
    monkeypatch: pytest.MonkeyPatch, corruption: str | None = None
) -> list[list[str]]:
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(command)
        args = command[3:]
        if (
            (corruption == "ancestry" and args[0] == "merge-base")
            or (
                corruption == "production_change"
                and args[:4] == ["diff", "--exit-code", "a" * 40, "b" * 40]
            )
            or (
                corruption == "dirty_production"
                and args[:4] == ["diff", "--exit-code", "b" * 40, "--"]
            )
        ):
            raise subprocess.CalledProcessError(1, command)
        assert kwargs["check"] is True and kwargs["capture_output"] is True
        return subprocess.CompletedProcess(command, 0, b"", b"")

    def output(command: list[str], **kwargs: Any) -> bytes:
        calls.append(command)
        args = command[3:]
        if args[0] == "ls-files":
            return b"untracked.py\n" if corruption == "untracked_production" else b""
        assert args[0] == "show"
        if corruption == "protocol" and args[1].startswith("a" * 40):
            return b"different original protocol"
        return b"original prospective protocol"

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", output)
    return calls


def test_producer_and_observer_commits_are_separate_with_unchanged_production_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = git_stub(monkeypatch)
    verify_production_revision(
        tmp_path, "a" * 40, "b" * 40, b"original prospective protocol"
    )
    arguments = [command[3:] for command in calls]
    assert ["merge-base", "--is-ancestor", "a" * 40, "b" * 40] in arguments
    assert [
        "diff",
        "--exit-code",
        "a" * 40,
        "b" * 40,
        "--",
        *PRODUCTION_PATHS,
    ] in arguments
    assert ["diff", "--exit-code", "b" * 40, "--", *PRODUCTION_PATHS] in arguments
    assert ["show", "a" * 40 + ":" + PROTOCOL] in arguments
    assert ["show", "b" * 40 + ":" + PROTOCOL] in arguments
    assert not any(
        "krageholm_regional_coupled/verification.py" in path
        for path in PRODUCTION_PATHS
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "ancestry",
        "production_change",
        "dirty_production",
        "untracked_production",
        "protocol",
    ],
)
def test_ancestry_production_byte_worktree_or_original_protocol_changes_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    git_stub(monkeypatch, corruption)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        verify_production_revision(
            tmp_path, "a" * 40, "b" * 40, b"original prospective protocol"
        )


@pytest.mark.parametrize("producer", ["a" * 39, "g" * 40, "", "HEAD"])
def test_original_producer_commit_requires_full_literal_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, producer: str
) -> None:
    calls = git_stub(monkeypatch)
    with pytest.raises(ValueError):
        verify_production_revision(
            tmp_path, producer, "b" * 40, b"original prospective protocol"
        )
    assert calls == []
