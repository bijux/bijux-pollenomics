"""SEAD atlas projection fixtures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)

from .materialization import _write_json, _write_sead_evidence_fixture


def write_sead_projection_fixture(
    root: Path, *, observation_entity_id: str = "sead-analysis-entity:90"
) -> tuple[str, str]:
    run_id = SEAD_GOVERNED_EVIDENCE_RUN_ID
    build_id = "sha256:" + "c" * 64
    acquisition = root / "sead" / "raw" / "acquisitions" / run_id
    countries = (("1", "Sweden"), ("2", "Denmark"), ("3", "Norway"), ("4", "Finland"))
    site_payload = _write_json(
        acquisition / "payloads" / "tbl_sites.json",
        {
            "table": "tbl_sites",
            "rows": [{"site_id": int(site_id)} for site_id, _ in countries],
        },
    )
    manifest_payload = _write_json(
        acquisition / "manifest.json", {"status": "complete"}
    )
    country_codes = {
        "Sweden": "SE",
        "Denmark": "DK",
        "Norway": "NO",
        "Finland": "FI",
    }
    decisions_payload = _write_json(
        acquisition / "country-decisions.json",
        {
            "decisions": [
                {
                    "site_id": int(site_id),
                    "governed_country_code": country_codes[country],
                    "decision": {"decision_status": "assigned"},
                }
                for site_id, country in countries
            ]
        },
    )
    copied = []
    for relative, payload in (
        ("manifest.json", manifest_payload),
        ("country-decisions.json", decisions_payload),
        ("payloads/tbl_sites.json", site_payload),
    ):
        copied.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    acquisition_manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
    country_decisions_sha256 = hashlib.sha256(decisions_payload).hexdigest()
    acquisition_bundle_sha256 = "sha256:" + "d" * 64
    admission_payload = _write_json(
        acquisition / "admission.json",
        {
            "schema_version": "sead-acquisition-admission.v1",
            "source_family": "sead",
            "run_id": run_id,
            "build_id": build_id,
            "acquisition_manifest_sha256": acquisition_manifest_sha256,
            "acquisition_bundle_sha256": acquisition_bundle_sha256,
            "release_status": "refused",
            "copied_files": copied,
        },
    )
    claim = {
        "chronology_claim_id": "sead:site-2:dating_range:9",
        "source_family": "sead",
        "source_site_id": "2",
        "site_uuid": "site-2",
        "country_code": "DK",
        "latitude_dd": 55.0,
        "longitude_dd": 10.0,
        "country_assignment_method": "strict_boundary_containment",
        "source_table": "tbl_analysis_dating_ranges",
        "source_record_id": "9",
        "source_native_record_id": "9",
        "subject_type": "analysis_entity",
        "subject_id": "90",
        "sample_group_id": 20,
        "physical_sample_id": 21,
        "analysis_entity_id": 90,
        "analysis_value_id": 91,
        "dataset_id": 30,
        "claim_type": "dating_range",
        "source_age_type": "AD",
        "source_age_value": {
            "analysis_entity_id": 90,
            "physical_sample_id": 21,
            "sample_group_id": 20,
            "dataset_id": 30,
            "analysis_dating_range_id": 9,
            "analysis_value_id": 91,
            "age_type_id": 1,
            "dating_uncertainty_id": None,
            "age_type": "AD",
            "age_type_description": "Anno Domini",
            "low_value": 1850,
            "high_value": None,
            "low_qualifier": "",
            "high_qualifier": "",
            "low_is_uncertain": False,
            "high_is_uncertain": False,
            "uncertainty_label": "",
            "uncertainty_description": "",
            "time_start_bp": 100,
            "time_end_bp": 100,
        },
        "source_age_unit": "calendar_year",
        "calibration_status": "not_applicable",
        "younger_bp": 100,
        "older_bp": 100,
        "comparability_status": "comparable",
        "chronology_eligibility": "eligible",
        "propagation_eligibility": "refused",
        "propagation_reason_codes": ["source_classification_not_accepted"],
        "publication_role": "chronology_display_only",
        "reason_codes": [],
        "transformation_id": "sead-calendar-year-to-cal-bp-1950-v1",
        "original_interval_orientation": "point",
        "selection_status": "retained_unselected",
        "selection_rule_version": "sead-retain-all-source-chronologies-v1",
        "observation_link_status": "linked_at_analysis_entity",
        "observation_relation_id": "sead-analysis-entity:90",
        "linked_source_native_observation_count": 2,
        "provenance_record_id": "sead-acquisition-manifest:fixture",
        "build_id": build_id,
        "source_relation_path": [
            {"table": "tbl_sites", "key": "site_id", "value": "2"},
            {
                "table": "tbl_sample_groups",
                "key": "sample_group_id",
                "value": 20,
            },
            {
                "table": "tbl_physical_samples",
                "key": "physical_sample_id",
                "value": 21,
            },
            {
                "table": "tbl_analysis_entities",
                "key": "analysis_entity_id",
                "value": 90,
            },
            {"table": "tbl_datasets", "key": "dataset_id", "value": 30},
            {
                "table": "tbl_analysis_values",
                "key": "analysis_value_id",
                "value": 91,
            },
            {
                "table": "tbl_analysis_dating_ranges",
                "key": "analysis_dating_range_id",
                "value": "9",
            },
        ],
        "schema_version": "sead-chronology-claim.v1",
        "source_payload_sha256": "e" * 64,
        "acquisition_manifest_sha256": acquisition_manifest_sha256,
    }
    evidence_manifest_sha256 = _write_sead_evidence_fixture(
        root,
        run_id=run_id,
        build_id=build_id,
        acquisition_manifest_sha256=acquisition_manifest_sha256,
        acquisition_bundle_sha256=acquisition_bundle_sha256,
        country_decisions_sha256=country_decisions_sha256,
        table_payload_sha256=hashlib.sha256(site_payload).hexdigest(),
        parent_admission_sha256=hashlib.sha256(admission_payload).hexdigest(),
        claim=claim,
        observation_entity_id=observation_entity_id,
    )
    features = []
    for site_id, country in countries:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [10, 55]},
                "properties": {
                    "source": "SEAD",
                    "layer_key": "sead-sites",
                    "layer_label": "SEAD sites",
                    "category": "Environmental archaeology",
                    "record_id": site_id,
                    "name": f"Site {site_id}",
                    "country": country,
                    "source_url": f"https://example.test/{site_id}",
                    "popup_rows": [{"label": "Source", "value": "SEAD"}],
                },
            }
        )
    _write_json(
        root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
        {"type": "FeatureCollection", "features": features},
    )
    return evidence_manifest_sha256, hashlib.sha256(admission_payload).hexdigest()


def sead_projection_layers() -> list[dict[str, object]]:
    return [
        {
            "key": "neotoma-pollen",
            "features": [{"evidence_row_id": "10", "country": "Sweden"}],
        },
        {
            "key": "sead-sites",
            "features": [
                {"evidence_row_id": str(index), "country": country}
                for index, country in enumerate(
                    ("Sweden", "Denmark", "Norway", "Finland"), start=1
                )
            ],
        },
        {
            "key": "sweden-archaeology-site-discovery",
            "features": [
                {"evidence_row_id": "1:unresolved:discovery", "country": "Sweden"}
            ],
        },
    ]
