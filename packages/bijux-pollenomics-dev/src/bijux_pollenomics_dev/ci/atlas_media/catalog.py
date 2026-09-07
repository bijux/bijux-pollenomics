"""Canonical website publication selection for governed atlas chronology media."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicationStorySpec:
    """One exact public story identity and its source selector."""

    story_id: str
    title: str
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
        "Neotoma source sample presence",
        "observation_chronology",
        "source_sample_presence",
        "all",
    ),
    PublicationStorySpec(
        "neotoma-source-code-trsh",
        "Neotoma TRSH — Trees and Shrubs",
        "observation_chronology",
        "source_ecological_code",
        "TRSH",
    ),
    PublicationStorySpec(
        "neotoma-source-code-uphe",
        "Neotoma UPHE — Upland Herbs",
        "observation_chronology",
        "source_ecological_code",
        "UPHE",
    ),
    PublicationStorySpec(
        "neotoma-source-code-aqvp",
        "Neotoma AQVP — Aquatic Vascular Plants",
        "observation_chronology",
        "source_ecological_code",
        "AQVP",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-416",
        "Neotoma exact source-reported taxon — Poaceae (Cerealia)",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:416",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-427",
        "Neotoma exact source-reported taxon — Poaceae (Cerealia) undiff.",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:427",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-1947",
        "Neotoma exact source-reported taxon — Poaceae (Cerealia-type)",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:1947",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-3924",
        "Neotoma exact source-reported taxon — Hordeum/Secale",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:3924",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-967",
        "Neotoma exact source-reported taxon — Secale",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:967",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-3926",
        "Neotoma exact source-reported taxon — Secale cereale",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:3926",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-488",
        "Neotoma exact source-reported taxon — Secale-type",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:488",
    ),
    PublicationStorySpec(
        "neotoma-source-taxon-969",
        "Neotoma exact source-reported taxon — Triticum",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:969",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-cerealia-t",
        "PANGAEA 937075 modeled context — Cerealia-t",
        "modeled_context",
        "modeled_metric",
        "Cerealia.t",
        "exact_taxa",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-secale",
        "PANGAEA 937075 modeled context — Secale cereale",
        "modeled_context",
        "modeled_metric",
        "Secale",
        "exact_taxa",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-ol",
        "PANGAEA 937075 modeled context — Open land (OL)",
        "modeled_context",
        "modeled_metric",
        "OL",
        "source_land_cover_types",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-et",
        "PANGAEA 937075 modeled context — Evergreen trees (ET)",
        "modeled_context",
        "modeled_metric",
        "ET",
        "source_land_cover_types",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-st",
        "PANGAEA 937075 modeled context — Summer-green trees (ST)",
        "modeled_context",
        "modeled_metric",
        "ST",
        "source_land_cover_types",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-lse",
        "PANGAEA 937075 modeled context — Low shrub, broadleaved evergreen (LSE)",
        "modeled_context",
        "modeled_metric",
        "LSE",
        "source_pft_codes",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-gl",
        "PANGAEA 937075 modeled context — Grassland - all herbs (GL)",
        "modeled_context",
        "modeled_metric",
        "GL",
        "source_pft_codes",
    ),
    PublicationStorySpec(
        "pangaea-937075-metric-al",
        "PANGAEA 937075 modeled context — Agricultural land - cereals (AL)",
        "modeled_context",
        "modeled_metric",
        "AL",
        "source_pft_codes",
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
PUBLICATION_STORY_TITLES = {
    story.story_id: story.title for story in PUBLICATION_STORIES
}

# v3 was released with exactly these 15 stories. Keep the complete inventory
# literal so later catalog additions cannot silently rewrite a governed legacy
# destination's contract.
LEGACY_PUBLICATION_STORY_TUPLES_V3 = (
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
        "neotoma-source-taxon-416",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:416",
        None,
    ),
    (
        "neotoma-source-taxon-427",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:427",
        None,
    ),
    (
        "neotoma-source-taxon-1947",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:1947",
        None,
    ),
    (
        "neotoma-source-taxon-3924",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:3924",
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
        "neotoma-source-taxon-3926",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:3926",
        None,
    ),
    (
        "neotoma-source-taxon-488",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:488",
        None,
    ),
    (
        "neotoma-source-taxon-969",
        "observation_chronology",
        "source_taxon",
        "source:neotoma:taxon:969",
        None,
    ),
    (
        "pangaea-937075-metric-cerealia-t",
        "modeled_context",
        "modeled_metric",
        "Cerealia.t",
        "exact_taxa",
    ),
    (
        "pangaea-937075-metric-secale",
        "modeled_context",
        "modeled_metric",
        "Secale",
        "exact_taxa",
    ),
    (
        "pangaea-937075-metric-ol",
        "modeled_context",
        "modeled_metric",
        "OL",
        "source_land_cover_types",
    ),
)
LEGACY_PUBLICATION_STORY_TITLES_V3 = {
    story_id: PUBLICATION_STORY_TITLES[story_id].replace(
        "exact source-reported taxon", "exact source taxon"
    )
    for story_id, *_ in LEGACY_PUBLICATION_STORY_TUPLES_V3
}
PUBLICATION_ASSET_COUNT = len(PUBLICATION_STORIES) * 2
PUBLICATION_SCHEMA_VERSION = "atlas-media-publication.v4"
LEGACY_PUBLICATION_SCHEMA_VERSION_V3 = "atlas-media-publication.v3"
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
LEGACY_PUBLICATION_STORY_TUPLES_V2 = (
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
        "pangaea-937075-metric-cerealia-t",
        "modeled_context",
        "modeled_metric",
        "Cerealia.t",
        "exact_taxa",
    ),
    (
        "pangaea-937075-metric-secale",
        "modeled_context",
        "modeled_metric",
        "Secale",
        "exact_taxa",
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
        "atlas-media-publication.v2",
        LEGACY_PUBLICATION_STORY_TUPLES_V2,
    ),
    (
        LEGACY_PUBLICATION_SCHEMA_VERSION_V3,
        LEGACY_PUBLICATION_STORY_TUPLES_V3,
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
    "LEGACY_PUBLICATION_SCHEMA_VERSION_V3",
    "LEGACY_PUBLICATION_STORY_TITLES_V3",
    "LEGACY_PUBLICATION_STORY_TUPLES_V1",
    "LEGACY_PUBLICATION_STORY_TUPLES_V2",
    "LEGACY_PUBLICATION_STORY_TUPLES_V3",
    "PUBLICATION_ASSET_COUNT",
    "PUBLICATION_SCHEMA_VERSION",
    "PUBLICATION_STORIES",
    "PUBLICATION_STORY_TITLES",
    "PUBLICATION_STORY_TUPLES",
    "SUPPORTED_EXISTING_PUBLICATION_CONTRACTS",
    "PublicationStorySpec",
]
