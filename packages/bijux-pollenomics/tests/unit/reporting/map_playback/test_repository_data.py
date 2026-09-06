"""Committed-data proof for playback discovery and frame accounting."""

from __future__ import annotations

import json
import math
from pathlib import Path

from bijux_pollenomics.reporting.context.points import build_external_point_layer
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from bijux_pollenomics.reporting.map_playback import (
    build_exact_taxon_storyboard,
    build_source_chronology_storyboards,
)

from tests.unit.reporting.map_playback.support import NORDIC_COUNTRIES

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]


def test_committed_neotoma_projection_builds_complete_real_story_inventory() -> None:
    source_path = (
        REPOSITORY_ROOT / "data/neotoma/normalized/nordic_pollen_sites.geojson"
    )
    base_layer = build_external_point_layer(
        json.loads(source_path.read_text(encoding="utf-8")),
        source_path=source_path,
    )
    _details, _accounting, layers = _project_neotoma(
        REPOSITORY_ROOT / "data", base_layer
    )

    stories, exact_taxa = build_source_chronology_storyboards(
        layers,
        countries=NORDIC_COUNTRIES,
    )
    frame_counts = {story.selector_value: len(story.frames) for story in stories}
    assert frame_counts == {"all": 230, "TRSH": 230, "UPHE": 230, "AQVP": 192}
    assert len(exact_taxa) == 972
    assert len({taxon.feature_key for taxon in exact_taxa}) == 972

    fractional = next(
        taxon
        for taxon in exact_taxa
        if taxon.younger_bp != taxon.older_bp
        and (
            not float(taxon.younger_bp).is_integer()
            or not float(taxon.older_bp).is_integer()
        )
    )
    selected = build_exact_taxon_storyboard(
        fractional,
        countries=NORDIC_COUNTRIES,
    )
    assert len(selected.frames) == math.ceil(
        (fractional.older_bp - fractional.younger_bp) / 100
    )
    assert selected.frames[0].older_bp == fractional.older_bp
    assert selected.frames[-1].younger_bp == fractional.younger_bp
    serialized = selected.as_dict()["frames"]
    assert isinstance(serialized, list)
    assert serialized[0]["source_taxon"] == fractional.feature_key
    assert serialized[0]["countries"] == list(NORDIC_COUNTRIES)
    assert serialized[0]["time_end_bp"] == fractional.older_bp
    assert serialized[-1]["time_start_bp"] == fractional.younger_bp

    exact_instants = [
        taxon for taxon in exact_taxa if taxon.younger_bp == taxon.older_bp
    ]
    assert len(exact_instants) == 100
    instant_story = build_exact_taxon_storyboard(
        exact_instants[0],
        countries=NORDIC_COUNTRIES,
    )
    instant_frames = instant_story.as_dict()["frames"]
    assert isinstance(instant_frames, list)
    assert len(instant_frames) == 1
    assert instant_frames[0]["time_start_bp"] == instant_frames[0]["time_end_bp"]
