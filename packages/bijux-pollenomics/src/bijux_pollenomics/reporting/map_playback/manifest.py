"""Canonical manifest assembly for atlas playback publication."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, cast

from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)

from .contracts import (
    ExactTaxonDiscovery,
    PlaybackContractError,
    PlaybackRefusal,
    PlaybackStory,
    validate_playback_countries,
)
from .source_chronology import SourceChronologyPlayback

_ATLAS_BUILD_ID = re.compile(r"atlas-[a-f0-9]{64}")
_SCOPE_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")


def canonical_json_bytes(value: object) -> bytes:
    """Encode JSON deterministically while refusing non-standard numeric values."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def build_playback_manifest(
    *,
    source_chronology: SourceChronologyPlayback,
    modeled_stories: tuple[PlaybackStory, ...],
    candidate_succession: PlaybackRefusal,
    atlas_build_id: str,
    scope_slug: str,
    version: str,
    countries: tuple[str, ...],
) -> dict[str, Any]:
    """Build a deterministic manifest whose digest covers all scientific content."""
    ordered_source = sorted(
        source_chronology.stories, key=lambda story: story.story_id
    )
    ordered_modeled = sorted(modeled_stories, key=lambda story: story.story_id)
    ordered_taxa = sorted(
        source_chronology.exact_taxa,
        key=lambda taxon: (
            taxon.label.casefold(),
            taxon.source_taxon_id,
            taxon.feature_key,
        ),
    )
    _validate_release_identity(
        atlas_build_id=atlas_build_id,
        scope_slug=scope_slug,
        version=version,
        countries=countries,
    )
    _validate_manifest_members(
        ordered_source,
        ordered_modeled,
        ordered_taxa,
        countries=countries,
    )
    catalog, accountability = _validated_source_label_presets(source_chronology)
    if candidate_succession.product_key != "candidate_succession":
        raise PlaybackContractError("manifest received the wrong refusal product")
    content: dict[str, Any] = {
        "schema_version": "map-playback-manifest.v1",
        "atlas_identity": {
            "build_id": atlas_build_id,
            "scope_slug": scope_slug,
            "version": version,
            "countries": list(countries),
        },
        "scientific_posture": {
            "temporal_direction": "oldest_to_present",
            "interval_semantics": "[younger_bp, older_bp]",
            "null_handling": "null_not_zero",
            "observation_is_propagation": False,
            "modeled_context_is_observation": False,
        },
        "source_chronology": {
            "status": "available",
            "rendered_media_status": "not_materialized",
            "evidence_role": "observation_chronology",
            "story_count": len(ordered_source),
            "stories": [story.as_dict() for story in ordered_source],
            "source_label_preset_catalog": catalog,
            "source_label_preset_accountability": accountability,
            "exact_taxon_discovery": {
                "status": "available",
                "facet_count": len(ordered_taxa),
                "bulk_story_materialization_allowed": False,
                "facets": [taxon.as_dict() for taxon in ordered_taxa],
            },
        },
        "modeled_context": {
            "status": "available",
            "rendered_media_status": "not_materialized",
            "evidence_role": "modeled_context",
            "story_count": len(ordered_modeled),
            "stories": [story.as_dict() for story in ordered_modeled],
        },
        "candidate_succession": candidate_succession.as_dict(),
    }
    return {
        **content,
        "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
    }


def _validate_manifest_members(
    source_stories: list[PlaybackStory],
    modeled_stories: list[PlaybackStory],
    exact_taxa: list[ExactTaxonDiscovery],
    *,
    countries: tuple[str, ...],
) -> None:
    if not source_stories or not modeled_stories or not exact_taxa:
        raise PlaybackContractError("playback manifest inventories must not be empty")
    story_ids = [story.story_id for story in (*source_stories, *modeled_stories)]
    if len(story_ids) != len(set(story_ids)):
        raise PlaybackContractError("playback story ids must be unique")
    if any(story.evidence_role != "observation_chronology" for story in source_stories):
        raise PlaybackContractError("source story has the wrong evidence role")
    if any(story.evidence_role != "modeled_context" for story in modeled_stories):
        raise PlaybackContractError("modeled story has the wrong evidence role")
    if any(
        story.countries != countries for story in (*source_stories, *modeled_stories)
    ):
        raise PlaybackContractError(
            "playback story countries differ from the atlas release identity"
        )
    facet_keys = [taxon.feature_key for taxon in exact_taxa]
    if len(facet_keys) != len(set(facet_keys)):
        raise PlaybackContractError("exact taxon discovery keys must be unique")


