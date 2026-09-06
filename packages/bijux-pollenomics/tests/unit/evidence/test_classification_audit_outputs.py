from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from bijux_pollenomics.evidence.classification.audit_outputs import (
    ClassificationAuditMaterializationResult,
    ClassificationAuditOutputPaths,
    ClassificationAuditRefusalError,
    materialize_classification_audit,
)
from bijux_pollenomics.evidence.classification.neotoma import (
    build_neotoma_classification_accounting,
)

_COUNTRY_PARTITION = ("SE", "DK", "NO", "FI", "UNASSIGNED")


def _observation(
    observation_id: str,
    *,
    variable_id: str,
    taxon_id: int,
    name: str,
    site_id: str,
    country_code: str,
    taxon_group: str = "Vascular plants",
    ecological_group: str = "UPHE",
    element: str = "pollen",
    element_type: str | None = "pollen",
    unit: str = "NISP",
    unit_family: str = "count",
) -> dict[str, Any]:
    return {
        "observation_id": observation_id,
        "variable_id": variable_id,
        "site_id": site_id,
        "country_code": country_code,
        "source_taxon_id": taxon_id,
        "source_reported_name": name,
        "source_taxon_group": taxon_group,
        "source_ecological_group": ecological_group,
        "source_element": element,
        "source_element_type": element_type,
        "source_unit": unit,
        "unit_family": unit_family,
    }


def _accounting(*, reverse: bool = False) -> dict[str, object]:
    observations = [
        _observation(
            "observation:plantago",
            variable_id="variable:plantago",
            taxon_id=220,
            name="Plantago lanceolata",
            site_id="site:sweden",
            country_code="NO",
        ),
        _observation(
            "observation:rumex",
            variable_id="variable:rumex",
            taxon_id=268,
            name="Rumex",
            site_id="site:unassigned",
            country_code="FI",
        ),
        _observation(
            "observation:laboratory",
            variable_id="variable:laboratory",
            taxon_id=63,
            name="Pollen concentration",
            site_id="site:denmark",
            country_code="DK",
            taxon_group="Laboratory analyses",
            ecological_group="LABO",
            element="concentration",
            element_type="concentration",
            unit="grains/cm3",
            unit_family="concentration_per_volume",
        ),
    ]
    sites = [
        {"site_id": "site:sweden", "source_geopolitical": ["Sweden"]},
        {"site_id": "site:unassigned", "source_geopolitical": []},
        {"site_id": "site:denmark", "source_geopolitical": ["Denmark"]},
    ]
    if reverse:
        observations.reverse()
        sites.reverse()
    variables = [
        {
            "variable_id": observation["variable_id"],
            "source_taxon_id": observation["source_taxon_id"],
            "source_reported_name": observation["source_reported_name"],
        }
        for observation in observations
    ]
    snapshot = {
        "schema_version": "neotoma-relational-snapshot.v1",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:classification-fixture",
        "build_id": "classification-build-1",
        "sites": sites,
        "variables": variables,
        "observations": observations,
    }
    return build_neotoma_classification_accounting(snapshot)


