"""Tests for deterministic playback manifest and propagation refusal."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib

import pytest

from bijux_pollenomics.reporting.map_playback import (
    PlaybackContractError,
    build_modeled_context_storyboards,
    build_playback_manifest,
    build_source_chronology_storyboards,
    canonical_json_bytes,
    refuse_candidate_succession_storyboard,
)
from tests.unit.reporting.map_playback.support import (
    NORDIC_COUNTRIES,
    modeled_manifest,
    source_layers,
)


def _manifest(
    *,
    reverse: bool = False,
    atlas_build_id: str = "atlas-" + ("a" * 64),
    scope_slug: str = "nordic",
    version: str = "v66",
    countries: tuple[str, ...] = NORDIC_COUNTRIES,
) -> dict[str, object]:
    source_chronology = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )
    modeled_stories = build_modeled_context_storyboards(
        modeled_manifest(), countries=NORDIC_COUNTRIES
    )
    refusal = refuse_candidate_succession_storyboard(
        {
            "propagation_status": "refused",
            "edge_count": 0,
            "reason_code": "accepted_scientific_classifications_not_available",
        }
    )
    if reverse:
        source_chronology = replace(
            source_chronology,
            stories=tuple(reversed(source_chronology.stories)),
            exact_taxa=tuple(reversed(source_chronology.exact_taxa)),
        )
        modeled_stories = tuple(reversed(modeled_stories))
    return build_playback_manifest(
        source_chronology=source_chronology,
        modeled_stories=modeled_stories,
        candidate_succession=refusal,
        atlas_build_id=atlas_build_id,
        scope_slug=scope_slug,
        version=version,
        countries=countries,
    )


def test_manifest_is_canonical_and_input_order_independent() -> None:
    manifest = _manifest()

    assert canonical_json_bytes(manifest) == canonical_json_bytes(
        _manifest(reverse=True)
    )
    assert manifest["atlas_identity"] == {
        "build_id": "atlas-" + ("a" * 64),
        "scope_slug": "nordic",
        "version": "v66",
        "countries": ["Denmark", "Finland", "Norway", "Sweden"],
    }
    digest = manifest.pop("content_sha256")
    assert digest == hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()
    source = manifest["source_chronology"]
    assert isinstance(source, dict)
    assert source["story_count"] == 9
    catalog = source["source_label_preset_catalog"]
    accountability = source["source_label_preset_accountability"]
    assert isinstance(catalog, dict)
    assert isinstance(accountability, dict)
    assert catalog["content_sha256"] == accountability["catalog_content_sha256"]
    stories = source["stories"]
    assert isinstance(stories, list)
    preset_stories = [
        story
        for story in stories
        if isinstance(story, dict)
        and story["selector"]["kind"] == "source_label_preset"
    ]
    assert len(preset_stories) == 5
    assert all(
        isinstance(story["site_count"], int) and story["site_count"] > 0
        for story in preset_stories
    )
    discovery = source["exact_taxon_discovery"]
    assert isinstance(discovery, dict)
    assert discovery["facet_count"] == 972
    assert discovery["bulk_story_materialization_allowed"] is False
    candidate = manifest["candidate_succession"]
    assert isinstance(candidate, dict)
    assert candidate["status"] == "refused"
    assert candidate["story_count"] == candidate["edge_count"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("atlas_build_id", "atlas-not-a-digest"),
        ("scope_slug", "../nordic"),
        ("version", "v66 release"),
        ("countries", ("Sweden", "Denmark")),
        ("countries", ("Atlantis",)),
    ],
)
def test_release_identity_fails_closed(field: str, value: object) -> None:
    kwargs = {field: value}

    with pytest.raises(PlaybackContractError):
        _manifest(**kwargs)  # type: ignore[arg-type]


def test_release_identity_is_covered_by_the_manifest_digest() -> None:
    baseline = _manifest()
    changed = _manifest(version="v67")

    assert baseline["content_sha256"] != changed["content_sha256"]


def test_manifest_refuses_story_countries_that_differ_from_release() -> None:
    with pytest.raises(PlaybackContractError, match="countries differ"):
        _manifest(countries=("Denmark", "Finland", "Sweden"))


def test_candidate_succession_cannot_be_published_from_edges() -> None:
    with pytest.raises(PlaybackContractError, match="unsupported"):
        refuse_candidate_succession_storyboard(
            {
                "propagation_status": "available",
                "edge_count": 1,
                "reason_code": None,
            }
        )


def test_canonical_encoder_rejects_nonstandard_numbers() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"scientific_value": float("nan")})


def test_manifest_rejects_post_build_preset_accountability_tampering() -> None:
    source_chronology = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )
    accountability = deepcopy(source_chronology.source_label_preset_accountability)
    presets = accountability["presets"]
    assert isinstance(presets, list) and isinstance(presets[0], dict)
    presets[0]["site_count"] = 1
    tampered = replace(
        source_chronology,
        source_label_preset_accountability=accountability,
    )
    modeled_stories = build_modeled_context_storyboards(
        modeled_manifest(), countries=NORDIC_COUNTRIES
    )
    refusal = refuse_candidate_succession_storyboard(
        {
            "propagation_status": "refused",
            "edge_count": 0,
            "reason_code": "accepted_scientific_classifications_not_available",
        }
    )

    with pytest.raises(PlaybackContractError, match="identity or denominator differs"):
        build_playback_manifest(
            source_chronology=tampered,
            modeled_stories=modeled_stories,
            candidate_succession=refusal,
            atlas_build_id="atlas-" + ("a" * 64),
            scope_slug="nordic",
            version="v66",
            countries=NORDIC_COUNTRIES,
        )
