"""Validate and project source-reported EMPD2 coverage evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ...constants import (
    COUNTRIES,
    EMPD2_COVERAGE_EVIDENCE_PATH,
    EMPD2_SOURCE_ARTIFACT_SHA256,
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
_SOURCE_SHA = EMPD2_SOURCE_ARTIFACT_SHA256
_SCREEN_SHA = "6ca256d6e74d6129ee058bea36e8d28c1199bb276d68c0548e0b998853773aaa"
_EXPECTED = {
    "SE": (132, 3379, 131, 21),
    "DK": (20, 968, 20, 0),
    "NO": (622, 19774, 622, 66),
    "FI": (141, 3040, 141, 25),
}
_EXPECTED_POSTURE = {
    "SE": (
        "source_reported_candidate",
        [
            "candidate_screen_only",
            "cross_source_identity_unresolved",
            "scientific_admission_not_established",
        ],
    ),
    "DK": (
        "source_reported_candidate",
        ["candidate_screen_only", "scientific_admission_not_established"],
    ),
    "NO": (
        "source_reported_candidate",
        [
            "candidate_screen_only",
            "cross_source_identity_unresolved",
            "scientific_admission_not_established",
        ],
    ),
    "FI": (
        "source_reported_candidate",
        [
            "candidate_screen_only",
            "cross_source_identity_unresolved",
            "scientific_admission_not_established",
        ],
    ),
    "UNASSIGNED": ("not_materialized", ["source_partition_not_materialized"]),
    "OUTSIDE": ("not_materialized", ["source_partition_not_materialized"]),
}


def _nullable_count(value: object, label: str) -> int | None:
    return None if value is None else _integer(value, label)


def _validated_rows(document: Mapping[str, object]) -> list[dict[str, object]]:
    if (
        set(document) != _DOCUMENT_KEYS
        or document.get("schema_version") != "source-country-coverage-evidence.v1"
        or document.get("source_key") != "empd2"
        or document.get("review_status") != "candidate_only"
        or _integer(document.get("reviewed_record_count"), "EMPD2 reviewed records")
        != 915
        or _integer(
            document.get("scientifically_admitted_record_count"),
            "EMPD2 scientific admissions",
        )
        != 0
    ):
        raise CountryCoverageError("EMPD2 coverage evidence identity changed")
    raw_rows = document.get("countries")
    if not isinstance(raw_rows, list) or any(
        not isinstance(row, dict) for row in raw_rows
    ):
        raise CountryCoverageError("EMPD2 countries must be an object array")
    rows = cast(list[dict[str, object]], raw_rows)
    if [row.get("country_code") for row in rows] != list(COUNTRIES):
        raise CountryCoverageError("EMPD2 country inventory or order changed")
    for row in rows:
        if set(row) != _COUNTRY_KEYS:
            raise CountryCoverageError("EMPD2 country fields changed")
        country = _required_text(row, "country_code")
        reasons = _text_list(row.get("reason_codes"), "EMPD2 country reasons")
        if (row.get("source_status"), reasons) != _EXPECTED_POSTURE[country]:
            raise CountryCoverageError(f"EMPD2 {country} posture changed")
        values = tuple(
            _nullable_count(row.get(field), f"EMPD2 {country} {field}")
            for field in (
                "source_reported_record_count",
                "source_reported_observation_count",
                "candidate_record_count",
                "unresolved_record_count",
            )
        )
        if country in _EXPECTED:
            if (
                values != _EXPECTED[country]
                or row.get("source_reported_site_count") is not None
                or row.get("source_artifact_sha256") != _SOURCE_SHA
                or _nullable_count(
                    row.get("scientifically_admitted_record_count"),
                    f"EMPD2 {country} scientific admissions",
                )
                != 0
            ):
                raise CountryCoverageError(f"EMPD2 {country} evidence changed")
        elif any(value is not None for value in values) or any(
            row.get(field) is not None
            for field in (
                "source_reported_site_count",
                "scientifically_admitted_record_count",
                "source_artifact_sha256",
            )
        ):
            raise CountryCoverageError("EMPD2 unmaterialized counts must remain null")
    _validate_paths(document.get("evidence_paths"))
    return rows


def _validate_paths(value: object) -> None:
    expected = [
        ("reference-sources/empd2-nfi/empd2/source.sqlite3", _SOURCE_SHA),
        ("reference-sources/empd2-nfi/empd2/product-screen.json", _SCREEN_SHA),
    ]
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise CountryCoverageError("EMPD2 evidence paths must be an object array")
    observed = []
    for row in cast(list[dict[str, object]], value):
        if set(row) != _EVIDENCE_KEYS:
            raise CountryCoverageError("EMPD2 evidence path fields changed")
        observed.append((_required_text(row, "path"), _required_text(row, "sha256")))
    if observed != expected:
        raise CountryCoverageError("EMPD2 evidence path identities changed")


def add_empd2_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    """Add only source-native named-country counts; no assignment is inferred."""
    for row in _validated_rows(documents[EMPD2_COVERAGE_EVIDENCE_PATH]):
        country = cast(str, row["country_code"])
        if country not in _EXPECTED:
            continue
        evidence[("empd2", "source_reported", country)] = {
            **_empty_counts(),
            "received_records": cast(int, row["source_reported_record_count"]),
            "unresolved_records": cast(int, row["unresolved_record_count"]),
            "samples": cast(int, row["source_reported_record_count"]),
            "observations": cast(int, row["source_reported_observation_count"]),
            "possible_candidates": cast(int, row["candidate_record_count"]),
        }


def empd2_cell_posture(
    counts: Mapping[str, int | None], *, dimension: str, country_code: str
) -> tuple[str, str, list[str]]:
    """Return the non-admission posture for one EMPD2 ledger cell."""
    if dimension == "source_reported" and country_code in _EXPECTED:
        reasons = ["candidate_screen_only", "scientific_admission_not_established"]
        if counts["unresolved_records"]:
            reasons.append("cross_source_identity_unresolved")
        return "available_partial", "review_required", reasons
    if dimension == "source_reported":
        return "blocked", "unavailable", ["source_partition_not_materialized"]
    if dimension == "governed_assignment":
        return "blocked", "refused", ["governed_country_assignment_not_materialized"]
    return "blocked", "refused", ["publication_not_materialized"]
