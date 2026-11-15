"""Keep the three atlas extensions confined to exact source and old byte authority."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as chronology,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as current,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    PAYLOAD,
    VERDICT,
    WORKFLOW,
    atlas_extension_matches,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)


def _buffer(
    root: Path, monkeypatch: pytest.MonkeyPatch, name: str, old: bytes, new: bytes
) -> SourceCapsule:
    """Bind an owned presentation example to an actual inert Git capture."""
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    _write(root / name, old)
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
        "test(atlas): bind owned presentation extension",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + name).decode().strip()
    prefix, logical = "data/atlas/source-view-capture", "source/" + name
    members = {logical: _identity(old)}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    entries = json.dumps([[name, blob]], separators=(",", ":")).encode()
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
                "git_entries_sha256": hashlib.sha256(entries).hexdigest(),
                "paths": [[logical, name]],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    Consumer(
        "qualification",
        root,
        prefix,
        members,
        frozenset(members),
        {logical: old},
        descriptor,
        [],
    ).repin(monkeypatch)
    result = index.validated_descriptor(root, prefix, members)
    assert result.read_source(logical) == old
    (root / name).write_bytes(new)
    return result


@pytest.fixture
def own_sources() -> dict[str, tuple[bytes, bytes]]:
    """Declare short owned source examples, not copies of a maintained package."""
    workflow = """from __future__ import annotations

def _map(stage, layers, *, temporal_profile=None):
    if not layers:
        return None
    copy_map_assets(stage)
    return 7
"""
    new_workflow = workflow.replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\nfrom importlib.resources import files\n",
    ).replace(
        "    copy_map_assets(stage)\n",
        """    asset_directory = copy_map_assets(stage)
    (asset_directory / "native-lra.js").write_bytes(
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/native-lra.js")
        .read_bytes()
    )
""",
    )
    payload = """from __future__ import annotations

def build_map_document_payload(native_lra=None, static_assets=None, asset_base_path="own", escape_html_fn=str):
    return {
        "own": 7,
        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER
        if native_lra is not None
        else "",
    }
"""
    new_payload = payload.replace(
        '        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER\n',
        """        "__NATIVE_LRA_SCRIPT_TAG__": (
            f'<script src="{escape_html_fn(asset_base_path)}/native-lra.js"></script>'
            if native_lra is not None and static_assets is not None
            else ""
        ),
        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER
""",
    ).replace(
        "        if native_lra is not None\n",
        "        if native_lra is not None and static_assets is None\n",
    )
    verdict = '''from __future__ import annotations

def evaluate_browser_report(report: object, *, candidate: BrowserCandidate, verification_profile: str) -> JsonObject:
    """Preserve the owned old complete-report behavior."""
    document = _mapping(report, label="browser report")
    return 7
'''
    new_verdict = (
        verdict.replace(
            '    document = _mapping(report, label="browser report")\n',
            """    document = _mapping(report, label="browser report")
    if document.get("verification_mode", "complete-profile") != "complete-profile":
        raise AtlasBrowserContractError(
            "scoped provider matrix is not a complete browser profile"
        )
