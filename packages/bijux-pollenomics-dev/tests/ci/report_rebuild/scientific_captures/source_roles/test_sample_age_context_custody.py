"""Keep additive chronology context bound to original bytes and explicit refusals."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
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
    sample_age_context as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_NAMES = tuple(sorted(subject.SAMPLE_AGE_CONTEXT_SOURCES))
_CONTEXTS = tuple(subject._SAMPLE_AGE_CONTEXT_CAPTURES)
_ACCEPTED = "b08b9afe36806b78436a6ba80883cf9fbcc4fadd"
_ANCESTORS = (
    "f5ab77edcd3affee65723074d21b83161b4bf542",
    "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
)
_OLD = b"# Own inert chronology witness; never imported.\n# old context\n"
_PAIR = (b"# old context\n", b"# additive context and explicit refusal\n")
_CURRENT = _OLD.replace(*_PAIR)


@dataclass
class ContextCase:
    """Hold one invented comment object behind the real retained-source boundary."""

    consumer: Consumer
    name: str
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Observe the actual source role, with no mocked acceptance result."""
        return subject.validated_sample_age_context_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, name: str, prefix: str
) -> ContextCase:
    """Commit only invented comments under one of the fixed normal source names."""
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
        "test(chronology): retain owned context comments",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + name).decode().strip()
    context = subject._SAMPLE_AGE_CONTEXT_CAPTURES[prefix]
    logical = context[1] + name
    identity = _identity(_OLD)
    members = {logical: identity}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
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
                "git_entries_sha256": _identity(_encoded([[name, blob]]).rstrip(b"\n"))[
                    "sha256"
                ],
                "paths": [[logical, name]],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "sample-age",
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
        "_SAMPLE_AGE_CONTEXT_CONTRACTS",
        {name: (len(_OLD), identity["sha256"], (_PAIR,))},
    )
    contexts = dict(subject._SAMPLE_AGE_CONTEXT_CAPTURES)
    contexts[prefix] = (_identity(capture)["sha256"], context[1])
    monkeypatch.setattr(subject, "_SAMPLE_AGE_CONTEXT_CAPTURES", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return ContextCase(
        consumer, name, {"path": name, **identity}, logical, target, buffer
    )


def _dispatch(case: ContextCase) -> object:
    if case.consumer.prefix == _CONTEXTS[0]:
        return router.validated_current_scientific_source(
            case.consumer.repository, case.row, case.logical, case.buffer
        )
    chronology._validate_current_source(
        case.consumer.repository,
        case.name,
        case.logical,
        _OLD,
        _identity(_OLD)["sha256"],
        case.buffer.detached,
        source_buffer=case.buffer,
    )
    return None


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_fixed_contexts_report_addition_without_native_or_output_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, prefix: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, name, prefix)
    role = case.admit()
    assert role["classification"] == "additive_sample_age_source_context"
    assert role["original_member"] == case.logical
    assert role["whole_old_module_reconstructed"] is True
    assert role["old_selected_chronology_fields_preserved"] is True
    assert role["source_context_and_refusal_contract_intentionally_extended"] is True
    for key in (
        "current_provenance_output_equal_historical_claimed",
        "historical_native_execution_equal_current_claimed",
        "new_scientific_admission_claimed",
        "new_acquisition_or_native_execution_claimed",
        "historical_outputs_regenerated",
    ):
        assert role[key] is False


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_actual_owning_dispatch_accepts_only_the_complete_reviewed_addition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, prefix: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, name, prefix)
    assert case.admit()["whole_old_module_reconstructed"] is True
    role = _dispatch(case)
    if prefix == _CONTEXTS[0]:
        assert isinstance(role, dict)
        assert role["classification"] == "additive_sample_age_source_context"
    else:
        assert role is None
    case.target.write_bytes(_CURRENT + b"# unreviewed residual\n")
    with pytest.raises(ReportRebuildError):
        _dispatch(case)


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize(
    "damage",
    [
        "context",
        "capture",
        "logical",
        "path",
        "hash",
        "bool_size",
        "member",
        "group",
        "duplicate_group",
        "not_detached",
        "old_body",
        "physical_member",
        "symlink",
        "ancestor_symlink",
        "hardlink",
        "stale",
        "concurrent",
        "final_read",
    ],
)
def test_binding_and_current_observations_refuse_after_actual_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, damage: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, _NAMES[0], prefix)
    assert case.admit()["whole_old_module_reconstructed"] is True
    if damage == "context":
        case.buffer.prefix = "data/owned-unlisted-context"
    elif damage == "capture":
        case.buffer.descriptor.capture["sha256"] = "0" * 64
    elif damage == "logical":
        case.logical += "/alias"
    elif damage == "path":
        case.row["path"] = "packages/owned/unlisted.py"
    elif damage == "hash":
        case.row["sha256"] = "0" * 64
    elif damage == "bool_size":
        case.row["bytes"] = True
    elif damage == "member":
        case.buffer.descriptor.members[case.logical]["bytes"] += 1
    elif damage == "group":
        case.buffer.descriptor.groups[0]["resolved_paths"] = [
            (case.logical, "packages/owned/alias.py")
        ]
    elif damage == "duplicate_group":
        case.buffer.descriptor = replace(
            case.buffer.descriptor, groups=case.buffer.descriptor.groups * 2
        )
    elif damage == "not_detached":
        case.buffer.descriptor = replace(case.buffer.descriptor, detached=frozenset())
    elif damage == "old_body":
        case.buffer._payloads[case.logical] = _OLD + b"# different original\n"
    elif damage == "physical_member":
        _write(case.consumer.repository / prefix / case.logical, _OLD)
    elif damage == "symlink":
        backing = case.consumer.repository / "owned-backing"
        case.target.rename(backing)
        case.target.symlink_to(backing)
    elif damage == "ancestor_symlink":
        backing = case.consumer.repository / "owned-parent"
        case.target.parent.rename(backing)
        case.target.parent.symlink_to(backing, target_is_directory=True)
    elif damage == "hardlink":
        os.link(case.target, case.consumer.repository / "owned-alias")
    elif damage == "stale":
        capture = case.consumer.repository / prefix / "capture.json"
        capture.write_bytes(capture.read_bytes() + b"\n")
    elif damage == "concurrent":
        original = subject.sample_age_context_extension_matches

        def change_after_actual_inverse(name: str, old: bytes, current: bytes) -> bool:
            accepted = original(name, old, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# changed current source\n")
            return accepted

        monkeypatch.setattr(
            subject, "sample_age_context_extension_matches", change_after_actual_inverse
        )
    elif damage == "final_read":
        original_read = Path.read_bytes
        observations = 0

        def final_bytes(path: Path) -> bytes:
            nonlocal observations
            current = original_read(path)
            if path == case.target:
                observations += 1
                if observations == 3:
                    return current + b"# different final observation\n"
            return current

        monkeypatch.setattr(Path, "read_bytes", final_bytes)
        with pytest.raises(ReportRebuildError, match="changed during correspondence"):
            _dispatch(case)
        assert observations == 3
        return
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


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize("revision", _ANCESTORS)
def test_actual_accepted_ancestor_witnesses_close_every_current_byte(
    name: str, revision: str
) -> None:
    repository = Path(__file__).resolve().parents[7]
    _git(
        repository,
        "--no-replace-objects",
        "merge-base",
        "--is-ancestor",
        revision,
        _ACCEPTED,
    )
    captured = _git(repository, "--no-replace-objects", "show", revision + ":" + name)
    size, checksum, pairs = subject._SAMPLE_AGE_CONTEXT_CONTRACTS[name]
    assert len(captured) == size and _identity(captured)["sha256"] == checksum
    current = (repository / name).read_bytes()
    assert subject.sample_age_context_extension_matches(name, captured, current)
    assert not subject.sample_age_context_extension_matches(
        name, captured + b"# false old", current
    )
    assert not subject.sample_age_context_extension_matches(
        name, captured, current + b"# extra byte"
    )
    assert not subject.sample_age_context_extension_matches(
        "packages/owned/unlisted.py", captured, current
    )
    for previous, inserted in pairs:
        assert captured.count(previous) == current.count(inserted) == 1
        assert not subject.sample_age_context_extension_matches(
            name, captured, current.replace(inserted, previous, 1)
        )
    if name.endswith("/chronology/audits/provenance.py"):
        changed = current.replace(
            b"len(source_owners) != len(master_rows)",
            b"len(source_owners) == len(master_rows)",
            1,
        )
        old_field = current.replace(
            b'"time_start_bp": row.time_start_bp', b'"time_start_bp": None', 1
        )
        assert old_field != current
        assert not subject.sample_age_context_extension_matches(
            name, captured, old_field
        )
    elif name.endswith("/claims.py"):
        changed = current.replace(
            b"include_native_source_rows: bool = False",
            b"include_native_source_rows: bool = True",
            1,
        )
    else:
        changed = current.replace(
            b"NotRequired[dict[str, object]]", b"dict[str, object]", 1
        )
    assert changed != current
    assert not subject.sample_age_context_extension_matches(name, captured, changed)
