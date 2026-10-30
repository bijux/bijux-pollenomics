"""Exercise bounded Atlas controller and selected-interval source custody."""

from __future__ import annotations

import ast
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
    atlas_evidence_selection as subject,
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
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/source_chronology/features.py",
)
_RENDER, _FINALIZATION, _FEATURES = _SOURCES
_SOURCE = _FEATURES
_OTHER = _ROOT + "reporting/unlisted_source.py"
_CONTEXTS = (
    "data/method-certification/author-optimizer-diagnostic-source-capture",
    "data/atlas/sample-chronology-source-view-capture",
)
_OLD = b"from __future__ import annotations\n\n# Own inert source frame.\n# old section\n# old flags\n"
_PAIRS = (
    (b"# old section\n", b"# required section\n"),
    (b"# old flags\n", b"# required flags\n"),
)
_CURRENT = _OLD
for _before, _after in _PAIRS:
    _CURRENT = _CURRENT.replace(_before, _after)


def _owned_globals() -> dict[str, str]:
    return {
        name: name + " = " + repr("own literal " + name)
        for name in subject._RENDER_GLOBAL_DECLARATIONS
    }


def _declarations() -> dict[str, str]:
    globals_ = _owned_globals()
    return {
        name: globals_[name] + "\n"
        if name in globals_
        else subject._RENDER_DEFERRED_SIGNATURES[name] + "\n\n\n"
        for name in subject._RENDER_DECLARATION_ORDER
    }


def _fixture_current(source: str) -> bytes:
    if source != _RENDER:
        return _CURRENT
    return _CURRENT + "".join(_declarations().values()).encode()


