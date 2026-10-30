"""Authenticate declared Atlas relation context through real inert Git custody."""

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
    author_optimizer_diagnostics as optimizer,
)
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
    atlas_relation_context as subject,
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
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence.py",
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
class RelationCase:
    """Own immutable old Git comments and one current captured-source coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Invoke the maintained source-view context custody boundary."""
        return subject.validated_atlas_relation_context_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, source: str = _SOURCE
) -> RelationCase:
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
        "_RELATION_CONTEXT_CONTRACTS",
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
    return RelationCase(consumer, {"path": source, **identity}, logical, target, buffer)


def _dispatch(case: RelationCase) -> object:
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
    assert result["classification"] == "atlas_relation_context_extension"
    assert result["path"] == source
    assert result["original_member"] == case.logical
    assert result["original_bytes"] == len(_OLD)
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["preexisting_source_correspondence"] == "ordinary_original_bytes"
    assert (
        result["projection_method_context_and_refusals_intentionally_extended"] is True
    )
    assert result["producer_inventory_intentionally_extended"] is (source == _MODELS)
    assert result["retained_current_producer_digest_guard_relaxed"] is False
    assert result["all_current_projection_outputs_equal_claimed"] is False
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False
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
        assert result["classification"] == "atlas_relation_context_extension"
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
        original_match = subject.atlas_relation_context_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject,
            "atlas_relation_context_extension_matches",
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


_MODELS = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py"
_PAYLOAD = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)

_WITNESSES = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": (
        "c601b9c7d7ad91421e96b4de25004f82b256f23a",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py": (
        "ba88d6d50d66a72bf8333f906577688218ccceef",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py": (
        "ba88d6d50d66a72bf8333f906577688218ccceef",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence.py": (
        "484fd110a3a0785c264a26a4d84bcccf12a8439e",
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
    ),
}


