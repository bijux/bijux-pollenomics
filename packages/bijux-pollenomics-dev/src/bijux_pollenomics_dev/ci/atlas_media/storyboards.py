"""Governed storyboard loading, validation, and explicit selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
from typing import cast

from .catalog import CORE_SOURCE_STORIES
from .contracts import AtlasMediaError, SelectedStory, StorySelection
from .source_authority import SourceChronologyAuthority

_EXPECTED_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise AtlasMediaError(f"JSON contains duplicate key: {key}")
        value[key] = item
    return value


def load_storyboard_manifest(
    storyboard_path: Path,
    atlas_manifest_path: Path,
) -> dict[str, object]:
    """Load and bind the canonical playback manifest to one static atlas build."""
    try:
        storyboard = json.loads(
            storyboard_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        atlas = json.loads(
            atlas_manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasMediaError("atlas media manifest input is unreadable") from error
    if not isinstance(storyboard, dict) or not isinstance(atlas, dict):
        raise AtlasMediaError("atlas media manifests must be JSON objects")
    storyboard = cast(dict[str, object], storyboard)
    atlas = cast(dict[str, object], atlas)
    digest = storyboard.get("content_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise AtlasMediaError("storyboard content digest is absent")
    content = {
        key: value for key, value in storyboard.items() if key != "content_sha256"
    }
    if hashlib.sha256(_canonical_storyboard_bytes(content)).hexdigest() != digest:
        raise AtlasMediaError("storyboard content digest does not match")
    identity = _mapping(storyboard.get("atlas_identity"), "atlas_identity")
    if (
        storyboard.get("schema_version") != "map-playback-manifest.v1"
        or identity.get("build_id") != atlas.get("build_id")
        or identity.get("scope_slug") != atlas.get("scope_slug")
        or identity.get("version") != atlas.get("version")
    ):
        raise AtlasMediaError("storyboard identity does not match the static atlas")
    posture = _mapping(storyboard.get("scientific_posture"), "scientific_posture")
    if (
        posture.get("temporal_direction") != "oldest_to_present"
        or posture.get("interval_semantics") != "[younger_bp, older_bp]"
        or posture.get("null_handling") != "null_not_zero"
        or posture.get("observation_is_propagation") is not False
        or posture.get("modeled_context_is_observation") is not False
    ):
        raise AtlasMediaError("storyboard scientific posture is incompatible")
    refusal = _mapping(storyboard.get("candidate_succession"), "candidate_succession")
    if (
        refusal.get("product_key") != "candidate_succession"
        or refusal.get("reason_code")
        != "accepted_scientific_classifications_not_available"
        or refusal.get("status") != "refused"
        or refusal.get("story_count") != 0
        or refusal.get("edge_count") != 0
    ):
        raise AtlasMediaError("candidate succession media is not releasable")
    _text(refusal, "detail")
    return storyboard


def select_stories(
    manifest: Mapping[str, object],
    selection: StorySelection,
    *,
    source_authority: SourceChronologyAuthority,
) -> tuple[SelectedStory, ...]:
    """Select bounded core, exact-taxon, and modeled stories in durable order."""
    identity = _mapping(manifest.get("atlas_identity"), "atlas_identity")
    countries_value = identity.get("countries")
    if countries_value != list(_EXPECTED_COUNTRIES):
        raise AtlasMediaError("storyboard must cover the exact four Nordic countries")
    countries = tuple(cast(list[str], countries_value))
    source = _mapping(manifest.get("source_chronology"), "source_chronology")
    modeled = _mapping(manifest.get("modeled_context"), "modeled_context")
    if source.get("status") != "available" or modeled.get("status") != "available":
        raise AtlasMediaError("selected storyboard domains are unavailable")
    source_stories = _object_rows(source.get("stories"), "source stories")
    modeled_stories = _object_rows(modeled.get("stories"), "modeled stories")
    if source.get("story_count") != len(source_stories):
        raise AtlasMediaError("source story denominator differs")
    if modeled.get("story_count") != len(modeled_stories):
        raise AtlasMediaError("modeled story denominator differs")
    source_by_selector = _stories_by_selector(
        source_stories,
        label="source",
    )
    selected: list[SelectedStory] = []
    if selection.include_core_source_stories:
        for specification in CORE_SOURCE_STORIES:
            selector = specification.selector_value
            story = source_by_selector.get(selector)
            if story is None:
                raise AtlasMediaError(f"core source story is absent: {selector}")
            story_selector = _mapping(story.get("selector"), "story.selector")
            if story_selector.get("kind") != specification.selector_kind:
                raise AtlasMediaError(f"core source selector kind differs: {selector}")
            selected_story = _selected_story(
                story,
                countries=countries,
                source_authority=source_authority,
            )
            selected.append(selected_story)

    discovery = _mapping(source.get("exact_taxon_discovery"), "taxon discovery")
    if (
        discovery.get("status") != "available"
        or discovery.get("bulk_story_materialization_allowed") is not False
    ):
        raise AtlasMediaError("exact taxon discovery posture is incompatible")
    facets = _object_rows(discovery.get("facets"), "exact taxon facets")
    if discovery.get("facet_count") != len(facets):
        raise AtlasMediaError("exact taxon discovery denominator differs")
    for requested_taxon in selection.exact_taxa:
        matches = [
            facet
            for facet in facets
            if requested_taxon.casefold()
            in {
                str(facet.get("label", "")).casefold(),
                str(facet.get("feature_key", "")).casefold(),
                str(facet.get("source_taxon_id", "")).casefold(),
            }
        ]
        if len(matches) != 1:
            raise AtlasMediaError(
                f"exact taxon selector must resolve once: {requested_taxon}"
            )
        facet = matches[0]
        selected.append(
            _selected_story(
                _exact_taxon_story(facet, countries=countries),
                countries=countries,
                source_authority=source_authority,
            )
        )

    modeled_by_metric = _stories_by_selector(
        modeled_stories,
        label="modeled",
    )
    for metric in selection.modeled_metrics:
        story = modeled_by_metric.get(metric)
        if story is None:
            raise AtlasMediaError(f"modeled metric story is absent: {metric}")
        selected.append(
            _selected_story(story, countries=countries, source_authority=None)
        )
    ids = [story.story_id for story in selected]
    if len(ids) != len(set(ids)):
        raise AtlasMediaError("selected atlas media stories are not unique")
    if sum(len(story.frames) for story in selected) > 2_000:
        raise AtlasMediaError("selected atlas media frame inventory exceeds 2000")
    if (
        sum(
            len(story.frames) == 1
            and story.frames[0]["time_start_bp"] == story.frames[0]["time_end_bp"]
            for story in selected
        )
        > 1
    ):
        raise AtlasMediaError("only one exact-instant story may be selected")
    return tuple(selected)


def _stories_by_selector(
    stories: tuple[Mapping[str, object], ...], *, label: str
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for story in stories:
        selector = _mapping(story.get("selector"), "story.selector")
        value = _text(selector, "value")
        if value in indexed:
            raise AtlasMediaError(f"duplicate {label} story selector: {value}")
        indexed[value] = story
    return indexed


def _selected_story(
    story: Mapping[str, object],
    *,
    countries: tuple[str, ...],
    source_authority: SourceChronologyAuthority | None,
) -> SelectedStory:
    evidence_role = _text(story, "evidence_role")
    selector = _mapping(story.get("selector"), "story.selector")
    selector_kind = _text(selector, "kind")
    selector_value = _text(selector, "value")
    selector_family_value = selector.get("family")
    if selector_family_value is not None and (
        not isinstance(selector_family_value, str) or not selector_family_value.strip()
    ):
        raise AtlasMediaError("story selector family must be null or non-empty")
    selector_family = cast("str | None", selector_family_value)
    if (
        story.get("temporal_direction") != "oldest_to_present"
        or story.get("interval_semantics") != "[younger_bp, older_bp]"
        or story.get("interpolation_allowed") is not False
        or story.get("propagation_claim_allowed") is not False
        or story.get("edge_count") != 0
        or story.get("countries") != list(countries)
    ):
        raise AtlasMediaError("selected story violates scientific playback posture")
    frames = _object_rows(story.get("frames"), "story frames")
    if story.get("frame_count") != len(frames):
        raise AtlasMediaError("story frame denominator differs")
    normalized: list[dict[str, object]] = []
    previous_younger: float | int | None = None
    for ordinal, frame in enumerate(frames):
        if frame.get("ordinal") != ordinal:
            raise AtlasMediaError("story frame ordinals are not contiguous")
        younger = _number(frame, "time_start_bp")
        older = _number(frame, "time_end_bp")
        if younger > older:
            raise AtlasMediaError("story frame has a reversed BP interval")
        if previous_younger is not None and older != previous_younger:
            raise AtlasMediaError(
                "story frames must be exactly continuous from oldest to present"
            )
        previous_younger = younger
        if frame.get("basemap") != "none" or frame.get("countries") != list(countries):
            raise AtlasMediaError("story frame lacks deterministic capture state")
        expected_kind = (
            "source_chronology"
            if evidence_role == "observation_chronology"
            else "modeled_context"
        )
        if frame.get("story_kind") != expected_kind:
            raise AtlasMediaError("story frame kind differs from its evidence role")
        _validate_frame_selector(frame, story_kind=expected_kind)
        normalized.append(dict(frame))
    authority_facet = (
        source_authority.require(selector_kind, selector_value)
        if evidence_role == "observation_chronology" and source_authority is not None
        else None
    )
    if evidence_role == "observation_chronology" and authority_facet is None:
        raise AtlasMediaError(
            "source story selection requires governed atlas authority"
        )
    if evidence_role == "observation_chronology":
        _positive_int(story, "node_count")
        _positive_int(story, "observation_denominator")
    if authority_facet is not None and (
        story.get("node_count") != authority_facet.node_count
        or story.get("observation_denominator")
        != authority_facet.observation_denominator
    ):
        raise AtlasMediaError(
            "source story denominators differ from governed atlas assets"
        )
    return SelectedStory(
        story_id=_text(story, "story_id"),
        title=_text(story, "title"),
        evidence_role=evidence_role,
        selector_kind=selector_kind,
        selector_value=selector_value,
        selector_family=selector_family,
        node_count=(
            _positive_int(story, "node_count")
            if evidence_role == "observation_chronology"
            else cast("int | None", story.get("node_count"))
        ),
        observation_denominator=(
            _positive_int(story, "observation_denominator")
            if evidence_role == "observation_chronology"
            else cast("int | None", story.get("observation_denominator"))
        ),
        frame_feature_denominators=(
            tuple(_positive_int(frame, "feature_count") for frame in frames)
            if evidence_role == "modeled_context"
            else None
        ),
        expected_visible_feature_counts=(
            tuple(
                authority_facet.visible_count(
                    cast("float | int", frame["time_start_bp"]),
                    cast("float | int", frame["time_end_bp"]),
                )
                for frame in normalized
            )
            if authority_facet is not None
            else None
        ),
        source_authority_sha256=(
            source_authority.digest
            if authority_facet is not None and source_authority is not None
            else None
        ),
        frames=tuple(normalized),
    )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AtlasMediaError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _validate_frame_selector(frame: Mapping[str, object], *, story_kind: str) -> None:
    if story_kind == "modeled_context":
        for field in ("source_window_label", "metric_family_key", "metric_key"):
            _text(frame, field)
        return
    level = _text(frame, "source_level")
    if level not in {
        "source_sample_presence",
        "source_ecological_code",
        "source_taxon",
    }:
        raise AtlasMediaError("source chronology frame level is unsupported")
    if level == "source_ecological_code":
        _text(frame, "source_code")
    elif level == "source_taxon":
        _text(frame, "source_taxon")


def _object_rows(value: object, label: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise AtlasMediaError(f"{label} must be an array")
    rows: list[Mapping[str, object]] = []
    for row in value:
        rows.append(_mapping(row, label))
    return tuple(rows)


def _text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AtlasMediaError(f"{field} must be a non-empty string")
    return value


def _positive_int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AtlasMediaError(f"{field} must be a positive integer")
    return value


def _number(row: Mapping[str, object], field: str) -> float | int:
    value = row.get(field)
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise AtlasMediaError(f"{field} must be a non-negative number")
    return value


def _exact_taxon_story(
    facet: Mapping[str, object], *, countries: tuple[str, ...]
) -> dict[str, object]:
    feature_key = _text(facet, "feature_key")
    taxon_id = _text(facet, "source_taxon_id")
    label = _text(facet, "label")
    younger = _number(facet, "time_start_bp")
    older = _number(facet, "time_end_bp")
    if younger > older:
        raise AtlasMediaError("exact taxon discovery interval is reversed")
    frames: list[dict[str, object]] = []
    frame_older = older
    while frame_older > younger:
        frame_younger = max(younger, frame_older - 100)
        frames.append(
            _taxon_frame(
                ordinal=len(frames),
                feature_key=feature_key,
                younger=frame_younger,
                older=frame_older,
                countries=countries,
            )
        )
        frame_older = frame_younger
    if not frames:
        frames.append(
            _taxon_frame(
                ordinal=0,
                feature_key=feature_key,
                younger=younger,
                older=older,
                countries=countries,
            )
        )
    return {
        "story_id": f"neotoma-source-taxon-{taxon_id}",
        "title": f"Neotoma exact source taxon — {label}",
        "dataset_id": "neotoma",
        "evidence_role": "observation_chronology",
        "countries": list(countries),
        "selector": {
            "kind": "source_taxon",
            "value": feature_key,
            "family": None,
        },
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "interpolation_allowed": False,
        "propagation_claim_allowed": False,
        "edge_count": 0,
        "node_count": _positive_int(facet, "node_count"),
        "observation_denominator": _positive_int(facet, "observation_denominator"),
        "frame_count": len(frames),
        "frames": frames,
    }


def _taxon_frame(
    *,
    ordinal: int,
    feature_key: str,
    younger: float | int,
    older: float | int,
    countries: tuple[str, ...],
) -> dict[str, object]:
    label = f"{younger:g} BP" if younger == older else f"{younger:g}–{older:g} BP"
    return {
        "ordinal": ordinal,
        "time_start_bp": younger,
        "time_end_bp": older,
        "label": label,
        "source_window_label": None,
        "feature_count": None,
        "basemap": "none",
        "countries": list(countries),
        "story_kind": "source_chronology",
        "source_level": "source_taxon",
        "source_taxon": feature_key,
    }


def _canonical_storyboard_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


__all__ = ["load_storyboard_manifest", "select_stories"]
