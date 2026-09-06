"""Load atlas-visible animal locality summaries."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from ....adna import (
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    build_species_support_matrix,
)
from ....adna.workflow.paths import adna_species_dir
from .chronology import (
    _atlas_public_chronology,
    _optional_float,
    _optional_str,
    _parse_chronology,
)
from .service import build_tracked_animal_atlas_evidence_rows


def load_tracked_animal_mappable_localities(
    data_root: Path,
) -> tuple[AdnaLocalitySummary, ...]:
    """Load only the locality rows that are actually eligible for point publication."""
    visible_site_ids = {
        row.site_record_id
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
    }
    localities: list[AdnaLocalitySummary] = []
    species_dir = adna_species_dir(Path(data_root))
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        locality_path = (
            species_dir / species.slug / "normalized" / "locality_summaries.json"
        )
        if not locality_path.is_file():
            continue
        payload = json.loads(locality_path.read_text(encoding="utf-8"))
        for row in payload.get("localities", []):
            if not isinstance(row, dict):
                continue
            identity = row.get("identity", {})
            if not isinstance(identity, dict):
                continue
            if str(identity.get("stable_token", "")).strip() not in visible_site_ids:
                continue
            localities.append(_parse_locality_summary(row))
    localities.sort(
        key=lambda locality: (
            locality.species_latin_name,
            not locality.nordic_inclusion,
            locality.locality or "",
        )
    )
    return tuple(localities)


def _parse_locality_summary(payload: dict[str, object]) -> AdnaLocalitySummary:
    identity = payload.get("identity", {})
    coordinates = payload.get("coordinates", {})
    chronology = payload.get("chronology", {})
    if (
        not isinstance(identity, dict)
        or not isinstance(coordinates, dict)
        or not isinstance(chronology, dict)
    ):
        raise TypeError(
            "Tracked locality summary must include identity, coordinates, and chronology"
        )
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace=str(identity.get("namespace", "")),
            stable_token=str(identity.get("stable_token", "")),
            locality_text=str(identity.get("locality_text", "")),
            political_entity=_optional_str(identity.get("political_entity")),
            source_anchor_tokens=tuple(
                str(item)
                for item in cast(
                    Iterable[object], identity.get("source_anchor_tokens", [])
                )
            ),
        ),
        species_latin_name=str(payload.get("species_latin_name", "")),
        species_common_name=str(payload.get("species_common_name", "")),
        source_family=str(payload.get("source_family", "")),
        source_releases=tuple(
            str(item)
            for item in cast(Iterable[object], payload.get("source_releases", []))
        ),
        record_modalities=tuple(
            str(item)
            for item in cast(Iterable[object], payload.get("record_modalities", []))
        ),
        review_strengths=tuple(
            str(item)
            for item in cast(Iterable[object], payload.get("review_strengths", []))
        ),
        provenance_qualities=tuple(
            str(item)
            for item in cast(Iterable[object], payload.get("provenance_qualities", []))
        ),
        locality=_optional_str(payload.get("locality")),
        coordinates=AdnaCoordinate(
            latitude=_optional_float(coordinates.get("latitude")),
            longitude=_optional_float(coordinates.get("longitude")),
            latitude_text=str(coordinates.get("latitude_text", "")),
            longitude_text=str(coordinates.get("longitude_text", "")),
            confidence=str(coordinates.get("confidence", "unknown")),
        ),
        sample_count=int(cast(str, payload.get("sample_count", 0) or 0)),
        sample_ids=tuple(
            str(item) for item in cast(Iterable[object], payload.get("sample_ids", []))
        ),
        datasets=tuple(
            str(item) for item in cast(Iterable[object], payload.get("datasets", []))
        ),
        chronology=_atlas_public_chronology(_parse_chronology(chronology)),
        sample_namespace=str(payload.get("sample_namespace", "")),
        project_accessions=tuple(
            str(item)
            for item in cast(Iterable[object], payload.get("project_accessions", []))
        ),
        original_location_text=str(payload.get("original_location_text", "")),
        nordic_inclusion=bool(payload.get("nordic_inclusion", False)),
        nordic_inclusion_reason=str(payload.get("nordic_inclusion_reason", "")),
        interpretation_note=str(payload.get("interpretation_note", "")),
    )
