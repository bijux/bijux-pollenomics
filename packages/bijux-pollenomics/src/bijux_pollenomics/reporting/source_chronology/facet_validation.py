"""Fail-closed validation for source-chronology facet accountability."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Final

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)

from .source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)
from .time_density import time_density_matches_facet

FACET_SCHEMA_VERSION: Final = "neotoma-source-chronology-facets.v4"
PRESET_ACCOUNTABILITY_SCHEMA_VERSION: Final = (
    "neotoma-source-label-preset-accountability.v1"
)
SITE_COUNT_SEMANTICS: Final = "unique_site_union"

COUNTRY_NAMES: Final = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
_NODE_LEVELS: Final = (
    "source_sample_presence",
    "source_ecological_code",
    "source_taxon",
)


def validate_facet_accountability(
    metadata: Mapping[str, object],
    *,
    expected_node_level: str,
    source_snapshot_id: str,
    build_id: str,
) -> None:
    """Validate the complete identity-bound v4 facet-accountability contract."""
    if expected_node_level not in _NODE_LEVELS:
        raise ValueError("facet accountability node level is not governed")
    if (
        metadata.get("schema_version") != FACET_SCHEMA_VERSION
        or metadata.get("node_level") != expected_node_level
    ):
        raise ValueError("facet accountability schema or node level changed")
    _validate_no_scientific_promotion(metadata)
    _validate_aggregate(metadata, density_required=True)
    for key in ("source_ecological_codes", "source_taxa"):
        rows = metadata.get(key)
        if not isinstance(rows, list):
            raise TypeError(f"{key} must be a list")
        for row in rows:
            if not isinstance(row, Mapping):
                raise TypeError(f"{key} rows must be objects")
            _validate_aggregate(row, density_required=True)
    code_rows = metadata["source_ecological_codes"]
    taxon_rows = metadata["source_taxa"]
    if expected_node_level == "source_ecological_code":
        if taxon_rows:
            raise ValueError("source-code facets cannot contain source taxa")
    elif expected_node_level == "source_taxon":
        if code_rows:
            raise ValueError("source-taxon facets cannot contain source codes")
    elif code_rows or taxon_rows:
        raise ValueError("sample-presence facets cannot contain source selectors")
    _validate_selector_rows(code_rows, selector="source_ecological_code")
    _validate_selector_rows(taxon_rows, selector="source_taxon")
    _validate_value_counts(metadata.get("source_unit_counts"), metadata)
    _validate_preset_metadata(
        metadata,
        expected_node_level=expected_node_level,
        source_snapshot_id=source_snapshot_id,
        build_id=build_id,
    )


def _validate_aggregate(
    aggregate: Mapping[str, object], *, density_required: bool
) -> None:
    country_rows = aggregate.get("country_counts")
    if not isinstance(country_rows, list) or len(country_rows) != len(COUNTRY_NAMES):
        raise ValueError("facet accountability requires all four countries")
    expected_codes = list(COUNTRY_NAMES)
    if any(not isinstance(row, Mapping) for row in country_rows):
        raise TypeError("facet country accountability row must be an object")
    observed_codes = [row.get("country_code") for row in country_rows]
    if observed_codes != expected_codes:
        raise ValueError("facet accountability country order changed")
    for row, (country_code, country_name) in zip(
        country_rows, COUNTRY_NAMES.items(), strict=True
    ):
        if row.get("country_code") != country_code or row.get("value") != country_name:
            raise ValueError("facet accountability country identity changed")
        _validate_temporal_bounds(row)
    if aggregate.get("node_count") != sum(
        int(row["node_count"]) for row in country_rows
    ):
        raise ValueError("facet node count does not reconcile to countries")
    if aggregate.get("observation_denominator") != sum(
        int(row["observation_denominator"]) for row in country_rows
    ):
        raise ValueError(
            "facet observation denominator does not reconcile to countries"
        )
    if aggregate.get("site_count") != sum(
        int(row["site_count"]) for row in country_rows
    ):
        raise ValueError("facet unique-site union does not reconcile to countries")
    _validate_temporal_bounds(aggregate)
    nonempty_countries = [row for row in country_rows if row["node_count"] != 0]
    if nonempty_countries and (
        aggregate.get("time_min_bp")
        != min(_validated_time(row, "time_min_bp") for row in nonempty_countries)
        or aggregate.get("time_max_bp")
        != max(_validated_time(row, "time_max_bp") for row in nonempty_countries)
    ):
        raise ValueError("facet time bounds do not reconcile to countries")
    if density_required and not time_density_matches_facet(
        aggregate.get("time_density"), aggregate
    ):
        raise ValueError("facet time density does not reconcile")


def _validate_preset_metadata(
    metadata: Mapping[str, object],
    *,
    expected_node_level: str,
    source_snapshot_id: str,
    build_id: str,
) -> None:
    catalog = metadata.get("source_label_preset_catalog")
    accountability = metadata.get("source_label_preset_accountability")
    if expected_node_level != "source_taxon":
        if catalog is not None or accountability is not None:
            raise ValueError("source-label presets belong only to source-taxon facets")
        return
    if not isinstance(catalog, Mapping) or not isinstance(accountability, Mapping):
        raise TypeError("source-label preset catalog and accountability are required")
    expected_catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=source_snapshot_id,
        build_id=build_id,
    )
    if catalog != expected_catalog:
        raise ValueError("source-label preset catalog identity changed")
    if (
        accountability.get("schema_version") != PRESET_ACCOUNTABILITY_SCHEMA_VERSION
        or accountability.get("catalog_content_sha256")
        != expected_catalog["content_sha256"]
        or accountability.get("membership_semantics") != MEMBERSHIP_SEMANTICS
        or accountability.get("source_taxon_count") != len(NEOTOMA_SOURCE_LABEL_TAXA)
        or accountability.get("preset_count") != len(NEOTOMA_SOURCE_LABEL_PRESETS)
        or accountability.get("membership_count")
        != sum(len(preset.member_taxon_ids) for preset in NEOTOMA_SOURCE_LABEL_PRESETS)
    ):
        raise ValueError("source-label preset accountability identity changed")
    _validate_refusal_flags(accountability)

    preset_rows = accountability.get("presets")
    union = accountability.get("union")
    if not isinstance(preset_rows, list) or not isinstance(union, Mapping):
        raise TypeError("source-label preset accountability rows are invalid")
    if len(preset_rows) != len(NEOTOMA_SOURCE_LABEL_PRESETS):
        raise ValueError("source-label preset accountability inventory changed")
    for row, preset in zip(preset_rows, NEOTOMA_SOURCE_LABEL_PRESETS, strict=True):
        if not isinstance(row, Mapping):
            raise TypeError("source-label preset accountability row must be an object")
        if any(row.get(key) != value for key, value in preset.as_dict().items()):
            raise ValueError("source-label preset membership changed")
        _validate_refusal_flags(row)
        _validate_aggregate(row, density_required=True)

    union_ids = [taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA]
    if (
        union.get("key") != "all-governed-source-labels"
        or union.get("member_taxon_count") != len(union_ids)
        or union.get("member_taxon_ids") != union_ids
        or union.get("membership_semantics") != MEMBERSHIP_SEMANTICS
    ):
        raise ValueError("source-label preset union membership changed")
    _validate_refusal_flags(union)
    _validate_aggregate(union, density_required=True)
    _validate_preset_denominators(metadata, preset_rows, union)


def _validate_refusal_flags(row: Mapping[str, object]) -> None:
    if any(
        row.get(field) is not False
        for field in (
            "accepted_classification",
            "aggregation_is_abundance",
            "propagation_allowed",
        )
    ):
        raise ValueError("source-label preset scientific refusal semantics changed")


def _validated_time(row: Mapping[str, object], field: str) -> float | int:
    value = row[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssertionError("validated nonempty country lost its temporal bound")
    return value


def _validated_count(row: Mapping[str, object], field: str) -> int:
    value = row[field]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AssertionError("validated aggregate lost its count contract")
    return value


def _validate_temporal_bounds(aggregate: Mapping[str, object]) -> None:
    counts = (
        aggregate.get("site_count"),
        aggregate.get("node_count"),
        aggregate.get("observation_denominator"),
    )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in counts
    ):
        raise ValueError("facet accountability counts must be nonnegative integers")
    if aggregate.get("site_count_semantics") != SITE_COUNT_SEMANTICS:
        raise ValueError("facet site count semantics changed")
    if aggregate.get("node_count") == 0:
        if (
            aggregate.get("site_count") != 0
            or aggregate.get("observation_denominator") != 0
            or aggregate.get("time_min_bp") is not None
            or aggregate.get("time_max_bp") is not None
        ):
            raise ValueError(
                "empty facet accountability must preserve null time bounds"
            )
        return
    if (
        aggregate.get("site_count") == 0
        or aggregate.get("observation_denominator") == 0
        or _validated_count(aggregate, "site_count")
        > _validated_count(aggregate, "node_count")
        or _validated_count(aggregate, "observation_denominator")
        < _validated_count(aggregate, "node_count")
    ):
        raise ValueError(
            "nonempty facet accountability requires sites and observations"
        )
    younger = aggregate.get("time_min_bp")
    older = aggregate.get("time_max_bp")
    if (
        isinstance(younger, bool)
        or not isinstance(younger, (int, float))
        or isinstance(older, bool)
        or not isinstance(older, (int, float))
        or not isfinite(float(younger))
        or not isfinite(float(older))
        or younger < 0
        or younger > older
    ):
        raise ValueError("nonempty facet accountability requires a valid BP interval")


def validate_node_partition(nodes: Sequence[SourceChronologyNode]) -> None:
    node_ids: set[str] = set()
    observation_ids: set[str] = set()
    site_countries: dict[str, str] = {}
    for node in nodes:
        if node.node_id in node_ids:
            raise ValueError("facet accountability contains duplicate node identity")
        node_ids.add(node.node_id)
        duplicate_observations = observation_ids.intersection(node.observation_ids)
        if duplicate_observations:
            raise ValueError(
                "facet accountability contains duplicate observation identity"
            )
        observation_ids.update(node.observation_ids)
        prior_country = site_countries.setdefault(node.site_id, node.country_code)
        if prior_country != node.country_code:
            raise ValueError("facet site identity crosses country ownership")


def _validate_selector_rows(rows: object, *, selector: str) -> None:
    if not isinstance(rows, list):
        raise TypeError(f"{selector} rows must be a list")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError(f"{selector} rows must be objects")
        value = row.get("value")
        if not isinstance(value, str) or not value or value in seen:
            raise ValueError(f"{selector} identity is empty or duplicated")
        seen.add(value)
        if selector == "source_ecological_code" and (
            row.get("source_code") != value
            or row.get("feature_key") != f"source:neotoma:ecological-code:{value}"
        ):
            raise ValueError("source ecological-code facet identity changed")
        if selector == "source_taxon":
            taxon_id = row.get("source_taxon_id")
            label = row.get("label")
            if (
                not isinstance(taxon_id, str)
                or not taxon_id
                or value != f"source:neotoma:taxon:{taxon_id}"
                or not isinstance(label, str)
                or not label
            ):
                raise ValueError("source taxon facet identity changed")


def _validate_value_counts(rows: object, aggregate: Mapping[str, object]) -> None:
    if not isinstance(rows, list):
        raise TypeError("source_unit_counts must be a list")
    values: set[str] = set()
    node_count = 0
    observation_denominator = 0
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("source unit rows must be objects")
        value = row.get("value")
        row_node_count = row.get("node_count")
        row_observation_count = row.get("observation_denominator")
        if not isinstance(value, str) or not value or value in values:
            raise ValueError("source unit identity is empty or duplicated")
        if any(
            isinstance(count, bool) or not isinstance(count, int) or count < 0
            for count in (row_node_count, row_observation_count)
        ):
            raise ValueError("source unit counts must be nonnegative integers")
        values.add(value)
        node_count += _validated_count(row, "node_count")
        observation_denominator += _validated_count(row, "observation_denominator")
    if node_count != aggregate.get(
        "node_count"
    ) or observation_denominator != aggregate.get("observation_denominator"):
        raise ValueError("source unit counts do not reconcile")


def _validate_preset_denominators(
    metadata: Mapping[str, object],
    preset_rows: Sequence[Mapping[str, object]],
    union: Mapping[str, object],
) -> None:
    raw_taxa = metadata.get("source_taxa")
    if not isinstance(raw_taxa, list):
        raise TypeError("source taxa must be a list")
    taxa_by_id: dict[int, Mapping[str, object]] = {}
    for row in raw_taxa:
        if not isinstance(row, Mapping):
            raise TypeError("source taxon facets must be objects")
        raw_id = row.get("source_taxon_id")
        if not isinstance(raw_id, str) or not raw_id.isdigit():
            continue
        taxon_id = int(raw_id)
        if taxon_id in taxa_by_id:
            raise ValueError("source taxon ID is duplicated")
        taxa_by_id[taxon_id] = row

    expected_names = {
        taxon.source_taxon_id: taxon.source_reported_name
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
    }
    for taxon_id, expected_name in expected_names.items():
        row = taxa_by_id.get(taxon_id)
        if row is not None and row.get("label") != expected_name:
            raise ValueError("governed source taxon label changed")

    for row, preset in zip(preset_rows, NEOTOMA_SOURCE_LABEL_PRESETS, strict=True):
        members = [
            taxa_by_id[taxon_id]
            for taxon_id in preset.member_taxon_ids
            if taxon_id in taxa_by_id
        ]
        _validate_aggregate_derived_from_rows(row, members)
    union_members = [
        taxa_by_id[taxon.source_taxon_id]
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
        if taxon.source_taxon_id in taxa_by_id
    ]
    _validate_aggregate_derived_from_rows(union, union_members)


def _validate_aggregate_derived_from_rows(
    aggregate: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    *,
    country_accountability: bool = True,
) -> None:
    populated = [row for row in rows if row.get("node_count") != 0]
    expected = {
        "node_count": sum(_validated_count(row, "node_count") for row in rows),
        "observation_denominator": sum(
            _validated_count(row, "observation_denominator") for row in rows
        ),
        "time_min_bp": min(
            (_validated_time(row, "time_min_bp") for row in populated),
            default=None,
        ),
        "time_max_bp": max(
            (_validated_time(row, "time_max_bp") for row in populated),
            default=None,
        ),
    }
    if any(aggregate.get(field) != value for field, value in expected.items()):
        raise ValueError("source-label preset denominator changed")
    if not country_accountability:
        return
    raw_country_rows = aggregate.get("country_counts")
    if not isinstance(raw_country_rows, list):
        raise TypeError("source-label preset country rows must be a list")
    for index in range(len(COUNTRY_NAMES)):
        member_country_rows: list[Mapping[str, object]] = []
        for row in rows:
            country_rows = row.get("country_counts")
            if not isinstance(country_rows, list) or not isinstance(
                country_rows[index], Mapping
            ):
                raise TypeError("source taxon country rows are invalid")
            member_country_rows.append(country_rows[index])
        if member_country_rows:
            country_row = raw_country_rows[index]
            if not isinstance(country_row, Mapping):
                raise TypeError("source-label preset country row is invalid")
            _validate_aggregate_derived_from_rows(
                country_row,
                member_country_rows,
                country_accountability=False,
            )
        else:
            _validate_empty_derived_country(raw_country_rows[index])


def _validate_empty_derived_country(row: object) -> None:
    if not isinstance(row, Mapping) or any(
        row.get(field) != value
        for field, value in (
            ("node_count", 0),
            ("observation_denominator", 0),
            ("time_min_bp", None),
            ("time_max_bp", None),
        )
    ):
        raise ValueError("source-label preset country denominator changed")


def _validate_no_scientific_promotion(value: object) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if (
                key
                in {
                    "accepted_classification",
                    "aggregation_is_abundance",
                    "propagation_allowed",
                    "propagation_eligible",
                }
                and child is not False
            ):
                raise ValueError("source-label facet scientific refusal changed")
            if key == "propagation_status" and child != "refused":
                raise ValueError("source-label facet propagation status changed")
            if key == "edge_count" and child != 0:
                raise ValueError("source-label facet edge count changed")
            _validate_no_scientific_promotion(child)
    elif isinstance(value, list):
        for child in value:
            _validate_no_scientific_promotion(child)


__all__ = [
    "COUNTRY_NAMES",
    "FACET_SCHEMA_VERSION",
    "PRESET_ACCOUNTABILITY_SCHEMA_VERSION",
    "SITE_COUNT_SEMANTICS",
    "validate_facet_accountability",
    "validate_node_partition",
]
