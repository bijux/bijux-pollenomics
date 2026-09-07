"""Animal source chronology integration and analytical-isolation contracts."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.analysis import (
    build_ranking_sensitivity_report,
    rank_localities,
)
from bijux_pollenomics.reporting.adna import build_animal_sample_chronology_context
from bijux_pollenomics.reporting.bundles import atlas_bundle
from bijux_pollenomics.reporting.bundles.atlas_bundle import contracts
from bijux_pollenomics.reporting.bundles.atlas_bundle.contracts import publish_contracts
from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers
from bijux_pollenomics.reporting.map_document.static_assets import (
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_playback import (
    build_source_chronology_storyboards,
)
from tests.unit.reporting.map_playback.support import source_layers
from tests.support.repository import REPOSITORY_ROOT


def _animal_chronology_layer() -> dict[str, object]:
    return {
        "key": "animal-source-chronology",
        "label": "Animal source chronology",
        "source_name": "Governed animal sample evidence",
        "description": "Source-native sample chronology for display.",
        "group": "animal-chronology-context",
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "default_enabled": False,
        "applies_time_filter": True,
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "features": [
            {
                "title": "sample-1",
                "subtitle": "Bos taurus",
                "country": "Sweden",
                "latitude": 59.3,
                "longitude": 18.1,
                "time_start_bp": 900,
                "time_end_bp": 1100,
                "time_mean_bp": 1000,
                "record_count": 1,
            }
        ],
    }


def _ordinary_context_layer() -> dict[str, object]:
    return {
        "key": "ordinary-context",
        "label": "Ordinary context",
        "source_name": "Context source",
        "features": [
            {
                "title": "context-1",
                "subtitle": "Archaeology",
                "country": "Sweden",
                "latitude": 59.4,
                "longitude": 18.2,
                "time_start_bp": 800,
                "time_end_bp": 1200,
                "record_count": 1,
            }
        ],
    }


def test_prepare_layers_publishes_default_disabled_animal_chronology_before_static_assets(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "atlas-map-assets.json"
    bundle_paths = SimpleNamespace(
        samples_geojson_path=tmp_path / "samples.geojson",
        map_static_assets_manifest_path=manifest_path,
    )
    static_assets = SimpleNamespace(manifest_path=manifest_path, asset_paths=())
    captured: dict[str, object] = {}
    calls: list[tuple[Path, object]] = []
    chronology_layer = _animal_chronology_layer()

    def build_animal_context(
        *, data_root: Path, geography_scope: object
    ) -> object:
        calls.append((data_root, geography_scope))
        return SimpleNamespace(
            point_layers=(chronology_layer,),
            accountability={"propagation_status": "refused", "edge_count": 0},
        )

    def write_static_assets(*args: object, **kwargs: object) -> object:
        captured.update(kwargs)
        return static_assets

    surface = SimpleNamespace(
        json=json,
        AnimalCoordinateVisibilityReview=SimpleNamespace,
        build_tracked_animal_atlas_bundle=lambda **kwargs: SimpleNamespace(
            point_layers=(),
            extra_artifacts=(),
            localities=(),
            coordinate_review=SimpleNamespace(
                direct_coordinate_feature_count=0,
                named_site_geocoded_feature_count=0,
                weaker_geography_feature_count=0,
            ),
        ),
        build_animal_sample_chronology_context=build_animal_context,
        build_sweden_lake_atlas_layers=lambda **kwargs: [],
        _attach_traceability_surfaces=lambda point_layers, paths: None,
        write_static_atlas_assets=write_static_assets,
    )
    context_root = tmp_path / "data"
    geography_scope = object()

    result = prepare_layers(
        tmp_path,
        report=SimpleNamespace(slug="atlas", output_dir=tmp_path),
        version="v66",
        all_samples=(),
        context_root=context_root,
        geography_scope=geography_scope,
        build_atlas_bundle_paths_fn=lambda **kwargs: bundle_paths,
        build_context_layers_fn=lambda **kwargs: ([], [], []),
        build_samples_geojson_fn=lambda samples: {
            "type": "FeatureCollection",
            "features": [],
        },
        atlas_detail_records=[],
        atlas_scientific_signals=None,
        atlas_edge_records=None,
        atlas_sequence_records=None,
        surface=surface,
    )

    written = cast(list[dict[str, object]], captured["point_layers"])
    assert calls == [(context_root, geography_scope)]
    assert written == [chronology_layer]
    assert result[1] == [chronology_layer]
    assert chronology_layer["default_enabled"] is False
    assert chronology_layer["applies_time_filter"] is True
    feature = cast(list[dict[str, object]], chronology_layer["features"])[0]
    assert (feature["time_start_bp"], feature["time_end_bp"]) == (900, 1100)


def test_animal_chronology_is_excluded_from_rankings_and_sensitivity() -> None:
    ordinary = _ordinary_context_layer()
    baseline = atlas_bundle._extract_context_points([ordinary])
    with_animal = atlas_bundle._extract_context_points(
        [ordinary, _animal_chronology_layer()]
    )

    assert with_animal == baseline
    assert rank_localities((), with_animal) == rank_localities((), baseline)
    assert (
        build_ranking_sensitivity_report((), with_animal).as_dict()
        == build_ranking_sensitivity_report((), baseline).as_dict()
    )


@pytest.mark.parametrize(
    "field,contradiction",
    (
        ("semantic_role", None),
        ("group", None),
        ("contribution_role", "analytical"),
        ("default_enabled", True),
        ("applies_time_filter", False),
        ("candidate_ranking_eligible", True),
        ("scientific_classification_eligible", True),
        ("scientific_selection_enabled", True),
        ("propagation_status", "available"),
        ("propagation_reason_code", ""),
        ("edge_count", 1),
    ),
)
def test_animal_chronology_extraction_fails_closed_on_missing_or_contradictory_posture(
    field: str,
    contradiction: object,
) -> None:
    layer = _animal_chronology_layer()
    if contradiction is None:
        layer.pop(field)
    else:
        layer[field] = contradiction

    with pytest.raises(ValueError, match="animal source chronology context posture"):
        atlas_bundle._extract_context_points([layer])


def test_animal_chronology_does_not_change_neotoma_playback_inventory() -> None:
    layers = source_layers()
    baseline = build_source_chronology_storyboards(
        layers,
        countries=("Denmark", "Finland", "Norway", "Sweden"),
    )
    extended = build_source_chronology_storyboards(
        [*layers, _animal_chronology_layer()],
        countries=("Denmark", "Finland", "Norway", "Sweden"),
    )

    assert extended == baseline
    assert len(extended.stories) == 9


def test_real_animal_chronology_projection_is_display_only_for_atlas_analysis() -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")

    assert projection.point_layers
    assert atlas_bundle._extract_context_points(list(projection.point_layers)) == ()
    assert all(layer["default_enabled"] is False for layer in projection.point_layers)
    assert all(layer["applies_time_filter"] is True for layer in projection.point_layers)


def test_real_animal_chronology_layers_link_the_accountability_artifact(
    tmp_path: Path,
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    layers = [dict(layer) for layer in projection.point_layers]
    artifact_path = tmp_path / "atlas_animal_sample_chronology_context.json"

    atlas_bundle._attach_traceability_surfaces(
        layers,
        SimpleNamespace(
            animal_sample_chronology_context_json_path=artifact_path,
            samples_geojson_path=tmp_path / "samples.geojson",
            animal_point_traceability_json_path=tmp_path / "animal-points.json",
        ),
    )

    assert all(
        layer["traceability_artifact"] == artifact_path.name for layer in layers
    )


def test_real_animal_chronology_is_time_indexed_as_ordinary_static_point_data(
    tmp_path: Path,
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    assets = write_static_atlas_assets(
        tmp_path,
        slug="animal-chronology",
        version="v66",
        point_layers=list(projection.point_layers),
        polygon_layers=[],
    )

    validate_static_atlas_assets(assets)
    rows = normalize_asset_inventory(assets.manifest["assets"])
    animal_node_rows = [
        row
        for row in rows
        if row.get("domain") == "nodes"
        and str(row["layer_key"]).startswith("animal-source-chronology-")
    ]
    assert animal_node_rows
    assert all(
        isinstance(row["time_min_bp"], (int, float))
        and not isinstance(row["time_min_bp"], bool)
        and isinstance(row["time_max_bp"], (int, float))
        and not isinstance(row["time_max_bp"], bool)
        for row in animal_node_rows
    )


def test_animal_chronology_accountability_is_identity_bound_in_atlas_contract(
    tmp_path: Path,
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    artifact_path = tmp_path / "atlas_animal_sample_chronology_context.json"
    contract_json_path = tmp_path / "map-contract.json"
    contract_markdown_path = tmp_path / "map-contract.md"
    written: dict[Path, dict[str, object]] = {}
    artifacts: list[tuple[str, str]] = []
    bundle_paths = SimpleNamespace(
        animal_sample_chronology_context_json_path=artifact_path,
        map_point_traceability_json_path=tmp_path / "traceability.json",
        map_point_traceability_markdown_path=tmp_path / "traceability.md",
        map_publication_contract_json_path=contract_json_path,
        map_publication_contract_markdown_path=contract_markdown_path,
        map_html_path=tmp_path / "map.html",
        summary_json_path=tmp_path / "summary.json",
    )
    surface = SimpleNamespace(
        resolve_map_scope_policy=lambda scope: {"scope": scope},
        build_map_point_traceability=lambda **kwargs: {},
        render_map_point_traceability_markdown=lambda payload: "traceability\n",
        build_map_publication_contract=lambda **kwargs: {},
        render_map_publication_contract_markdown=lambda payload: "contract\n",
    )

    _, contract = publish_contracts(
        report=object(),
        geography_scope=None,
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        point_layers=list(projection.point_layers),
        polygon_layers=[],
        bundle_paths=bundle_paths,
        detail_projection_reconciliation=None,
        static_assets=SimpleNamespace(
            manifest_path=tmp_path / "static.json",
            manifest={
                "schema_version": "atlas-map-static-assets.v1",
                "budgets": {},
                "domains": {},
            },
        ),
        animal_chronology_context=projection,
        extra_artifacts=artifacts,
        write_summary_json_fn=lambda path, payload: written.update({path: payload}),
        surface=surface,
    )

    payload = written[artifact_path]
    identity = cast(dict[str, object], contract["animal_sample_chronology_context"])
    assert payload["accountability"] == projection.accountability
    assert payload["input_identity"] == projection.input_identity.as_dict()
    assert payload["refusals"] == [row.as_dict() for row in projection.refusals]
    assert identity["content_sha256"] == payload["content_sha256"]
    assert identity["scope"] == projection.accountability["scope"]
    assert identity["global_admitted_node_count"] == projection.accountability[
        "global_admitted_node_count"
    ]
    assert identity["refusal_count"] == len(projection.refusals)
    assert identity["governed_country_rows"] == projection.accountability[
        "governed_country_rows"
    ]
    assert artifacts == [
        (
            "Animal source-sample chronology accountability",
            artifact_path.name,
        )
    ]


@pytest.mark.parametrize(
    "field,value,message",
    (
        ("input_identity", {}, "input identity differs"),
        ("refusal_count", -1, "refusal count differs"),
    ),
)
def test_animal_chronology_publication_refuses_accountability_drift(
    field: str,
    value: object,
    message: str,
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    accountability = dict(projection.accountability)
    accountability[field] = value
    contradictory = SimpleNamespace(
        accountability=accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
    )

    with pytest.raises(ValueError, match=message):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )
