"""Authenticate source-view context extensions through real inert Git custody."""

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
    atlas_context as subject,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles.atlas_runtime_transport import (
    atlas_runtime_transport_extension_matches,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/"
_SOURCES = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/neotoma.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/service.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/layers.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
)
_SOURCE = _SOURCES[0]
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
class ContextCase:
    """Own immutable old Git comments and one current captured-source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Invoke the maintained source-view context custody boundary."""
        return subject.validated_atlas_context_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str = _SOURCE
) -> ContextCase:
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
        "test(atlas): bind inert source context comments",
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
        "_SOURCE_CONTEXT_CONTRACTS",
        {
            name: (len(_OLD), identity["sha256"], "ordinary_original_bytes", _PAIRS)
            for name in _SOURCES
        },
    )
    contexts = dict(subject._CAPTURE_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], context[1])
    monkeypatch.setattr(subject, "_CAPTURE_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return ContextCase(consumer, {"path": source, **identity}, logical, target, buffer)


def _dispatch(case: ContextCase) -> object:
    """Use the real owning optimizer router or chronology current-source guard."""
    if case.consumer.prefix == _CONTEXTS[0]:
        return router.validated_current_scientific_source(
            case.consumer.repository, case.row, case.logical, case.buffer
        )
    chronology._validate_current_source(
        case.consumer.repository,
        case.row["path"],
        case.logical,
        _OLD,
        _identity(_OLD)["sha256"],
        case.buffer.detached,
        source_buffer=case.buffer,
    )
    return None


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize("source", _SOURCES)
def test_fixed_contexts_preserve_old_identity_without_native_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    """Read actual Git bytes and retain explicit source-view extension scope."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    result = case.admit()
    assert result["classification"] == "source_view_context_extension"
    assert result["path"] == source
    assert result["original_member"] == case.logical
    assert result["original_bytes"] == len(_OLD)
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["preexisting_source_correspondence"] == "ordinary_original_bytes"
    assert result["runtime_transport_law_composed"] is False
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False
    assert result["current_runtime_transport_byte_equal_claimed"] is False
    assert (
        result["source_projection_metadata_and_refusals_intentionally_extended"] is True
    )
    assert result["all_current_source_projection_outputs_equal_claimed"] is False
    assert result["optional_publication_input_default"] is None
    assert result["publication_capture_epoch"] == "neotoma/publication-links/2026-09-29"
    assert result["publication_capture_is_original_pollen_epoch_claimed"] is False
    assert (
        result["historical_outputs_revalidated_under_current_contract_claimed"] is False
    )
    assert result["old_native_equal_current_admission_claimed"] is False
    assert result["new_native_or_scientific_execution_claimed"] is False


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize("source", _SOURCES)
def test_owning_dispatch_refuses_unknown_code_after_real_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    """Exercise both actual guarded entrypoints and their strict current-byte refusal."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    assert case.admit()["whole_old_module_reconstructed"] is True
    result = _dispatch(case)
    if prefix == _CONTEXTS[0]:
        assert isinstance(result, dict)
        assert result["classification"] == "source_view_context_extension"
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
def test_source_context_binding_and_freshness_refuse_after_positive_baseline(
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
        original_match = subject.atlas_context_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "atlas_context_extension_matches",
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


_WITNESSES = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/neotoma.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/service.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/layers.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
}


@pytest.mark.parametrize("source", _SOURCES)
def test_actual_two_normal_git_witnesses_require_only_known_context_spans(
    source: str,
) -> None:
    """Compare fixed original source bytes without importing historical programmes."""
    repository = Path(__file__).resolve().parents[7]
    expected_bytes, expected_sha256, _, pairs = subject._SOURCE_CONTEXT_CONTRACTS[
        source
    ]
    old = []
    for revision in _WITNESSES[source]:
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == expected_bytes
        assert _identity(body)["sha256"] == expected_sha256
        old.append(body)
    assert old[0] == old[1]
    current = (repository / source).read_bytes()
    assert subject.atlas_context_extension_matches(source, old[0], current)
    assert not subject.atlas_context_extension_matches(
        source, old[0], current + b"# foreign statement\n"
    )
    assert not subject.atlas_context_extension_matches(
        source, old[0] + b"# counterfeit old bytes\n", current
    )
    assert not subject.atlas_context_extension_matches(_OTHER, old[0], current)
    for before, after in pairs:
        assert current.count(after) == 1
        assert not subject.atlas_context_extension_matches(
            source, old[0], current.replace(after, before, 1)
        )


_RUNTIME_PREDECESSOR_SOURCES = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
)
_STAGE_SENSITIVE_SOURCES = _RUNTIME_PREDECESSOR_SOURCES[1:]


