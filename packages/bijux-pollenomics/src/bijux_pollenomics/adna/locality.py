from __future__ import annotations

import re

from .models import AdnaLocalityIdentity
from .species import resolve_species_definition

__all__ = ["build_locality_identity"]


def build_locality_identity(
    *,
    species_name: str,
    source_family: str,
    locality_text: str,
    political_entity: str,
    latitude_text: str,
    longitude_text: str,
) -> AdnaLocalityIdentity:
    """Build a canonical shared locality anchor for species-aware ancient-DNA records."""
    species = resolve_species_definition(species_name)
    locality_slug = _slugify(locality_text)
    political_slug = _slugify(political_entity)
    source_slug = _slugify(source_family)
    coordinate_slug = _slugify(f"{latitude_text}:{longitude_text}")
    stable_token = (
        f"{species.slug}:{source_slug}:{political_slug}:{locality_slug}:{coordinate_slug}"
    )
    return AdnaLocalityIdentity(
        namespace=f"{species.slug}:locality",
        stable_token=stable_token,
        locality_text=locality_text,
        political_entity=political_entity,
        source_anchor_tokens=(source_family, latitude_text, longitude_text),
    )


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold())
    return normalized.strip("-") or "unknown"
