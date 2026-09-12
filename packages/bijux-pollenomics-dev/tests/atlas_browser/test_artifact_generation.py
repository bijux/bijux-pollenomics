"""Frozen generator launch boundaries and input/output receipts."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.atlas_browser import artifact_candidate as audit
from bijux_pollenomics_dev.ci.atlas_browser import artifact_generation as generation
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    AtlasArtifactCandidate,
    AtlasBrowserContractError,
)
from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand

from .artifact_fixtures import artifact_plan


@pytest.mark.parametrize(
    "failure",
    [None, "dirty_source", "input_mutation", "process_failure", "receipt_in_input"],
)
def test_generator_records_only_successful_frozen_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    candidate = plan.candidate
    assert isinstance(candidate, AtlasArtifactCandidate)
    old_receipt = json.loads((tmp_path / candidate.generator_receipt).read_bytes())
    for directory in (tmp_path / "artifacts/source").iterdir():
        if directory.is_dir():
            shutil.copytree(directory, tmp_path / directory.name)
        else:
            shutil.copy2(directory, tmp_path / directory.name)
    monkeypatch.setattr(generation, "committed_source", audit.committed_source)
    monkeypatch.setattr(
        generation,
        "git_bytes",
        lambda _root, *_args: b"a" * 40 if _args[-1] == "HEAD" else b"b" * 40,
    )
    called: list[tuple[str, ...]] = []

    def launch(
        command: tuple[str, ...], *, cwd: Path, timeout_seconds: int
    ) -> CompletedCommand:
        called.append(command)
        assert timeout_seconds == 120
        assert cwd == tmp_path / "artifacts/captured-source"
        assert command[1:4] == ("-I", "-c", audit.GENERATOR_SCRIPT)
        shutil.copytree(tmp_path / candidate.presentation_root, Path(command[-1]))
        if failure == "input_mutation":
            (tmp_path / "artifacts/input/extra").write_text("mutated")
        return CompletedCommand(
            command=command,
            returncode=1 if failure == "process_failure" else 0,
            stdout=json.dumps(old_receipt["runtime"]).encode(),
            stderr=b"",
            duration_seconds=0.1,
            timed_out=False,
            termination="not_required",
        )

    monkeypatch.setattr(generation, "run_bounded_argv", launch)
    if failure == "dirty_source":
        (tmp_path / "uv.lock").write_text("uncommitted")
    receipt = tmp_path / (
        "artifacts/input/receipt.json"
        if failure == "receipt_in_input"
        else "artifacts/new-receipt.json"
    )
    arguments: dict[str, Any] = {
        "repository_root": tmp_path,
        "source_root": tmp_path / "artifacts/captured-source",
        "product_directory": tmp_path / "artifacts/input",
        "expected_product_manifest_sha256": candidate.product_manifest_sha256,
        "geometry_path": tmp_path / "artifacts/geometry.json",
        "expected_geometry_sha256": candidate.display_geometry_sha256,
        "destination": tmp_path / "artifacts/generated",
        "receipt_path": receipt,
        "python_binary": Path("/python"),
    }
    if failure:
        with pytest.raises(AtlasBrowserContractError):
            generation.generate_artifact_candidate(**arguments)
        assert not receipt.exists()
        if failure in {"dirty_source", "receipt_in_input"}:
            assert not called
            assert not (tmp_path / "artifacts/captured-source").exists()
    else:
        generated = generation.generate_artifact_candidate(**arguments)
        payload = json.loads(receipt.read_bytes())
        assert generated.generator_receipt_sha256 == audit.sha256(receipt.read_bytes())
        assert payload["runtime"] == old_receipt["runtime"]
        assert payload["invocation"] == {
            "argv": list(called[0]),
            "cwd": str(tmp_path / "artifacts/captured-source"),
            "python_binary": "/python",
        }
        assert payload["source_files"] == old_receipt["source_files"]
        assert payload["source_relation"] == "committed_tree"
