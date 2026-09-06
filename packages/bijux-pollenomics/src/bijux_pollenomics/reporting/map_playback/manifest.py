"""Canonical manifest assembly for atlas playback publication."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .contracts import (
    ExactTaxonDiscovery,
    PlaybackContractError,
    PlaybackRefusal,
    PlaybackStory,
    validate_playback_countries,
)

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
    source_stories: tuple[PlaybackStory, ...],
    modeled_stories: tuple[PlaybackStory, ...],
    exact_taxa: tuple[ExactTaxonDiscovery, ...],
    candidate_succession: PlaybackRefusal,
    atlas_build_id: str,
    scope_slug: str,
    version: str,
    countries: tuple[str, ...],
) -> dict[str, Any]:
    """Build a deterministic manifest whose digest covers all scientific content."""
    ordered_source = sorted(source_stories, key=lambda story: story.story_id)
    ordered_modeled = sorted(modeled_stories, key=lambda story: story.story_id)
    ordered_taxa = sorted(
        exact_taxa,
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
