"""Selected proof metadata uses bounded parts and preserves every rooted occurrence."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from .native_products import products


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence"
    )


def test_selected_target_opens_only_its_proof_parts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = owner()
    monkeypatch.setattr(module, "PART_TARGET_BYTES", 1100)
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    index = json.loads((result.directory / "evidence-manifest.json").read_bytes())
    target_parts = {
        ref["part_sha256"] for ref in index["targets"]["taxon-11"]["proof_ranges"]
    }
    all_parts = {row["sha256"] for row in index["parts"]}
    assert target_parts < all_parts
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent == result.directory / "proofs":
            opened.append(path.stem)
            assert path.stem in target_parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    selected = module.read_neotoma_linked_evidence_target(
        result.directory,
        expected_manifest_sha256=result.manifest_sha256,
        kind="taxon",
        native_id=11,
    )
    assert set(opened) == target_parts
    assert len(opened) == len(target_parts)
    assert len(selected["source_proofs"]) == 2


def test_protected_contact_metadata_keeps_all_development_occurrences(
    tmp_path: Path,
) -> None:
    module = owner()
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    selected = module.read_neotoma_linked_evidence_target(
        result.directory,
        expected_manifest_sha256=result.manifest_sha256,
        kind="contact",
        native_id=900,
    )
    assert selected["target"]["exposure_role"] == "heldout_no_numerical_access"
    assert len(selected["target"]["metadata_dependencies"]) == 1
    assert {p["root_dataset_id"] for p in selected["source_proofs"]} == {201, 203}


def test_reordered_proof_ranges_refuse_even_with_a_different_external_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = owner()
    monkeypatch.setattr(module, "PART_TARGET_BYTES", 1100)
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    path = result.directory / "evidence-manifest.json"
    index = json.loads(path.read_bytes())
    refs = index["targets"]["taxon-11"]["proof_ranges"]
    assert len(refs) == 2
    refs.reverse()
    raw = json.dumps(index).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="order|range"):
        module.read_neotoma_linked_evidence_target(
            result.directory,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            kind="taxon",
            native_id=11,
        )


def test_scoped_target_selection_references_complete_proofs_and_protected_metadata(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    inputs = products(tmp_path)
    evidence = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    protocol = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.protocol"
    )
    plan = NeotomaLinkedResourcePlan(
        tuple(inputs["source_facets"]),
        (NeotomaLinkedTarget("contact", 900), NeotomaLinkedTarget("taxon", 11)),
    )
    targets, _, reference = protocol.prepare_scoped_targets(
        plan,
        inputs["source_facets"],
        DEFAULT_RESOURCE_LIMITS,
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
    )
    assert reference["manifest_sha256"] == evidence.manifest_sha256
    assert targets[0]["exposure_role"] == "heldout_no_numerical_access"
    assert targets[0]["metadata_dependency_count"] == 1
    assert targets[0]["source_proof_reference"]["occurrence_count"] == 2
    assert "source_proofs" not in targets[0]
    assert targets[1]["source_proof_reference"]["occurrence_count"] == 2


def test_new_capture_skips_protected_shared_target_and_reopens_with_compact_evidence(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )

    from ...resources.native_payloads import response

    inputs = products(tmp_path)
    evidence = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    api = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources"
    )
    plan = NeotomaLinkedResourcePlan(
        tuple(inputs["source_facets"]),
        (NeotomaLinkedTarget("contact", 900), NeotomaLinkedTarget("taxon", 11)),
    )
    calls = []
    raw = b'{"status":"success","data":[{"taxonid":11}],"message":"native"}'

    def fetch(url: str, **_: Any) -> Any:
        calls.append(url)
        return response(url, raw)

    target = tmp_path / "linked"
    captured = api.capture_neotoma_linked_resources(
        target,
        plan=plan,
        source_facets=inputs["source_facets"],
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
        fetch=fetch,
    )
    assert calls == ["https://api.neotomadb.org/v2.0/data/taxa/11"]
    assert captured.request_count == 1
    assert captured.partitions == {
        "not_attempted_exposure_role": 1,
        "received_complete_unqualified_linked_resource": 1,
    }
    manifest = json.loads((target / "capture-manifest.json").read_bytes())
    control = json.loads((target / "request-plan.json").read_bytes())
    assert manifest["source_evidence"] == control["source_evidence"]
    assert manifest["source_evidence"]["manifest_sha256"] == evidence.manifest_sha256
    assert "source_proofs" not in control["targets"][0]
    body = api.read_neotoma_linked_body(
        target,
        expected_manifest_sha256=captured.manifest_sha256,
        target_key="taxon-11",
        source_facets=inputs["source_facets"],
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
    )
    assert body.body == raw
    assert {proof["root_dataset_id"] for proof in body.source_proofs} == {201, 203}


def test_scoped_qualification_uses_proof_references_without_semantic_source_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )

    from ...resources.native_payloads import response

    inputs = products(tmp_path)
    module = owner()
    evidence = module.publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    api = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources"
    )
    plan = NeotomaLinkedResourcePlan(
        tuple(inputs["source_facets"]), (NeotomaLinkedTarget("taxon", 11),)
    )
    source = {
        "status": "success",
        "message": "native",
        "data": [
            {
                "taxonid": 11,
                "taxoncode": None,
                "taxonname": "Native plant",
                "author": None,
                "ecolgroup": "UPHE",
                "highertaxonid": 12,
                "status": "extant",
                "taxagroupid": "VPL",
                "publicationid": 13,
                "publication": "Native reference",
            }
        ],
    }
    captured = api.capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan,
        source_facets=inputs["source_facets"],
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
        fetch=lambda url, **_: response(url, json.dumps(source).encode()),
    )
    monkeypatch.setattr(
        module,
        "discover_neotoma_facet_links",
        lambda *a, **k: pytest.fail("old source semantics repeated"),
    )
    qualified = api.qualify_neotoma_linked_capture(
        tmp_path / "linked",
        expected_manifest_sha256=captured.manifest_sha256,
        source_facets=inputs["source_facets"],
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
    )
    assert qualified["partitions"] == {"parsed_linked_source": 1}
    assert qualified["resources"][0]["source_proof_reference"]["occurrence_count"] == 2
    assert "source_proofs" not in qualified["resources"][0]
    assert (
        qualified["HTTP_requests"] == 0
        and qualified["source_capture_relabelled"] is False
    )


@pytest.mark.parametrize(
    "mutation", ["missing_evidence", "late_bool_id", "omitted_protected_source"]
)
def test_new_capture_refuses_scope_bypass_before_outcome_access_or_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )

    inputs = products(tmp_path, separate=True)
    evidence = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    sources = dict(inputs["source_facets"])
    targets = [NeotomaLinkedTarget("taxon", 11)]
    if mutation == "missing_evidence":
        evidence = None
    elif mutation == "late_bool_id":
        targets.append(NeotomaLinkedTarget("taxon", True))
    else:
        del sources[
            next(
                key for key, path in sources.items() if path.name == "protected-facets"
            )
        ]
    plan = NeotomaLinkedResourcePlan(tuple(sources), tuple(targets))
    api = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources"
    )
    numerical = set(inputs["source_facets"].values())
    original = Path.open
    reads = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent in numerical and path.suffix == ".body":
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError):
        api.capture_neotoma_linked_resources(
            tmp_path / "linked",
            plan=plan,
            source_facets=sources,
            evidence=evidence,
            scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
            fetch=lambda *a, **k: pytest.fail("Unproved linked target reached HTTP"),
        )
    assert reads == []
    assert (
        not (tmp_path / "linked").exists()
        and not (tmp_path / ".linked.staging").exists()
    )


@pytest.mark.parametrize(
    "mutation", ["proof_count", "proof_range", "role", "foreign_state"]
)
def test_rehashed_capture_cannot_forge_state_pointer_or_restrictive_role(
    tmp_path: Path,
    mutation: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )

    from ...resources.native_payloads import response

    inputs = products(tmp_path)
    evidence = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    api = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources"
    )
    plan = NeotomaLinkedResourcePlan(
        tuple(inputs["source_facets"]), (NeotomaLinkedTarget("taxon", 11),)
    )
    directory = tmp_path / "linked"
    api.capture_neotoma_linked_resources(
        directory,
        plan=plan,
        source_facets=inputs["source_facets"],
        evidence=evidence,
        scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
        fetch=lambda url, **_: response(url, b'{"status":"success","data":[]}'),
    )
    manifest = json.loads((directory / "capture-manifest.json").read_bytes())
    control = json.loads((directory / "request-plan.json").read_bytes())
    target = control["targets"][0]
    if mutation == "proof_count":
        target["source_proof_reference"]["occurrence_count"] = 1
    elif mutation == "proof_range":
        target["source_proof_reference"]["proof_ranges"][0]["count"] = 0
    elif mutation == "role":
        target["exposure_role"] = "reserved_candidate_confirmation"
    else:
        control["source_evidence"]["manifest_sha256"] = "f" * 64
        manifest["source_evidence"] = control["source_evidence"]
    manifest["resources"][0]["identity"] = target
    raw = (json.dumps(control, sort_keys=True) + "\n").encode()
    (directory / "request-plan.json").write_bytes(raw)
    manifest["plan_sha256"] = sha256(raw).hexdigest()
    raw = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    (directory / "capture-manifest.json").write_bytes(raw)
    with pytest.raises(ValueError, match="evidence|proof|closure"):
        api.replay_neotoma_linked_resources(
            directory,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            source_facets=inputs["source_facets"],
            evidence=evidence,
            scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
        )