def _validated_source_label_presets(
    source: SourceChronologyPlayback,
) -> tuple[dict[str, object], dict[str, object]]:
    expected_catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=source.source_snapshot_id,
        build_id=source.build_id,
    )
    if source.source_label_preset_catalog != expected_catalog:
        raise PlaybackContractError("source-label preset catalog identity differs")
    accountability = source.source_label_preset_accountability
    if (
        accountability.get("schema_version")
        != "neotoma-source-label-preset-accountability.v1"
        or accountability.get("catalog_content_sha256")
        != expected_catalog["content_sha256"]
        or accountability.get("membership_semantics") != MEMBERSHIP_SEMANTICS
        or accountability.get("accepted_classification") is not False
        or accountability.get("aggregation_is_abundance") is not False
        or accountability.get("propagation_allowed") is not False
    ):
        raise PlaybackContractError("source-label preset accountability differs")
    raw_rows = accountability.get("presets")
    if not isinstance(raw_rows, list) or any(
        not isinstance(row, dict) for row in raw_rows
    ):
        raise PlaybackContractError("source-label preset rows are unavailable")
    rows = cast(list[dict[str, object]], raw_rows)
    if [row.get("key") for row in rows] != [
        preset.key for preset in NEOTOMA_SOURCE_LABEL_PRESETS
    ]:
        raise PlaybackContractError("source-label preset row order differs")
    if (
        accountability.get("source_taxon_count") != len(NEOTOMA_SOURCE_LABEL_TAXA)
        or accountability.get("preset_count") != len(NEOTOMA_SOURCE_LABEL_PRESETS)
        or accountability.get("membership_count")
        != sum(
            len(preset.member_taxon_ids)
            for preset in NEOTOMA_SOURCE_LABEL_PRESETS
        )
    ):
        raise PlaybackContractError("source-label preset inventory count differs")
    preset_stories = [
        story
        for story in source.stories
        if story.selector_kind == "source_label_preset"
    ]
    stories = {
        story.selector_value: story
        for story in preset_stories
    }
    if (
        len(preset_stories) != len(NEOTOMA_SOURCE_LABEL_PRESETS)
        or len(stories) != len(NEOTOMA_SOURCE_LABEL_PRESETS)
    ):
        raise PlaybackContractError("source-label preset story inventory differs")
    for row, preset in zip(rows, NEOTOMA_SOURCE_LABEL_PRESETS, strict=True):
        story = stories.get(preset.key)
        if (
            story is None
            or story.story_id != f"neotoma-source-preset-{preset.key}"
            or story.title
            != f"Neotoma literal exact-ID union — {preset.label}"
            or any(
                row.get(field) != getattr(story, field)
                for field in (
                    "site_count",
                    "node_count",
                    "observation_denominator",
                )
            )
        ):
            raise PlaybackContractError(
                "source-label preset story identity or denominator differs"
            )
        first_frame, last_frame = story.frames[0], story.frames[-1]
        if (
            first_frame.older_bp != row.get("time_max_bp")
            or last_frame.younger_bp != row.get("time_min_bp")
        ):
            raise PlaybackContractError("source-label preset story extent differs")
        if (
            row.get("label") != preset.label
            or row.get("member_taxon_ids") != list(preset.member_taxon_ids)
            or row.get("member_taxon_count") != len(preset.member_taxon_ids)
            or row.get("accepted_classification") is not False
            or row.get("aggregation_is_abundance") is not False
            or row.get("propagation_allowed") is not False
        ):
            raise PlaybackContractError("source-label preset membership differs")
    union = accountability.get("union")
    union_ids = [taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA]
    if not isinstance(union, dict) or (
        union.get("key") != "all-governed-source-labels"
        or union.get("membership_semantics") != MEMBERSHIP_SEMANTICS
        or union.get("member_taxon_count") != len(union_ids)
        or union.get("member_taxon_ids") != union_ids
        or union.get("accepted_classification") is not False
        or union.get("aggregation_is_abundance") is not False
        or union.get("propagation_allowed") is not False
    ):
        raise PlaybackContractError("source-label preset union differs")
    return dict(expected_catalog), json.loads(canonical_json_bytes(accountability))


def _validate_release_identity(
    *,
    atlas_build_id: str,
    scope_slug: str,
    version: str,
    countries: tuple[str, ...],
) -> None:
    if (
        not isinstance(atlas_build_id, str)
        or _ATLAS_BUILD_ID.fullmatch(atlas_build_id) is None
    ):
        raise PlaybackContractError("atlas_build_id must match atlas-[a-f0-9]{64}")
    if not isinstance(scope_slug, str) or _SCOPE_SLUG.fullmatch(scope_slug) is None:
        raise PlaybackContractError("playback scope_slug is invalid")
    if not isinstance(version, str) or _VERSION.fullmatch(version) is None:
        raise PlaybackContractError("playback version is invalid")
    validate_playback_countries(countries)


__all__ = ["build_playback_manifest", "canonical_json_bytes"]
