"""Source identity enrichment from the validated Neotoma variable relation."""

from __future__ import annotations

from collections.abc import Mapping

from .identity import optional_text


def _taxon_id(value: object) -> int | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return optional_text(value)


def _semantic_codes(variable: Mapping[str, object]) -> set[str]:
    semantics = variable.get("source_semantics")
    if not isinstance(semantics, list):
        return set()
    return {
        code
        for row in semantics
        if isinstance(row, Mapping)
        if (code := optional_text(row.get("source_ecological_group"))) is not None
    }


def enrich_source_identity(
    observation: Mapping[str, object], variable: Mapping[str, object]
) -> tuple[dict[str, object], str | None]:
    """Fill nullable identity fields only from a matching source variable row."""
    enriched = dict(observation)
    if optional_text(observation.get("variable_id")) != optional_text(
        variable.get("variable_id")
    ):
        return enriched, "source_variable_identity_mismatch"
    for field_name in ("source_snapshot_id", "build_id"):
        if optional_text(observation.get(field_name)) != optional_text(
            variable.get(field_name)
        ):
            return enriched, "source_variable_lineage_mismatch"

    observed_taxon = _taxon_id(observation.get("source_taxon_id"))
    variable_taxon = _taxon_id(variable.get("source_taxon_id"))
    if observed_taxon is not None and variable_taxon is not None:
        if observed_taxon != variable_taxon:
            return enriched, "source_variable_identity_mismatch"
    elif observed_taxon is None:
        enriched["source_taxon_id"] = variable_taxon

    observed_name = optional_text(observation.get("source_reported_name"))
    variable_name = optional_text(variable.get("source_reported_name"))
    if observed_name is not None and variable_name is not None:
        if observed_name != variable_name:
            return enriched, "source_variable_identity_mismatch"
    elif observed_name is None:
        enriched["source_reported_name"] = variable_name

    source_unit = optional_text(observation.get("source_unit"))
    raw_units = variable.get("source_units")
    variable_units = (
        {value for item in raw_units if (value := optional_text(item)) is not None}
        if isinstance(raw_units, list)
        else set()
    )
    if source_unit is not None and variable_units and source_unit not in variable_units:
        return enriched, "source_variable_unit_mismatch"

    observed_code = optional_text(observation.get("source_ecological_group"))
    variable_codes = _semantic_codes(variable)
    if (
        observed_code is not None
        and variable_codes
        and observed_code not in variable_codes
    ):
        return enriched, "source_variable_identity_mismatch"
    if observed_code is None and len(variable_codes) == 1:
        enriched["source_ecological_group"] = next(iter(variable_codes))
    return enriched, None


def source_taxon_identity_was_enriched(
    source: Mapping[str, object], enriched: Mapping[str, object]
) -> bool:
    """Return whether the variable relation completed a source taxon identity."""
    source_identity = (
        _taxon_id(source.get("source_taxon_id")),
        optional_text(source.get("source_reported_name")),
    )
    enriched_identity = (
        _taxon_id(enriched.get("source_taxon_id")),
        optional_text(enriched.get("source_reported_name")),
    )
    return None in source_identity and None not in enriched_identity


__all__ = ["enrich_source_identity", "source_taxon_identity_was_enriched"]
