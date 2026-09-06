"""Derive sample-level identifiers and support annotations."""

from __future__ import annotations


ATLAS_PUBLICATION_INCLUSION_STATUSES = frozenset(
    {
        "comparator_site_curated",
        "nordic_lead_site_curated",
        "site_curated",
    }
)


def _atlas_admitted_sample_rows(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        row
        for row in sample_rows
        if str(row.get("inclusion_status", "")).strip()
        in ATLAS_PUBLICATION_INCLUSION_STATUSES
    )


def _sample_locality_token(row: dict[str, object]) -> str:
    locality_identity = row.get("locality_identity", {})
    if not isinstance(locality_identity, dict):
        return ""
    return str(locality_identity.get("stable_token", "")).strip()


def _sample_record_ids_for(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    identifiers: set[str] = set()
    for row in sample_rows:
        identity = row.get("identity")
        if not isinstance(identity, dict):
            continue
        stable_token = str(identity.get("stable_token", "")).strip()
        if stable_token:
            identifiers.add(stable_token)
    return tuple(sorted(identifiers))


def _sample_group_ids_for(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(row.get("group_id", "")).strip()
                for row in sample_rows
                if str(row.get("group_id", "")).strip()
            }
        )
    )


def _source_native_taxonomy_for(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    taxon_pairs = {
        (
            str(row.get("source_native_tax_id", "")).strip(),
            str(row.get("source_native_scientific_name", "")).strip(),
        )
        for row in sample_rows
        if str(row.get("source_native_tax_id", "")).strip()
        or str(row.get("source_native_scientific_name", "")).strip()
    }
    ordered_pairs = tuple(sorted(taxon_pairs, key=lambda pair: (pair[1], pair[0])))
    labels = tuple(
        (
            f"{scientific_name} (tax_id {tax_id})"
            if scientific_name and tax_id
            else scientific_name or f"tax_id {tax_id}"
        )
        for tax_id, scientific_name in ordered_pairs
    )
    tax_ids = tuple(sorted({tax_id for tax_id, _ in ordered_pairs if tax_id}))
    scientific_names = tuple(sorted({name for _, name in ordered_pairs if name}))
    alignment_statuses = tuple(
        sorted(
            {
                str(row.get("taxon_alignment_status", "")).strip()
                for row in sample_rows
                if str(row.get("taxon_alignment_status", "")).strip()
            }
        )
    )
    return labels, tax_ids, scientific_names, alignment_statuses


def _inclusion_statuses_for(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    statuses = sorted(
        {
            str(row.get("inclusion_status", "")).strip()
            for row in sample_rows
            if str(row.get("inclusion_status", "")).strip()
        }
    )
    return tuple(statuses)


def _inclusion_notes_for(sample_rows: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    notes = sorted(
        {
            str(row.get("inclusion_note", "")).strip()
            for row in sample_rows
            if str(row.get("inclusion_note", "")).strip()
        }
    )
    return tuple(notes)


def _supplementary_sources_for(
    sample_rows: tuple[dict[str, object], ...],
    provenance: dict[str, object],
    site_evidence: dict[str, object],
) -> tuple[str, ...]:
    sources = {
        str(row.get("supplementary_source", "")).strip()
        for row in sample_rows
        if str(row.get("supplementary_source", "")).strip()
    }
    for row in (provenance, site_evidence):
        value = str(row.get("supplementary_source", "")).strip()
        if value:
            sources.add(value)
    return tuple(sorted(sources))
