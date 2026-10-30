"""Bind optional literal-context source spans through real owned Git readers."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    read_blob,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    galician_context as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/adna/"
)
_SOURCE = _ROOT + "galician_sample_review.py"
_OTHER_SOURCE = _ROOT + "unlisted_source.py"
_OPTIMIZER = "data/method-certification/author-optimizer-diagnostic-source-capture"
_OLD = b"# Own inert bytes; never imported.\n# prior annotation\n# prior flag\n"
_PAIRS = (
    (b"# prior annotation", b"# optional annotation"),
    (b"# prior flag", b"# optional flag"),
)
_CURRENT = _OLD
for _previous, _qualified in _PAIRS:
    _CURRENT = _CURRENT.replace(_previous, _qualified)
_ALLOWED = ((_OPTIMIZER, _SOURCE),)


@dataclass
class GalicianCase:
    """Own inert bytes and actual descriptor state for one fixed source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Use the maintained wrapper without replacing its Git reader."""
        return subject.validated_galician_literal_context_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> GalicianCase:
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
        "test(source): bind inert context comments",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + name).decode().strip()
    assert prefix == _OPTIMIZER
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
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
        "galician_context",
        root,
        prefix,
        members,
        frozenset({logical}),
        {logical: _OLD},
        descriptor,
        [],
    )
    consumer.repin(monkeypatch)
    monkeypatch.setattr(subject, "_OLD_SOURCE_BYTES", len(_OLD))
    monkeypatch.setattr(subject, "_OLD_SOURCE_SHA256", identity["sha256"])
    monkeypatch.setattr(subject, "_OPTIONAL_CONTEXT_SPANS", _PAIRS)
    monkeypatch.setattr(subject, "_CAPTURE_SHA256", _identity(capture)["sha256"])
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return GalicianCase(consumer, {"path": name, **identity}, logical, target, buffer)


@pytest.mark.parametrize(("prefix", "name"), _ALLOWED)
def test_own_optional_spans_use_real_git_without_native_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> None:
    """Keep old member identity separate from intentional current authority changes."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, name)
    result = case.admit()
    assert (
        result["classification"] == "finite_optional_galician_literal_context_extension"
    )
    assert result["original_member"] == case.logical
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["original_bytes"] == len(_OLD)
    assert result["whole_old_module_reconstructed"] is True
    assert result["old_default_successful_input_path_preserved"] is True
    assert result["optional_literal_annotation_feature_added"] is True
    assert result["historical_native_equal_current_claimed"] is False
    assert result["new_native_or_model_execution_claimed"] is False
    assert not (case.consumer.repository / prefix / case.logical).exists()


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
        "hardlink",
        "ancestor_symlink",
        "oversize",
        "stale",
        "reread_mutation",
    ),
)
def test_binding_and_freshness_refuse_after_a_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Preserve fixed scope, detached correspondence and fresh current bytes."""
    prefix = _OPTIMIZER
    case = _case(tmp_path / "repository", monkeypatch, prefix, _SOURCE)
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
        case.row["path"] = _ROOT + "analysis/unlisted.py"
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
        buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _OTHER_SOURCE)]
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
    elif damage == "hardlink":
        os.link(case.target, case.consumer.repository / "own-alias")
    elif damage == "ancestor_symlink":
        directory = case.target.parent
        backing = directory.with_name("own-context-backing")
        directory.rename(backing)
        directory.symlink_to(backing, target_is_directory=True)
    elif damage == "oversize":
        case.target.write_bytes(b"#" * (32 * 1024 + 1))
    elif damage == "stale":
        metadata = case.consumer.repository / prefix / "capture.json"
        metadata.write_bytes(metadata.read_bytes() + b"\n")
    else:
        original = buffer.fresh
        observations = 0

        def mutate_during_final_evidence_observation() -> None:
            nonlocal observations
            observations += 1
            original()
            if observations == 3:
                case.target.write_bytes(_CURRENT + b"# concurrent edit\n")

        monkeypatch.setattr(buffer, "fresh", mutate_during_final_evidence_observation)
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


@pytest.mark.parametrize(
    "damage",
    (
        "partial",
        "wrong_pair",
        "comment",
        "code",
        "import",
        "duplicate",
        "old_hash",
        "old_size",
    ),
)
def test_whole_old_bytes_remain_required_outside_exact_pairs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Refuse every unreviewed byte rather than pinning the current postimage."""
    case = _case(tmp_path / "repository", monkeypatch, _OPTIMIZER, _SOURCE)
    assert case.admit()["whole_old_module_reconstructed"] is True
    captured, current = _OLD, _CURRENT
    if damage == "partial":
        current = current.replace(_PAIRS[1][1], _PAIRS[1][0])
    elif damage == "wrong_pair":
        current = current.replace(_PAIRS[0][1], b"# unrelated optional context")
    elif damage == "comment":
        current += b"# unrelated comment\n"
    elif damage == "code":
        current += b"unexpected_action()\n"
    elif damage == "import":
        current = b"import unexpected\n" + current
    elif damage == "duplicate":
        current += _PAIRS[0][1] + b"\n"
    elif damage == "old_hash":
        captured = captured.replace(b"inert", b"other")
    else:
        captured += b"\n"
    assert not subject.galician_literal_context_extension_matches(captured, current)


