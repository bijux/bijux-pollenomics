"""Authenticate runtime transport custody and structural declaration refusals."""

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
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    atlas_extension_matches,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    atlas_runtime_transport as subject,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles.documentation import (
    _documented_source_matches,
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
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
)
_SOURCE = _SOURCES[0]
_OTHER = _ROOT + "analysis/propagation/outputs/producer.py"
_CONTEXTS = (
    "data/method-certification/author-optimizer-diagnostic-source-capture",
    "data/atlas/sample-chronology-source-view-capture",
)
_OLD = b"from __future__ import annotations\n\n# Own inert old source; never imported.\n# old section\n# old flags\n"
_PAIRS = (
    (b"# old section\n", b"# required section\n"),
    (b"# old flags\n", b"# required qualification flags\n"),
)
_CURRENT = _OLD
for _before, _after in _PAIRS:
    _CURRENT = _CURRENT.replace(_before, _after)


_RENDER = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py"
)
_WORKFLOW = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py"
_DOCUMENTED = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py"
_VALID_BINDINGS = (
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
    ),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
    ),
    (
        "data/atlas/sample-chronology-source-view-capture",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
    ),
)
_OWN_SIGNATURES = {
    "render_multi_country_map_html": "def render_multi_country_map_html() -> None:\n    pass\n",
    "_runtime_resources": "def _runtime_resources() -> None:\n    pass\n",
    "write_static_map_document": "def write_static_map_document() -> None:\n    pass\n",
}
_OWN_GLOBALS = {
    "_RUNTIME_BEGIN": "own begin",
    "_RUNTIME_END": "own end",
    "_RUNTIME_LOADER": "own loader",
}
_OWN_BOOTSTRAP = "re.compile('own', re.DOTALL)"
_OWN_DECLARATIONS = (
    b"def render_multi_country_map_html() -> None:\n    pass\n\n\n"
    b"_RUNTIME_BEGIN = 'own begin'\n"
    b"_RUNTIME_END = 'own end'\n"
    b"_BOOTSTRAP = re.compile('own', re.DOTALL)\n"
    b"_RUNTIME_LOADER = 'own loader'\n\n\n"
    b"def _runtime_resources() -> None:\n    pass\n\n\n"
    b"def write_static_map_document() -> None:\n    pass\n"
)


def _current(source: str) -> bytes:
    """Invent only comments, closed tiny declarations and pass bodies, never import them."""
    return _CURRENT + (b"\n\n" + _OWN_DECLARATIONS if source == _RENDER else b"")


