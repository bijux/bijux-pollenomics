"""Derive sample-level identifiers and support annotations."""

from __future__ import annotations


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
