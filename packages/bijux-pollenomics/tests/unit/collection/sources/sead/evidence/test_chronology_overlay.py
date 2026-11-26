"""Controls for the explicitly requested historical chronology overlay."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
    reconcile_chronology_rows,
)


def row(identifier: str) -> dict[str, Any]:
    return {
        "chronology_claim_id": identifier,
        "source_age_value": {"age": 42, "time_start_bp": 10, "time_end_bp": 20},
        "original_interval_orientation": "younger_to_older",
        "chronology_eligibility": "refused",
        "source_site_id": "1",
    }


def test_overlay_corrects_only_derived_interval_fields() -> None:
    original = row("a")
    original["observation_relation_id"] = "relation"
    corrected = row("a")
    corrected["source_age_value"] = {
        "age": 42,
        "time_start_bp": None,
        "time_end_bp": None,
    }
    corrected["original_interval_orientation"] = "unavailable"
    result = reconcile_chronology_rows(
        [original, row("b")], [corrected, row("b")], expected_count=2
    )
    assert result == [
        {
            "chronology_claim_id": "a",
            "time_start_bp": None,
            "time_end_bp": None,
            "original_interval_orientation": "unavailable",
        }
    ]
    assert original["observation_relation_id"] == "relation"
    assert original["source_age_value"] == {
        "age": 42,
        "time_start_bp": 10,
        "time_end_bp": 20,
    }


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "foreign",
        "literal",
        "eligibility",
        "json_type",
        "boolean_type",
        "missing_bound",
    ],
)
def test_overlay_refuses_noninterval_changes(corruption: str) -> None:
    old = [row("a"), row("b")]
    new = deepcopy(old)
    if corruption == "duplicate":
        new[1]["chronology_claim_id"] = "a"
    elif corruption == "foreign":
        new[1]["chronology_claim_id"] = "c"
    elif corruption == "literal":
        new[0]["source_age_value"]["age"] = 43
    elif corruption == "eligibility":
        new[0]["chronology_eligibility"] = "eligible"
    elif corruption == "json_type":
        new[0]["source_age_value"]["age"] = 42.0
    elif corruption == "boolean_type":
        new[0]["source_age_value"]["age"] = True
        old[0]["source_age_value"]["age"] = 1
    elif corruption == "missing_bound":
        del new[0]["source_age_value"]["time_start_bp"]
    with pytest.raises(ValueError):
        reconcile_chronology_rows(old, new, expected_count=2)


def test_lineage_binding_rejects_changed_authority_or_claim_digest() -> None:
    import hashlib
    import json

    from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.contract import (
        historical_country_membership,
    )
    from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
        validate_chronology_lineage,
    )
    from bijux_pollenomics.evidence.sources.sead import (
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )

    claim_bytes = b'{"claims": []}'
    admission = {
        "run_id": "run",
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
    }
    lineage: dict[str, Any] = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": "run",
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
        "country_membership": historical_country_membership(),
        "normalized_surface_sha256": {
            "normalized/chronology_claims.json": hashlib.sha256(claim_bytes).hexdigest()
        },
        "refresh_input_sha256": {
            "evidence/evidence_materialization_manifest.json": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
            "boundary/normalized/nordic_country_boundaries.geojson": historical_country_membership()[
                "artifact_digest"
            ].removeprefix("sha256:"),
        },
    }
    payload = json.dumps(lineage).encode()
    pin = hashlib.sha256(payload).hexdigest()
    validate_chronology_lineage(payload, claim_bytes, admission, pin)
    with pytest.raises(ValueError, match="lineage"):
        validate_chronology_lineage(payload, b"changed", admission, pin)
    lineage["country_membership"]["authority_id"] = "other"
    payload = json.dumps(lineage).encode()
    with pytest.raises(ValueError, match="lineage"):
        validate_chronology_lineage(
            payload, claim_bytes, admission, hashlib.sha256(payload).hexdigest()
        )


def test_bad_lineage_pin_fails_before_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.acquisition import governed
    from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
        build_historical_chronology_overlay,
    )

    target = tmp_path / "sead/normalized"
    target.mkdir(parents=True)
    (target / "source_lineage.json").write_bytes(b"{}")
    (target / "chronology_claims.json").write_bytes(b"{}")

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("admission should not be consulted")

    monkeypatch.setattr(governed, "validate_governed_sead_admission", forbidden)
    with pytest.raises(ValueError, match="lineage digest"):
        build_historical_chronology_overlay(tmp_path, tmp_path, lineage_sha256="0" * 64)


def test_full_owner_checks_sources_and_claim_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Synthetic owner replay checks the production count and captured lineage."""
    import hashlib
    import json
    from types import SimpleNamespace

    from bijux_pollenomics.collection.sources.sead.acquisition import governed
    from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.contract import (
        historical_country_membership,
    )
    from bijux_pollenomics.collection.sources.sead.evidence import claims
    from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
        build_historical_chronology_overlay,
    )
    from bijux_pollenomics.evidence.sources import sead

    admission = {
        "run_id": sead.SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
    }
    admission_bytes = (
        json.dumps(admission, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()
    monkeypatch.setattr(
        sead,
        "SEAD_GOVERNED_ADMISSION_SHA256",
        hashlib.sha256(admission_bytes).hexdigest(),
    )
    snapshot = SimpleNamespace(
        admission=admission, copied_files={"manifest.json": b"captured"}
    )
    monkeypatch.setattr(
        governed, "validate_governed_sead_admission", lambda *a, **k: snapshot
    )
    original = [row(str(i)) for i in range(25109)]
    corrected = deepcopy(original)
    corrected[0]["source_age_value"]["time_start_bp"] = None
    corrected[0]["source_age_value"]["time_end_bp"] = None
    corrected[0]["original_interval_orientation"] = "unavailable"
    metadata = {
        "source_run_id": admission["run_id"],
        "source_build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "acquisition_bundle_sha256": "bundle",
        "country_decisions_sha256": "decisions",
        "table_payload_sha256": {},
        "claim_count": 25109,
    }
    computed = dict(metadata, claims=corrected)
    retained = dict(metadata, claims=original)
    monkeypatch.setattr(
        claims,
        "build_sead_chronology_claim_bundle_from_snapshot",
        lambda value: computed,
    )
    monkeypatch.setattr(
        sead,
        "read_validated_sead_evidence_documents",
        lambda *a, **k: {"chronology_claims.json": retained},
    )
    payload = json.dumps(computed, sort_keys=True).encode()
    membership = historical_country_membership()
    lineage = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": admission["run_id"],
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
        "country_membership": membership,
        "normalized_surface_sha256": {
            "normalized/chronology_claims.json": hashlib.sha256(payload).hexdigest()
        },
        "refresh_input_sha256": {
            "evidence/evidence_materialization_manifest.json": sead.SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
            "boundary/normalized/nordic_country_boundaries.geojson": membership[
                "artifact_digest"
            ].removeprefix("sha256:"),
        },
    }
    lineage_bytes = json.dumps(lineage).encode()
    normalized = tmp_path / "sead/normalized"
    normalized.mkdir(parents=True)
    (normalized / "source_lineage.json").write_bytes(lineage_bytes)
    (normalized / "chronology_claims.json").write_bytes(payload)
    pin = hashlib.sha256(lineage_bytes).hexdigest()
    result = build_historical_chronology_overlay(tmp_path, tmp_path, lineage_sha256=pin)
    assert result["producer_code_identity"] == "external_execution_receipt_required"
    assert result["claim_count"] == 25109 and result["changed_claim_count"] == 1
    assert result["changes"][0]["chronology_claim_id"] == "0"
    assert (
        result["admission_input_sha256"]["manifest.json"]
        == hashlib.sha256(b"captured").hexdigest()
    )
    (normalized / "chronology_claims.json").write_bytes(payload + b" ")
    with pytest.raises(ValueError, match="lineage input"):
        build_historical_chronology_overlay(tmp_path, tmp_path, lineage_sha256=pin)