def _actual_composed_pair(source: str) -> tuple[bytes, bytes]:
    """Read fixed old normal Git witnesses and current candidate bytes without execution."""
    repository = Path(__file__).resolve().parents[7]
    size, digest, _, _ = subject._SOURCE_CONTEXT_CONTRACTS[source]
    old = []
    for revision in _WITNESSES[source]:
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == size and _identity(body)["sha256"] == digest
        old.append(body)
    assert old[0] == old[1]
    return old[0], (repository / source).read_bytes()


@pytest.mark.parametrize("source", _RUNTIME_PREDECESSOR_SOURCES)
def test_actual_context_inverse_uses_unchanged_runtime_predecessor(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Observe the real inherited matcher after all context spans have been removed."""
    captured, current = _actual_composed_pair(source)
    assert subject._SOURCE_CONTEXT_CONTRACTS[source][2] == "runtime_transport_extension"
    assert subject.atlas_context_extension_matches(source, captured, current)
    calls: list[str] = []

    def observed(name: str, old: bytes, restored_post_runtime: bytes) -> bool:
        calls.append(name)
        assert name == source and old == captured
        for original, _ in subject._SOURCE_CONTEXT_CONTRACTS[name][3]:
            assert restored_post_runtime.count(original) == 1
        return atlas_runtime_transport_extension_matches(
            name, old, restored_post_runtime
        )

    monkeypatch.setattr(subject, "atlas_runtime_transport_extension_matches", observed)
    assert subject.atlas_context_extension_matches(source, captured, current)
    assert calls == [source]


@pytest.mark.parametrize(
    "source",
    tuple(name for name in _SOURCES if name not in _RUNTIME_PREDECESSOR_SOURCES),
)
def test_other_actual_context_sources_stay_on_whole_original_bytes(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the remaining three source-view additions outside runtime correspondence."""
    captured, current = _actual_composed_pair(source)
    assert subject._SOURCE_CONTEXT_CONTRACTS[source][2] == "ordinary_original_bytes"
    assert subject.atlas_context_extension_matches(source, captured, current)

    def forbidden(name: str, old: bytes, restored: bytes) -> bool:
        raise AssertionError("Raw original context must not use runtime fallback")

    monkeypatch.setattr(subject, "atlas_runtime_transport_extension_matches", forbidden)
    assert subject.atlas_context_extension_matches(source, captured, current)
    assert not subject.atlas_context_extension_matches(
        source, captured, current + b"# unknown byte\n"
    )


@pytest.mark.parametrize("source", _STAGE_SENSITIVE_SOURCES)
def test_actual_post_runtime_original_spans_are_unique_at_restored_stage(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reproduce the old stage mismatch and retain uniqueness before any inherited call."""
    captured, current = _actual_composed_pair(source)
    spans = subject._SOURCE_CONTEXT_CONTRACTS[source][3]
    assert any(captured.count(original) != 1 for original, _ in spans)
    assert subject.atlas_context_extension_matches(source, captured, current)
    restored = current
    for original, extension in spans:
        assert restored.count(extension) == 1
        restored = restored.replace(extension, original, 1)
    assert all(restored.count(original) == 1 for original, _ in spans)
    assert atlas_runtime_transport_extension_matches(source, captured, restored)
    calls: list[str] = []

    def observed(name: str, old: bytes, post_runtime: bytes) -> bool:
        calls.append(name)
        return atlas_runtime_transport_extension_matches(name, old, post_runtime)

    monkeypatch.setattr(subject, "atlas_runtime_transport_extension_matches", observed)
    assert subject.atlas_context_extension_matches(source, captured, current)
    assert calls == [source]
    calls.clear()
    duplicate = next(
        original
        for original, _ in spans
        if all((current + original).count(extension) == 1 for _, extension in spans)
    )
    assert not subject.atlas_context_extension_matches(
        source, captured, current + duplicate
    )
    assert calls == []
