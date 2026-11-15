"""Lossless source issue and dated-specimen transport for Neotoma readers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
import copy
import json

from .io import _required_text
from .records import _row_table, _unavailable, _unique_rows

LoadedSurfaces = Mapping[str, tuple[list[Mapping[str, object]], tuple[int, ...]]]
_ID_FIELDS = {
    "sites": "site_id",
    "collection_units": "collection_unit_id",
    "datasets": "dataset_id",
    "samples": "sample_id",
    "age_claims": "chronology_claim_id",
    "chronologies": "chronology_id",
    "chronology_controls": "chronology_control_id",
    "observations": "observation_id",
}
_FIELDS = {
    "conflicts": (
        "conflict_id",
        "conflict_kind",
        "subject_id",
        "detail",
        "review_status",
        "source_record",
        "source_part_number",
        "source_locator",
    ),
    "orphans": (
        "orphan_id",
        "entity_type",
        "parent_id",
        "reason",
        "source_value",
        "review_status",
        "source_record",
        "source_part_number",
        "source_locator",
    ),
    "chronology_control_variants": (
        "conflict_id",
        "variant_index",
        "chronology_control_id",
        "source_record",
        "source_part_number",
        "source_locator",
    ),
}
_MULTIPLICITY_SOURCE = (
    "https://open.neotomadb.org/dbschema/tables/geochroncontrols.html"
)


def _control_variants(row: Mapping[str, object]) -> list[Mapping[str, object]]:
    if row.get("conflict_kind") != "chronology_control_payload_conflict":
        return []
    detail = row.get("detail")
    variants = detail.get("variants") if isinstance(detail, Mapping) else None
    if not isinstance(variants, list) or any(
        not isinstance(v, Mapping) for v in variants
    ):
        raise ValueError("Neotoma control conflict variants are invalid")
    return variants


def _review_status(row: Mapping[str, object]) -> str:
    variants = _control_variants(row)
    if variants:
        owners = {
            json.dumps(
                {
                    key: value
                    for key, value in variant.items()
                    if key != "source_payload"
                },
                sort_keys=True,
            )
            for variant in variants
        }
        payloads = [v.get("source_payload") for v in variants]
        if all(isinstance(p, Mapping) for p in payloads):
            bare = {
                json.dumps(
                    {k: v for k, v in p.items() if k != "geochron"}, sort_keys=True
                )
                for p in payloads
                if isinstance(p, Mapping)
            }
            ids = [
                p["geochron"].get("geochronid")
                if isinstance(p, Mapping) and isinstance(p.get("geochron"), Mapping)
                else None
                for p in payloads
            ]
            if (
                len(bare) == 1
                and len(owners) == 1
                and all(type(i) is int and i > 0 for i in ids)
                and len(set(ids)) == len(ids)
            ):
                return "confirmed_source_geochron_specimen_multiplicity"
        return "unresolved_control_payload_conflict"
    if row.get("conflict_kind") == "default_chronology_assertions_conflict":
        return "source_default_chronology_assertions_conflict"
    if row.get("reason") == "missing_source_identifier":
        return "missing_source_identifier_retained"
    return "unresolved_source_issue"


def source_issue_tables(
    loaded: LoadedSurfaces, site_ids: set[str], projected_site_ids: set[str]
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, object],
    dict[str, list[str]],
    dict[str, tuple[str, ...]],
]:
    """Retain each issue once per relevant site, with an explicit unresolved partition."""
    issue_rows = {
        surface: loaded.get(surface, ([], ()))[0]
        for surface in ("conflicts", "orphans")
    }
    wanted = {
        value
        for rows in issue_rows.values()
        for row in rows
        for value in (row.get("subject_id"), row.get("parent_id"))
        if isinstance(value, str)
    }
    owners: dict[str, set[str]] = defaultdict(set)
    for surface, field in _ID_FIELDS.items():
        for row in loaded.get(surface, ([], ()))[0]:
            identity, site = row.get(field), row.get("site_id")
            if (
                isinstance(identity, str)
                and identity in wanted
                and isinstance(site, str)
            ):
                owners[identity].add(site)
            variable = row.get("variable_id") if surface == "observations" else None
            if (
                isinstance(variable, str)
                and variable in wanted
                and isinstance(site, str)
            ):
                owners[variable].add(site)
    grouped: dict[str, dict[str, list[list[object]]]] = {
        site: {name: [] for name in _FIELDS} for site in site_ids
    }
    by_subject: dict[str, list[str]] = defaultdict(list)
    counts = dict.fromkeys(_FIELDS, 0)
    projected = dict.fromkeys(_FIELDS, 0)
    excluded = dict.fromkeys(_FIELDS, 0)
    unresolved_counts = dict.fromkeys(_FIELDS, 0)
    excluded_records: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    for surface in ("conflicts", "orphans"):
        rows, parts = loaded.get(surface, ([], ()))
        id_field = "conflict_id" if surface == "conflicts" else "orphan_id"
        _unique_rows(rows, id_field, f"Neotoma {surface}")
        for row, part in zip(rows, parts, strict=True):
            identity = _required_text(row.get(id_field), f"Neotoma {id_field}")
            subject = row.get("subject_id" if surface == "conflicts" else "parent_id")
            sites = set(owners.get(subject, ())) if isinstance(subject, str) else set()
            variants = _control_variants(row)
            for variant in variants:
                site = variant.get("site_id")
                if isinstance(site, str):
                    sites.add(site)
            if not sites <= site_ids:
                raise ValueError("Neotoma source issue references unknown site")
            locator = f"surfaces/{surface}/part-{part:05d}.json#{id_field}={identity}"
            enriched = {
                **row,
                "review_status": _review_status(row),
                "source_record": copy.deepcopy(dict(row)),
                "source_part_number": part,
                "source_locator": locator,
            }
            values = [enriched.get(field) for field in _FIELDS[surface]]
            counts[surface] += 1
            counts["chronology_control_variants"] += len(variants)
            category = projected if sites & projected_site_ids else excluded
            if sites:
                category[surface] += 1
                category["chronology_control_variants"] += len(variants)
                if not sites & projected_site_ids:
                    excluded_records.append(
                        {
                            "issue_id": identity,
                            "site_ids": sorted(sites),
                            "source_record": enriched["source_record"],
                            "source_locator": locator,
                            "reason_code": "site_without_governed_country_assignment",
                        }
                    )
            else:
                unresolved_counts[surface] += 1
                unresolved_counts["chronology_control_variants"] += len(variants)
                unresolved.append(
                    {
                        "issue_id": identity,
                        "source_record": enriched["source_record"],
                        "source_locator": locator,
                        "reason_code": "source_issue_site_owner_not_resolved",
                    }
                )
            if isinstance(subject, str):
                by_subject[subject].append(identity)
            detail = row.get("detail")
            if isinstance(detail, Mapping) and isinstance(
                detail.get("collection_unit_id"), str
            ):
                by_subject[detail["collection_unit_id"]].append(identity)
            for site in sites:
                grouped[site][surface].append(values)
                for index, variant in enumerate(variants):
                    grouped[site]["chronology_control_variants"].append(
                        [
                            identity,
                            index,
                            variant.get("chronology_control_id"),
                            copy.deepcopy(dict(variant)),
                            part,
                            f"{locator}/detail/variants/{index}",
                        ]
                    )
    tables: dict[str, dict[str, object]] = {}
    for site, groups in grouped.items():
        tables[site] = {
            **{
                name: {
                    **_row_table(fields, groups[name]),
                    "source_locator_contract": (
                        "surfaces/conflicts/part-{source_part_number:05d}.json#conflict_id={conflict_id}/detail/variants/{variant_index}"
                        if name == "chronology_control_variants"
                        else f"surfaces/{name}/part-{{source_part_number:05d}}.json#{fields[0]}={{{fields[0]}}}"
                    ),
                }
                if ("conflicts" if name == "chronology_control_variants" else name)
                in loaded
                else _unavailable(f"neotoma_{name}_surface_not_available")
                for name, fields in _FIELDS.items()
            },
            "semantics": "Retained source issues and specimen variants; not new observations or an adjudicated chronology.",
            "control_multiplicity_contract": _MULTIPLICITY_SOURCE,
            "canonical_control_posture": "A retained canonical control payload is one representation; all retained variants remain available here without preferring a dated specimen.",
        }
    account: dict[str, object] = {
        "source_counts": counts,
        "projected_counts": projected,
        "excluded_site_counts": excluded,
        "excluded_site_records": excluded_records,
        "unresolved_site_counts": unresolved_counts,
        "unresolved_site_issue_ids": [r["issue_id"] for r in unresolved],
        "unresolved_site_records": unresolved,
        "excluded_site_reason_code": "site_without_governed_country_assignment",
    }
    if any(
        counts[name] != projected[name] + excluded[name] + unresolved_counts[name]
        for name in _FIELDS
    ):
        raise ValueError("Neotoma source issue ownership partition does not reconcile")
    return (
        tables,
        account,
        {subject: sorted(set(ids)) for subject, ids in by_subject.items()},
        {
            site: tuple(
                sorted(
                    {
                        row[2]
                        for row in groups["chronology_control_variants"]
                        if isinstance(row[2], str)
                    }
                )
            )
            for site, groups in grouped.items()
        },
    )
