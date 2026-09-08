"""Projection of captured SEAD chronology rows into typed claims."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ......core.text import clean_optional_text
from ...acquisition.fetch import parse_optional_int
from .chronology_policy import sead_claim_age_policy, source_interval_orientation
from .models import SeadChronologyClaim, SeadRelationStep
from .values import parse_optional_float

CHRONOLOGY_CLAIM_SPECS = (
    (
        "dating_range_rows",
        "dating_range",
        "analysis_dating_range_id",
        "tbl_analysis_dating_ranges",
    ),
    (
        "relative_period_rows",
        "relative_period",
        "relative_date_id",
        "tbl_relative_dates",
    ),
    (
        "analysis_entity_age_rows",
        "analysis_entity_age",
        "analysis_entity_age_id",
        "tbl_analysis_entity_ages",
    ),
    ("geochronology_rows", "geochronology", "geochron_id", "tbl_geochronology"),
    ("dendro_date_rows", "dendrochronology", "dendro_date_id", "tbl_dendro_dates"),
)


def normalize_sead_chronology_claims(
    rows: Iterable[dict[str, object]],
    *,
    provenance_record_id: str,
    build_id: str,
) -> list[SeadChronologyClaim]:
    """Build one typed, source-owned claim for every captured SEAD chronology row."""
    if not provenance_record_id.strip():
        raise ValueError("SEAD chronology claims require a provenance record ID")
    if not build_id.strip():
        raise ValueError("SEAD chronology claims require a build ID")

    claims: list[SeadChronologyClaim] = []
    for site_row in rows:
        site_id = clean_optional_text(site_row.get("site_id"))
        site_uuid = clean_optional_text(site_row.get("site_uuid"))
        for row_key, kind, id_key, source_table in CHRONOLOGY_CLAIM_SPECS:
            source_rows = site_row.get(row_key, [])
            if not isinstance(source_rows, list):
                continue
            for row_index, source_row in enumerate(source_rows):
                if not isinstance(source_row, dict):
                    continue
                source_record_id = clean_optional_text(source_row.get(id_key))
                stable_source_record_id = source_record_id or f"missing-{row_index}"
                analysis_entity_id = parse_optional_int(
                    source_row.get("analysis_entity_id")
                )
                subject_type, subject_id = sead_claim_subject(
                    kind,
                    source_row,
                    analysis_entity_id=analysis_entity_id,
                    source_record_id=stable_source_record_id,
                )
                age_policy = sead_claim_age_policy(kind, source_row)
                reason_codes = list(age_policy["reason_codes"])
                if not source_record_id:
                    reason_codes.append("missing_source_record_id")
                if not site_uuid:
                    reason_codes.append("missing_site_uuid")
                chronology_eligibility = "eligible"
                if age_policy["comparability_status"] != "comparable":
                    chronology_eligibility = "refused"
                    reason_codes.append("chronology_not_comparable")
                if analysis_entity_id is None:
                    chronology_eligibility = "refused"
                    reason_codes.append("missing_analysis_entity_lineage")
                if not site_uuid or not source_record_id:
                    chronology_eligibility = "refused"

                claim_site_key = site_uuid or f"site-{site_id or 'missing'}"
                claims.append(
                    {
                        "chronology_claim_id": (
                            f"sead:{claim_site_key}:{kind}:{stable_source_record_id}"
                        ),
                        "source_family": "sead",
                        "source_table": source_table,
                        "source_record_id": stable_source_record_id,
                        "source_native_record_id": source_record_id or None,
                        "site_uuid": site_uuid or None,
                        "source_site_id": site_id or None,
                        "country_code": clean_optional_text(
                            site_row.get("country_code")
                        )
                        or None,
                        "latitude_dd": parse_optional_float(
                            site_row.get("latitude_dd")
                        ),
                        "longitude_dd": parse_optional_float(
                            site_row.get("longitude_dd")
                        ),
                        "country_assignment_method": clean_optional_text(
                            site_row.get("country_assignment_method")
                        )
                        or None,
                        "subject_type": subject_type,
                        "subject_id": subject_id,
                        "sample_group_id": parse_optional_int(
                            source_row.get("sample_group_id")
                        ),
                        "physical_sample_id": parse_optional_int(
                            source_row.get("physical_sample_id")
                        ),
                        "analysis_entity_id": analysis_entity_id,
                        "analysis_value_id": parse_optional_int(
                            source_row.get("analysis_value_id")
                        ),
                        "dataset_id": parse_optional_int(source_row.get("dataset_id")),
                        "claim_type": kind,
                        "source_age_type": age_policy["source_age_type"],
                        "source_age_value": dict(source_row),
                        "source_age_unit": age_policy["source_age_unit"],
                        "calibration_status": age_policy["calibration_status"],
                        "younger_bp": age_policy["younger_bp"],
                        "older_bp": age_policy["older_bp"],
                        "comparability_status": age_policy["comparability_status"],
                        "chronology_eligibility": chronology_eligibility,
                        "propagation_eligibility": "refused",
                        "propagation_reason_codes": [
                            "observation_link_not_materialized"
                        ],
                        "publication_role": (
                            "chronology_display_only"
                            if chronology_eligibility == "eligible"
                            else "review_only"
                        ),
                        "reason_codes": sorted(set(reason_codes)),
                        "transformation_id": age_policy["transformation_id"],
                        "original_interval_orientation": source_interval_orientation(
                            source_row
                        ),
                        "selection_status": "retained_unselected",
                        "selection_rule_version": (
                            "sead-retain-all-source-chronologies-v1"
                        ),
                        "provenance_record_id": provenance_record_id,
                        "build_id": build_id,
                        "source_relation_path": sead_source_relation_path(
                            site_id=site_id,
                            source_table=source_table,
                            source_key=id_key,
                            source_record_id=stable_source_record_id,
                            source_row=source_row,
                        ),
                    }
                )
    return sorted(claims, key=lambda claim: str(claim["chronology_claim_id"]))


def sead_claim_subject(
    kind: str,
    source_row: Mapping[str, object],
    *,
    analysis_entity_id: int | None,
    source_record_id: str,
) -> tuple[str, str]:
    """Choose the closest source subject available for one claim."""
    if analysis_entity_id is not None:
        return ("analysis_entity", str(analysis_entity_id))
    if kind == "dating_range":
        analysis_value_id = parse_optional_int(source_row.get("analysis_value_id"))
        if analysis_value_id is not None:
            return ("analysis_value", str(analysis_value_id))
    return ("source_chronology_record", source_record_id)


def sead_source_relation_path(
    *,
    site_id: str,
    source_table: str,
    source_key: str,
    source_record_id: str,
    source_row: Mapping[str, object],
) -> list[SeadRelationStep]:
    """Build the relational lineage from site through chronology record."""
    path: list[SeadRelationStep] = [
        {"table": "tbl_sites", "key": "site_id", "value": site_id or None},
        {
            "table": "tbl_sample_groups",
            "key": "sample_group_id",
            "value": parse_optional_int(source_row.get("sample_group_id")),
        },
        {
            "table": "tbl_physical_samples",
            "key": "physical_sample_id",
            "value": parse_optional_int(source_row.get("physical_sample_id")),
        },
        {
            "table": "tbl_analysis_entities",
            "key": "analysis_entity_id",
            "value": parse_optional_int(source_row.get("analysis_entity_id")),
        },
        {
            "table": "tbl_datasets",
            "key": "dataset_id",
            "value": parse_optional_int(source_row.get("dataset_id")),
        },
    ]
    analysis_value_id = parse_optional_int(source_row.get("analysis_value_id"))
    if analysis_value_id is not None:
        path.append(
            {
                "table": "tbl_analysis_values",
                "key": "analysis_value_id",
                "value": analysis_value_id,
            }
        )
    path.append({"table": source_table, "key": source_key, "value": source_record_id})
    return path