@dataclass
class TransportCase:
    """Own immutable old Git comments and one current captured-source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Invoke the maintained runtime transport custody boundary."""
        return subject.validated_atlas_runtime_transport_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str = _SOURCE
) -> TransportCase:
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
        "test(atlas): bind inert runtime transport comments",
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
        "_RUNTIME_TRANSPORT_CONTRACTS",
        {
            name: (len(_OLD), identity["sha256"], "ordinary_original_bytes", _PAIRS)
            for name in _SOURCES
        },
    )
    monkeypatch.setattr(subject, "_RUNTIME_NEW_SIGNATURES", _OWN_SIGNATURES)
    monkeypatch.setattr(subject, "_RUNTIME_LITERAL_GLOBALS", _OWN_GLOBALS)
    monkeypatch.setattr(subject, "_RUNTIME_BOOTSTRAP_EXPRESSION", _OWN_BOOTSTRAP)
    contexts = dict(subject._CAPTURE_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], context[1])
    monkeypatch.setattr(subject, "_CAPTURE_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_current(source))
    return TransportCase(
        consumer, {"path": source, **identity}, logical, target, buffer
    )


def _dispatch(case: TransportCase) -> object:
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


@pytest.mark.parametrize("prefix,source", _VALID_BINDINGS)
def test_fixed_contexts_preserve_old_identity_without_native_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    """Read actual Git bytes and retain explicit source-view extension scope."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    result = case.admit()
    assert result["classification"] == "runtime_transport_extension"
    assert result["path"] == source
    assert result["original_member"] == case.logical
    assert result["original_bytes"] == len(_OLD)
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert (
        result["runtime_sidecar_and_writer_callback_API_intentionally_changed"] is True
    )
    assert (
        result["current_runtime_SRI_and_protocol_behavior_requires_software_controls"]
        is True
    )
    assert (
        result["scientific_chunk_identity_preservation_requires_separate_controls"]
        is True
    )
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False
    assert result["current_runtime_transport_byte_equal_claimed"] is False
    assert (
        result["new_deferred_runtime_bodies_part_of_historical_equality_claim"] is False
    )
    assert result["seven_closed_runtime_declarations_checked"] is (source == _RENDER)
    assert result["preexisting_correspondence"] == "ordinary_original_bytes"
    assert (
        result["historical_outputs_revalidated_under_current_contract_claimed"] is False
    )
    assert result["old_native_equal_current_admission_claimed"] is False
    assert result["new_native_or_scientific_execution_claimed"] is False


@pytest.mark.parametrize("prefix,source", _VALID_BINDINGS)
def test_owning_dispatch_refuses_unknown_code_after_real_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    """Exercise both actual guarded entrypoints and their strict current-byte refusal."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    assert case.admit()["whole_old_module_reconstructed"] is True
    result = _dispatch(case)
    if prefix == _CONTEXTS[0]:
        assert isinstance(result, dict)
        assert result["classification"] == "runtime_transport_extension"
    else:
        assert result is None
    case.target.write_bytes(
        case.target.read_bytes() + b"# unrelated executable statement\n"
    )
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
def test_runtime_transport_binding_and_freshness_refuse_after_positive_baseline(
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
        original_match = subject.atlas_runtime_transport_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "atlas_runtime_transport_extension_matches",
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
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled_panel_candidate.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py": (
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
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
}


def _actual_pair(source: str) -> tuple[bytes, bytes]:
    """Read normal immutable old Git and current source in memory without execution."""
    repository = Path(__file__).resolve().parents[7]
    expected_bytes, expected_sha, _, _ = subject._RUNTIME_TRANSPORT_CONTRACTS[source]
    old = []
    for revision in _WITNESSES[source]:
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == expected_bytes and _identity(body)["sha256"] == expected_sha
        old.append(body)
    assert all(body == old[0] for body in old)
    return old[0], (repository / source).read_bytes()


@pytest.mark.parametrize("source", _SOURCES)
def test_actual_old_witnesses_require_only_runtime_and_exact_preexisting_laws(
    source: str,
) -> None:
    """Separate original ordinary bytes and the two prior named correspondence laws."""
    old, current = _actual_pair(source)
    assert subject.atlas_runtime_transport_extension_matches(source, old, current)
    assert not subject.atlas_runtime_transport_extension_matches(
        source, old, current + b"# foreign tail\n"
    )
    assert not subject.atlas_runtime_transport_extension_matches(
        source, old + b"# counterfeit old\n", current
    )
    assert not subject.atlas_runtime_transport_extension_matches(_OTHER, old, current)
    for before, after in subject._RUNTIME_TRANSPORT_CONTRACTS[source][3]:
        assert current.count(after) == 1
        assert not subject.atlas_runtime_transport_extension_matches(
            source, old, current.replace(after, before, 1)
        )


@pytest.mark.parametrize("source", (_WORKFLOW, _DOCUMENTED))
def test_existing_named_correspondence_executes_after_runtime_inverse(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Observe the actual existing predicate, without mocking its acceptance result."""
    old, current = _actual_pair(source)
    assert subject.atlas_runtime_transport_extension_matches(source, old, current)
    calls: list[str] = []
    original = (
        atlas_extension_matches if source == _WORKFLOW else _documented_source_matches
    )

    def observed(name: str, captured: bytes, reversed_transport: bytes) -> bool:
        calls.append(name)
        return original(name, captured, reversed_transport)

    name = (
        "atlas_extension_matches"
        if source == _WORKFLOW
        else "_documented_source_matches"
    )
    monkeypatch.setattr(subject, name, observed)
    assert subject.atlas_runtime_transport_extension_matches(source, old, current)
    assert calls == [source]


@pytest.mark.parametrize(
    "source", tuple(name for name in _SOURCES if name not in {_WORKFLOW, _DOCUMENTED})
)
def test_ordinary_sources_have_no_generic_correspondence_fallback(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep the other ten paths on exact reconstructed original bytes."""
    old, current = _actual_pair(source)
    assert subject.atlas_runtime_transport_extension_matches(source, old, current)

    def forbidden(name: str, captured: bytes, reversed_transport: bytes) -> bool:
        raise AssertionError("Ordinary source must not use another correspondence")

    monkeypatch.setattr(subject, "atlas_extension_matches", forbidden)
    monkeypatch.setattr(subject, "_documented_source_matches", forbidden)
    assert subject.atlas_runtime_transport_extension_matches(source, old, current)
    assert not subject.atlas_runtime_transport_extension_matches(
        source, old, current + b"# foreign tail\n"
    )


def test_chronology_refuses_optimizer_only_cross_border_coordinate_after_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not manufacture a twelfth chronology member from the optimizer catalogue."""
    baseline = _case(tmp_path / "baseline", monkeypatch, _CONTEXTS[1])
    assert baseline.admit()["whole_old_module_reconstructed"] is True
    cross_border = next(
        name
        for name in _SOURCES
        if name.endswith("/cross_border_neighbor_candidate.py")
    )
    case = _case(tmp_path / "unselected", monkeypatch, _CONTEXTS[1], cross_border)
    with pytest.raises(ReportRebuildError):
        case.admit()


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize(
    "damage",
    (
        "future",
        "wrapper_signature",
        "wrapper_decorator",
        "wrapper_async",
        "resource_signature",
        "writer_signature",
        "global_begin",
        "global_end",
        "global_loader",
        "bootstrap_pattern",
        "bootstrap_flags",
        "extra_global",
        "declaration_order",
        "old_statement",
        "trailing_comment",
        "default_call",
        "writer_decorator",
    ),
)
def test_closed_runtime_declarations_refuse_after_real_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, damage: str
) -> None:
    """Close names, signatures, import-time values and every old source byte."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, _RENDER)
    assert case.admit()["seven_closed_runtime_declarations_checked"] is True
    current = case.target.read_bytes()
    changes = {
        "future": (b"from __future__ import annotations\n", b""),
        "wrapper_signature": (
            b"def render_multi_country_map_html()",
            b"def render_multi_country_map_html(extra)",
        ),
        "wrapper_decorator": (
            b"def render_multi_country_map_html()",
            b"@untrusted\ndef render_multi_country_map_html()",
        ),
        "wrapper_async": (
            b"def render_multi_country_map_html()",
            b"async def render_multi_country_map_html()",
        ),
        "resource_signature": (
            b"def _runtime_resources()",
            b"def _runtime_resources(extra)",
        ),
        "writer_signature": (
            b"def write_static_map_document()",
            b"def write_static_map_document(extra)",
        ),
        "global_begin": (
            b"_RUNTIME_BEGIN = 'own begin'",
            b"_RUNTIME_BEGIN = unknown()",
        ),
        "global_end": (b"_RUNTIME_END = 'own end'", b"_RUNTIME_END = 'other'"),
        "global_loader": (
            b"_RUNTIME_LOADER = 'own loader'",
            b"_RUNTIME_LOADER = 'other'",
        ),
        "bootstrap_pattern": (
            b"re.compile('own', re.DOTALL)",
            b"re.compile('other', re.DOTALL)",
        ),
        "bootstrap_flags": (
            b"re.compile('own', re.DOTALL)",
            b"re.compile('own', re.IGNORECASE)",
        ),
        "extra_global": (
            b"_RUNTIME_END = 'own end'\n",
            b"_RUNTIME_END = 'own end'\nEXTRA = unknown()\n",
        ),
        "declaration_order": (
            b"_RUNTIME_BEGIN = 'own begin'\n_RUNTIME_END = 'own end'",
            b"_RUNTIME_END = 'own end'\n_RUNTIME_BEGIN = 'own begin'",
        ),
        "old_statement": (
            b"# Own inert old source; never imported.",
            b"old_state = unknown()",
        ),
        "trailing_comment": (
            b"def write_static_map_document() -> None:\n    pass\n",
            b"def write_static_map_document() -> None:\n    pass\n# foreign tail\n",
        ),
        "default_call": (
            b"def write_static_map_document()",
            b"def write_static_map_document(value=unknown())",
        ),
        "writer_decorator": (
            b"def write_static_map_document()",
            b"@untrusted\ndef write_static_map_document()",
        ),
    }
    before, after = changes[damage]
    assert current.count(before) == 1
    case.target.write_bytes(current.replace(before, after, 1))
    with pytest.raises(ReportRebuildError):
        case.admit()


@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_new_deferred_bodies_are_separate_software_scope_not_historical_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    """Retain the explicitly bounded historical claim when an owned deferred body differs."""
    case = _case(tmp_path / "repository", monkeypatch, prefix, _RENDER)
    assert case.admit()["whole_old_module_reconstructed"] is True
    before = b"def write_static_map_document() -> None:\n    pass\n"
    after = b"def write_static_map_document() -> None:\n    return None\n"
    current = case.target.read_bytes()
    assert current.count(before) == 1
    case.target.write_bytes(current.replace(before, after, 1))
    result = case.admit()
    assert result["whole_old_module_reconstructed"] is True
    assert (
        result["new_deferred_runtime_bodies_part_of_historical_equality_claim"] is False
    )
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False
