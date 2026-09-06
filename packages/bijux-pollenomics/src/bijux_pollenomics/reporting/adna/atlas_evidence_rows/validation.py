"""Reject animal-atlas rows that would erase sample-site identity."""

from __future__ import annotations

from pathlib import Path

_SOURCE_NATIVE_TAXON_SCOPE_RULES = {
    ("bos_taurus", "bos primigenius"): "wild_or_progenitor_context",
    ("felis_catus", "felis silvestris lybica"): "wild_or_progenitor_context",
    ("felis_catus", "felis silvestris silvestris"): "wild_or_progenitor_context",
    ("felis_catus", "felis ornata"): "comparator",
    ("felis_catus", "prionailurus bengalensis"): "comparator",
}

_SOURCE_NATIVE_SAMPLE_SCOPE_RULES = {
    ("sus_scrofa_domesticus", "PRJEB30282", "SAMEA5160867"): "domesticated_core",
    ("sus_scrofa_domesticus", "PRJEB30282", "SAMEA5160868"): "domesticated_core",
}

_SOURCE_SAMPLE_SCOPE_MARKERS = {
    ("capra_hircus", "PRJEB90141"): {
        "domesticated_core": (" domestic",),
        "wild_or_progenitor_context": ("bezoar",),
    },
    ("equus_caballus", "PRJEB31613"): {
        "wild_or_progenitor_context": ("upper palaeolithic", "wild archaic"),
    },
    ("equus_caballus", "PRJEB44430"): {
        "wild_or_progenitor_context": (
            "palaeolithic",
            "paleolithic",
            "pleistocene",
        ),
    },
}

_SOURCE_SAMPLE_GROUP_SCOPE_RULES = {
    ("equus_caballus", "PRJEB44430"): {
        "DOM2": "domesticated_core",
    },
}


def _project_sample_animal_scope_for(
    species_root: Path,
    project_scope_lookup: dict[str, str] | None,
    *,
    project_accessions: tuple[str, ...],
    sample_rows: tuple[dict[str, object], ...],
) -> str | None:
    scope, _reason = _project_sample_animal_scope_resolution_for(
        species_root,
        project_scope_lookup,
        project_accessions=project_accessions,
        sample_rows=sample_rows,
    )
    return scope


def _project_sample_animal_scope_resolution_for(
    species_root: Path,
    project_scope_lookup: dict[str, str] | None,
    *,
    project_accessions: tuple[str, ...],
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[str | None, str | None]:
    """Resolve sample-owned scope and expose the exact fail-closed reason."""
    declared_projects = tuple(accession.strip() for accession in project_accessions)
    sample_projects = tuple(
        str(row.get("project_accession", "")).strip() for row in sample_rows
    )
    if (
        len(declared_projects) != 1
        or any(not accession for accession in declared_projects)
        or not sample_projects
        or any(not accession for accession in sample_projects)
        or set(sample_projects) != set(declared_projects)
    ):
        return None, "sample_scope_not_evidenced"
    if project_scope_lookup is None:
        return None, "project_scope_not_evidenced"
    project_scope = project_scope_lookup.get(declared_projects[0])
    if project_scope is None:
        return None, "project_scope_not_evidenced"
    if project_scope != "domesticated_core":
        return project_scope, None

    sample_scopes: set[str] = set()
    for row in sample_rows:
        marker_rules = _SOURCE_SAMPLE_SCOPE_MARKERS.get(
            (species_root.name, declared_projects[0])
        )
        if marker_rules is not None:
            lineage_text = str(row.get("sample_lineage_excerpt", ""))
            evidence_text = " ".join(
                (lineage_text, str(row.get("chronology_provenance_text", "")))
            ).casefold()
            evidenced_scopes = {
                scope
                for scope, markers in marker_rules.items()
                if any(marker in evidence_text for marker in markers)
            }
            group_scope_rules = _SOURCE_SAMPLE_GROUP_SCOPE_RULES.get(
                (species_root.name, declared_projects[0]),
                {},
            )
            lineage_fields = tuple(field.strip() for field in lineage_text.split("|"))
            if len(lineage_fields) > 4:
                group_scope = group_scope_rules.get(lineage_fields[4])
                if group_scope is not None:
                    evidenced_scopes.add(group_scope)
            if not evidenced_scopes:
                return None, "sample_scope_not_evidenced"
            if len(evidenced_scopes) > 1:
                return None, "mixed_sample_scope"
            sample_scopes.update(evidenced_scopes)
            continue
        alignment = str(row.get("taxon_alignment_status", "")).strip()
        if alignment in {"", "not_reported", "project_species_match"}:
            sample_scopes.add(project_scope)
            continue
        if alignment != "project_species_mismatch":
            return None, "sample_scope_not_evidenced"
        archive_sample_id = str(row.get("archive_native_sample_id", "")).strip()
        sample_scope = _SOURCE_NATIVE_SAMPLE_SCOPE_RULES.get(
            (species_root.name, declared_projects[0], archive_sample_id)
        )
        if sample_scope is not None:
            sample_scopes.add(sample_scope)
            continue
        source_native_name = str(row.get("source_native_scientific_name", "")).strip()
        taxon_scope = _SOURCE_NATIVE_TAXON_SCOPE_RULES.get(
            (species_root.name, source_native_name.casefold())
        )
        if taxon_scope is None:
            return None, "sample_scope_not_evidenced"
        sample_scopes.add(taxon_scope)
    if len(sample_scopes) == 1:
        return next(iter(sample_scopes)), None
    if len(sample_scopes) > 1:
        return None, "mixed_sample_scope"
    return None, "sample_scope_not_evidenced"


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
