"""Neotoma country evidence derivation."""

from __future__ import annotations

from collections.abc import Mapping

from ..constants import INPUT_PATHS, CountryCoverageError
from ..decoding import (
    _country_code,
    _geojson_country_counts,
    _integer,
    _integer_counts,
    _object,
    _require_sha256_id,
)
from .partitions import EvidenceMap, _empty_counts, _site_partition


def add_neotoma_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    neotoma = _object(
        documents["data/neotoma/relational/reconciliation.json"].get("reconciliation"),
        "Neotoma reconciliation",
    )
    attribution = _object(
        neotoma.get("country_attribution_counts"), "country attribution"
    )
    _site_partition(
        evidence,
        "neotoma",
        "source_reported",
        _integer_counts(attribution.get("raw_country_codes"), "Neotoma raw countries"),
    )
    country_rows = _object(neotoma.get("country_counts"), "Neotoma country counts")
    normalized_country_rows: dict[str, object] = {}
    for country, raw_counts in country_rows.items():
        country_code = _country_code(country)
        if country_code in normalized_country_rows:
            raise CountryCoverageError(
                "Neotoma governed countries contain a duplicate partition"
            )
        normalized_country_rows[country_code] = raw_counts
    for country, raw_counts in normalized_country_rows.items():
        counts = _object(raw_counts, f"Neotoma {country} counts")
        evidence[("neotoma", "governed_assignment", country)] = {
            **_empty_counts(),
            "accepted_records": _integer(
                counts.get("assigned_sites"), "Neotoma assigned sites"
            ),
            "excluded_records": _integer(
                counts.get("refused_sites"), "Neotoma refused sites"
            ),
            "unresolved_records": _integer(
                counts.get("review_sites"), "Neotoma review sites"
            ),
            "sites": _integer(counts.get("sites"), "Neotoma sites"),
            "datasets": _integer(counts.get("datasets"), "Neotoma datasets"),
            "collection_units": _integer(
                counts.get("collection_units"), "Neotoma collection units"
            ),
            "samples": _integer(counts.get("samples"), "Neotoma samples"),
            "age_claims": _integer(counts.get("age_claim_rows"), "Neotoma age claims"),
            "observations": _integer(
                counts.get("observation_rows"), "Neotoma observations"
            ),
        }
    if "OUTSIDE" not in normalized_country_rows:
        evidence[("neotoma", "governed_assignment", "OUTSIDE")] = {
            **_empty_counts(),
            "accepted_records": 0,
            "excluded_records": 0,
            "unresolved_records": 0,
            "sites": 0,
        }
    _site_partition(
        evidence,
        "neotoma",
        "publication",
        _geojson_country_counts(documents[INPUT_PATHS[9]]),
        published=True,
    )


def publication_boundary_digest(document: Mapping[str, object]) -> str | None:
    """Read an explicitly retained publication authority, never infer today's one."""
    digests: set[str | None] = set()
    features = document.get("features")
    if not isinstance(features, list):
        raise CountryCoverageError("publication country features are missing")
    for feature in features:
        properties = _object(
            _object(feature, "published feature").get("properties"),
            "published properties",
        )
        rows = properties.get("popup_rows", [])
        if not isinstance(rows, list):
            raise CountryCoverageError("publication popup rows are invalid")
        values = [
            row.get("value")
            for row in rows
            if isinstance(row, Mapping) and row.get("label") == "Boundary digest"
        ]
        if len(values) > 1:
            raise CountryCoverageError(
                "publication has duplicate boundary digest labels"
            )
        if not values:
            digests.add(None)
        elif not isinstance(values[0], str):
            raise CountryCoverageError("publication boundary digest must be text")
        else:
            digests.add(_require_sha256_id(values[0], "publication boundary digest"))
    if len(digests) > 1:
        raise CountryCoverageError("publication boundary authorities are mixed")
    return next(iter(digests), None)
