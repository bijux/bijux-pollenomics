"""Retain actual historical PDF producer authority across renderer changes."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "paper_export_producer_identity", ROOT / "reports/exports/papers/verify.py"
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)
PRODUCER = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/export.py"
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def source_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Bijux")
    _git(tmp_path, "config", "user.email", "tests@bijux.invalid")
    from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
        index as source_index,
    )

    registry = "configs/ci/source-retention/index.json"
    registry_raw = b'{"schema_version":"retained-source-index.v1","capsules":{},"source_revisions":{}}\n'
    registry_file = tmp_path / registry
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_bytes(registry_raw)
    monkeypatch.setattr(
        source_index,
        "INDEX_SHA256",
        hashlib.sha256(registry_raw).hexdigest(),
    )
    monkeypatch.setattr(source_index, "INDEX_BYTES", len(registry_raw))
    path = tmp_path / PRODUCER
    path.parent.mkdir(parents=True)
    path.write_text('"""Original renderer."""\n')
    original_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _git(tmp_path, "add", PRODUCER, registry)
    _git(tmp_path, "commit", "-qm", "test(reports): define original renderer")
    original = _git(tmp_path, "rev-parse", "HEAD")
    path.write_text('"""Successor renderer."""\n')
    successor_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _git(tmp_path, "add", PRODUCER)
    _git(tmp_path, "commit", "-qm", "test(reports): define successor renderer")
    successor = _git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.setattr(VERIFIER, "ROOT", tmp_path)
    return {
        "producer_revision": original,
        "producer_sha256": {PRODUCER: original_digest},
        "successor": successor,
        "successor_digest": successor_digest,
    }


def test_current_renderer_does_not_replace_retained_production_identity(
    source_history: dict[str, Any],
) -> None:
    VERIFIER.verify_producer(source_history, {})


def test_separately_rebuilt_paper_verifies_its_actual_successor(
    source_history: dict[str, Any],
) -> None:
    VERIFIER.verify_producer(
        source_history,
        {
            "producer_revision": source_history["successor"],
            "producer_sha256": {PRODUCER: source_history["successor_digest"]},
        },
    )


def test_forged_historical_hash_is_rejected(source_history: dict[str, Any]) -> None:
    source_history["producer_sha256"][PRODUCER] = "0" * 64
    with pytest.raises(ValueError, match="Historical export producer changed"):
        VERIFIER.verify_producer(source_history, {})


@pytest.mark.parametrize("field", ["producer_revision", "producer_sha256"])
def test_partial_successor_identity_is_rejected(
    source_history: dict[str, Any], field: str
) -> None:
    with pytest.raises(ValueError, match="complete producer identity"):
        VERIFIER.verify_producer(source_history, {field: source_history[field]})


def test_missing_historical_revision_is_rejected(
    source_history: dict[str, Any],
) -> None:
    source_history["producer_revision"] = "a" * 40
    with pytest.raises(ValueError, match="absent from accepted source history"):
        VERIFIER.verify_producer(source_history, {})


def test_incomplete_successor_closure_is_rejected(
    source_history: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="complete exact historical producer closure"):
        VERIFIER.verify_producer(
            source_history,
            {"producer_revision": source_history["successor"], "producer_sha256": {}},
        )


def test_source_path_outside_renderer_owner_is_rejected(
    source_history: dict[str, Any],
) -> None:
    source_history["producer_sha256"] = {"README.md": "0" * 64}
    with pytest.raises(ValueError, match="Historical export producer changed"):
        VERIFIER.verify_producer(source_history, {})
