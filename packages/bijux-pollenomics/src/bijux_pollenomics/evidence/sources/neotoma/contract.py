"""Neotoma relational materialization identity and reconciliation rules."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import hashlib
import json

MATERIALIZATION_MANIFEST_SCHEMA_VERSION = (
    "neotoma-relational-materialization-manifest.v1"
)
PART_SCHEMA_VERSION = "neotoma-relational-part.v1"
RECONCILIATION_SCHEMA_VERSION = "neotoma-relational-reconciliation.v2"
RELATIONAL_SNAPSHOT_SCHEMA_VERSION = "neotoma-relational-snapshot.v2"
DEFAULT_ROWS_PER_PART = 50_000

SURFACE_ID_FIELDS = {
    "sites": "site_id",
    "collection_units": "collection_unit_id",
    "datasets": "dataset_id",
    "chronologies": "chronology_id",
    "chronology_controls": "chronology_control_id",
    "samples": "sample_id",
    "age_claims": "chronology_claim_id",
    "variables": "variable_id",
    "observations": "observation_id",
    "conflicts": "conflict_id",
    "orphans": "orphan_id",
}
RELATIONAL_TABLE_SURFACES = tuple(SURFACE_ID_FIELDS)[:9]
COUNTRY_CODES = ("SE", "DK", "NO", "FI", "UNASSIGNED")
COUNTRY_SURFACE_COUNT_FIELDS = {
    "sites": "sites",
    "collection_units": "collection_units",
    "datasets": "datasets",
    "chronologies": "chronologies",
    "chronology_controls": "chronology_controls",
    "samples": "samples",
    "age_claims": "age_claim_rows",
    "observations": "observation_rows",
}
COUNTRY_DECISION_STATUSES = ("assigned", "review", "unassigned", "refused")
PROPAGATION_ELIGIBILITY = ("eligible", "blocked")

__all__ = [
    "COUNTRY_CODES",
    "COUNTRY_DECISION_STATUSES",
    "COUNTRY_SURFACE_COUNT_FIELDS",
    "DEFAULT_ROWS_PER_PART",
    "MATERIALIZATION_MANIFEST_SCHEMA_VERSION",
    "PART_SCHEMA_VERSION",
    "PROPAGATION_ELIGIBILITY",
    "RECONCILIATION_SCHEMA_VERSION",
    "RELATIONAL_SNAPSHOT_SCHEMA_VERSION",
    "RELATIONAL_TABLE_SURFACES",
    "SURFACE_ID_FIELDS",
    "accumulate_country_partition",
    "accumulate_site_attribution",
    "canonical_json_bytes",
    "expect_equal",
    "materialization_digest",
    "non_negative_integer",
    "required_text",
    "surface_schema_version",
    "validate_reconciliation_counts",
]


def validate_reconciliation_counts(
    reconciliation: Mapping[str, object],
    surface_row_counts: Mapping[str, int],
    *,
    country_partitions: Mapping[str, Counter[str]],
    site_statuses: Counter[str],
    site_eligibility: Counter[str],
) -> None:
    normalized_counts = reconciliation.get("normalized_row_counts")
    if not isinstance(normalized_counts, Mapping):
        raise ValueError("Reconciliation normalized_row_counts must be an object")
    for surface_name in RELATIONAL_TABLE_SURFACES:
        expected = non_negative_integer(
            normalized_counts.get(surface_name),
            f"reconciliation normalized_row_counts.{surface_name}",
        )
        expect_equal(
            surface_row_counts[surface_name],
            expected,
            f"reconciled {surface_name} row_count",
        )
    for surface_name, reconciliation_field in (
        ("conflicts", "conflict_count"),
        ("orphans", "orphan_count"),
    ):
        expected = non_negative_integer(
            reconciliation.get(reconciliation_field),
            f"reconciliation {reconciliation_field}",
        )
        expect_equal(
            surface_row_counts[surface_name],
            expected,
            f"reconciled {surface_name} row_count",
        )

    country_counts = reconciliation.get("country_counts")
    if not isinstance(country_counts, Mapping) or set(country_counts) != set(
        COUNTRY_CODES
    ):
        raise ValueError(
            "Reconciliation country_counts must contain exactly "
            "SE, DK, NO, FI, and UNASSIGNED"
        )
    for surface_name, reconciliation_field in COUNTRY_SURFACE_COUNT_FIELDS.items():
        partition = country_partitions.get(surface_name)
        if partition is None:
            raise ValueError(f"Missing country partition for surface {surface_name}")
        if sum(partition.values()) != surface_row_counts[surface_name]:
            raise ValueError(f"Country partition does not cover surface {surface_name}")
        for country_code in COUNTRY_CODES:
            country = country_counts.get(country_code)
            if not isinstance(country, Mapping):
                raise ValueError(f"Invalid country_counts bin: {country_code}")
            reconciled_count = non_negative_integer(
                country.get(reconciliation_field),
                f"country_counts.{country_code}.{reconciliation_field}",
            )
            expect_equal(
                partition[country_code],
                reconciled_count,
                f"{surface_name} {country_code} country partition",
            )

    attribution_counts = reconciliation.get("country_attribution_counts")
    if not isinstance(attribution_counts, Mapping):
        raise ValueError("Reconciliation country_attribution_counts must be an object")
    _validate_named_partition(
        attribution_counts.get("decision_statuses"),
        names=COUNTRY_DECISION_STATUSES,
        observed=site_statuses,
        expected_total=surface_row_counts["sites"],
        label="country attribution decision statuses",
    )
    _validate_named_partition(
        attribution_counts.get("propagation_eligibility"),
        names=PROPAGATION_ELIGIBILITY,
        observed=site_eligibility,
        expected_total=surface_row_counts["sites"],
        label="country attribution propagation eligibility",
    )
    _validate_named_partition(
        attribution_counts.get("final_country_codes"),
        names=COUNTRY_CODES,
        observed=country_partitions["sites"],
        expected_total=surface_row_counts["sites"],
        label="country attribution final country codes",
    )


def accumulate_country_partition(
    rows: Iterable[object],
    *,
    surface_name: str,
    partition: Counter[str],
) -> None:
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"Non-object row in surface {surface_name}")
        country_code = row.get("country_code")
        if country_code not in COUNTRY_CODES:
            raise ValueError(
                f"Invalid or missing country_code in surface {surface_name}: "
                f"{country_code!r}"
            )
        partition[str(country_code)] += 1


def accumulate_site_attribution(
    rows: Iterable[object],
    *,
    statuses: Counter[str],
    eligibility: Counter[str],
) -> None:
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("Non-object row in surface sites")
        status = row.get("country_decision_status")
        if status not in COUNTRY_DECISION_STATUSES:
            raise ValueError(f"Invalid country decision status on site: {status!r}")
        statuses[str(status)] += 1
        propagation_eligible = row.get("country_propagation_eligible")
        if not isinstance(propagation_eligible, bool):
            raise ValueError("Site country_propagation_eligible must be boolean")
        eligibility["eligible" if propagation_eligible else "blocked"] += 1


def _validate_named_partition(
    value: object,
    *,
    names: tuple[str, ...],
    observed: Counter[str],
    expected_total: int,
    label: str,
) -> None:
    if not isinstance(value, Mapping) or not set(value).issubset(names):
        raise ValueError(f"Invalid {label}")
    reconciled = {
        name: non_negative_integer(value.get(name, 0), f"{label}.{name}")
        for name in names
    }
    if sum(reconciled.values()) != expected_total:
        raise ValueError(f"{label} do not sum to site rows")
    for name in names:
        expect_equal(observed[name], reconciled[name], f"{label}.{name}")


def surface_schema_version(surface_name: str) -> str:
    return f"neotoma-relational-{surface_name.replace('_', '-')}.v2"


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def materialization_digest(records: list[dict[str, str]]) -> str:
    return hashlib.sha256(
        canonical_json_bytes({"files": sorted(records, key=lambda row: row["path"])})
    ).hexdigest()


def required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def non_negative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"Unexpected {label}: {actual!r}; expected {expected!r}")
