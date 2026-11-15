"""Qualify only fixed facade bytes through the original inert Git source owners."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as chronology,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as router,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    import_facades as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/"
_SOURCES = tuple(
    _ROOT + suffix
    for suffix in (
        "__init__.py",
        "collection/__init__.py",
        "collection/sources/neotoma/__init__.py",
        "reporting/__init__.py",
    )
)
_CONTEXTS = (
    "data/atlas/sample-chronology-source-view-capture",
    "data/method-certification/author-optimizer-diagnostic-source-capture",
)
_OLD = b"# Inert original import-facade fixture, never executed.\n"
_CURRENT = b"# Inert current import-facade fixture, never executed.\n"


def test_role_is_limited_to_declared_facades_and_original_capture_epochs() -> None:
    assert frozenset(_SOURCES) == subject.PUBLIC_IMPORT_FACADE_SOURCES
    assert set(subject._SOURCE_PAIRS) == set(_SOURCES)
    assert {
        _CONTEXTS[0]: (
            "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
            "source/",
        ),
        _CONTEXTS[1]: (
            "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
            "executions/optimizer-diagnostics/first-party-inputs/",
        ),
    } == subject._CAPTURE_CONTEXTS


@dataclass
class FacadeCase:
    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        return subject.validated_import_facade_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )

    def dispatch(self) -> object:
        if self.consumer.prefix == _CONTEXTS[1]:
            return router.validated_current_scientific_source(
                self.consumer.repository, self.row, self.logical, self.buffer
            )
        chronology._validate_current_source(
            self.consumer.repository,
            self.row["path"],
            self.logical,
            _OLD,
            self.row["sha256"],
            self.buffer.detached,
            source_buffer=self.buffer,
        )
        return None


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> FacadeCase:
    root.mkdir()
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    target = root / source
    _write(target, _OLD)
    _git(root, "add", "--", source)
    _git(
        root,
        "-c",
        "user.name=Bijux fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--no-gpg-sign",
        "-m",
        "test(imports): retain inert facade source",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + source).decode().strip()
    context = subject._CAPTURE_CONTEXTS[prefix]
    logical = context[1] + source
    identity = _identity(_OLD)
    members = {logical: identity}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    mapping = json.dumps([[source, blob]], separators=(",", ":")).encode()
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": "capture.json", **_identity(capture)},
        "historical_native_epochs": [revision],
        "source_revision_correspondence": [
            {"historical_source_commit": revision, "source_revision": revision}
        ],
        "git_groups": [
            {
                "historical_source_commit": revision,
                "source_revision": revision,
                "member_count": 1,
                "git_entries_sha256": hashlib.sha256(mapping).hexdigest(),
                "paths": [[logical, source]],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "qualification",
        root,
        prefix,
        members,
        frozenset({logical}),
        {logical: _OLD},
        descriptor,
        [],
    )
    consumer.repin(monkeypatch)
    monkeypatch.setattr(
        subject,
        "_SOURCE_PAIRS",
        {
            name: (
                len(_OLD),
                identity["sha256"],
                len(_CURRENT),
                _identity(_CURRENT)["sha256"],
            )
            for name in _SOURCES
        },
    )
    contexts = dict(subject._CAPTURE_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], context[1])
    monkeypatch.setattr(subject, "_CAPTURE_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    target.write_bytes(_CURRENT)
    return FacadeCase(consumer, {"path": source, **identity}, logical, target, buffer)


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize("source", _SOURCES)
def test_fixed_pair_uses_real_git_and_both_maintained_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    role = case.admit()
    assert role["classification"] == "fixed_public_import_facade_correspondence"
    assert role["current_source_or_numerical_equivalence_claimed"] is False
    assert role["historical_execution_epoch_changed"] is False
    assert role["current_api_qualification_required_separately"] is True
    case.dispatch()
    assert case.buffer.read_source(case.logical) == _OLD
    assert not (case.consumer.repository / prefix / case.logical).exists()


@pytest.mark.parametrize("source", _SOURCES)
def test_actual_two_git_witnesses_bind_whole_old_and_current_facades(
    source: str,
) -> None:
    repository = Path(__file__).resolve().parents[7]
    originals = []
    for revision in (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ):
        old = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        originals.append(old)
    assert originals[0] == originals[1]
    current = (repository / source).read_bytes()
    assert subject.import_facade_pair_matches(source, originals[0], current)
    assert not subject.import_facade_pair_matches(
        source, originals[0] + b"# foreign\n", current
    )
    assert not subject.import_facade_pair_matches(
        source, originals[0], current + b"# foreign\n"
    )
    assert not subject.import_facade_pair_matches(
        _ROOT + "analysis/__init__.py", originals[0], current
    )


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize(
    "mutation",
    (
        "current",
        "historical",
        "unknown_source",
        "logical",
        "detached",
        "mapping",
        "member",
        "capture",
        "context",
        "source_symlink",
        "source_hardlink",
        "changed_during_read",
        "changed_after_pair",
        "capture_changed_after_pair",
        "repository_alias",
    ),
)
def test_successful_pair_then_each_binding_and_byte_mutation_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, mutation: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, prefix, _SOURCES[0])
    case.admit()
    case.dispatch()
    if mutation == "current":
        case.target.write_bytes(_CURRENT + b"# unexpected\n")
    elif mutation == "historical":
        case.row = {**case.row, "sha256": "0" * 64}
    elif mutation == "unknown_source":
        case.row = {**case.row, "path": _ROOT + "analysis/__init__.py"}
    elif mutation == "logical":
        case.logical = "foreign/" + case.row["path"]
    elif mutation == "detached":
        case.buffer = replace(
            case.buffer,
            descriptor=replace(case.buffer.descriptor, detached=frozenset()),
        )
    elif mutation == "mapping":
        group = {
            **case.buffer.descriptor.groups[0],
            "resolved_paths": [[case.logical, "packages/foreign.py"]],
        }
        case.buffer = replace(
            case.buffer, descriptor=replace(case.buffer.descriptor, groups=(group,))
        )
    elif mutation == "member":
        case.buffer = replace(
            case.buffer,
            descriptor=replace(
                case.buffer.descriptor, members={case.logical: _identity(_CURRENT)}
            ),
        )
    elif mutation == "capture":
        case.buffer = replace(
            case.buffer,
            descriptor=replace(
                case.buffer.descriptor,
                capture={**case.buffer.descriptor.capture, "sha256": "0" * 64},
            ),
        )
    elif mutation == "context":
        case.buffer = replace(case.buffer, prefix="data/foreign-import-context")
    elif mutation == "repository_alias":
        alias = case.consumer.repository.parent / "repository-alias"
        alias.symlink_to(case.consumer.repository, target_is_directory=True)
        case.consumer.repository = alias
    elif mutation in {"source_symlink", "source_hardlink"}:
        original = case.target.with_name("retained-current.py")
        case.target.rename(original)
        if mutation == "source_symlink":
            case.target.symlink_to(original)
        else:
            os.link(original, case.target)
    elif mutation == "changed_during_read":
        original_read = SourceCapsule.read_source

        def changing(buffer: SourceCapsule, logical: str) -> bytes:
            old = original_read(buffer, logical)
            case.target.write_bytes(_CURRENT + b"# concurrent edit\n")
            return old

        monkeypatch.setattr(SourceCapsule, "read_source", changing)
    else:
        original_match = subject.import_facade_pair_matches

        def changing_pair(name: str, old: bytes, current: bytes) -> bool:
            valid = original_match(name, old, current)
            if mutation == "changed_after_pair":
                replacement = case.target.with_name("replacement-facade.py")
                replacement.write_bytes(current)
                replacement.replace(case.target)
            else:
                capture = case.consumer.repository / prefix / "capture.json"
                capture.write_bytes(capture.read_bytes() + b" ")
            return valid

        monkeypatch.setattr(subject, "import_facade_pair_matches", changing_pair)
    with pytest.raises(
        (ReportRebuildError, ReportOwnershipError),
        match="(?i)facade|source|confined",
    ):
        case.admit()
    with pytest.raises((ReportRebuildError, ReportOwnershipError)):
        case.dispatch()
