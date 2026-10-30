"""Authenticate whole-pollen refusal refinements through real inert Git custody."""

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
    propagation_qualification as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/"
_SOURCE = _ROOT + "analysis/propagation/outputs/contracts.py"
_OTHER = _ROOT + "analysis/propagation/outputs/producer.py"
_CONTEXTS = (
    "data/method-certification/author-optimizer-diagnostic-source-capture",
    "data/atlas/sample-chronology-source-view-capture",
)
_OLD = b"# Own inert old contract; never imported.\n# old section\n# old flags\n"
_PAIRS = (
    (b"# old section\n", b"# required section\n"),
    (b"# old flags\n", b"# required qualification flags\n"),
)
_CURRENT = _OLD
for _before, _after in _PAIRS:
    _CURRENT = _CURRENT.replace(_before, _after)


@dataclass
class QualificationCase:
    """Own immutable old Git comments and one current captured-source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Invoke the maintained refusal-refinement custody boundary."""
        return subject.validated_propagation_qualification_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> QualificationCase:
    """Bind invented comments through the existing real Git/descriptor machinery."""
    root.mkdir()
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    target = root / _SOURCE
    _write(target, _OLD)
    _git(root, "add", "--", _SOURCE)
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
        "test(propagation): bind inert qualification comments",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + _SOURCE).decode().strip()
    context = subject._CAPTURE_CONTEXTS[prefix]
    logical = context[1] + _SOURCE
    identity = _identity(_OLD)
    members = {logical: identity}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    mapping = json.dumps([[_SOURCE, blob]], separators=(",", ":")).encode()
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
                "paths": [[logical, _SOURCE]],
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
    monkeypatch.setattr(subject, "_SOURCE_BYTES", len(_OLD))
    monkeypatch.setattr(subject, "_SOURCE_SHA256", identity["sha256"])
    monkeypatch.setattr(subject, "_QUALIFICATION_SPANS", _PAIRS)
    contexts = dict(subject._CAPTURE_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], context[1])
    monkeypatch.setattr(subject, "_CAPTURE_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return QualificationCase(
        consumer, {"path": _SOURCE, **identity}, logical, target, buffer
    )


def _dispatch(case: QualificationCase) -> object:
    """Use the real owning optimizer router or chronology current-source guard."""
    if case.consumer.prefix == _CONTEXTS[0]:
        return router.validated_current_scientific_source(
            case.consumer.repository, case.row, case.logical, case.buffer
        )
    chronology._validate_current_source(
        case.consumer.repository,
        _SOURCE,
        case.logical,
        _OLD,
        _identity(_OLD)["sha256"],
        case.buffer.detached,
        source_buffer=case.buffer,
    )
    return None


@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_fixed_contexts_preserve_old_identity_without_native_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    """Read actual Git bytes and retain explicit refusal-refinement scope."""
    case = _case(tmp_path / "repository", monkeypatch, prefix)
    result = case.admit()
    assert result["classification"] == "whole_pollen_contract_refusal_refinement"
    assert result["path"] == _SOURCE
    assert result["original_member"] == case.logical
    assert result["original_bytes"] == len(_OLD)
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["missing_or_invalid_whole_pollen_qualification_newly_refused"] is True
    assert result["current_refusal_behavior_intentionally_stricter"] is True
    assert (
        result["historical_outputs_revalidated_under_current_contract_claimed"] is False
    )
    assert result["old_native_equal_current_admission_claimed"] is False
    assert result["new_native_or_scientific_execution_claimed"] is False


@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_owning_dispatch_refuses_unknown_code_after_real_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    """Exercise both actual guarded entrypoints and their strict current-byte refusal."""
    case = _case(tmp_path / "repository", monkeypatch, prefix)
    assert case.admit()["whole_old_module_reconstructed"] is True
    result = _dispatch(case)
    if prefix == _CONTEXTS[0]:
        assert isinstance(result, dict)
        assert result["classification"] == "whole_pollen_contract_refusal_refinement"
    else:
        assert result is None
    case.target.write_bytes(_CURRENT + b"# unrelated executable statement\n")
    with pytest.raises(ReportRebuildError):
        _dispatch(case)


@pytest.mark.parametrize("prefix", _CONTEXTS)
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
def test_qualification_binding_and_freshness_refuse_after_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, damage: str
) -> None:
    """Keep exact source coordinates and final current-byte observations mandatory."""
    case = _case(tmp_path / "repository", monkeypatch, prefix)
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
        case.row["path"] = _ROOT + "source_completion/unlisted.py"
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
        buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _OTHER)]
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
        original_match = subject.propagation_qualification_extension_matches

        def mutate_after_actual_inverse(captured: bytes, current: bytes) -> bool:
            accepted = original_match(captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "propagation_qualification_extension_matches",
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


def test_actual_both_old_git_witnesses_require_the_exact_two_refinements() -> None:
    """Inspect known normal Git source bytes without importing historical programmes."""
    repository = Path(__file__).resolve().parents[7]
    old = []
    for revision in (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ):
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + _SOURCE],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == 10067
        assert (
            _identity(body)["sha256"]
            == "bf955aa90b22269d8c8b6d662b715e2c0ad17b76b61dfc5f11470d0d3843ab5f"
        )
        old.append(body)
    assert old[0] == old[1]
    current = (repository / _SOURCE).read_bytes()
    assert subject.propagation_qualification_extension_matches(old[0], current)
    assert not subject.propagation_qualification_extension_matches(
        old[0], current + b"# foreign statement\n"
    )
    assert not subject.propagation_qualification_extension_matches(
        old[0] + b"# counterfeit old bytes\n", current
    )
    for before, after in (
        (
            b'whole_pollen.get("heterogeneous_taxa_warning_required") is not True',
            b'whole_pollen.get("heterogeneous_taxa_warning_required") != True',
        ),
        (b'"exploratory_aggregate"', b'"confirmed_aggregate"'),
    ):
        assert current.count(before) == 1
        assert not subject.propagation_qualification_extension_matches(
            old[0], current.replace(before, after, 1)
        )
