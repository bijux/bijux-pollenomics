from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "SOURCE_IDENTITIES",
    "SourceIdentity",
    "resolve_source_identity",
]


@dataclass(frozen=True)
class SourceIdentity:
    """Stable identity for one tracked source family."""

    key: str
    display_name: str
    evidence_family: str


SOURCE_IDENTITIES: dict[str, SourceIdentity] = {
    "aadr": SourceIdentity(
        key="aadr",
        display_name="AADR",
        evidence_family="ancient_dna_context",
    ),
    "boundaries": SourceIdentity(
        key="boundaries",
        display_name="Nordic Boundaries",
        evidence_family="geospatial_boundary_context",
    ),
    "landclim": SourceIdentity(
        key="landclim",
        display_name="LandClim",
        evidence_family="pollen_paleoclimate_context",
    ),
    "neotoma": SourceIdentity(
        key="neotoma",
        display_name="Neotoma",
        evidence_family="pollen_context",
    ),
    "raa": SourceIdentity(
        key="raa",
        display_name="RAÄ",
        evidence_family="archaeology_context",
    ),
    "sead": SourceIdentity(
        key="sead",
        display_name="SEAD",
        evidence_family="environmental_archaeology_context",
    ),
}


def resolve_source_identity(source_key: str) -> SourceIdentity:
    """Resolve one stable source identity by key."""
    try:
        return SOURCE_IDENTITIES[source_key]
    except KeyError as exc:
        raise ValueError(f"Unsupported source identity: {source_key}") from exc