""",
        )
        + '''

def evaluate_provider_failure_matrix(
    report: object, *, candidate: BrowserCandidate, scopes: frozenset[str]
) -> JsonObject:
    """This new API needs current tests, not historical qualification."""
    return {"scope": "new-current-api-only"}
'''
    )
    return {
        WORKFLOW: (workflow.encode(), new_workflow.encode()),
        PAYLOAD: (payload.encode(), new_payload.encode()),
        VERDICT: (verdict.encode(), new_verdict.encode()),
    }


@pytest.mark.parametrize("name", [WORKFLOW, PAYLOAD, VERDICT])
def test_exact_named_extensions_preserve_the_entire_owned_old_module(
    own_sources: dict[str, tuple[bytes, bytes]], name: str
) -> None:
    old, new = own_sources[name]
    assert atlas_extension_matches(name, old, new)
    assert not atlas_extension_matches("packages/unknown/math.py", old, new)
    assert not atlas_extension_matches(name, old + b"\n# changed original\n", new)


@pytest.mark.parametrize("name", [WORKFLOW, PAYLOAD, VERDICT])
@pytest.mark.parametrize("damage", ["math", "header", "comment", "import", "guard"])
def test_noninserted_math_headers_comments_imports_and_guards_remain_exact(
    own_sources: dict[str, tuple[bytes, bytes]], name: str, damage: str
) -> None:
    old, new = own_sources[name]
    if damage == "math":
        new = new.replace(b"return 7", b"return 9").replace(b'"own": 7', b'"own": 9')
    elif damage == "header":
        new = new.replace(b"def _map(stage, layers,", b"def _map(changed, layers,")
        new = new.replace(b"native_lra=None", b"native_lra=True")
        new = new.replace(b"verification_profile: str", b"verification_profile: int")
    elif damage == "comment":
        new += b"\n# unreviewed source drift\n"
    elif damage == "import":
        new = new.replace(
            b"from __future__ import annotations\n",
            b"from __future__ import annotations\nimport unreviewed\n",
        )
    elif name == WORKFLOW:
        new = new.replace(b'"assets/native-lra.js"', b'"../unreviewed.js"')
    elif name == PAYLOAD:
        new = new.replace(b"and static_assets is None", b"or static_assets is None")
    else:
        new = new.replace(
            b'"complete-profile") != "complete-profile"',
            b'"other") != "complete-profile"',
        )
    assert not atlas_extension_matches(name, old, new)


@pytest.mark.parametrize("consumer", ["chronology", "router"])
@pytest.mark.parametrize("name", [WORKFLOW, PAYLOAD, VERDICT])
@pytest.mark.parametrize(
    "damage",
    [
        "none",
        "captured_hash",
        "wrong_logical",
        "not_detached",
        "missing",
        "symlink",
        "hardlink",
    ],
)
def test_normal_import_consumers_keep_real_file_and_source_binding_guards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    consumer: str,
    name: str,
    damage: str,
) -> None:
    old, new = own_sources[name]
    target = tmp_path / name
    logical = "source/" + name
    delegated = consumer == "router" and name in {PAYLOAD, WORKFLOW}
    if delegated:
        from ..test_optimizer_atlas_source_roles import _world

        rows, capsule, bodies = _world(tmp_path, monkeypatch, own_sources)
        logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        old, new = bodies[logical], target.read_bytes()
        assert rows[name] == {"path": name, **_identity(old)}
    else:
        capsule = _buffer(tmp_path, monkeypatch, name, old, new)
    detached = frozenset({logical})
    digest = hashlib.sha256(old).hexdigest()

    def check() -> None:
        if consumer == "chronology":
            chronology._validate_current_source(
                tmp_path, name, logical, old, digest, detached, source_buffer=capsule
            )
        else:
            facts = current.validated_current_scientific_source(
                tmp_path,
                {"path": name, "sha256": digest, "bytes": len(old)},
                logical,
                capsule,
            )
            assert facts is not None
            if delegated:
                assert (
                    facts["classification"]
                    == {
                        PAYLOAD: "atlas_relation_context_extension",
                        WORKFLOW: "runtime_transport_extension",
                    }[name]
                )
                assert facts["historical_native_equal_current_output_claimed"] is False
                assert (
                    facts["historical_browser_equal_current_browser_claimed"] is False
                )
            else:
                assert facts["current_browser_or_native_equivalence_claimed"] is False
                assert facts["new_provider_api_qualified_by_historical_source"] is False

    check()
    if damage == "captured_hash":
        digest = "0" * 64
    elif damage == "wrong_logical":
        logical = "runtime/" + name
        detached = frozenset({logical})
    elif damage == "not_detached":
        detached = frozenset()
        capsule.descriptor = replace(capsule.descriptor, detached=detached)
    elif damage == "missing":
        target.unlink()
    elif damage in {"symlink", "hardlink"}:
        other = tmp_path / "own-link-source"
        other.write_bytes(new)
        target.unlink()
        if damage == "symlink":
            target.symlink_to(other)
        else:
            target.hardlink_to(other)

    if damage == "none":
        check()
    else:
        with pytest.raises((ReportRebuildError, ValueError, OSError)):
            check()
