"""Bind token-parser source spans through real owned Git readers."""

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
    reference_vector_precision as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/"
_SOURCE = _ROOT + "reference_replay.py"
_SOURCES = (
    _SOURCE,
    _ROOT + "live_reference_comparison.py",
    _ROOT + "retained_reference/comparison.py",
)
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
_LINUX = "data/method-certification/linux-r-source-capture"
_ALLOWED = tuple((prefix, name) for prefix in (_OPTIMIZER, _LINUX) for name in _SOURCES)


@dataclass
class ReferenceVectorCase:
    """Own inert bytes and actual descriptor state for one fixed source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Use the maintained wrapper without replacing its Git reader."""
        return subject.validated_reference_vector_precision_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> ReferenceVectorCase:
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
    lane = (
        "executions/optimizer-diagnostics/first-party-inputs/"
        if prefix == _OPTIMIZER
        else "source/"
    )
    logical = lane + name
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
        "reference_vector_precision",
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
        subject, "_REFERENCE_VECTOR_IDENTITIES", {name: (len(_OLD), identity["sha256"])}
    )
    monkeypatch.setattr(subject, "_REFERENCE_VECTOR_SPANS", {name: _PAIRS})
    monkeypatch.setattr(
        subject,
        "_REFERENCE_VECTOR_CAPTURES",
        {prefix: (_identity(capture)["sha256"], lane)},
    )
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return ReferenceVectorCase(
        consumer, {"path": name, **identity}, logical, target, buffer
    )


@pytest.mark.parametrize(("prefix", "name"), _ALLOWED)
def test_parser_spans_bind_both_contexts_and_three_paths_without_native_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> None:
    """Keep old member identity separate from intentional current authority changes."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, name)
    result = case.admit()
    assert result["classification"] == "finite_reference_vector_precision_extension"
    assert result["original_member"] == case.logical
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["original_bytes"] == len(_OLD)
    assert result["whole_old_module_reconstructed"] is True
    assert result["current_numeric_parser_changes_binary64_coordinates"] is True
    assert result["current_csv_token_lexical_controls_required"] is True
    assert result["historical_native_outputs_equal_current_claimed"] is False
    assert result["historical_outputs_regenerated"] is False
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
@pytest.mark.parametrize("prefix", (_OPTIMIZER, _LINUX))
def test_binding_and_freshness_refuse_after_a_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str, prefix: str
) -> None:
    """Preserve fixed scope, detached correspondence and fresh current bytes."""
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
        case.target.write_bytes(b"#" * (128 * 1024 + 1))
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
    assert not subject.reference_vector_precision_matches(_SOURCE, captured, current)


_REAL_OLD = {
    _ROOT + "live_reference_comparison.py": (
        "41298ace143d003247628443f9d7d9196472adf1",
        "8e725129e23f92c594084116c0d2a5e282af9fb71048b28ea58adac3f2e460d2",
        12289,
    ),
    _ROOT + "reference_replay.py": (
        "f1d600eb09099ec5fa4fd6382b2a5b0ddaf57808",
        "09414776bf42a8ae475e55d84a8874ba8afdc83523b845fd11ec4944cbdaf1fa",
        12286,
    ),
    _ROOT + "retained_reference/comparison.py": (
        "94886d438835e1b7ec232be1acace4a0b635ff57",
        "3dce275e685e0b868bf54f3b3fece648fc0be28089fafe46739f8c0e9844c3f5",
        12359,
    ),
}


def _actual_old_and_current(name: str) -> tuple[bytes, bytes]:
    """Read three authenticated normal Git objects and current bytes without imports."""
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    blob, checksum, size = _REAL_OLD[name]
    captured = read_blob(
        root,
        GitSourceMember(
            name, name, "c601b9c7d7ad91421e96b4de25004f82b256f23a", blob, checksum, size
        ),
    )
    return captured, (root / name).read_bytes()


@pytest.mark.parametrize("name", _SOURCES)
def test_actual_three_reader_sources_reconstruct_whole_original_bytes(
    name: str,
) -> None:
    """Keep production old identities separate from fixture-only inert contracts."""
    old, current = _actual_old_and_current(name)
    assert subject.reference_vector_precision_matches(name, old, current)
    assert (
        len(old),
        hashlib.sha256(old).hexdigest(),
    ) == subject._REFERENCE_VECTOR_IDENTITIES[name]


@pytest.mark.parametrize("name", _SOURCES)
@pytest.mark.parametrize(
    "damage",
    (
        "unrelated_comment",
        "new_import",
        "code",
        "partial",
        "wrong_token",
        "old_hash",
        "old_size",
        "unknown_path",
    ),
)
def test_actual_reader_spans_refuse_every_other_byte(name: str, damage: str) -> None:
    """Preserve current IO/refusal functions and unknown code outside the reviewed parser."""
    old, current = _actual_old_and_current(name)
    assert subject.reference_vector_precision_matches(name, old, current)
    tested_name = name
    if damage == "unrelated_comment":
        current += b"# unknown annotation\n"
    elif damage == "new_import":
        current = b"import unexpected\n" + current
    elif damage == "code":
        current += b"unexpected_action()\n"
    elif damage == "partial":
        previous, inserted = subject._REFERENCE_VECTOR_SPANS[name][0]
        assert current.count(inserted) == 1
        current = current.replace(inserted, previous, 1)
    elif damage == "wrong_token":
        assert b"numeric_vector_values" in current
        current = current.replace(b"numeric_vector_values", b"wrong_token_parser", 1)
    elif damage == "old_hash":
        old = old.replace(b"from", b"xxxx", 1)
    elif damage == "old_size":
        old += b"\n"
    else:
        tested_name = _ROOT + "unknown_reader.py"
    assert not subject.reference_vector_precision_matches(tested_name, old, current)
