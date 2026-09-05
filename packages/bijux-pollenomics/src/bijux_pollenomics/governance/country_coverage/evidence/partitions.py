"""Country-partition count construction."""

from __future__ import annotations

from collections.abc import Mapping

from ..constants import COUNTRIES, COUNT_FIELDS, CountryCoverageError

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
