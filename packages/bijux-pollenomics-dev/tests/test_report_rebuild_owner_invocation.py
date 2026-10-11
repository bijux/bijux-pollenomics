"""Bind local configured-owner artifacts to the declared producer invocation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as owner_runner
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.verification import (
    _require_current_owner_inputs,
)

OWNER_ID = "domain/summary"
MODULE = "bijux_pollenomics_dev.source_completion.example"
MODULE_PATH = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/example.py"
PARENT = "docs/report/domain/source.json"
OUTPUT = "docs/report/domain/summary.json"


def _write(repository: Path, name: str, content: str) -> None:
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _write(tmp_path, MODULE_PATH, "# maintained producer\n")
    _write(tmp_path, PARENT, '{"source": 1}\n')
    _write(tmp_path, OUTPUT, '{"summary": 1}\n')
    _write(
        tmp_path,
        "configs/ci/report-ownership.json",
        json.dumps(
            {
                "owners": [
                    {
                        "owner_id": OWNER_ID,
                        "role": "generated_owner",
                        "paths": [OUTPUT],
                        "producer_paths": [MODULE_PATH],
                        "producer_inputs": [PARENT],
                    }
                ]
            }
        ),
    )
    _write(
        tmp_path,
        "configs/ci/report-owner-execution.json",
        json.dumps(
            {
                "schema_version": owner_runner.SCHEMA,
                "owners": [
                    {
                        "owner_id": OWNER_ID,
                        "module": MODULE,
                        "source_paths": {"summary.json": OUTPUT},
                        "source_arguments": [{"flag": "--screen", "path": PARENT}],
                        "output_mode": "single_file",
                        "timeout_seconds": 120,
                    }
                ],
            }
        ),
    )
    # Isolate invocation checks from the separately exercised full ownership tree.
    monkeypatch.setattr(
        owner_runner, "check_report_ownership", lambda *_args, **_kwargs: None
    )
    return tmp_path


def test_local_configured_owner_guard_accepts_exact_declaration(
    repository: Path,
) -> None:
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    _require_current_owner_inputs(
        {
            "producer_inputs": producer_input_identity(selected.inputs, repository),
            "source_paths": selected.source_paths,
            "producer_command": list(selected.command),
        },
        repository,
        OWNER_ID,
        {"tracked_report_root": "docs/report"},
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-code",
        "missing-data",
        "extra-input",
        "unreadable-extra",
        "relabelled-input",
        "absolute-input-alias",
        "command",
        "source-map",
        "changed-data",
    ],
)
def test_local_configured_owner_guard_rejects_self_consistent_receipt_drift(
    repository: Path, mutation: str
) -> None:
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    inputs: dict[str, Any] = producer_input_identity(selected.inputs, repository)
    manifest: dict[str, Any] = {
        "producer_inputs": inputs,
        "source_paths": selected.source_paths.copy(),
        "producer_command": list(selected.command),
    }
    if mutation == "missing-code":
        inputs.pop(MODULE_PATH)
    elif mutation == "missing-data":
        inputs.pop(PARENT)
    elif mutation == "extra-input":
        _write(repository, "extra.csv", "undeclared input\n")
        inputs.update(
            producer_input_identity({"extra.csv": repository / "extra.csv"}, repository)
        )
    elif mutation == "unreadable-extra":
        inputs["unreadable.csv"] = {
            "path": "unreadable.csv",
            "sha256": "0" * 64,
            "size": 1,
        }
    elif mutation == "relabelled-input":
        inputs["wrong-label"] = inputs.pop(PARENT)
    elif mutation == "absolute-input-alias":
        inputs[PARENT]["path"] = str(repository / PARENT)
    elif mutation == "command":
        manifest["producer_command"] = [sys.executable, "-c", "pass", "{output_root}"]
    elif mutation == "source-map":
        manifest["source_paths"] = {"unconfigured.json": "domain/summary.json"}
    else:
        _write(repository, PARENT, '{"changed": 2}\n')
    with pytest.raises(
        ReportRebuildError,
        match="configured owner invocation or input declaration differs",
    ):
        _require_current_owner_inputs(
            manifest, repository, OWNER_ID, {"tracked_report_root": "docs/report"}
        )


@pytest.mark.parametrize("configuration_present", [False, True])
def test_unconfigured_independent_owner_retains_its_input_contract(
    repository: Path, configuration_present: bool
) -> None:
    if not configuration_present:
        (repository / owner_runner.DEFAULT_CONFIGURATION).unlink()
    manifest = {
        "producer_inputs": producer_input_identity(
            {"independent-source": repository / PARENT}, repository
        ),
        "source_paths": {"summary.json": "domain/summary.json"},
        "producer_command": [sys.executable, "-c", "pass", "{output_root}"],
    }
    policy: dict[str, object] = {"tracked_report_root": "docs/report"}
    _require_current_owner_inputs(manifest, repository, "independent/summary", policy)
    _write(repository, PARENT, '{"changed": 2}\n')
    with pytest.raises(ReportRebuildError, match="owner producer inputs changed"):
        _require_current_owner_inputs(
            manifest, repository, "independent/summary", policy
        )


@pytest.mark.parametrize("mutation", ["none", "missing-code", "command", "source-map"])
def test_owner_artifact_loader_enforces_local_configured_invocation(
    repository: Path, mutation: str
) -> None:
    from bijux_pollenomics_dev.ci.rebuild_reports import inventory_reports
    from bijux_pollenomics_dev.ci.report_rebuild.contracts import RebuildBinding
    from bijux_pollenomics_dev.ci.report_rebuild.evidence import inventory_json
    from bijux_pollenomics_dev.ci.report_rebuild.verification import _load_owner_outputs

    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    policy: dict[str, Any] = {
        "tracked_report_root": "docs/report",
        "volatile_text_rules": [],
    }
    binding = RebuildBinding("a" * 64, {"mode": "fixture"}, "b" * 64)
    owners_root = repository / "artifacts/owners/reference"
    evidence = owners_root / OWNER_ID
    target = evidence / "output/domain/summary.json"
    target.parent.mkdir(parents=True)
    target.write_bytes((repository / OUTPUT).read_bytes())
    producer_root = evidence / "producer-output"
    producer_root.mkdir()
    command = list(selected.command)
    inputs: dict[str, Any] = producer_input_identity(selected.inputs, repository)
    sources = selected.source_paths.copy()
    if mutation == "missing-code":
        inputs.pop(MODULE_PATH)
    elif mutation == "command":
        command = [sys.executable, "-c", "pass", "{output_root}"]
    elif mutation == "source-map":
        sources = {"unconfigured.json": "domain/summary.json"}
    manifest = {
        "schema_version": "partitioned-report-owner.v1",
        "binding": binding.as_json(),
        "inventory": inventory_json(inventory_reports(evidence / "output", policy)),
        "lane": "reference",
        "owner_id": OWNER_ID,
        "producer_command": command,
        "producer_argv": [
            arg.replace("{output_root}", str(producer_root)) for arg in command
        ],
        "producer_output_root": str(producer_root),
        "producer_inputs": inputs,
        "source_paths": sources,
    }
    (evidence / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    arguments: dict[str, Any] = {
        "artifacts_root": owners_root,
        "repo_root": repository,
        "lane": "reference",
        "binding": binding,
        "policy": policy,
        "publisher_ids": {"world"},
    }
    if mutation == "none":
        assert set(_load_owner_outputs(**arguments)) == {OWNER_ID}
    else:
        with pytest.raises(
            ReportRebuildError,
            match="configured owner invocation or input declaration differs",
        ):
            _load_owner_outputs(**arguments)
