"""Reject animal-atlas rows that would erase sample-site identity."""

from __future__ import annotations


def _assert_no_project_level_flattening(
    *,
    primary_project_accession: str,
    site_record_id: str,
    sample_rows: tuple[dict[str, object], ...],
) -> None:
    retained_rows = tuple(
        row
        for row in sample_rows
        if str(row.get("inclusion_status", "")).strip() != "sample_context_blocked"
    )
    locality_tokens: set[str] = set()
    locality_texts: set[str] = set()
    for row in retained_rows:
        locality_identity = row.get("locality_identity")
        if not isinstance(locality_identity, dict):
            continue
        stable_token = str(locality_identity.get("stable_token", "")).strip()
        locality_text = str(locality_identity.get("locality_text", "")).strip()
        if stable_token:
            locality_tokens.add(stable_token)
        if locality_text:
            locality_texts.add(_normalize_locality_text(locality_text))
    if len(locality_tokens) <= 1 and len(locality_texts) <= 1:
        return
    raise ValueError(
        "Project-level flattening detected for "
        f"{primary_project_accession}: one locality summary would collapse "
        f"multiple sample-site identities {sorted(locality_tokens)} and "
        f"locality labels {sorted(locality_texts)} into {site_record_id}."
    )


def _normalize_locality_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
