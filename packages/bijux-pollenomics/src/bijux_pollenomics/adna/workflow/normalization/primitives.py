"""Species, breed, and coordinate normalization primitives."""

from __future__ import annotations
import re
from bijux_pollenomics.adna.domain.models import (
    AdnaCoordinate,
)
from ...species.definitions import AdnaSpeciesDefinition, resolve_species_definition

from .models import AdnaCoordinateResolution


def normalize_species_anchor(
    value: str,
    *,
    expected_species_name: str | None = None,
) -> AdnaSpeciesDefinition:
    """Normalize one species anchor and optionally enforce one expected identity."""
    species = resolve_species_definition(value)
    if (
        expected_species_name is not None
        and species.latin_name
        != resolve_species_definition(expected_species_name).latin_name
    ):
        raise ValueError(
            f"Species anchor mismatch: expected {expected_species_name}, got {value}"
        )
    return species


def normalize_breed_label(value: str | None) -> str | None:
    """Normalize a breed-like label without inventing unsupported precision."""
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value.strip())
    if not cleaned:
        return None
    if cleaned.casefold() in {"unknown", "n/a", "na", "not yet curated"}:
        return None
    return cleaned.casefold().replace("_", " ")


def normalize_coordinate_resolution(
    *,
    latitude_text: str,
    longitude_text: str,
    geographic_basis: str | None,
) -> AdnaCoordinateResolution:
    """Normalize a latitude/longitude pair while allowing honest withholding."""
    basis = geographic_basis or ""
    lat_clean = latitude_text.strip()
    lon_clean = longitude_text.strip()
    confidence = _coordinate_confidence_for(basis)
    if not lat_clean and not lon_clean:
        return AdnaCoordinateResolution(
            coordinate=None,
            confidence=confidence,
            source_basis=basis,
            reason="coordinates_withheld_by_source_policy",
        )
    if not lat_clean or not lon_clean:
        raise ValueError(
            "Coordinate normalization requires both latitude and longitude"
        )
    latitude = float(lat_clean)
    longitude = float(lon_clean)
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"Latitude out of range: {latitude_text}")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"Longitude out of range: {longitude_text}")
    return AdnaCoordinateResolution(
        coordinate=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=lat_clean,
            longitude_text=lon_clean,
            confidence=confidence,
        ),
        confidence=confidence,
        source_basis=basis,
        reason="parsed_coordinate_pair",
    )


def _coordinate_confidence_for(geographic_basis: str) -> str:
    basis = geographic_basis.casefold()
    if "exact" in basis:
        return "exact"
    if "supplementary_proximal_site_coordinates" in basis:
        return "approximate"
    if "named_site_geocoding" in basis:
        return "approximate"
    if any(
        token in basis
        for token in (
            "direct_published_coordinates",
            "supplementary_table_coordinates",
        )
    ):
        return "exact"
    if "archive_coordinates" in basis:
        return "approximate"
    if "approximate" in basis or "site_level" in basis:
        return "approximate"
    if "inferred" in basis:
        return "inferred"
    if any(
        token in basis
        for token in (
            "country_only",
            "locality_text",
            "withheld",
            "region_centroid_fallback",
            "unresolved_location_state",
        )
    ):
        return "withheld"
    return "unknown"
