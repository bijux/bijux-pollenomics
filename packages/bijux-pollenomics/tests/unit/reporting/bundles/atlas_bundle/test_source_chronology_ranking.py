"""Candidate-only isolation for source chronology display facets."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis import (
    build_ranking_sensitivity_report,
    rank_localities,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.evidence import build_scientific_review_surface
from bijux_pollenomics.reporting.bundles import atlas_bundle
from bijux_pollenomics.reporting.bundles.atlas_bundle.evidence import (
    publish_evidence_and_rankings,
)
from bijux_pollenomics.reporting.bundles.atlas_bundle.ranking_context import (
    candidate_ranking_context_points,
)
from tests.unit.evidence.scientific_review.support import locality
from tests.unit.reporting.source_chronology.support import projection


class _OutputPath:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = path.name

    def write_text(self, value: str, *, encoding: str) -> None:
        del value, encoding


def _bundle_paths(tmp_path: Path) -> SimpleNamespace:
    names = (
        "evidence_surface_json_path",
        "evidence_surface_markdown_path",
        "scientific_review_json_path",
        "scientific_review_markdown_path",
        "candidate_sites_csv_path",
        "candidate_sites_json_path",
        "candidate_sites_markdown_path",
        "candidate_site_sensitivity_json_path",
        "candidate_site_sensitivity_markdown_path",
        "candidate_ranking_engine_manifest_path",
    )
    return SimpleNamespace(
        **{name: _OutputPath(tmp_path / f"{name}.txt") for name in names}
    )


def _ordinary_layer() -> dict[str, object]:
    return {
        "key": "ordinary-context",
        "label": "Ordinary context",
        "source_name": "Context",
        "count": 1,
        "features": [
            {
                "title": "ordinary",
                "latitude": 59.0,
                "longitude": 18.0,
                "record_count": 1,
            }
        ],
    }


def test_canonical_source_projection_is_excluded_only_from_candidate_inputs() -> None:
    _, source_projection = projection()
    source_layers = [dict(layer) for layer in source_projection.point_layers]
    ordinary = _ordinary_layer()
    baseline = atlas_bundle._extract_context_points([ordinary])
    general = atlas_bundle._extract_context_points([ordinary, *source_layers])

    assert len(general) == len(baseline) + 3
    assert {
        point.layer_key
        for point in general
        if point.layer_key.startswith("neotoma-source-")
    } == {
        "neotoma-source-sample-pollen-context",
        "neotoma-source-ecological-code",
        "neotoma-source-exact-taxon",
    }
    assert (
        candidate_ranking_context_points([ordinary, *source_layers], general)
        == baseline
    )
    ranking_points = candidate_ranking_context_points(
        [ordinary, *source_layers], general
    )
    localities = (locality(),)
    assert rank_localities(localities, ranking_points) == rank_localities(
        localities, baseline
    )
    assert (
        build_ranking_sensitivity_report(localities, ranking_points).as_dict()
        == build_ranking_sensitivity_report(localities, baseline).as_dict()
    )

    scientific_review = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=localities,
        context_points=general,
        include_tracked_nonhuman_review=False,
    )
    chronology_layers = {
        row.context_layer_key
        for row in scientific_review.chronology_overlaps
        if row.context_layer_key.startswith("neotoma-source-")
    }
    assert chronology_layers == {
        "neotoma-source-sample-pollen-context",
        "neotoma-source-ecological-code",
        "neotoma-source-exact-taxon",
    }


def test_publication_retains_source_chronology_for_review_but_not_ranking(
    tmp_path: Path,
) -> None:
    _, source_projection = projection()
    source_layers = [dict(layer) for layer in source_projection.point_layers]
    captured: dict[str, tuple[ContextPointRecord, ...]] = {}

    def capture(name: str, context_points: tuple[ContextPointRecord, ...]) -> object:
        captured[name] = context_points
        return SimpleNamespace(as_dict=dict)

    surface = SimpleNamespace(
        ContextPointRecord=ContextPointRecord,
        json=SimpleNamespace(dumps=lambda value, indent: "{}"),
        summarize_localities=lambda samples: (),
        _extract_context_points=atlas_bundle._extract_context_points,
        build_atlas_evidence_surface=lambda **kwargs: capture(
            "evidence", kwargs["context_points"]
        ),
        build_scientific_review_surface=lambda **kwargs: capture(
            "scientific_review", kwargs["context_points"]
        ),
        rank_localities=lambda localities, context_points, **kwargs: (
            capture("ranking", context_points) and []
        ),
        build_ranking_sensitivity_report=lambda localities, context_points: capture(
            "sensitivity", context_points
        ),
        build_ranking_engine_manifest=lambda: SimpleNamespace(as_dict=dict),
        write_atlas_evidence_surface_json=lambda *args: None,
        render_atlas_evidence_surface_markdown=lambda value: "",
        write_scientific_review_surface_json=lambda *args: None,
        render_scientific_review_surface_markdown=lambda value: "",
        write_candidate_sites_csv=lambda *args: None,
        write_candidate_sites_json=lambda *args: None,
        render_candidate_site_markdown=lambda *args, **kwargs: "",
        write_candidate_site_sensitivity_json=lambda *args: None,
        render_candidate_site_sensitivity_markdown=lambda *args, **kwargs: "",
    )

    publish_evidence_and_rankings(
        title="Atlas",
        countries=("Sweden",),
        all_samples=(),
        context_root=Path("data"),
        bundle_paths=_bundle_paths(tmp_path),
        point_layers=source_layers,
        animal_localities=(),
        animal_coordinate_review=object(),
        extra_artifacts=[],
        surface=surface,
    )

    assert len(captured["evidence"]) == 3
    assert captured["scientific_review"] == captured["evidence"]
    assert captured["ranking"] == ()
    assert captured["sensitivity"] == ()


@pytest.mark.parametrize(
    "field,value",
    (
        ("propagation_status", "available"),
        ("edge_count", 1),
        ("edge_count", False),
        ("count", True),
        ("semantic_role", None),
    ),
)
def test_source_chronology_candidate_filter_fails_closed(
    field: str, value: object
) -> None:
    _, source_projection = projection()
    layers = [dict(layer) for layer in source_projection.point_layers]
    if value is None:
        layers[0].pop(field)
    else:
        layers[0][field] = value
    general = atlas_bundle._extract_context_points(
        [dict(layer) for layer in source_projection.point_layers]
    )

    with pytest.raises(ValueError, match="source chronology candidate-ranking"):
        candidate_ranking_context_points(layers, general)


@pytest.mark.parametrize(
    "reason",
    (
        "unknown_refusal",
        "source_taxon_equivalence_not_reviewed",
    ),
)
def test_source_chronology_candidate_filter_requires_exact_refusal_reason(
    reason: str,
) -> None:
    _, source_projection = projection()
    layers = [dict(layer) for layer in source_projection.point_layers]
    raw_features = layers[0]["features"]
    assert isinstance(raw_features, list)
    features = [dict(feature) for feature in raw_features if isinstance(feature, dict)]
    features[0]["candidate_refusal_reason"] = reason
    layers[0]["features"] = features
    general = atlas_bundle._extract_context_points(
        [dict(layer) for layer in source_projection.point_layers]
    )

    with pytest.raises(ValueError, match="feature posture differs"):
        candidate_ranking_context_points(layers, general)


def test_source_chronology_feature_marker_prevents_coordinated_layer_disguise() -> None:
    _, source_projection = projection()
    layers = [dict(layer) for layer in source_projection.point_layers]
    layers[0]["semantic_role"] = "ordinary_context"
    layers[0]["key"] = "ordinary-context"
    layers[0]["node_level"] = "ordinary"
    general = atlas_bundle._extract_context_points(
        [dict(layer) for layer in source_projection.point_layers]
    )

    with pytest.raises(ValueError, match="candidate-ranking posture differs"):
        candidate_ranking_context_points(layers, general)
