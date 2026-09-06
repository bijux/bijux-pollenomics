"""Exact-window playback stories for pinned PANGAEA modeled context."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import cast

from bijux_pollenomics.core.text import slugify

from .contracts import PlaybackContractError, PlaybackFrame, PlaybackStory

_STORY_ID = re.compile(r"[a-z][a-z0-9-]*")


def build_modeled_context_storyboards(
    modeled_manifest: Mapping[str, object],
    *,
    countries: tuple[str, ...],
) -> tuple[PlaybackStory, ...]:
    """Build one non-interpolated 25-window story for every source metric."""
    if (
        modeled_manifest.get("schema_version") != "modeled-context-manifest.v3"
        or modeled_manifest.get("status") != "available"
        or modeled_manifest.get("evidence_role") != "context_only"
        or modeled_manifest.get("propagation_use_allowed") is not False
        or modeled_manifest.get("interpolation_allowed") is not False
    ):
        raise PlaybackContractError(
            "modeled context is unavailable or lacks its fail-closed posture"
        )
    dataset_id = _required_text(modeled_manifest, "dataset_id")
    frames = _exact_source_frames(modeled_manifest.get("windows_oldest_to_present"))
    metrics = _source_metrics(modeled_manifest.get("metric_families"))
    if modeled_manifest.get("metric_count") != len(metrics):
        raise PlaybackContractError("modeled metric denominator does not reconcile")
    story_ids = tuple(
        _modeled_story_id(dataset_id, metric_key)
        for _family_key, metric_key, _label in metrics
    )
    if len(story_ids) != len(set(story_ids)):
        raise PlaybackContractError("modeled metric story identifiers collide")
    return tuple(
        PlaybackStory(
            story_id=story_id,
            title=f"PANGAEA {dataset_id} modeled context — {label}",
            dataset_id=dataset_id,
            evidence_role="modeled_context",
            selector_kind="modeled_metric",
            selector_value=metric_key,
            frames=frames,
            countries=countries,
            selector_family=family_key,
        )
        for (family_key, metric_key, label), story_id in zip(
            metrics, story_ids, strict=True
        )
    )


def _modeled_story_id(dataset_id: str, metric_key: str) -> str:
    story_id = f"pangaea-{slugify(dataset_id)}-metric-{slugify(metric_key)}"
    if _STORY_ID.fullmatch(story_id) is None:
        raise PlaybackContractError("modeled metric story identifier is unsafe")
    return story_id


def _exact_source_frames(value: object) -> tuple[PlaybackFrame, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PlaybackContractError("modeled context windows must be a sequence")
    frames: list[PlaybackFrame] = []
    seen_labels: set[str] = set()
    for ordinal, candidate in enumerate(value):
        if not isinstance(candidate, Mapping):
            raise PlaybackContractError("modeled context window must be an object")
        row = cast(Mapping[str, object], candidate)
        label = _required_text(row, "label")
        if label in seen_labels:
            raise PlaybackContractError(f"duplicate modeled source window: {label}")
        seen_labels.add(label)
        younger = row.get("time_start_bp")
        older = row.get("time_end_bp")
        feature_count = row.get("feature_count")
        no_pollen_data_count = row.get("no_pollen_data_count")
        frames.append(
            PlaybackFrame(
                ordinal=ordinal,
                younger_bp=cast("float | int", younger),
                older_bp=cast("float | int", older),
                label=label,
                source_window_label=label,
                feature_count=cast("int | None", feature_count),
                no_pollen_data_count=cast("int | None", no_pollen_data_count),
            )
        )
    if len(frames) != 25:
        raise PlaybackContractError(
            "PANGAEA 937075 playback requires all 25 exact source windows"
        )
    for older, newer in zip(frames, frames[1:], strict=False):
        if older.younger_bp != newer.older_bp:
            raise PlaybackContractError(
                "modeled context windows must retain exact source adjacency"
            )
    return tuple(frames)


def _source_metrics(value: object) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PlaybackContractError("modeled metric families must be a sequence")
    metrics: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for candidate_family in value:
        if not isinstance(candidate_family, Mapping):
            raise PlaybackContractError("modeled metric family must be an object")
        family = cast(Mapping[str, object], candidate_family)
        family_key = _required_text(family, "key")
        family_metrics = family.get("metrics")
        if not isinstance(family_metrics, Sequence) or isinstance(
            family_metrics, (str, bytes)
        ):
            raise PlaybackContractError("modeled metric family lacks metric rows")
        if family.get("metric_count") != len(family_metrics):
            raise PlaybackContractError("modeled metric-family denominator differs")
        for candidate_metric in family_metrics:
            if not isinstance(candidate_metric, Mapping):
                raise PlaybackContractError("modeled metric must be an object")
            metric = cast(Mapping[str, object], candidate_metric)
            key = _required_text(metric, "key")
            if key in seen:
                raise PlaybackContractError(f"duplicate modeled metric: {key}")
            seen.add(key)
            metrics.append((family_key, key, _required_text(metric, "label")))
    if not metrics:
        raise PlaybackContractError("modeled metric inventory is empty")
    return tuple(metrics)


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PlaybackContractError(f"modeled context {field} must not be empty")
    return value


__all__ = ["build_modeled_context_storyboards"]
