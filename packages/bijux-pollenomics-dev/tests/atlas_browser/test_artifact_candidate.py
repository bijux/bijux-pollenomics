"""Counterexamples for local artifact identity without invented output commits."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import zipfile

import pytest

from bijux_pollenomics_dev.ci.atlas_browser import artifact_candidate as audit
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    GENERIC_TIME_AWARE_PROFILE,
    AtlasArtifactCandidate,
    AtlasBrowserContractError,
    BrowserVerificationPlan,
    safe_artifact_path,
)

from .artifact_fixtures import artifact_plan, encode, rewrite_receipt


def test_v3_roundtrip_and_exact_candidate_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    assert plan.as_json()["schema_version"] == "atlas-browser-verification-plan.v3"
    assert BrowserVerificationPlan.from_json(plan.as_json()) == plan
    assert "atlas_output_commit" not in plan.candidate.as_json()
    with pytest.raises(AtlasBrowserContractError, match="fields must be exact"):
        AtlasArtifactCandidate.from_json(
            {**plan.candidate.as_json(), "atlas_output_commit": "a" * 40}
        )
    with pytest.raises(AtlasBrowserContractError, match="one native"):
        replace(plan, verification_profile=GENERIC_TIME_AWARE_PROFILE)


@pytest.mark.parametrize(
    "value",
    [
        "/absolute",
        "artifacts//x",
        "artifacts/../x",
        "artifacts/./x",
        "a\\b",
        "a\0b",
        "",
        None,
    ],
)
def test_ambiguous_artifact_paths_refuse(value: object) -> None:
    with pytest.raises(AtlasBrowserContractError):
        safe_artifact_path(value)


def test_artifact_inventory_and_actual_served_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    observed = audit.audit_artifact_candidate(plan)
    report = {"served_artifact_bytes": observed["files"], "refused_artifact_reads": []}
    audit.verify_served_bytes(plan, observed, report)
    changed = json.loads(json.dumps(report))
    changed["served_artifact_bytes"][0]["sha256"] = "0" * 64
    with pytest.raises(AtlasBrowserContractError, match="served artifact bytes"):
        audit.verify_served_bytes(plan, observed, changed)
    with pytest.raises(AtlasBrowserContractError, match="refused altered"):
        audit.verify_served_bytes(
            plan,
            observed,
            {
                **report,
                "refused_artifact_reads": [
                    {"path": "changed-then-restored", "error": "digest"}
                ],
            },
        )
    with pytest.raises(AtlasBrowserContractError, match="required artifact identities"):
        audit.verify_served_bytes(
            plan, observed, {**report, "served_artifact_bytes": []}
        )


@pytest.mark.parametrize(
    "member",
    [
        "artifacts/source/uv.lock",
        "artifacts/geometry.json",
        "artifacts/presentation/map.html",
        "artifacts/generation.json",
    ],
)
def test_source_input_output_receipt_mutations_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, member: str
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    path = tmp_path / member
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(AtlasBrowserContractError):
        audit.audit_artifact_candidate(plan)


@pytest.mark.parametrize(
    "updates",
    [
        {"source_relation": "recorded_snapshot"},
        {"runtime": {"python": "3.11"}},
        {"invocation": {}},
        {"inputs": None},
        {"source_files": {}},
        {"generator_repository_tree": "0" * 40},
    ],
)
def test_self_rehashed_receipt_cannot_bypass_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, updates: dict[str, object]
) -> None:
    plan = rewrite_receipt(artifact_plan(tmp_path, monkeypatch), **updates)
    with pytest.raises(AtlasBrowserContractError):
        audit.audit_artifact_candidate(plan)


def test_source_and_output_overlap_refuse_before_browser_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    with pytest.raises(AtlasBrowserContractError, match="disjoint"):
        replace(plan, artifact_root=tmp_path / "artifacts/presentation/browser")
    with pytest.raises(AtlasBrowserContractError, match="overlaps generation inputs"):
        audit.audit_artifact_candidate(
            replace(plan, artifact_root=tmp_path / "artifacts/input/browser")
        )
    assert not (tmp_path / "artifacts/input/browser").exists()


def test_source_inventory_refuses_extra_and_symbolic_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    extra = tmp_path / "artifacts/source/configs/scientific-contracts/extra"
    extra.write_text("uncommitted")
    with pytest.raises(AtlasBrowserContractError, match="inventory differs"):
        audit.audit_artifact_candidate(plan)
    extra.unlink()
    extra.symlink_to(tmp_path / "artifacts/geometry.json")
    with pytest.raises(AtlasBrowserContractError, match="symbolic"):
        audit.audit_artifact_candidate(plan)


def test_duplicate_and_nonfinite_json_refuse() -> None:
    for value in (b'{"a":1,"a":2}', b'{"a":NaN}', b"[]"):
        with pytest.raises(AtlasBrowserContractError):
            audit.json_bytes(value)


def test_rehashed_zip_must_still_match_original_product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    assert isinstance(plan.candidate, AtlasArtifactCandidate)
    presentation = tmp_path / plan.candidate.presentation_root
    with zipfile.ZipFile(presentation / "product.zip", "w") as archive:
        archive.writestr("manifest.json", b"wrong bytes")
    manifest = json.loads((presentation / "manifest.json").read_bytes())
    manifest["files"]["product.zip"] = audit.sha256(
        (presentation / "product.zip").read_bytes()
    )
    (presentation / "manifest.json").write_bytes(encode(manifest))
    candidate = replace(
        plan.candidate,
        presentation_manifest_sha256=audit.sha256(encode(manifest)),
        presentation_inventory_sha256=audit.canonical_digest(
            audit.inventory(presentation)
        ),
    )
    plan = replace(plan, candidate=candidate)
    receipt = json.loads((tmp_path / candidate.generator_receipt).read_bytes())
    receipt["output"].update(
        presentation_manifest_sha256=candidate.presentation_manifest_sha256,
        presentation_inventory_sha256=candidate.presentation_inventory_sha256,
    )
    plan = rewrite_receipt(plan, output=receipt["output"])
    with pytest.raises(AtlasBrowserContractError, match="ZIP"):
        audit.audit_artifact_candidate(plan)


@pytest.mark.parametrize(
    "schema", [[], None, True, "atlas-browser-verification-plan.v2"]
)
def test_v3_schema_cannot_be_downgraded_or_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, schema: object
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    with pytest.raises(AtlasBrowserContractError):
        BrowserVerificationPlan.from_json({**plan.as_json(), "schema_version": schema})
