"""Three source-informed static circles, without historical shoreline inference."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import isfinite, pi, sqrt
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_development import _rings


@dataclass(frozen=True)
class BasinProfile:
    """A declared alternative, not a probabilistic basin estimate."""

    name: str
    radius_m: float
    source: str


def profiles() -> tuple[BasinProfile, ...]:
    """Keep both reported modern areas distinct from the metadata radius."""
    return (
        BasinProfile(
            "modern_1_5_ha",
            sqrt(15000 / pi),
            "SMHI chart3-1832/catalogue1987; modern1.5ha",
        ),
        BasinProfile(
            "modern_1_6_ha",
            sqrt(16000 / pi),
            "OUP Table I; Bokesjön; Area(km²)=0.016; https://academic.oup.com/view-large/80999410",
        ),
        BasinProfile("metadata_80_m", 80.0, "LandClimII metadata BOKE row977;80m"),
    )


def profiles_from_sources(card: dict[str, Any]) -> tuple[BasinProfile, ...]:
    """Derive the declared radii from authenticated extracted facts and locators."""
    if (
        card.get("schema_version") != "bokesjon-basin-sources.v1"
        or card.get("document_kind")
        != "authored_fact_extraction_and_profile_declaration"
        or not card.get("static_circle_assumption")
    ):
        raise ValueError("Authored static-basin source declaration required")
    expected = (
        ("modern_1_5_ha", 0.015, "km2", ("county_report_1985", "smhi_catalogue_1987")),
        ("modern_1_6_ha", 0.016, "km2", ("oup_table_I",)),
        ("metadata_80_m", 80, "m", ("landclim_metadata", "saved_nominal_request")),
    )
    rows = card.get("profiles", [])
    if len(rows) != 3:
        raise ValueError("Exactly three source-declared profiles required")
    result = []
    for row, (name, value, unit, source_ids) in zip(rows, expected, strict=True):
        quantity = row.get("quantity", {})
        if (
            row.get("name") != name
            or isinstance(quantity.get("value"), bool)
            or quantity.get("value") != value
            or quantity.get("unit") != unit
        ):
            raise ValueError("Declared basin quantity or unit differs")
        references = row.get("source_refs", [])
        if [ref.get("source_id") for ref in references] != list(source_ids):
            raise ValueError("Required primary source references differ")
        citations = []
        for reference in references:
            source = card.get("sources", {}).get(reference["source_id"], {})
            if any(
                not isinstance(locator, str) or not locator.strip()
                for locator in (reference.get("locator"), source.get("locator"))
            ):
                raise ValueError("Primary source fact locators required")
            route = source.get("url", source.get("repository_path"))
            if not isinstance(route, str) or not route.strip():
                raise ValueError("Primary source route required")
            facts = source.get("facts", {})
            fact = (
                facts.get("area_km2")
                if unit == "km2"
                else facts.get("radius_m", facts.get("diameter_m", 0) / 2)
            )
            if isinstance(fact, bool) or fact != value:
                raise ValueError("Primary numerical fact and declared quantity differ")
            citations.append(f"{route}#{reference['locator']}")
        radius = (
            sqrt(quantity["value"] * 1000000 / pi)
            if unit == "km2"
            else float(quantity["value"])
        )
        result.append(BasinProfile(name, radius, "; ".join(citations)))
    return tuple(result)


def static_geometry(original: dict[str, Any], radius_m: float) -> dict[str, Any]:
    """Rebuild support as radius changes, retaining center-relative outer edges."""
    if isinstance(radius_m, bool) or not isfinite(radius_m) or not 0 < radius_m < 499:
        raise ValueError(
            "Finite positive radius below499m required for shore+1 support"
        )
    geometry = deepcopy(original)
    geometry["basin"]["diameter_m"] = 2 * radius_m
    geometry["inversion_rings"] = _rings(radius_m, inversion=True)[:2]
    geometry["forward_rings"] = _rings(radius_m, inversion=False)
    return geometry
