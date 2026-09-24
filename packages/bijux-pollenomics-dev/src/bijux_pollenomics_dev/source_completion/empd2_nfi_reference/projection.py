"""Authenticate and project the 16 outcome-free EMPD2--NFI review leads."""

from __future__ import annotations

import json
import math
import re
from datetime import date
from hashlib import sha256
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.contracts import (
    canonical_json,
    manifest_sha256,
)

_HEX = re.compile(r"[0-9a-f]{64}")
_DOSSIER_KEYS = {
    "schema_version",
    "source_sha256",
    "spatial_report_sha256",
    "selection",
    "source_metadata_columns",
    "source_explicit_collection_date_column",
    "selected_lead_count",
    "samples_with_publication_links",
    "samples_with_collection_note_cues",
    "source_age_uncertainty_counts",
    "source_age_value_kinds",
    "rows",
    "scientific_admission",
    "independent_vegetation_pair_count",
}
_DOSSIER_ROW_KEYS = {
    "spatial_lead",
    "source_metadata_excluding_vegdescription",
    "source_age_uncertainty_lookup",
    "source_publications",
    "publication_link_count",
    "collection_time_source_note",
    "collection_time_status",
    "independent_vegetation_pair_admission",
}
_METADATA_KEYS = {
    "samplename",
    "originalsamplename",
    "sitename",
    "country",
    "longitude",
    "latitude",
    "locationreliability",
    "locationnotes",
    "areaofsite",
    "samplecontext",
    "sampletype",
    "samplemethod",
    "agebp",
    "ageuncertainty",
    "notes",
    "empd_version",
}
_LEAD_KEYS = {
    "pollen_sample",
    "pollen_agebp_source_native",
    "pollen_ageuncertainty_source_native",
    "pollen_review_reason_codes",
    "mechanical_count_candidate",
    "nfi_tract",
    "nfi_plot",
    "nfi_year",
    "nfi_inventory_date_source_native",
    "distance_m_wgs84",
    "nearest_row_selection",
    "time_support",
    "pair_admission",
}
_SPATIAL_KEYS = {
    "schema_version",
    "evidence_role",
    "source_hashes",
    "nfi_plot_year_rows",
    "nfi_distinct_plots",
    "swedish_pollen_samples",
    "pollen_invalid_coordinate_count",
    "thresholds_descriptive_only",
    "thresholds_mechanical_count_candidates_only",
    "nearest_nfi_row_by_pollen_sample",
    "nfi_source_crs",
    "distance_method",
    "worksheet_access",
    "collection_time_comparability",
    "independent_vegetation_pair_count",
    "scientific_admission",
}
_SOURCE_HASH_KEYS = {
    "nfi_workbook",
    "nfi_schema",
    "nfi_eligibility",
    "empd2_screen",
    "empd2_source",
}
_THRESHOLD_KEYS = {
    "candidate_plot_year_sample_pairs",
    "nfi_plot_years",
    "nfi_plots",
    "pollen_samples",
}


def digest_bytes(content: bytes) -> str:
    """Identify exact source bytes."""
    return sha256(content).hexdigest()


def digest(value: object) -> str:
    """Identify canonical JSON content."""
    return manifest_sha256(value)


def sha_identity(value: object, field: str) -> str:
    """Require one lowercase SHA-256 identity."""
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 identity")
    return value


def identity(value: object, field: str) -> str:
    """Require an exact nonblank identity without normalization."""
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be an exact nonempty identity")
    return value


def identities(value: object, field: str, *, nonempty: bool = True) -> list[str]:
    """Require sorted, unique identity arrays."""
    if not isinstance(value, list):
        raise TypeError(f"{field} must be an identity array")
    result = [identity(item, field) for item in value]
    if (
        (nonempty and not result)
        or result != sorted(result)
        or len(result) != len(set(result))
    ):
        raise ValueError(f"{field} must contain canonical unique identities")
    return result


