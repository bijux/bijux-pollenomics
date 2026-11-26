"""Compact transport of source chronology models, controls and age claims.

These are source assertions, not an analysis-selected chronology. Native payloads
retain model types, units, control values and nulls without interpretation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy

from bijux_pollenomics.collection.sources.neotoma.chronology.quality import (
    assess_neotoma_chronology_quality,
)
from bijux_pollenomics.collection.sources.neotoma.relational.identifiers import (
    source_reference_matches,
)

from ..io import _required_text
from ..records import _row_table, _unavailable, _unique_rows

_MODEL_FIELDS = (
    "chronology_id",
    "source_chronology_id",
    "collection_unit_id",
    "selected_by_collection_unit_reference",
    "source_is_default_assertion",
    "source_payload",
    "source_part_number",
    "effective_reference_selected",
    "reference_verification_status",
    "source_issue_ids",
)
_CONTROL_FIELDS = (
    "chronology_control_id",
    "source_chronology_control_id",
    "chronology_id",
    "collection_unit_id",
    "source_payload",
    "source_part_number",
    "source_issue_ids",
    "source_payload_posture",
)


def chronology_quality_tables(
    loaded: Mapping[str, tuple[list[Mapping[str, object]], tuple[int, ...]]],
    site_ids: set[str],
) -> dict[str, dict[str, object]]:
    """Encode the shared quality owner; legacy missing metadata stays unavailable."""
    required = (
        "samples",
        "age_claims",
        "chronologies",
        "chronology_controls",
        "conflicts",
    )
    if any(surface not in loaded for surface in required):
        return {
            site: _unavailable("neotoma_chronology_quality_metadata_unavailable")
            for site in site_ids
        }
    quality = assess_neotoma_chronology_quality(
        **{surface: loaded[surface][0] for surface in required}
    )
    samples = _unique_rows(loaded["samples"][0], "sample_id", "Neotoma quality samples")
    profiles = quality["profiles"]
    identity_fields = (
        "profile_id",
        "dataset_id",
        "collection_unit_id",
        "site_id",
        "country_code",
        "chronology_id",
        "source_age_type",
        "source_age_unit",
    )
    profile_fields = identity_fields + tuple(
        sorted(
            {field for profile in profiles for field in profile} - set(identity_fields)
        )
    )
    claim_fields = (
        "chronology_claim_id",
        "sample_id",
        "profile_id",
        "point_status",
        "flags",
    )
    sample_sites: dict[str, str] = {}
    samples_by_site: dict[str, list[str]] = {site: [] for site in site_ids}
    profiles_by_site: dict[str, list[Mapping[str, object]]] = {
        site: [] for site in site_ids
    }
    claims_by_site: dict[str, list[list[object]]] = {site: [] for site in site_ids}
    for identity, row in samples.items():
        site = _required_text(row.get("site_id"), "Neotoma quality sample site owner")
        if site not in samples_by_site:
            raise ValueError("Neotoma quality sample has an unknown site owner")
        sample_sites[identity] = site
        samples_by_site[site].append(identity)
    for profile in profiles:
        site = _required_text(
            profile.get("site_id"), "Neotoma quality profile site owner"
        )
        if site not in profiles_by_site:
            raise ValueError("Neotoma quality profile has an unknown site owner")
        profiles_by_site[site].append(profile)
    for identity, row in sorted(quality["claim_diagnostics"].items()):
        claim_site = sample_sites.get(row["sample_id"])
        if claim_site is None:
            raise ValueError("Neotoma quality claim has an unknown source sample owner")
        claims_by_site[claim_site].append(
            [identity, *[row.get(field) for field in claim_fields[1:]]]
        )
    result: dict[str, dict[str, object]] = {}
    for site in site_ids:
        site_samples = samples_by_site[site]
        site_profiles = profiles_by_site[site]
        claim_rows = claims_by_site[site]
        result[site] = {
            "schema_version": quality["schema_version"],
            "source_profile": copy.deepcopy(quality["source_profile"]),
            "profiles": _row_table(
                profile_fields,
                [
                    [profile.get(field) for field in profile_fields]
                    for profile in site_profiles
                ],
            ),
            "sample_flags": _row_table(
                ("sample_id", "flags"),
                [
                    [identity, quality["sample_flags"][identity]]
                    for identity in sorted(site_samples)
                ],
            ),
            "claim_diagnostics": _row_table(claim_fields, claim_rows),
            "site_denominators": {
                "samples": len(site_samples),
                "age_claims": len(claim_rows),
                "profiles": len(site_profiles),
            },
            "source_wide_denominators": quality["source_denominators"],
            "source_wide_diagnostic_denominators": quality["diagnostic_denominators"],
            "claim_diagnostic_semantics": quality["claim_diagnostic_semantics"],
            "profile_identity_semantics": "Dataset, collection unit, site, country, source chronology, source age type and age unit within the parent bound source snapshot; no source chronology selected.",
            "scope": "all_site_source_profiles_not_filtered_to_map_time_window",
        }
    return result


def chronology_model_tables(
    loaded: Mapping[str, tuple[list[Mapping[str, object]], tuple[int, ...]]],
    site_ids: set[str],
    *,
    source_issues_by_subject: Mapping[str, Sequence[str]] | None = None,
    control_variant_ids_by_site: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, dict[str, object]]:
    """Transport already authenticated source surfaces, with explicit absence.

    The caller validates the whole materialization before loading its parts. An
    absent legacy surface is unavailable; an authenticated empty surface has zero
    records. Part numbers refer to that materialization, not a copied source.
    """
    result: dict[str, dict[str, object]] = {site: {} for site in site_ids}
    issue_index = source_issues_by_subject or {}
    variant_coverage = control_variant_ids_by_site or {}
    for surface, name, fields in (
        ("chronologies", "models", _MODEL_FIELDS),
        ("chronology_controls", "controls", _CONTROL_FIELDS),
    ):
        if surface not in loaded:
            for tables in result.values():
                tables[name] = _unavailable(f"neotoma_{surface}_surface_not_available")
            continue
        rows, parts = loaded[surface]
        _unique_rows(rows, fields[0], f"Neotoma {surface}")
        grouped: dict[str, list[list[object]]] = {site: [] for site in site_ids}
        for row, part in zip(rows, parts, strict=True):
            site = _required_text(row.get("site_id"), f"Neotoma {surface} site ID")
            if site not in grouped:
                raise ValueError(f"Neotoma {surface} reference unknown site: {site}")
            if not isinstance(row.get("source_payload"), Mapping):
                raise ValueError(f"Neotoma {surface} source payload is invalid")
            if surface == "chronologies" and any(
                not isinstance(row.get(field), bool) for field in fields[3:5]
            ):
                raise ValueError(
                    "Neotoma chronology default assertions must be Boolean"
                )
            issue_ids = sorted(
                {
                    issue_id
                    for key in (fields[0], "chronology_id", "collection_unit_id")
                    for value in (row.get(key),)
                    if isinstance(value, str)
                    for issue_id in issue_index.get(value, ())
                }
            )
            enriched = {
                **row,
                "source_part_number": part,
                "source_issue_ids": issue_ids,
            }
            if surface == "chronologies":
                identified = source_reference_matches(
                    row.get("source_chronology_id"), row.get("source_chronology_id")
                )
                enriched["effective_reference_selected"] = (
                    identified and row["selected_by_collection_unit_reference"] is True
                )
                enriched["reference_verification_status"] = (
                    "retained_reference_assertion_with_identified_source"
                    if identified
                    else "refused_invalid_source_identifier"
                    if isinstance(row.get("source_chronology_id"), (dict, list))
                    else "refused_missing_source_identifier"
                )
            else:
                enriched["source_payload_posture"] = (
                    "retained_canonical_variant_with_all_variants_in_source_issues"
                    if row["chronology_control_id"] in variant_coverage.get(site, ())
                    else "retained_source_control_payload"
                )
            grouped[site].append([enriched.get(field) for field in fields])
        prefixes = {
            field: "neotoma:chronology:"
            for field in fields
            if field in {"chronology_id", "chronology_control_id"}
        }
        prefixes["collection_unit_id"] = "neotoma:collection-unit:"
        for site, records in grouped.items():
            result[site][name] = {
                **_row_table(fields, records, identifier_prefixes=prefixes),
                "source_locator_contract": (
                    f"surfaces/{surface}/part-{{source_part_number:05d}}.json"
                    f"#{fields[0]}={{{fields[0]}}}"
                ),
            }
    return result


def chronology_tab(
    age_fields: Sequence[str],
    age_rows: Sequence[Sequence[object]],
    model_tables: Mapping[str, object],
) -> dict[str, object]:
    """Keep the primary age-table API while exposing independent model metadata."""
    if not age_rows and all(
        isinstance(table, Mapping) and table.get("status") == "unavailable"
        for table in model_tables.values()
    ):
        return _unavailable("neotoma_site_age_claims_not_available")
    return {
        **_row_table(
            age_fields,
            age_rows,
            identifier_prefixes={
                "chronology_claim_id": "neotoma:age-claim:",
                "subject_id": "neotoma:sample:",
                "source_record_id": "neotoma:sample:",
                "chronology_id": "neotoma:chronology:",
                "collection_unit_id": "neotoma:collection-unit:",
                "dataset_id": "neotoma:dataset:",
            },
        ),
        "interval_semantics": "[younger_bp, older_bp]",
        "null_semantics": "source null remains null",
        "selection_posture": "all source age assignments retained",
        "age_assignments": (
            {"status": "available", "record_count": len(age_rows)}
            if age_rows
            else _unavailable("neotoma_site_age_claims_not_available")
        ),
        **model_tables,
        "model_metadata_posture": (
            "Source models and controls only. The collection-unit reference and "
            "source default assertion are distinct; neither selects an analysis "
            "chronology or establishes calibration, comparable ages or a fitted curve."
        ),
        "reference_verification_posture": (
            "The retained collection-reference flag is preserved literally. An effective "
            "selection requires an identified source chronology; the original collection "
            "reference is not rederived from a retained flag."
        ),
    }