def _materialize(
    accounting: dict[str, object],
    *,
    output_root: Path,
    allowed_output_parent: Path,
    paths: ClassificationAuditOutputPaths | None = None,
) -> ClassificationAuditMaterializationResult:
    return materialize_classification_audit(
        accounting,
        paths=paths or ClassificationAuditOutputPaths.under(output_root),
        allowed_output_parent=allowed_output_parent,
        classification_contract_version="1.0.0",
        classification_contract_digest=f"sha256:{'a' * 64}",
        classification_producer_id="bijux-pollenomics.classification-audit",
        classification_producer_version="1",
        classification_producer_digest=f"sha256:{'b' * 64}",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_zero_accepted_accounting_emits_lossless_queues_and_release_refusal(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "classification-audit"

    result = _materialize(
        _accounting(), output_root=output_root, allowed_output_parent=tmp_path
    )

    concepts = _read_json(output_root / "concept_denominators.json")
    observations = _read_json(output_root / "observation_denominators.json")
    memberships = _read_json(output_root / "observation_memberships.json")
    accepted = _read_json(output_root / "accepted_mapping_queue.json")
    unmapped = _read_json(output_root / "unmapped_mapping_queue.json")
    not_applicable = _read_json(output_root / "not_applicable_mapping_queue.json")
    review = _read_json(output_root / "review_queue.json")
    release = _read_json(output_root / "release_metadata.json")

    assert result.disposition == "created"
    assert result.file_count == 10
    assert result.concept_count == 3
    assert result.observation_count == 3
    assert result.accepted_mapping_count == 0
    assert result.release_status == "refused"
    assert concepts["mapping_status_counts"] == {
        "accepted": 0,
        "accepted_qualified": 0,
        "contested": 0,
        "not_applicable": 1,
        "refused": 0,
        "unmapped": 2,
    }
    assert observations["total_observation_count"] == 3
    assert memberships["record_count"] == 3
    assert {row["observation_id"] for row in memberships["records"]} == {
        "observation:plantago",
        "observation:rumex",
        "observation:laboratory",
    }
    assert accepted["record_count"] == 0
    assert unmapped["record_count"] == 2
    assert not_applicable["record_count"] == 1
    assert review["record_count"] == 2
    assert release["release_status"] == "refused"
    assert release["public_release_allowed"] is False
    assert release["accepted_mapping_count"] == 0
    assert release["human_approval_synthesized"] is False
    assert release["release_reason_codes"] == [
        "accepted_mapping_not_available",
        "mapping_evidence_not_available",
        "human_review_not_available",
    ]


def test_queues_preserve_empty_mapping_review_and_citation_fields(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "classification-audit"
    _materialize(_accounting(), output_root=output_root, allowed_output_parent=tmp_path)

    unmapped = _read_json(output_root / "unmapped_mapping_queue.json")
    records = unmapped["records"]
    assert isinstance(records, list)
    assert records
    for row in records:
        assert row["mapping_version"] is None
        assert row["reviewer_id"] is None
        assert row["decision_date"] is None
        assert row["citation_reference_ids"] == []
        assert row["accepted_taxon_concept_id"] is None
        assert row["review_complete"] is False
        assert row["release_eligible"] is False


def test_country_partitions_are_exact_and_include_unassigned(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "classification-audit"
    _materialize(_accounting(), output_root=output_root, allowed_output_parent=tmp_path)

    payload = _read_json(output_root / "country_partitions.json")
    assert [row["country_code"] for row in payload["source_country"]] == list(
        _COUNTRY_PARTITION
    )
    assert [row["country_code"] for row in payload["governed_country"]] == list(
        _COUNTRY_PARTITION
    )
    relation = {
        (row["source_country_code"], row["governed_country_code"]): row
        for row in payload["country_relation"]
    }
    assert len(relation) == 25
    assert relation[("SE", "NO")]["observation_count"] == 1
    assert relation[("SE", "NO")]["concept_membership_count"] == 1
    assert relation[("UNASSIGNED", "FI")]["observation_count"] == 1
    assert relation[("UNASSIGNED", "FI")]["concept_membership_count"] == 1
    assert relation[("DK", "DK")]["observation_count"] == 1
    assert relation[("DK", "DK")]["concept_membership_count"] == 1


def test_manifest_hashes_and_counts_every_payload(tmp_path: Path) -> None:
    output_root = tmp_path / "classification-audit"
    first = _materialize(
        _accounting(), output_root=output_root, allowed_output_parent=tmp_path
    )
    second = _materialize(
        _accounting(), output_root=output_root, allowed_output_parent=tmp_path
    )

    manifest = _read_json(output_root / "manifest.json")
    entries = manifest["files"]
    assert isinstance(entries, list)
    assert first.manifest_sha256 == second.manifest_sha256
    assert second.disposition == "unchanged"
    assert manifest["payload_file_count"] == 9
    assert manifest["classification_contract_digest"] == f"sha256:{'a' * 64}"
    assert manifest["classification_producer_digest"] == f"sha256:{'b' * 64}"
    assert [row["path"] for row in entries] == sorted(row["path"] for row in entries)
    for row in entries:
        payload_bytes = (output_root / row["path"]).read_bytes()
        payload = json.loads(payload_bytes)
        assert hashlib.sha256(payload_bytes).hexdigest() == row["sha256"]
        assert payload["record_count"] == row["record_count"]


def test_reordered_source_accounting_materializes_identical_bytes(
    tmp_path: Path,
) -> None:
    forward_root = tmp_path / "forward"
    reverse_root = tmp_path / "reverse"

    forward = _materialize(
        _accounting(), output_root=forward_root, allowed_output_parent=tmp_path
    )
    reverse = _materialize(
        _accounting(reverse=True),
        output_root=reverse_root,
        allowed_output_parent=tmp_path,
    )

    assert forward.manifest_sha256 == reverse.manifest_sha256
    assert {path.name: path.read_bytes() for path in forward_root.iterdir()} == {
        path.name: path.read_bytes() for path in reverse_root.iterdir()
    }


def test_non_identical_overwrite_is_refused_without_modification(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "classification-audit"
    accounting = _accounting()
    _materialize(accounting, output_root=output_root, allowed_output_parent=tmp_path)
    altered_path = output_root / "release_metadata.json"
    altered_path.write_text("altered\n", encoding="utf-8")

    with pytest.raises(ClassificationAuditRefusalError) as refusal:
        _materialize(
            accounting, output_root=output_root, allowed_output_parent=tmp_path
        )

    assert refusal.value.reason_code == "non_identical_overwrite_refused"
    assert altered_path.read_text(encoding="utf-8") == "altered\n"
    assert not tuple(tmp_path.glob(".classification-audit.staging-*"))
    assert not (tmp_path / ".classification-audit.materialization.lock").exists()


def test_staging_failure_leaves_no_partial_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_root = tmp_path / "classification-audit"

    def refuse_fsync(_descriptor: int) -> None:
        raise OSError("injected classification staging failure")

    monkeypatch.setattr(
        "bijux_pollenomics.evidence.classification.audit_outputs.os.fsync",
        refuse_fsync,
    )
    with pytest.raises(OSError, match="injected classification staging failure"):
        _materialize(
            _accounting(), output_root=output_root, allowed_output_parent=tmp_path
        )

    assert not output_root.exists()
    assert not tuple(tmp_path.glob(".classification-audit.staging-*"))
    assert not (tmp_path / ".classification-audit.materialization.lock").exists()


def test_explicit_unsafe_output_path_is_refused_before_writing(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "classification-audit"
    paths = ClassificationAuditOutputPaths.under(output_root)
    unsafe_paths = replace(paths, review_queue=tmp_path / "escaped-review.json")

    with pytest.raises(ClassificationAuditRefusalError) as refusal:
        _materialize(
            _accounting(),
            output_root=output_root,
            allowed_output_parent=tmp_path,
            paths=unsafe_paths,
        )

    assert refusal.value.reason_code == "unsafe_output_path"
    assert not output_root.exists()
    assert not (tmp_path / "escaped-review.json").exists()


def test_invalid_contract_digest_is_refused_before_writing(tmp_path: Path) -> None:
    output_root = tmp_path / "classification-audit"

    with pytest.raises(ClassificationAuditRefusalError) as refusal:
        materialize_classification_audit(
            _accounting(),
            paths=ClassificationAuditOutputPaths.under(output_root),
            allowed_output_parent=tmp_path,
            classification_contract_version="1.0.0",
            classification_contract_digest="not-a-digest",
            classification_producer_id="bijux-pollenomics.classification-audit",
            classification_producer_version="1",
            classification_producer_digest=f"sha256:{'b' * 64}",
        )

    assert refusal.value.reason_code == "invalid_contract_digest"
    assert not output_root.exists()


def test_tampered_reconciliation_is_refused_before_writing(tmp_path: Path) -> None:
    accounting = copy.deepcopy(_accounting())
    reconciliation = accounting["reconciliation"]
    assert isinstance(reconciliation, dict)
    reconciliation["concept_count"] = 99
    output_root = tmp_path / "classification-audit"

    with pytest.raises(ClassificationAuditRefusalError) as refusal:
        _materialize(
            accounting, output_root=output_root, allowed_output_parent=tmp_path
        )

    assert refusal.value.reason_code == "invalid_accounting_reconciliation"
    assert not output_root.exists()
