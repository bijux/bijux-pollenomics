"""Validate and project Nordic national-forest-inventory coverage evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ...constants import (
    COUNTRIES,
    NFI_COVERAGE_EVIDENCE_PATH,
    NFI_SOURCE_ARTIFACT_SHA256,
    CountryCoverageError,
)
from ...decoding import _integer, _required_text, _text_list
from ..partitions import EvidenceMap, _empty_counts

_DOCUMENT_KEYS = {
    "countries",
    "evidence_paths",
    "review_status",
    "reviewed_record_count",
    "schema_version",
    "scientifically_admitted_record_count",
    "source_key",
}
_COUNTRY_KEYS = {
    "candidate_record_count",
    "country_code",
    "reason_codes",
    "scientifically_admitted_record_count",
    "source_artifact_sha256",
    "source_reported_observation_count",
    "source_reported_record_count",
    "source_reported_site_count",
    "source_status",
    "unresolved_record_count",
}
_EVIDENCE_KEYS = {"path", "sha256"}
_COUNTRY_SHA = {
    "SE": "a0632bbff92e79c490a6bceb4fa21d69133d7fee7221c93e5b340de6c0b0b375",
    "DK": "ab0a563eafe4755414b44d43b0262322a645983996c873777ff830fb937b9f5f",
    "NO": "3ae1e97f5dec256f2a324832131b40063b4f5a8769c538366a329fffca425ec0",
    "FI": "f789c22acaa5c5ca4a3095479c6084bb87ceadbf7f1372305955a12ee1f2a1d1",
}
_EXPECTED_POSTURE = {
    "SE": (
        "source_reported_candidate",
        (
            "candidate_point_plot_geometry_only",
            "regional_area_cover_truth_not_admitted",
            "scientific_admission_not_established",
        ),
    ),
    "DK": (
        "nonpublic_agreement_required",
        ("individual_plot_data_nonpublic", "research_agreement_required"),
    ),
    "NO": (
        "plot_data_unavailable",
        ("plot_download_license_and_site_data_unavailable",),
    ),
    "FI": (
        "access_review_required",
        (
            "authoritative_release_access_review_required",
            "scientific_admission_not_established",
        ),
    ),
    "UNASSIGNED": ("not_applicable", ("partition_not_applicable",)),
    "OUTSIDE": ("not_applicable", ("partition_not_applicable",)),
}


def _nullable_count(value: object, label: str) -> int | None:
    return None if value is None else _integer(value, label)


def _validated_rows(document: Mapping[str, object]) -> list[dict[str, object]]:
    if (
        set(document) != _DOCUMENT_KEYS
        or document.get("schema_version") != "source-country-coverage-evidence.v1"
        or document.get("source_key") != "nfi"
        or document.get("review_status") != "candidate_only"
        or _integer(document.get("reviewed_record_count"), "NFI reviewed records")
        != 43_892
        or _integer(
            document.get("scientifically_admitted_record_count"), "NFI admissions"
        )
        != 0
    ):
        raise CountryCoverageError("NFI coverage evidence identity changed")
    raw_rows = document.get("countries")
    if not isinstance(raw_rows, list) or any(
        not isinstance(row, dict) for row in raw_rows
    ):
        raise CountryCoverageError("NFI countries must be an object array")
    rows = cast(list[dict[str, object]], raw_rows)
    if [row.get("country_code") for row in rows] != list(COUNTRIES):
        raise CountryCoverageError("NFI country inventory or order changed")
    for row in rows:
        if set(row) != _COUNTRY_KEYS:
            raise CountryCoverageError("NFI country fields changed")
        country = _required_text(row, "country_code")
        reasons = _text_list(row.get("reason_codes"), "NFI country reasons")
        if (row.get("source_status"), tuple(reasons)) != _EXPECTED_POSTURE[country]:
            raise CountryCoverageError(f"NFI {country} posture changed")
        for field in (
            "source_reported_record_count",
            "source_reported_site_count",
            "source_reported_observation_count",
            "candidate_record_count",
            "unresolved_record_count",
            "scientifically_admitted_record_count",
        ):
            _nullable_count(row.get(field), f"NFI {country} {field}")
        if (
            country in _COUNTRY_SHA
            and row.get("source_artifact_sha256") != _COUNTRY_SHA[country]
        ):
            raise CountryCoverageError(f"NFI {country} source identity changed")
        if (
            country not in _COUNTRY_SHA
            and row.get("source_artifact_sha256") is not None
        ):
            raise CountryCoverageError("NFI noncountry source identity must be null")
    sweden = rows[0]
    if (
        sweden.get("source_status") != "source_reported_candidate"
        or sweden.get("source_reported_record_count") != 43_892
        or sweden.get("source_reported_site_count") != 6_018
        or sweden.get("source_reported_observation_count") is not None
        or sweden.get("candidate_record_count") != 16
        or sweden.get("unresolved_record_count") != 16
        or sweden.get("scientifically_admitted_record_count") != 0
    ):
        raise CountryCoverageError("Swedish NFI candidate counts changed")
    for row in rows[1:]:
        country = cast(str, row["country_code"])
        if any(
            row.get(field) is not None
            for field in (
                "source_reported_record_count",
                "source_reported_site_count",
                "source_reported_observation_count",
                "candidate_record_count",
                "unresolved_record_count",
            )
        ):
            raise CountryCoverageError("non-Swedish NFI counts must remain null")
        expected_admissions = 0 if country in _COUNTRY_SHA else None
        if row.get("scientifically_admitted_record_count") != expected_admissions:
            raise CountryCoverageError(
                f"NFI {country} scientific admission denominator changed"
            )
    _validate_paths(document.get("evidence_paths"))
    return rows


def _validate_paths(value: object) -> None:
    expected = [
        (
            "reference-sources/empd2-nfi/nfi/nordic-access.json",
            "b0ab87f8016b561d84cdff16e74500df1b2f1e4013f4600a3d7e0ec0942d6825",
        ),
        (
            "reference-sources/empd2-nfi/nfi/swedish-eligibility.json",
            "a38cba2995ec1c71f7276a4798f2ea79778f4cbbbb587bc507f902b71abc33fd",
        ),
        (
            "reference-sources/empd2-nfi/pairing/spatial-feasibility.json",
            "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
        ),
        (
            "reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx",
            NFI_SOURCE_ARTIFACT_SHA256,
        ),
    ]
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise CountryCoverageError("NFI evidence paths must be an object array")
    observed = []
    for row in cast(list[dict[str, object]], value):
        if set(row) != _EVIDENCE_KEYS:
            raise CountryCoverageError("NFI evidence path fields changed")
        observed.append((_required_text(row, "path"), _required_text(row, "sha256")))
    if observed != expected:
        raise CountryCoverageError("NFI evidence path identities changed")


def add_nfi_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    """Add Swedish source counts without treating point plots as area cover."""
    sweden = _validated_rows(documents[NFI_COVERAGE_EVIDENCE_PATH])[0]
    evidence[("nfi", "source_reported", "SE")] = {
        **_empty_counts(),
        "received_records": cast(int, sweden["source_reported_record_count"]),
        "unresolved_records": cast(int, sweden["unresolved_record_count"]),
        "sites": cast(int, sweden["source_reported_site_count"]),
        "possible_candidates": cast(int, sweden["candidate_record_count"]),
    }


def nfi_cell_posture(
    *, dimension: str, country_code: str
) -> tuple[str, str, list[str]]:
    """Return the source-access or non-admission posture for one NFI cell."""
    if dimension != "source_reported":
        if country_code in {"UNASSIGNED", "OUTSIDE"}:
            return "not_applicable", "not_required", ["partition_not_applicable"]
        return "blocked", "refused", [f"{dimension}_partition_not_materialized"]
    states = {
        "SE": ("available_partial", "review_required"),
        "FI": ("available_not_collected", "review_required"),
        "NO": ("not_available_from_source", "unavailable"),
        "DK": ("blocked", "refused"),
    }
    if country_code not in states:
        return "not_applicable", "not_required", ["partition_not_applicable"]
    availability, lifecycle = states[country_code]
    return availability, lifecycle, list(_EXPECTED_POSTURE[country_code][1])
