"""Committed-output tests for the two publishable Danish pig samples."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.adna.projects.registry.sample_truth import (
    build_project_locality_count_drift,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts

SPECIES_ROOT = DATA_ROOT / "adna" / "species" / "sus_scrofa_domesticus"


def _read_json(relative_path: str) -> dict[str, object]:
    value = json.loads((SPECIES_ROOT / relative_path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_committed_sample_export_maps_only_the_two_supported_samples() -> None:
    payload = _read_json("normalized/sample_records.json")
    samples = payload["samples"]
    assert isinstance(samples, list)
    mapped = {
        str(sample["archive_native_sample_id"]): sample
        for sample in samples
        if isinstance(sample, dict)
        and isinstance(sample.get("coordinates"), dict)
        and (
            sample["coordinates"].get("latitude_text")
            or sample["coordinates"].get("longitude_text")
        )
    }

    assert payload["admitted_sample_count"] == 343
    assert payload["refused_sample_count"] == 3
    assert set(mapped) == {"SAMEA5160867", "SAMEA5160868"}
    assert mapped["SAMEA5160867"]["coordinates"] == {
        "latitude": 55.02158609,
        "longitude": 9.77344984,
        "latitude_text": "55.02158609",
        "longitude_text": "9.77344984",
        "confidence": "approximate",
    }
    assert mapped["SAMEA5160868"]["coordinates"] == {
        "latitude": 55.39416667,
        "longitude": 11.26527778,
        "latitude_text": "55.39416667",
        "longitude_text": "11.26527778",
        "confidence": "approximate",
    }


def test_committed_coordinate_export_retains_non_findspot_provenance() -> None:
    payload = _read_json("normalized/coordinate_provenance.json")
    records = payload["coordinate_provenance"]
    assert isinstance(records, list)
    by_site = {
        str(record["site_label"]): record
        for record in records
        if isinstance(record, dict)
    }

    assert set(by_site) == {"Bundsø", "Trelleborg"}
    assert all(
        row["coordinate_confidence"] == "approximate" for row in by_site.values()
    )
    assert all(
        row["coordinate_basis"] == "named_site_geocoding" for row in by_site.values()
    )
    assert all(
        "not a specimen findspot" in str(row["interpretation_note"])
        for row in by_site.values()
    )
    assert {
        site: (row["time_start_bp"], row["time_end_bp"], row["dating_basis"])
        for site, row in by_site.items()
    } == {
        "Bundsø": (4700, 4700, "archaeological_context"),
        "Trelleborg": (1000, 1000, "archaeological_context"),
    }

    site_payload = _read_json("normalized/site_evidence.json")
    site_records = site_payload["site_evidence"]
    assert isinstance(site_records, list)
    direct_sites = {
        str(record["site_label"]): record
        for record in site_records
        if isinstance(record, dict)
        and record.get("site_label") in {"Bundsø", "Trelleborg"}
    }
    assert {
        site: (row["time_start_bp"], row["time_end_bp"], row["dating_basis"])
        for site, row in direct_sites.items()
    } == {
        "Bundsø": (4700, 4700, "archaeological_context"),
        "Trelleborg": (1000, 1000, "archaeological_context"),
    }


def test_archive_denominator_reconciles_to_two_sample_backed_sites() -> None:
    payload = _read_json("normalized/sample_records.json")
    samples = payload["samples"]
    assert isinstance(samples, list)
    archive_only = [
        sample
        for sample in samples
        if isinstance(sample, dict)
        and sample.get("inclusion_status") == "archive_identity_only"
    ]
    supported = {
        str(sample["archive_native_sample_id"]): sample
        for sample in samples
        if isinstance(sample, dict)
        and sample.get("paper_native_sample_label") in {"AA015", "AA016"}
    }

    assert len(archive_only) == 341
    assert set(supported) == {"SAMEA5160867", "SAMEA5160868"}
    assert {accession: row["chronology"] for accession, row in supported.items()} == {
        "SAMEA5160867": {
            "original_text": "4700 BP",
            "time_start_bp": 4700,
            "time_end_bp": 4700,
            "time_mean_bp": 4700,
            "date_stddev_bp": "",
            "source_mean_bp_text": "",
            "dating_basis": "archaeological_context",
            "evidence_class": "archaeological_context_date",
            "precision_posture": "sample_approximate_or_modeled",
            "refusal_reason_code": "",
        },
        "SAMEA5160868": {
            "original_text": "1000 BP",
            "time_start_bp": 1000,
            "time_end_bp": 1000,
            "time_mean_bp": 1000,
            "date_stddev_bp": "",
            "source_mean_bp_text": "",
            "dating_basis": "archaeological_context",
            "evidence_class": "archaeological_context_date",
            "precision_posture": "sample_approximate_or_modeled",
            "refusal_reason_code": "",
        },
    }
    assert not any(
        row["project_accession"] == "PRJEB30282"
        for row in build_project_locality_count_drift(DATA_ROOT)
    )
