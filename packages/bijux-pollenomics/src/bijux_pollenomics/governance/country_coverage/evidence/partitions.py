"""Country-partition count construction."""

from __future__ import annotations

from collections.abc import Mapping

from ..constants import COUNT_FIELDS, COUNTRIES, CountryCoverageError

EvidenceCounts = dict[str, int | None]
EvidenceMap = dict[tuple[str, str, str], EvidenceCounts]


def _site_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "published_records": value if published else None,
            "sites": value,
        }


def _record_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "accepted_records": value if dimension == "governed_assignment" else None,
            "published_records": value if published else None,
        }


def _empty_counts() -> dict[str, int | None]:
    return dict.fromkeys(COUNT_FIELDS)


def assignment_basis(source: str, dimension: str, *, materialized: bool) -> str | None:
    """Describe the numerical partition actually read by the coverage consumer."""
    if dimension == "source_reported":
        return None
    if dimension == "publication":
        return "product-country-publication-partition.v1"
    if not materialized:
        return "governed-country-assignment-not-materialized.v1"
    if source == "sead":
        return "retained-sead-capture-country-assignment.v1"
    if source == "neotoma":
        return "retained-neotoma-country-reconciliation.v1"
    if source == "boundaries":
        return "declared-public-country-artifact-membership.v1"
    return "materialized-country-field-partition.v1"


def assignment_scope_reasons(
    source: str, dimension: str, *, materialized: bool
) -> list[str]:
    if source == "boundaries":
        return ["counts_are_named_public_country_artifacts_not_admin0_features"]
    if dimension == "source_reported":
        return []
    if source == "sead":
        return ["retained_source_capture_country_assignment_epoch"]
    if materialized and source not in {"hyde", "empd2", "nfi"}:
        return ["materialized_country_partition_no_fresh_spatial_replay"]
    return []
