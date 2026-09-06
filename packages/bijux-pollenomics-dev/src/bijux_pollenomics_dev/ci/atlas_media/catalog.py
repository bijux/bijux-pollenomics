"""Canonical website publication selection for governed atlas chronology media."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicationStorySpec:
    """One exact public story identity and its source selector."""

    story_id: str
    evidence_role: str
    selector_kind: str
    selector_value: str
    selector_family: str | None = None

    def as_tuple(self) -> tuple[str, str, str, str, str | None]:
        """Return the downstream validator's immutable comparison shape."""
        return (
            self.story_id,
            self.evidence_role,
            self.selector_kind,
            self.selector_value,
            self.selector_family,
        )


PUBLICATION_STORIES = (
    PublicationStorySpec(
        "neotoma-source-sample-presence",
        "observation_chronology",
        "source_sample_presence",
        "all",
    ),
    PublicationStorySpec(
        "neotoma-source-code-trsh",
        "observation_chronology",
        "source_ecological_code",
        "TRSH",
    ),
    PublicationStorySpec(
        "neotoma-source-code-uphe",
        "observation_chronology",
        "source_ecological_code",
        "UPHE",
    ),
    PublicationStorySpec(
        "neotoma-source-code-aqvp",
        "observation_chronology",
        "source_ecological_code",
        "AQVP",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-967",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:967",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-cerealia-t",
        "modeled_context",
        "modeled_metric",
        "Cerealia.t",
        "exact_taxa",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-secale",
        "modeled_context",
        "modeled_metric",
        "Secale",
        "exact_taxa",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-ol",
        "modeled_context",
        "modeled_metric",
        "OL",
        "source_land_cover_types",
    ),
)

CORE_SOURCE_STORIES = tuple(
    story
    for story in PUBLICATION_STORIES
    if story.evidence_role == "observation_chronology"
    and story.selector_kind != "source_taxon"
)
DEFAULT_EXACT_TAXA = tuple(
    story.selector_value
    for story in PUBLICATION_STORIES
    if story.selector_kind == "source_taxon"
)
DEFAULT_MODELED_METRICS = tuple(
    story.selector_value
    for story in PUBLICATION_STORIES
    if story.selector_kind == "modeled_metric"
)
PUBLICATION_STORY_TUPLES = tuple(story.as_tuple() for story in PUBLICATION_STORIES)
PUBLICATION_ASSET_COUNT = len(PUBLICATION_STORIES) * 2
PUBLICATION_SCHEMA_VERSION = "atlas-media-publication.v2"
LEGACY_PUBLICATION_STORY_TUPLES_V1 = (
    (
        "neotoma-source-sample-presence",
        "observation_chronology",
        "source_sample_presence",
        "all",
        None,
    ),
    (
        "neotoma-source-code-trsh",
        "observation_chronology",
        "source_ecological_code",
        "TRSH",
        None,
    ),
    (
        "neotoma-source-code-uphe",
        "observation_chronology",
        "source_ecological_code",
        "UPHE",
        None,
    ),
    (
        "neotoma-source-code-aqvp",
        "observation_chronology",
        "source_ecological_code",
        "AQVP",
        None,
    ),
    (
        "neotoma-source-taxon-967",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:967",
        None,
    ),
    (
        "pangaea-937075-metric-ol",
        "modeled_context",
        "modeled_metric",
        "OL",
        "source_land_cover_types",
    ),
)
SUPPORTED_EXISTING_PUBLICATION_CONTRACTS = (
    (
        "atlas-media-publication.v1",
        LEGACY_PUBLICATION_STORY_TUPLES_V1,
    ),
    (
        PUBLICATION_SCHEMA_VERSION,
        PUBLICATION_STORY_TUPLES,
    ),
)


__all__ = [
    "CORE_SOURCE_STORIES",
    "DEFAULT_EXACT_TAXA",
    "DEFAULT_MODELED_METRICS",
    "LEGACY_PUBLICATION_STORY_TUPLES_V1",
    "PUBLICATION_ASSET_COUNT",
    "PUBLICATION_SCHEMA_VERSION",
    "PUBLICATION_STORIES",
    "PUBLICATION_STORY_TUPLES",
    "SUPPORTED_EXISTING_PUBLICATION_CONTRACTS",
    "PublicationStorySpec",
]
