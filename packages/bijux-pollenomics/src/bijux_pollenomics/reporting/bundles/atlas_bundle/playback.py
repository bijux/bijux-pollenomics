"""Governed playback-storyboard publication for the Nordic atlas."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ...map_playback import (
    build_modeled_context_storyboards,
    build_playback_manifest,
    build_source_chronology_storyboards,
    refuse_candidate_succession_storyboard,
)
from ...modeled_context import build_modeled_context_manifest


def publish_playback_storyboards(
    *,
    scope_key: str,
    countries: tuple[str, ...],
    bundle_paths: Any,
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    static_assets: Any,
    extra_artifacts: list[tuple[str, str]],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    """Publish exact chronology stories only where both Nordic inputs are governed."""
    if scope_key != "nordic":
        return

    if not any(
        layer.get("semantic_role") == "source_chronology_context"
        for layer in point_layers
    ):
        return

    canonical_countries = tuple(sorted(countries))
    source_chronology = build_source_chronology_storyboards(
        point_layers,
        countries=canonical_countries,
    )
    if not source_chronology.stories:
        return
    modeled_stories = build_modeled_context_storyboards(
        build_modeled_context_manifest(polygon_layers),
        countries=canonical_countries,
    )
    static_manifest = cast(dict[str, object], static_assets.manifest)
    domains = _required_mapping(static_manifest, "domains")
    classifications = _required_mapping(domains, "classifications")
    edges = _required_mapping(domains, "edges")
    reason_code = classifications.get("reason_code")
    if classifications.get("status") != "unavailable" or not isinstance(
        reason_code, str
    ):
        raise ValueError(
            "candidate-succession playback requires explicit unavailable "
            "classification evidence"
        )
    if edges.get("record_count") != 0:
        raise ValueError(
            "candidate-succession playback cannot ignore governed atlas edges"
        )

    manifest = build_playback_manifest(
        source_chronology=source_chronology,
        modeled_stories=modeled_stories,
        candidate_succession=refuse_candidate_succession_storyboard(
            {
                "propagation_status": "refused",
                "edge_count": 0,
                "reason_code": reason_code,
            }
        ),
        atlas_build_id=_required_text(static_manifest, "build_id"),
        scope_slug=_required_text(static_manifest, "scope_slug"),
        version=_required_text(static_manifest, "version"),
        countries=canonical_countries,
    )
    write_summary_json_fn(bundle_paths.playback_storyboards_path, manifest)
    extra_artifacts.append(
        (
            "Governed oldest-to-present playback storyboards",
            bundle_paths.playback_storyboards_path.name,
        )
    )


def _required_mapping(value: dict[str, object], field: str) -> dict[str, object]:
    candidate = value.get(field)
    if not isinstance(candidate, dict):
        raise ValueError(f"static atlas {field} contract is unavailable")
    return candidate


def _required_text(value: dict[str, object], field: str) -> str:
    candidate = value.get(field)
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError(f"static atlas {field} identity is unavailable")
    return candidate


__all__ = ["publish_playback_storyboards"]