def _real_original_and_current() -> tuple[bytes, bytes]:
    """Read genuine original Git bytes and the installed candidate source, never execute them."""
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    captured = read_blob(
        root,
        GitSourceMember(
            _SOURCE,
            _SOURCE,
            "484fd110a3a0785c264a26a4d84bcccf12a8439e",
            "2fec7999342ccfa0f2257507b125695b9c3e5b91",
            "284847d0e77c2bf6b1592ea028f92296f9f6565943c8fe6deb1116f51ac04d07",
            4312,
        ),
    )
    return captured, (root / _SOURCE).read_bytes()


def test_actual_optional_spans_reconstruct_the_genuine_old_module() -> None:
    """Keep the actual fixed production contract separate from invented fixture seals."""
    captured, current = _real_original_and_current()
    assert subject.galician_literal_context_extension_matches(captured, current)
    assert len(captured) == subject._OLD_SOURCE_BYTES == 4312
    assert hashlib.sha256(captured).hexdigest() == subject._OLD_SOURCE_SHA256


@pytest.mark.parametrize(
    "damage",
    (
        "default",
        "CLI",
        "producer",
        "species",
        "cells",
        "comment",
        "import",
        "partial",
    ),
)
def test_real_optional_spans_refuse_other_byte_changes(damage: str) -> None:
    """Preserve every default, source/refusal, species and atomic-publication clause."""
    captured, current = _real_original_and_current()
    assert subject.galician_literal_context_extension_matches(captured, current)
    if damage == "default":
        changed = current.replace(
            b"literal_context: bool = False", b"literal_context: bool = True"
        )
    elif damage == "CLI":
        changed = current.replace(b'action="store_true"', b'action="store_false"')
    elif damage == "producer":
        changed = current.replace(b"!= CORE_SHA256", b"== CORE_SHA256")
    elif damage == "species":
        changed = current.replace(b'"Bos taurus": 8', b'"Bos taurus": 9')
    elif damage == "cells":
        changed = current.replace(
            b'context.get("selected_cell_count") != 110',
            b'context.get("selected_cell_count") != 111',
        )
    elif damage == "comment":
        changed = current + b"# unknown annotation\n"
    elif damage == "import":
        changed = b"import unexpected\n" + current
    else:
        changed = current.replace(
            b'    parser.add_argument("--literal-context", action="store_true")\n', b""
        )
    assert changed != current
    assert not subject.galician_literal_context_extension_matches(captured, changed)


def test_swedish_capture_does_not_acquire_this_optional_context_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Confine the new source law to its one reviewed optimizer capture."""
    case = _case(tmp_path / "repository", monkeypatch, _OPTIMIZER, _SOURCE)
    assert case.admit()["whole_old_module_reconstructed"] is True
    case.buffer.prefix = "data/surface-reference/swedish-direct-pollen-source-capture"
    with pytest.raises(ReportRebuildError, match="binding differs"):
        case.admit()
