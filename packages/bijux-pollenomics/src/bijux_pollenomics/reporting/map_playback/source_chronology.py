"""Playback stories for literal Neotoma source chronology."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import cast

from bijux_pollenomics.reporting.source_chronology.time_density import (
    time_density_matches_facet,
)

from .contracts import (
    ExactTaxonDiscovery,
    PlaybackContractError,
    PlaybackFrame,
    PlaybackStory,
    SelectorKind,
)

SOURCE_PLAYBACK_CODES = ("TRSH", "UPHE", "AQVP")
SOURCE_FRAME_WIDTH_BP = 100


def build_source_chronology_storyboards(
    point_layers: Sequence[Mapping[str, object]],
    *,
    countries: tuple[str, ...],
) -> tuple[tuple[PlaybackStory, ...], tuple[ExactTaxonDiscovery, ...]]:
    """Build four core stories and the complete exact-taxon discovery index."""
    layers = {
        str(layer.get("node_level")): layer
        for layer in point_layers
        if layer.get("semantic_role") == "source_chronology_context"
    }
    required_levels = {
        "source_sample_presence",
        "source_ecological_code",
        "source_taxon",
    }
    if set(layers) != required_levels:
        raise PlaybackContractError(
            "source chronology playback requires the three canonical node levels"
        )
    for layer in layers.values():
        _validate_refused_source_layer(layer)

    facets_by_level = {
        level: _facet_metadata(layer, level) for level, layer in layers.items()
    }
    if all(_is_explicit_empty_facet(facet) for facet in facets_by_level.values()):
        return (), ()

    sample_facets = facets_by_level["source_sample_presence"]
    stories = [
        _source_story(
            story_id="neotoma-source-sample-presence",
            title="Neotoma source sample presence",
            selector_kind="source_sample_presence",
            selector_value="all",
            facet=sample_facets,
            countries=countries,
        )
    ]

    code_facets = facets_by_level["source_ecological_code"]
    code_rows = _rows_by_value(code_facets.get("source_ecological_codes"))
    missing_codes = [code for code in SOURCE_PLAYBACK_CODES if code not in code_rows]
    if missing_codes:
        raise PlaybackContractError(
            "source chronology playback is missing required literal codes: "
            + ", ".join(missing_codes)
        )
    for code in SOURCE_PLAYBACK_CODES:
        row = code_rows[code]
        _validate_facet_density(row)
        label = _required_text(row, "label")
        stories.append(
            _source_story(
                story_id=f"neotoma-source-code-{code.casefold()}",
                title=f"Neotoma {code} — {label}",
                selector_kind="source_ecological_code",
                selector_value=code,
                facet=row,
                countries=countries,
            )
        )

    taxon_facets = facets_by_level["source_taxon"]
    taxa = _exact_taxa(taxon_facets.get("source_taxa"))
    return tuple(stories), taxa


def build_exact_taxon_storyboard(
    taxon: ExactTaxonDiscovery,
    *,
    countries: tuple[str, ...],
) -> PlaybackStory:
    """Materialize one explicitly selected exact source taxon, never the bulk index."""
    return PlaybackStory(
        story_id=f"neotoma-source-taxon-{taxon.source_taxon_id}",
        title=f"Neotoma exact source taxon — {taxon.label}",
        dataset_id="neotoma",
        evidence_role="observation_chronology",
        selector_kind="source_taxon",
        selector_value=taxon.feature_key,
        frames=_partition_oldest_to_present(
            taxon.younger_bp,
            taxon.older_bp,
            width_bp=SOURCE_FRAME_WIDTH_BP,
        ),
        countries=countries,
        node_count=taxon.node_count,
        observation_denominator=taxon.observation_denominator,
    )


def _validate_refused_source_layer(layer: Mapping[str, object]) -> None:
    if (
        layer.get("propagation_status") != "refused"
        or layer.get("edge_count") != 0
        or layer.get("temporal_direction") != "oldest_to_present"
        or layer.get("interval_semantics") != "[younger_bp, older_bp]"
    ):
        raise PlaybackContractError(
            "source chronology layer cannot be promoted to propagation playback"
        )


def _facet_metadata(
    layer: Mapping[str, object], expected_level: str
) -> Mapping[str, object]:
    facets = layer.get("facet_metadata")
    if not isinstance(facets, Mapping):
        raise PlaybackContractError("source chronology layer lacks facet metadata")
    if (
        facets.get("schema_version") != "neotoma-source-chronology-facets.v3"
        or facets.get("node_level") != expected_level
    ):
        raise PlaybackContractError("source chronology facet contract is incompatible")
    if not time_density_matches_facet(facets.get("time_density"), facets):
        raise PlaybackContractError("source chronology time density is incompatible")
    return cast(Mapping[str, object], facets)


def _is_explicit_empty_facet(facet: Mapping[str, object]) -> bool:
    return (
        facet.get("node_count") == 0
        and facet.get("observation_denominator") == 0
        and facet.get("time_min_bp") is None
        and facet.get("time_max_bp") is None
    )


def _source_story(
    *,
    story_id: str,
    title: str,
    selector_kind: SelectorKind,
    selector_value: str,
    facet: Mapping[str, object],
    countries: tuple[str, ...],
) -> PlaybackStory:
    younger_bp, older_bp = _closed_interval(facet)
    frames = _partition_oldest_to_present(
        younger_bp,
        older_bp,
        width_bp=SOURCE_FRAME_WIDTH_BP,
    )
    return PlaybackStory(
        story_id=story_id,
        title=title,
        dataset_id="neotoma",
        evidence_role="observation_chronology",
        selector_kind=selector_kind,
        selector_value=selector_value,
        frames=frames,
        countries=countries,
        node_count=_positive_int(facet, "node_count"),
        observation_denominator=_positive_int(facet, "observation_denominator"),
    )


def _partition_oldest_to_present(
    younger_bp: float,
    older_bp: float,
    *,
    width_bp: int,
) -> tuple[PlaybackFrame, ...]:
    if isinstance(width_bp, bool) or width_bp <= 0:
        raise PlaybackContractError("source frame width must be a positive integer")
    if younger_bp == older_bp:
        return (
            PlaybackFrame(
                ordinal=0,
                younger_bp=younger_bp,
                older_bp=older_bp,
                label=f"{younger_bp:g} BP",
            ),
        )
    frame_count = math.ceil((older_bp - younger_bp) / width_bp)
    frames: list[PlaybackFrame] = []
    frame_older = older_bp
    for ordinal in range(frame_count):
        frame_younger = max(younger_bp, frame_older - width_bp)
        frames.append(
            PlaybackFrame(
                ordinal=ordinal,
                younger_bp=frame_younger,
                older_bp=frame_older,
                label=f"{frame_younger:g}–{frame_older:g} BP",
            )
        )
        frame_older = frame_younger
    return tuple(frames)


def _closed_interval(row: Mapping[str, object]) -> tuple[float | int, float | int]:
    younger = row.get("time_min_bp")
    older = row.get("time_max_bp")
    if (
        isinstance(younger, bool)
        or not isinstance(younger, (float, int))
        or isinstance(older, bool)
        or not isinstance(older, (float, int))
        or not math.isfinite(float(younger))
        or not math.isfinite(float(older))
        or younger < 0
        or younger > older
    ):
        raise PlaybackContractError(
            "source chronology facet lacks a valid [younger_bp, older_bp] extent"
        )
    return younger, older


def _rows_by_value(value: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PlaybackContractError("source chronology facet rows must be a sequence")
    rows: dict[str, Mapping[str, object]] = {}
    for candidate in value:
        if not isinstance(candidate, Mapping):
            raise PlaybackContractError("source chronology facet row must be an object")
        row = cast(Mapping[str, object], candidate)
        key = _required_text(row, "value")
        if key in rows:
            raise PlaybackContractError(f"duplicate source chronology facet: {key}")
        rows[key] = row
    return rows


def _exact_taxa(value: object) -> tuple[ExactTaxonDiscovery, ...]:
    rows = _rows_by_value(value)
    for row in rows.values():
        _validate_facet_density(row)
    taxa = tuple(
        ExactTaxonDiscovery(
            feature_key=feature_key,
            source_taxon_id=_required_text(row, "source_taxon_id"),
            label=_required_text(row, "label"),
            node_count=_positive_int(row, "node_count"),
            observation_denominator=_positive_int(row, "observation_denominator"),
            younger_bp=_closed_interval(row)[0],
            older_bp=_closed_interval(row)[1],
        )
        for feature_key, row in sorted(
            rows.items(),
            key=lambda item: (
                _required_text(item[1], "label").casefold(),
                _required_text(item[1], "source_taxon_id"),
                item[0],
            ),
        )
    )
    if not taxa:
        raise PlaybackContractError("exact source taxon discovery index is empty")
    return taxa


def _validate_facet_density(row: Mapping[str, object]) -> None:
    if not time_density_matches_facet(row.get("time_density"), row):
        raise PlaybackContractError("source chronology facet density is incompatible")


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PlaybackContractError(f"source chronology {field} must not be empty")
    return value


def _positive_int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PlaybackContractError(f"source chronology {field} must be positive")
    return value


__all__ = [
    "SOURCE_FRAME_WIDTH_BP",
    "SOURCE_PLAYBACK_CODES",
    "build_exact_taxon_storyboard",
    "build_source_chronology_storyboards",
]
