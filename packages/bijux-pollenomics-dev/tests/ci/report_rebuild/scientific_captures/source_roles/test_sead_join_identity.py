"""Require exact join source identities in two explicit original capture contexts."""

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
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    sead_join_identity as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/sead/acquisition/full/"
_FACADE = _ROOT + "__init__.py"
_RECONCILIATION = _ROOT + "reconciliation.py"
_NAMES = (_FACADE, _RECONCILIATION)
_OPTIMIZER = "data/method-certification/author-optimizer-diagnostic-source-capture"
_CHRONOLOGY = "data/atlas/sample-chronology-source-view-capture"
_PREFIXES = (_OPTIMIZER, _CHRONOLOGY)
_OLD = b"# Own inert join source; never imported.\n# prior child label\n"
_PAIRS = ((b"# prior child label", b"# declared child label"),)
_CURRENT = _OLD.replace(*_PAIRS[0])


@dataclass
class JoinCase:
    """Own inert bytes and actual descriptor state for one fixed join coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Use the maintained wrapper without replacing its Git reader."""
        return subject.validated_declared_join_identity_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> JoinCase:
    """Commit one invented comment body and bind it through the existing parser."""
    root.mkdir()
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    target = root / name
    _write(target, _OLD)
    _git(root, "add", "--", name)
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
        "test(curation): bind inert child-key labels",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + name).decode().strip()
    logical_prefix = (
        "executions/optimizer-diagnostics/first-party-inputs/"
        if prefix == _OPTIMIZER
        else "source/"
    )
    logical = logical_prefix + name
    identity = _identity(_OLD)
    members = {logical: identity}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    mapping = json.dumps([[name, blob]], separators=(",", ":")).encode()
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
                "paths": [[logical, name]],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "join-identity",
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
        "_JOIN_IDENTITY_CONTRACTS",
        {path: (len(_OLD), identity["sha256"], _PAIRS) for path in _NAMES},
    )
    contexts = dict(subject._JOIN_IDENTITY_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], contexts[prefix][1])
    monkeypatch.setattr(subject, "_JOIN_IDENTITY_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return JoinCase(consumer, {"path": name, **identity}, logical, target, buffer)


@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize("name", _NAMES)
def test_two_original_contexts_bind_real_git_without_claiming_equal_join_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> None:
    """Use real old-member reads for each fixed path and each fixed original context."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, name)
    result = case.admit()
    assert result["classification"] == "declared_child_key_refusal_identity"
    assert result["original_member"] == case.logical
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["original_bytes"] == len(_OLD)
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["current_join_refusal_labels_intentionally_changed"] is True
    assert result["old_count_status_and_refusal_predicates_unchanged"] is True
    assert result["old_native_equal_current_join_output_claimed"] is False
    assert result["new_acquisition_or_native_execution_claimed"] is False
    assert not (case.consumer.repository / prefix / case.logical).exists()


@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize(
    "damage",
    (
        "context",
        "capture",
        "logical",
        "repository",
        "path",
        "hash",
        "size",
        "bool_size",
        "extra_field",
        "member_hash",
        "member_size",
        "group_alias",
        "duplicate_group",
        "not_detached",
        "physical_member",
        "old_body",
        "symlink",
        "ancestor_symlink",
        "hardlink",
        "stale",
        "reread_mutation",
        "reread_bytes",
    ),
)
def test_each_context_refuses_binding_and_freshness_defects_after_a_real_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str, prefix: str
) -> None:
    """Keep exact source coordinates and final current-byte observations mandatory."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, _RECONCILIATION)
    assert case.admit()["whole_old_module_reconstructed"] is True
    buffer = case.buffer
    if damage == "context":
        buffer.prefix = "data/own-unlisted-context"
    elif damage == "capture":
        buffer.descriptor.capture["sha256"] = "0" * 64
    elif damage == "logical":
        case.logical += "/alias"
    elif damage == "repository":
        buffer.repository = case.consumer.repository.parent
    elif damage == "path":
        case.row["path"] = _ROOT + "unlisted.py"
    elif damage == "hash":
        case.row["sha256"] = "0" * 64
    elif damage == "size":
        case.row["bytes"] += 1
    elif damage == "bool_size":
        case.row["bytes"] = True
    elif damage == "extra_field":
        case.row["current"] = True
    elif damage == "member_hash":
        buffer.descriptor.members[case.logical]["sha256"] = "0" * 64
    elif damage == "member_size":
        buffer.descriptor.members[case.logical]["bytes"] += 1
    elif damage == "group_alias":
        buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _FACADE)]
    elif damage == "duplicate_group":
        buffer.descriptor = replace(
            buffer.descriptor, groups=buffer.descriptor.groups * 2
        )
    elif damage == "not_detached":
        buffer.descriptor = replace(buffer.descriptor, detached=frozenset())
    elif damage == "physical_member":
        _write(case.consumer.repository / prefix / case.logical, b"# extra own bytes\n")
    elif damage == "old_body":
        buffer._payloads[case.logical] = _OLD + b"# counterfeit old bytes\n"
    elif damage == "symlink":
        backing = case.consumer.repository / "own-backing"
        case.target.rename(backing)
        case.target.symlink_to(backing)
    elif damage == "ancestor_symlink":
        parent = case.target.parent
        backing = case.consumer.repository / "own-parent"
        parent.rename(backing)
        parent.symlink_to(backing, target_is_directory=True)
    elif damage == "hardlink":
        os.link(case.target, case.consumer.repository / "own-alias")
    elif damage == "stale":
        metadata = case.consumer.repository / prefix / "capture.json"
        metadata.write_bytes(metadata.read_bytes() + b"\n")
    elif damage == "reread_mutation":
        original_match = subject.declared_join_identity_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "declared_join_identity_extension_matches",
            mutate_after_actual_inverse,
        )
    else:
        original_read = Path.read_bytes
        observations = 0

        def changing_final_read(path: Path) -> bytes:
            nonlocal observations
            body = original_read(path)
            if path == case.target:
                observations += 1
                if observations >= 2:
                    return body + b"# changed final byte observation\n"
            return body

        monkeypatch.setattr(Path, "read_bytes", changing_final_read)
    expected = (
        ReportOwnershipError
        if damage in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        if damage == "physical_member":
            index.validated_descriptor(
                case.consumer.repository, prefix, case.consumer.members
            )
        case.admit()


def _real_source_pair(name: str) -> tuple[bytes, bytes]:
    repository = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            text=True,
        ).strip()
    )
    old = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "show",
            "bfbe9a49348b8698b3dd9fa691601520af7d4930:" + name,
        ],
        cwd=repository,
    )
    current = (repository / name).read_bytes()
    assert subject.declared_join_identity_extension_matches(name, old, current)
    return old, current