@dataclass
class SelectionCase:
    """An invented immutable Git member and one actual guarded source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        return subject.validated_atlas_evidence_selection_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str = _SOURCE
) -> SelectionCase:
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
        "_SELECTION_TRANSPORT_CONTRACTS",
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
    monkeypatch.setattr(subject, "_RENDER_GLOBAL_DECLARATIONS", _owned_globals())
    target.write_bytes(_fixture_current(source))
    return SelectionCase(
        consumer, {"path": source, **identity}, logical, target, buffer
    )


def _dispatch(case: SelectionCase) -> object:
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
def test_fixed_three_sources_authenticate_owned_git_without_native_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    role = case.admit()
    assert role["classification"] == "atlas_evidence_selection_extension"
    assert role["path"] == source and role["original_member"] == case.logical
    assert (
        role["original_bytes"] == len(_OLD)
        and role["original_sha256"] == _identity(_OLD)["sha256"]
    )
    for key in (
        "whole_old_module_reconstructed",
        "all_other_old_source_bytes_exact",
        "current_regular_single_link_and_stable",
        "current_ordinary_software_controls_required",
    ):
        assert role[key] is True
    assert role["eight_closed_controller_declarations_checked"] is (source == _RENDER)
    assert role["optional_transport_and_budget_inventory_intentionally_changed"] is (
        source != _FEATURES
    )
    assert role["selected_interval_refusal_and_metadata_intentionally_extended"] is (
        source == _FEATURES
    )
    for key in (
        "new_deferred_controller_bodies_part_of_historical_equality_claimed",
        "all_current_source_projection_outputs_equal_claimed",
        "historical_native_equal_current_output_claimed",
        "historical_browser_equal_current_browser_claimed",
        "current_runtime_transport_byte_equal_claimed",
        "historical_outputs_revalidated_under_current_contract_claimed",
        "old_native_equal_current_admission_claimed",
        "new_native_or_scientific_execution_claimed",
    ):
        assert role[key] is False


@pytest.mark.parametrize("prefix", _CONTEXTS)
@pytest.mark.parametrize("source", _SOURCES)
def test_both_actual_dispatchers_refuse_unknown_code_after_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, prefix, source)
    result = _dispatch(case)
    if prefix == _CONTEXTS[0]:
        assert (
            isinstance(result, dict)
            and result["classification"] == "atlas_evidence_selection_extension"
        )
    else:
        assert result is None
    case.target.write_bytes(case.target.read_bytes() + b"unknown_call()\n")
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
def test_selected_source_binding_and_freshness_refuse_after_positive_baseline(
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
        original_match = subject.atlas_evidence_selection_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "atlas_evidence_selection_extension_matches",
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


@pytest.mark.parametrize("prefix", _CONTEXTS)
def test_outer_dispatch_final_current_read_is_observed_within_real_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, prefix)
    _dispatch(case)
    real_read = Path.read_bytes
    real_helper = subject.validated_atlas_evidence_selection_source
    active = False
    observations = 0

    def observed_helper(
        repository: Path, row: dict[str, Any], logical: str, buffer: SourceCapsule
    ) -> dict[str, Any]:
        nonlocal active
        active = True
        try:
            return real_helper(repository, row, logical, buffer)
        finally:
            active = False

    def observed_read(path: Path) -> bytes:
        nonlocal observations
        raw = real_read(path)
        if path == case.target and active:
            observations += 1
            if observations == 2:
                return raw + b"# changed final current observation\n"
        return raw

    owner = router if prefix == _CONTEXTS[0] else chronology
    monkeypatch.setattr(
        owner, "validated_atlas_evidence_selection_source", observed_helper
    )
    monkeypatch.setattr(Path, "read_bytes", observed_read)
    with pytest.raises(ReportRebuildError, match="changed during verification"):
        _dispatch(case)
    assert observations == 2


_WITNESSES = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/source_chronology/features.py": (
        "f5ab77edcd3affee65723074d21b83161b4bf542",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
}


def _actual_pair(source: str) -> tuple[bytes, bytes]:
    repository = Path(__file__).resolve().parents[7]
    size, digest, _, _ = subject._SELECTION_TRANSPORT_CONTRACTS[source]
    bodies = []
    for revision in _WITNESSES[source]:
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == size and _identity(body)["sha256"] == digest
        bodies.append(body)
    assert bodies[0] == bodies[1]
    return bodies[0], (repository / source).read_bytes()


@pytest.mark.parametrize("source", _SOURCES)
def test_three_actual_old_git_witnesses_and_all_named_inverse_stages(
    source: str,
) -> None:
    old, current = _actual_pair(source)
    assert subject.atlas_evidence_selection_extension_matches(source, old, current)
    assert not subject.atlas_evidence_selection_extension_matches(
        source, old + b"# counterfeit old\n", current
    )
    assert not subject.atlas_evidence_selection_extension_matches(
        source, old, current + b"unknown_call()\n"
    )
    assert not subject.atlas_evidence_selection_extension_matches(_OTHER, old, current)
    for before, after in subject._SELECTION_TRANSPORT_CONTRACTS[source][3]:
        assert current.count(after) == 1
        assert not subject.atlas_evidence_selection_extension_matches(
            source, old, current.replace(after, before, 1)
        )


@pytest.mark.parametrize("source", (_RENDER, _FINALIZATION))
def test_actual_whole_parent_is_restored_before_unchanged_runtime_law(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    old, current = _actual_pair(source)
    assert subject.atlas_evidence_selection_extension_matches(source, old, current)
    repository = Path(__file__).resolve().parents[7]
    parent = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "show",
            "d37a306ccd39ffb853352ec03cd8d8b6dce29483:" + source,
        ],
        cwd=repository,
        timeout=20,
    )
    calls: list[str] = []

    def observed(name: str, captured: bytes, restored: bytes) -> bool:
        assert restored == parent
        calls.append(name)
        return atlas_runtime_transport_extension_matches(name, captured, restored)

    monkeypatch.setattr(subject, "atlas_runtime_transport_extension_matches", observed)
    assert subject.atlas_evidence_selection_extension_matches(source, old, current)
    assert calls == [source]


def test_features_have_only_exact_raw_old_equality_not_runtime_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old, current = _actual_pair(_FEATURES)
    assert subject.atlas_evidence_selection_extension_matches(_FEATURES, old, current)

    def forbidden(name: str, captured: bytes, restored: bytes) -> bool:
        raise AssertionError("Selected-interval source must not use runtime fallback")

    monkeypatch.setattr(subject, "atlas_runtime_transport_extension_matches", forbidden)
    assert subject.atlas_evidence_selection_extension_matches(_FEATURES, old, current)
    assert not subject.atlas_evidence_selection_extension_matches(
        _FEATURES, old, current + b"unknown_call()\n"
    )


_STRUCTURAL_VECTORS = (
    ("missing", "_EVIDENCE_BEGIN"),
    ("missing", "_EVIDENCE_END"),
    ("missing", "_EVIDENCE_FACTORY"),
    ("missing", "_NATIVE_BINDING"),
    ("missing", "_separate_evidence_tools"),
    ("missing", "_code_reference"),
    ("missing", "_check_code_target"),
    ("missing", "static_map_optional_controller_paths"),
    ("duplicate", "_EVIDENCE_BEGIN"),
    ("duplicate", "_EVIDENCE_END"),
    ("duplicate", "_EVIDENCE_FACTORY"),
    ("duplicate", "_NATIVE_BINDING"),
    ("duplicate", "_separate_evidence_tools"),
    ("duplicate", "_code_reference"),
    ("duplicate", "_check_code_target"),
    ("duplicate", "static_map_optional_controller_paths"),
    ("global_value", "_EVIDENCE_BEGIN"),
    ("global_value", "_EVIDENCE_END"),
    ("global_value", "_EVIDENCE_FACTORY"),
    ("global_value", "_NATIVE_BINDING"),
    ("function_default", "_separate_evidence_tools"),
    ("function_default", "_code_reference"),
    ("function_default", "_check_code_target"),
    ("function_default", "static_map_optional_controller_paths"),
    ("decorator", "_separate_evidence_tools"),
    ("decorator", "_code_reference"),
    ("decorator", "_check_code_target"),
    ("decorator", "static_map_optional_controller_paths"),
    ("extra_top_level", ""),
    ("shared_line_executable", "_EVIDENCE_BEGIN"),
    ("future_annotations", ""),
    ("unknown_old_residual", ""),
    ("order", ""),
)


@pytest.mark.parametrize("defect,name", _STRUCTURAL_VECTORS)
def test_closed_eight_controller_shape_refuses_after_real_custody_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str, name: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, _CONTEXTS[0], _RENDER)
    assert case.admit()["eight_closed_controller_declarations_checked"] is True
    current = case.target.read_bytes().decode()
    declarations = _declarations()
    if defect == "missing":
        current = current.replace(declarations[name], "", 1)
    elif defect == "duplicate":
        current = current.replace(declarations[name], declarations[name] * 2, 1)
    elif defect == "global_value":
        current = current.replace(
            declarations[name], name + " = 'foreign literal'\n", 1
        )
    elif defect == "function_default":
        signature = subject._RENDER_DEFERRED_SIGNATURES[name]
        # A default on the final argument remains valid Python syntax.
        node = ast.parse(signature).body[0]
        assert isinstance(node, ast.FunctionDef)
        node.args.defaults = [ast.Constant(None)]
        altered = ast.unparse(node) + "\n\n\n"
        current = current.replace(declarations[name], altered, 1)
    elif defect == "decorator":
        current = current.replace(
            declarations[name], "@own_decorator\n" + declarations[name], 1
        )
    elif defect == "extra_top_level":
        current += "unknown_call()\n"
    elif defect == "shared_line_executable":
        current = current.replace(
            declarations[name],
            declarations[name].rstrip("\n") + "; unknown_call()\n",
            1,
        )
    elif defect == "future_annotations":
        current = current.replace("from __future__ import annotations\n", "", 1)
    elif defect == "unknown_old_residual":
        current = current.replace("# Own inert source frame.", "unclassified = True", 1)
    else:
        first, second = subject._RENDER_DECLARATION_ORDER[:2]
        current = current.replace(
            declarations[first] + declarations[second],
            declarations[second] + declarations[first],
            1,
        )
    assert current.encode() != case.target.read_bytes()
    assert not subject.atlas_evidence_selection_extension_matches(
        _RENDER, _OLD, current.encode()
    )
    case.target.write_text(current)
    with pytest.raises(ReportRebuildError):
        case.admit()


@pytest.mark.parametrize("name", tuple(subject._RENDER_DEFERRED_SIGNATURES))
def test_closed_new_deferred_bodies_are_software_scope_not_old_native_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    case = _case(tmp_path / "repository", monkeypatch, _CONTEXTS[0], _RENDER)
    assert case.admit()["whole_old_module_reconstructed"] is True
    before = _declarations()[name]
    after = before.replace("    pass", "    return None", 1)
    assert before != after
    case.target.write_bytes(
        case.target.read_bytes().replace(before.encode(), after.encode(), 1)
    )
    assert subject.atlas_evidence_selection_extension_matches(
        _RENDER, _OLD, case.target.read_bytes()
    )
    role = case.admit()
    assert (
        role["new_deferred_controller_bodies_part_of_historical_equality_claimed"]
        is False
    )
    assert role["current_ordinary_software_controls_required"] is True
    assert role["historical_native_equal_current_output_claimed"] is False