def _actual_relation_pair(source: str) -> tuple[bytes, bytes]:
    """Read normal immutable old and current source buffers without executing them."""
    repository = Path(__file__).resolve().parents[7]
    size, digest, _, _ = subject._RELATION_CONTEXT_CONTRACTS[source]
    originals = []
    for revision in _WITNESSES[source]:
        body = subprocess.check_output(
            ["git", "--no-replace-objects", "show", revision + ":" + source],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == size and _identity(body)["sha256"] == digest
        originals.append(body)
    assert originals[0] == originals[1]
    return originals[0], (repository / source).read_bytes()


@pytest.mark.parametrize("source", _SOURCES)
def test_actual_fixed_sources_require_only_relation_and_named_prior_spans(
    source: str,
) -> None:
    """Keep whole original bytes, including the exact two evidence documentation slots."""
    captured, current = _actual_relation_pair(source)
    assert subject.atlas_relation_context_extension_matches(source, captured, current)
    assert not subject.atlas_relation_context_extension_matches(
        source, captured, current + b"# unknown tail\n"
    )
    assert not subject.atlas_relation_context_extension_matches(
        source, captured + b"# counterfeit old\n", current
    )
    assert not subject.atlas_relation_context_extension_matches(
        _OTHER, captured, current
    )
    for before, after in subject._RELATION_CONTEXT_CONTRACTS[source][3]:
        assert current.count(after) == 1
        assert not subject.atlas_relation_context_extension_matches(
            source, captured, current.replace(after, before, 1)
        )


@pytest.mark.parametrize("source", (_MODELS, _PAYLOAD))
def test_actual_nested_constructor_or_asset_law_is_called_after_relation_inverse(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Observe unchanged owned predicates rather than mocking their acceptance result."""
    captured, current = _actual_relation_pair(source)
    assert subject.atlas_relation_context_extension_matches(source, captured, current)
    calls: list[str] = []
    original = (
        _documented_source_matches if source == _MODELS else atlas_extension_matches
    )

    def observed(name: str, old: bytes, restored: bytes) -> bool:
        calls.append(name)
        for before, _ in subject._RELATION_CONTEXT_CONTRACTS[name][3]:
            assert restored.count(before) == 1
        return original(name, old, restored)

    target = (
        "_documented_source_matches" if source == _MODELS else "atlas_extension_matches"
    )
    monkeypatch.setattr(subject, target, observed)
    assert subject.atlas_relation_context_extension_matches(source, captured, current)
    assert calls == [source]


@pytest.mark.parametrize(
    "source", tuple(name for name in _SOURCES if name not in {_MODELS, _PAYLOAD})
)
def test_other_three_actual_sources_have_no_generic_prior_correspondence(
    source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep exact ordinary old bytes as the only fallback for the remaining sources."""
    captured, current = _actual_relation_pair(source)
    assert subject.atlas_relation_context_extension_matches(source, captured, current)

    def forbidden(name: str, old: bytes, restored: bytes) -> bool:
        raise AssertionError("Ordinary source must not use an inherited law")

    monkeypatch.setattr(subject, "atlas_extension_matches", forbidden)
    monkeypatch.setattr(subject, "_documented_source_matches", forbidden)
    assert subject.atlas_relation_context_extension_matches(source, captured, current)
    assert not subject.atlas_relation_context_extension_matches(
        source, captured, current + b"# extra code\n"
    )


def _outer_payload_case(root: Path, monkeypatch: pytest.MonkeyPatch) -> RelationCase:
    """Repin invented fixture identities while preserving all other outer roles."""
    case = _case(root, monkeypatch, _CONTEXTS[0], _PAYLOAD)
    authority = dict(optimizer._OPTIMIZER_ATLAS_SOURCES)
    authority[_PAYLOAD] = (
        _identity(_OLD)["sha256"],
        len(_OLD),
        "finite_atlas_extension",
    )
    monkeypatch.setattr(optimizer, "_OPTIMIZER_ATLAS_SOURCES", authority)
    capture_sha = case.buffer.descriptor.capture["sha256"]
    assert isinstance(capture_sha, str)
    monkeypatch.setattr(optimizer, "CAPTURE_SHA256", capture_sha)
    return case


def _outer_payload(case: RelationCase) -> dict[str, Any] | None:
    """Use the actual outer adapter before its central source dispatch."""
    return optimizer._optimizer_source_input_correspondence(
        case.consumer.repository, case.row, case.logical, case.buffer
    )


def _observe_payload(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Call the actual relation helper and observe its invocation, never fake results."""
    calls: list[str] = []
    original = subject.validated_atlas_relation_context_source

    def observed(
        repository: Path, row: dict[str, Any], logical: str, resolver: SourceCapsule
    ) -> dict[str, Any]:
        calls.append(row["path"])
        return original(repository, row, logical, resolver)

    monkeypatch.setattr(optimizer, "validated_atlas_relation_context_source", observed)
    return calls


def test_actual_outer_payload_route_retains_relation_scope_and_old_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Close the exact payload branch without a broad presentation-matcher waiver."""
    case = _outer_payload_case(tmp_path / "repository", monkeypatch)
    calls = _observe_payload(monkeypatch)
    result = _outer_payload(case)
    assert isinstance(result, dict)
    assert calls == [_PAYLOAD] and result["path"] == _PAYLOAD
    assert result["classification"] == "atlas_relation_context_extension"
    assert result["original_member"] == case.logical
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["original_bytes"] == len(_OLD)
    assert result["whole_old_module_reconstructed"] is True
    assert result["retained_current_producer_digest_guard_relaxed"] is False
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False


@pytest.mark.parametrize(
    "damage", ("unknown_current", "wrong_group", "wrong_hash", "wrong_context")
)
def test_outer_payload_refuses_after_real_positive_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Keep exact outer membership guards before the fixed relation byte law."""
    case = _outer_payload_case(tmp_path / "repository", monkeypatch)
    calls = _observe_payload(monkeypatch)
    positive = _outer_payload(case)
    assert (
        isinstance(positive, dict)
        and positive["classification"] == "atlas_relation_context_extension"
    )
    assert calls == [_PAYLOAD]
    calls.clear()
    if damage == "unknown_current":
        case.target.write_bytes(case.target.read_bytes() + b"# unknown code\n")
    elif damage == "wrong_group":
        case.buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _MODELS)]
    elif damage == "wrong_hash":
        case.row["sha256"] = "0" * 64
    else:
        case.buffer.prefix = _CONTEXTS[1]
    with pytest.raises(ReportRebuildError):
        _outer_payload(case)
    assert calls == ([_PAYLOAD] if damage == "unknown_current" else [])


def test_existing_outer_workflow_route_stays_on_accepted_runtime_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retain the already qualified workflow route and its real runtime proof."""
    from .test_optimizer_runtime_workflow_route import (
        _invoke,
        _observe_runtime_route,
        _outer_case,
    )

    case = _outer_case(tmp_path / "repository", monkeypatch)
    calls = _observe_runtime_route(monkeypatch)

    def forbidden(
        repository: Path, row: dict[str, Any], logical: str, resolver: SourceCapsule
    ) -> dict[str, Any]:
        raise AssertionError("Workflow must retain its existing runtime route")

    monkeypatch.setattr(optimizer, "validated_atlas_relation_context_source", forbidden)
    result = _invoke(case)
    assert (
        isinstance(result, dict)
        and result["classification"] == "runtime_transport_extension"
    )
    assert calls == [case.row["path"]]


_NATIVE_METHOD_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/native-lra.js"


def _native_method_case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str = _CONTEXTS[1]
) -> RelationCase:
    """Repin inert comment bytes at the non-Python coordinate, never execute them."""
    case = _case(root, monkeypatch, prefix, _NATIVE_METHOD_SOURCE)
    contracts = dict(subject._RELATION_CONTEXT_CONTRACTS)
    contracts[_NATIVE_METHOD_SOURCE] = (
        len(_OLD),
        _identity(_OLD)["sha256"],
        "ordinary_original_bytes",
        _PAIRS,
    )
    monkeypatch.setattr(subject, "_RELATION_CONTEXT_CONTRACTS", contracts)
    return case


def _observe_native_method(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record actual custody results from the real chronology non-Python route."""
    observed: list[dict[str, Any]] = []
    original = subject.validated_atlas_relation_context_source

    def actual(
        repository: Path, row: dict[str, Any], logical: str, resolver: SourceCapsule
    ) -> dict[str, Any]:
        result = original(repository, row, logical, resolver)
        observed.append(result)
        return result

    monkeypatch.setattr(chronology, "validated_atlas_relation_context_source", actual)
    return observed


def test_chronology_nonpython_method_context_uses_real_fixed_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An actual .js dispatch reads old Git comments and current bytes exactly."""
    case = _native_method_case(tmp_path / "repository", monkeypatch)
    observed = _observe_native_method(monkeypatch)
    assert _dispatch(case) is None
    assert len(observed) == 1
    role = observed[0]
    assert role["path"] == _NATIVE_METHOD_SOURCE
    assert role["original_member"] == "source/" + _NATIVE_METHOD_SOURCE
    assert role["original_bytes"] == len(_OLD)
    assert role["original_sha256"] == _identity(_OLD)["sha256"]
    assert role["classification"] == "atlas_relation_context_extension"
    assert role["whole_old_module_reconstructed"] is True
    assert role["current_regular_single_link_and_stable"] is True
    assert role["declared_native_method_display_intentionally_extended"] is True
    assert role["producer_inventory_intentionally_extended"] is False
    assert role["retained_current_producer_digest_guard_relaxed"] is False
    assert role["historical_native_equal_current_output_claimed"] is False
    assert role["historical_browser_equal_current_browser_claimed"] is False
    assert role["old_native_equal_current_admission_claimed"] is False
    assert role["new_native_or_scientific_execution_claimed"] is False


def test_chronology_unknown_javascript_bytes_refuse_after_real_route_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A .js extension never becomes an unrestricted historical display role."""
    case = _native_method_case(tmp_path / "repository", monkeypatch)
    assert _dispatch(case) is None
    case.target.write_bytes(_CURRENT + b"globalThis.unclassified = true;\n")
    with pytest.raises(ReportRebuildError):
        _dispatch(case)


@pytest.mark.parametrize("defect", ("logical", "hash", "group", "detached"))
def test_chronology_method_binding_refuses_after_positive_nonpython_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    """The one new language coordinate keeps the original real capsule bindings."""
    case = _native_method_case(tmp_path / "repository", monkeypatch)
    assert _dispatch(case) is None
    if defect == "logical":
        case.logical = "source/" + _MODELS
    elif defect == "hash":
        case.row["sha256"] = "0" * 64
    elif defect == "group":
        case.buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _MODELS)]
    else:
        case.buffer.detached = frozenset()
    with pytest.raises(ReportRebuildError):
        _dispatch(case)


def test_optimizer_catalog_does_not_authorize_chronology_only_method_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A positive chronology source remains refused by both optimizer entrypoints."""
    chronology_case = _native_method_case(tmp_path / "chronology", monkeypatch)
    assert _dispatch(chronology_case) is None
    optimizer_case = _native_method_case(
        tmp_path / "optimizer", monkeypatch, _CONTEXTS[0]
    )
    assert optimizer_case.buffer.read_source(optimizer_case.logical) == _OLD
    assert _NATIVE_METHOD_SOURCE not in subject.ATLAS_RELATION_CONTEXT_SOURCES
    with pytest.raises(ReportRebuildError):
        optimizer_case.admit()
    with pytest.raises(ReportRebuildError):
        _dispatch(optimizer_case)


def test_nonpython_current_source_final_read_is_observed_after_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changing the final current observation is refused without faking a matcher."""
    case = _native_method_case(tmp_path / "repository", monkeypatch)
    assert _dispatch(case) is None
    read_bytes = Path.read_bytes
    reads = 0

    def changing(path: Path) -> bytes:
        nonlocal reads
        body = read_bytes(path)
        if path == case.target:
            reads += 1
            if reads == 2:
                return body + b"// changed final observation\n"
        return body

    monkeypatch.setattr(Path, "read_bytes", changing)
    with pytest.raises(ReportRebuildError, match="changed during verification"):
        _dispatch(case)
    assert reads == 2


def test_actual_native_method_asset_two_spans_restore_whole_old_git_module() -> None:
    """Read actual original/current buffers as data; never execute either script."""
    repository = Path(__file__).resolve().parents[7]
    size, digest, prior, spans = subject._RELATION_CONTEXT_CONTRACTS[
        _NATIVE_METHOD_SOURCE
    ]
    originals = []
    for revision in (
        "1286cd6b74e3cbe87a2cc94851a11cc8f941375c",
        "d37a306ccd39ffb853352ec03cd8d8b6dce29483",
    ):
        body = subprocess.check_output(
            [
                "git",
                "--no-replace-objects",
                "show",
                revision + ":" + _NATIVE_METHOD_SOURCE,
            ],
            cwd=repository,
            timeout=20,
        )
        assert len(body) == size == 18936
        assert _identity(body)["sha256"] == digest
        originals.append(body)
    assert originals[0] == originals[1] and prior == "ordinary_original_bytes"
    current = (repository / _NATIVE_METHOD_SOURCE).read_bytes()
    assert len(spans) == 2
    assert subject.atlas_relation_context_extension_matches(
        _NATIVE_METHOD_SOURCE, originals[0], current
    )
    assert not subject.atlas_relation_context_extension_matches(
        _NATIVE_METHOD_SOURCE, originals[0], current + b"globalThis.unknown = true;\n"
    )
    assert not subject.atlas_relation_context_extension_matches(
        _NATIVE_METHOD_SOURCE, originals[0] + b"// counterfeit old\n", current
    )
    for before, after in spans:
        assert current.count(after) == 1
        assert not subject.atlas_relation_context_extension_matches(
            _NATIVE_METHOD_SOURCE, originals[0], current.replace(after, before, 1)
        )


def test_fixed_context_source_sets_are_exactly_five_python_and_six_chronology() -> None:
    """Current selected scope stays distinct from the broad retained catalogue."""
    assert frozenset(_SOURCES) == subject.ATLAS_RELATION_CONTEXT_SOURCES
    assert frozenset((*_SOURCES, _NATIVE_METHOD_SOURCE)) == (
        subject.CHRONOLOGY_ATLAS_RELATION_CONTEXT_SOURCES
    )
    assert all(name.endswith(".py") for name in subject.ATLAS_RELATION_CONTEXT_SOURCES)