@pytest.mark.parametrize("name", _NAMES)
def test_actual_whole_old_source_is_required_before_any_other_byte_refusal(
    name: str,
) -> None:
    old, current = _real_source_pair(name)
    assert frozenset(_NAMES) == subject.SEAD_JOIN_IDENTITY_SOURCES
    assert not subject.declared_join_identity_extension_matches(
        name + ".alias", old, current
    )
    assert not subject.declared_join_identity_extension_matches(
        name, old + b"\n", current
    )
    assert not subject.declared_join_identity_extension_matches(name, old, b"")
    assert not subject.declared_join_identity_extension_matches(name, old, b"x" * 16385)


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize(
    "extra", (b"\n# unreviewed\n", b"\nimport os as unreviewed\n", b"\nUNKNOWN = 1\n")
)
def test_unrelated_source_changes_cannot_borrow_a_declared_child_identity(
    name: str, extra: bytes
) -> None:
    old, current = _real_source_pair(name)
    assert not subject.declared_join_identity_extension_matches(
        name, old, current + extra
    )


@pytest.mark.parametrize(
    ("before", "after"),
    (
        (
            b'identity = f"{child_key}:{child_id}" if child_id is not None else f"row:{index}"',
            b'identity = f"row:{index}"',
        ),
        (b"if foreign_key is None:", b"if False:"),
        (
            b'"status": "complete" if unexplained_loss_count == 0 else "failed",',
            b'"status": "complete",',
        ),
        (b"key_values.append(child_id)", b"key_values.append(None)"),
    ),
)
def test_refusal_and_count_predicates_are_not_normalized_with_the_new_labels(
    before: bytes, after: bytes
) -> None:
    old, current = _real_source_pair(_RECONCILIATION)
    assert current.count(before) == 1
    assert not subject.declared_join_identity_extension_matches(
        _RECONCILIATION, old, current.replace(before, after, 1)
    )