def finite_number(value: object, field: str) -> float:
    """Require a finite non-boolean number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def iso_date(value: object, field: str) -> str:
    """Require a canonical ISO calendar date."""
    text = identity(value, field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO calendar date") from exc
    if parsed.isoformat() != text:
        raise ValueError(f"{field} must use canonical ISO form")
    return text


def _json_object(content: bytes, field: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"{field} contains a duplicate JSON key")
            result[key] = item
        return result

    try:
        value = json.loads(content, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field} is not a JSON object") from exc
    if not isinstance(value, dict):
        raise TypeError(f"{field} is not a JSON object")
    return cast(dict[str, Any], value)


def _exact_source_schemas(dossier: dict[str, Any], spatial: dict[str, Any]) -> None:
    rows = dossier.get("rows")
    leads = spatial.get("nearest_nfi_row_by_pollen_sample")
    source_hashes = spatial.get("source_hashes")
    thresholds = (
        spatial.get("thresholds_descriptive_only"),
        spatial.get("thresholds_mechanical_count_candidates_only"),
    )
    if (
        set(dossier) != _DOSSIER_KEYS
        or set(spatial) != _SPATIAL_KEYS
        or not isinstance(rows, list)
        or not isinstance(leads, list)
        or not isinstance(source_hashes, dict)
        or set(source_hashes) != _SOURCE_HASH_KEYS
        or any(not isinstance(value, dict) for value in thresholds)
    ):
        raise ValueError("source reports differ from their exact governed schemas")
    for threshold_map in cast(tuple[dict[str, Any], dict[str, Any]], thresholds):
        if set(threshold_map) != {"1000", "5000", "10000"} or any(
            not isinstance(value, dict) or set(value) != _THRESHOLD_KEYS
            for value in threshold_map.values()
        ):
            raise ValueError("spatial thresholds differ from the exact schema")
    for lead in leads:
        if not isinstance(lead, dict) or set(lead) != _LEAD_KEYS:
            raise ValueError("spatial lead fields differ from the exact schema")
    for row in rows:
        if not isinstance(row, dict) or set(row) != _DOSSIER_ROW_KEYS:
            raise ValueError("dossier row fields differ from the exact schema")
        metadata = row.get("source_metadata_excluding_vegdescription")
        age_lookup = row.get("source_age_uncertainty_lookup")
        publications = row.get("source_publications")
        if (
            not isinstance(metadata, dict)
            or set(metadata) != _METADATA_KEYS
            or (
                age_lookup is not None
                and (
                    not isinstance(age_lookup, dict)
                    or set(age_lookup)
                    != {"source_age_range_label", "source_description"}
                )
            )
            or not isinstance(publications, list)
            or any(
                not isinstance(item, dict)
                or set(item) != {"publiid", "doi", "reference"}
                for item in publications
            )
            or not isinstance(row.get("spatial_lead"), dict)
            or set(row["spatial_lead"]) != _LEAD_KEYS
        ):
            raise ValueError("dossier nested fields differ from the exact schema")


def _pinned_inputs(
    dossier_bytes: bytes,
    dossier_sha256: str,
    spatial_bytes: bytes,
    spatial_sha256: str,
    guide_bytes: bytes,
    guide_sha256: str,
    workbook_sha256: str,
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    expected = {
        "dossier": sha_identity(dossier_sha256, "dossier_sha256"),
        "spatial": sha_identity(spatial_sha256, "spatial_sha256"),
        "guide": sha_identity(guide_sha256, "guide_sha256"),
        "workbook": sha_identity(workbook_sha256, "workbook_sha256"),
    }
    for name, content in (
        ("dossier", dossier_bytes),
        ("spatial", spatial_bytes),
        ("guide", guide_bytes),
    ):
        if digest_bytes(content) != expected[name]:
            raise ValueError(f"{name} bytes differ from their pinned identity")
    if not guide_bytes.startswith(b"%PDF-"):
        raise ValueError("guide bytes are not a PDF")
    dossier = _json_object(dossier_bytes, "dossier")
    spatial = _json_object(spatial_bytes, "spatial report")
    _exact_source_schemas(dossier, spatial)
    return expected, dossier, spatial


def _source_rows(
    dossier: dict[str, Any], spatial: dict[str, Any], expected: dict[str, str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_hashes = spatial.get("source_hashes")
    rows = dossier.get("rows")
    spatial_rows = spatial.get("nearest_nfi_row_by_pollen_sample")
    if (
        dossier.get("schema_version") != "empd2-nfi-source-dossier.v1"
        or dossier.get("spatial_report_sha256") != expected["spatial"]
        or dossier.get("scientific_admission") != "candidate_only"
        or dossier.get("independent_vegetation_pair_count") != 0
        or dossier.get("selected_lead_count") != 16
        or not isinstance(rows, list)
        or any(not isinstance(row, dict) for row in rows)
        or spatial.get("schema_version") != "empd2-nfi-spatial-feasibility.v2"
        or spatial.get("scientific_admission") != "candidate_only"
        or spatial.get("independent_vegetation_pair_count") != 0
        or spatial.get("worksheet_access")
        != "entire XML streamed; only first six identity/geometry cells selected, no tree measurements displayed or scored"
        or not isinstance(source_hashes, dict)
        or source_hashes.get("nfi_workbook") != expected["workbook"]
        or source_hashes.get("empd2_source") != dossier.get("source_sha256")
        or not isinstance(spatial_rows, list)
    ):
        raise ValueError(
            "source reports have an unsupported identity or claim boundary"
        )
    selected_rows = [
        row
        for row in spatial_rows
        if isinstance(row, dict)
        and isinstance(row.get("distance_m_wgs84"), (int, float))
        and not isinstance(row.get("distance_m_wgs84"), bool)
        and row["distance_m_wgs84"] <= 1000
    ]
    selected = {row.get("pollen_sample"): row for row in selected_rows}
    if len(selected_rows) != 16 or len(selected) != 16 or None in selected:
        raise ValueError("spatial report does not close the 16-lead denominator")
    return cast(dict[str, Any], source_hashes), cast(list[dict[str, Any]], rows)


def _candidate_rows(
    rows: list[dict[str, Any]], selected: dict[object, dict[str, Any]]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rows:
        lead = item.get("spatial_lead")
        metadata = item.get("source_metadata_excluding_vegdescription")
        if not isinstance(lead, dict) or not isinstance(metadata, dict):
            raise TypeError("dossier row lacks source lead metadata")
        lead = cast(dict[str, Any], lead)
        metadata = cast(dict[str, Any], metadata)
        sample = identity(lead.get("pollen_sample"), "pollen_sample")
        if (
            sample in seen
            or selected.get(sample) != lead
            or metadata.get("samplename") != sample
            or lead.get("pair_admission") != "candidate_only"
            or lead.get("mechanical_count_candidate") is not True
            or item.get("independent_vegetation_pair_admission") is not False
            or lead.get("time_support") != "unresolved_collection_time"
        ):
            raise ValueError("dossier and spatial lead identities differ")
        seen.add(sample)
        tract = identity(lead.get("nfi_tract"), "nfi_tract")
        plot = identity(lead.get("nfi_plot"), "nfi_plot")
        year = identity(lead.get("nfi_year"), "nfi_year")
        source_country = identity(metadata.get("country"), "source country")
        if source_country != "Sweden":
            raise ValueError("EMPD2--NFI reference country is not supported")
        distance = finite_number(lead.get("distance_m_wgs84"), "distance_m_wgs84")
        if not 0 <= distance <= 1000 or not year.isdigit():
            raise ValueError("candidate distance or NFI year is invalid")
        candidates.append(
            {
                "record_id": f"empd2-nfi:{sample}:nfi-{tract}-{plot}-{year}",
                "source_row_sha256": digest(item),
                "pollen_sample": sample,
                "pollen_latitude": finite_number(metadata.get("latitude"), "latitude"),
                "pollen_longitude": finite_number(
                    metadata.get("longitude"), "longitude"
                ),
                "nfi_tract": tract,
                "nfi_plot": plot,
                "nfi_year": year,
                "source_country": source_country,
                "country_code": "SE",
                "nfi_inventory_date_source_native": identity(
                    lead.get("nfi_inventory_date_source_native"),
                    "nfi_inventory_date_source_native",
                ),
                "mechanical_count_candidate": True,
                "distance_m_wgs84": distance,
                "collection_time_status": item.get("collection_time_status"),
                "cross_source_identity_status": (
                    "unresolved"
                    if "cross_source_identity_unresolved"
                    in lead.get("pollen_review_reason_codes", [])
                    else "not_established"
                ),
                "decision_status": "awaiting_qualified_return",
            }
        )
    candidates.sort(key=lambda row: row["record_id"])
    if seen != set(cast(dict[str, Any], selected)) or len(candidates) != 16:
        raise ValueError("dossier does not close the 16-lead denominator")
    return candidates


def build_empd2_nfi_decision_projection(
    *,
    dossier_bytes: bytes,
    dossier_sha256: str,
    spatial_bytes: bytes,
    spatial_sha256: str,
    guide_bytes: bytes,
    guide_sha256: str,
    workbook_sha256: str,
) -> dict[str, Any]:
    """Build a source-bound review projection without accepting any pair."""
    expected, dossier, spatial = _pinned_inputs(
        dossier_bytes,
        dossier_sha256,
        spatial_bytes,
        spatial_sha256,
        guide_bytes,
        guide_sha256,
        workbook_sha256,
    )
    source_hashes, rows = _source_rows(dossier, spatial, expected)
    spatial_rows = cast(
        list[dict[str, Any]], spatial["nearest_nfi_row_by_pollen_sample"]
    )
    selected = {
        row["pollen_sample"]: row
        for row in spatial_rows
        if finite_number(row["distance_m_wgs84"], "distance_m_wgs84") <= 1000
    }
    candidates = _candidate_rows(rows, selected)
    source_identities = {
        "dossier": expected["dossier"],
        "spatial": expected["spatial"],
        "guide": expected["guide"],
        "nfi_workbook": expected["workbook"],
        "empd2_source": sha_identity(dossier["source_sha256"], "empd2 source"),
        "empd2_screen": sha_identity(source_hashes.get("empd2_screen"), "EMPD2 screen"),
        "nfi_eligibility": sha_identity(
            source_hashes.get("nfi_eligibility"), "NFI eligibility"
        ),
        "nfi_schema": sha_identity(source_hashes.get("nfi_schema"), "NFI schema"),
    }
    source_manifest = digest(
        {"source_identities": source_identities, "candidate_rows": candidates}
    )
    payload: dict[str, Any] = {
        "schema_version": "empd2-nfi-reference-decision-projection.v1",
        "reviewer_authority": "declared_not_authenticated",
        "outcome_access_status": "not_started",
        "source_identities": source_identities,
        "candidate_source_manifest_sha256": source_manifest,
        "candidate_count": 16,
        "candidate_rows": candidates,
        "decision_status": "awaiting_qualified_return",
        "admitted_pair_count": 0,
        "awaiting_review_count": 16,
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
        "publication_allowed": False,
    }
    payload["projection_sha256"] = digest(payload)
    return cast(dict[str, Any], json.loads(canonical_json(payload)))
