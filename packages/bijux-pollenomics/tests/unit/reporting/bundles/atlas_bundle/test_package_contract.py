"""Compatibility and topology contract for atlas bundle publication."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.bundles import atlas_bundle
from bijux_pollenomics.reporting.bundles.atlas_bundle import (
    animal_chronology_publication,
)

EXPECTED_SIGNATURES = {
    "publish_multi_country_map_bundle": "(staging_output_dir: 'Path', *, report: 'MultiCountryMapReport', title: 'str', version: 'str', generated_on: 'str', countries: 'tuple[str, ...]', country_sample_counts: 'dict[str, int]', all_samples: 'tuple[SampleRecord, ...]', context_root: 'Path | None', geography_scope: 'GeographicScope | None', asset_base_path: 'str', build_atlas_bundle_paths_fn: 'Callable[..., AtlasBundlePaths]', build_context_layers_fn: 'Callable[..., tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]]', build_multi_country_map_summary_fn: 'Callable[..., dict[str, object]]', build_samples_geojson_fn: 'Callable[[Iterable[SampleRecord]], JsonObject]', copy_map_assets_fn: 'Callable[[Path], Path]', render_multi_country_map_html_fn: 'Callable[..., str]', render_multi_country_map_markdown_fn: 'Callable[..., str]', write_summary_json_fn: 'Callable[[Path, dict[str, object]], None]', atlas_detail_records: 'Sequence[JsonObject] | None' = None, atlas_scientific_signals: 'Sequence[JsonObject] | None' = None, atlas_edge_records: 'Sequence[JsonObject] | None' = None, atlas_sequence_records: 'Sequence[JsonObject] | None' = None) -> 'None'",
    "_extract_context_points": "(point_layers: 'list[dict[str, object]]') -> 'tuple[ContextPointRecord, ...]'",
    "_as_optional_int": "(value: 'object') -> 'int | None'",
    "_build_animal_atlas_summary": "(point_layers: 'list[dict[str, object]]', animal_localities: 'tuple[AdnaLocalitySummary, ...]', animal_coordinate_review: 'AnimalCoordinateVisibilityReview') -> 'dict[str, object]'",
    "_layer_features": "(layer: 'dict[str, object]') -> 'list[dict[str, object]]'",
    "_attach_traceability_surfaces": "(point_layers: 'list[dict[str, object]]', bundle_paths: 'AtlasBundlePaths') -> 'None'",
}


def test_facade_preserves_exports_and_signatures() -> None:
    assert atlas_bundle.__all__ == ["publish_multi_country_map_bundle"]
    assert {
        name: str(inspect.signature(getattr(atlas_bundle, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES
    assert all(
        getattr(atlas_bundle, name).__module__ == atlas_bundle.__name__
        for name in EXPECTED_SIGNATURES
    )


def test_context_projection_preserves_signed_coordinates_but_refuses_negative_bp() -> (
    None
):
    records = atlas_bundle._extract_context_points(
        [
            {
                "key": "context",
                "label": "Context",
                "source_name": "Source",
                "description": "Context source",
                "count": 1,
                "features": [
                    {
                        "latitude": -33.9,
                        "longitude": -70.7,
                        "title": "Signed coordinate",
                        "time_start_bp": -10,
                        "time_end_bp": 20,
                        "time_mean_bp": True,
                    }
                ],
            }
        ]
    )

    assert len(records) == 1
    record = records[0]
    assert (record.latitude, record.longitude) == (-33.9, -70.7)
    assert record.time_start_bp is None
    assert record.time_end_bp is None
    assert record.time_mean_bp is None
    assert record.temporal_semantics is not None
    assert record.temporal_semantics["comparability_posture"] == "refused"
    assert record.temporal_semantics["refusal_reason_code"] == "negative_bp"


def test_context_projection_preserves_feature_count_including_zero() -> None:
    records = atlas_bundle._extract_context_points(
        [
            {
                "key": "context",
                "label": "Context",
                "source_name": "Source",
                "count": 2,
                "features": [
                    {
                        "latitude": 59,
                        "longitude": 18,
                        "title": "Zero backing records",
                        "record_count": 0,
                    },
                    {
                        "latitude": 60,
                        "longitude": 19,
                        "title": "Legacy feature",
                    },
                ],
            }
        ]
    )

    assert [record.record_count for record in records] == [0, 1]


def test_context_projection_refuses_malformed_declared_feature_count() -> None:
    with pytest.raises(ValueError, match="record_count must be a nonnegative integer"):
        atlas_bundle._extract_context_points(
            [
                {
                    "key": "context",
                    "label": "Context",
                    "source_name": "Source",
                    "count": 1,
                    "features": [
                        {
                            "latitude": 59,
                            "longitude": 18,
                            "title": "Malformed count",
                            "record_count": False,
                        }
                    ],
                }
            ]
        )


def test_context_projection_preserves_standalone_mean_with_null_interval() -> None:
    records = atlas_bundle._extract_context_points(
        [
            {
                "key": "context",
                "label": "Context",
                "source_name": "Source",
                "description": "Context source",
                "count": 1,
                "features": [
                    {
                        "latitude": 59,
                        "longitude": 18,
                        "title": "Mean-only chronology",
                        "site_uuid": "site-uuid-1",
                        "time_start_bp": None,
                        "time_end_bp": None,
                        "time_mean_bp": 123,
                    }
                ],
            }
        ]
    )

    assert len(records) == 1
    assert records[0].time_start_bp is None
    assert records[0].time_end_bp is None
    assert records[0].time_mean_bp == 123
    assert records[0].site_uuid == "site-uuid-1"


def test_package_is_bounded_and_grouped_by_publication_intent() -> None:
    package_root = Path(atlas_bundle.__file__).parent
    modules = sorted(path.name for path in package_root.glob("*.py"))
    assert modules == [
        "__init__.py",
        "context.py",
        "contracts.py",
        "evidence.py",
        "finalization.py",
        "layers.py",
        "operations_api.py",
        "playback.py",
        "workflow.py",
    ]
    assert len(modules) <= 10
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )


def test_animal_chronology_publication_is_bounded_by_reconciliation_intent() -> None:
    package_root = Path(animal_chronology_publication.__file__).parent
    modules = sorted(path.name for path in package_root.glob("*.py"))
    assert modules == [
        "__init__.py",
        "contract_values.py",
        "corpus_reconciliation.py",
        "feature_reconciliation.py",
        "geography_reconciliation.py",
        "identity.py",
        "service.py",
    ]
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )
    assert animal_chronology_publication.__all__ == [
        "build_animal_chronology_publication"
    ]
    public = animal_chronology_publication.build_animal_chronology_publication
    assert str(inspect.signature(public)) == (
        "(projection: 'Any', *, artifact_name: 'str') "
        "-> 'tuple[dict[str, object], dict[str, object]]'"
    )
    assert public.__module__ == animal_chronology_publication.__name__


def test_package_refusals_are_explicit_and_bounded() -> None:
    package_root = Path(atlas_bundle.__file__).parent
    messages = [
        ast.unparse(node.exc)
        for path in package_root.glob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Raise)
        if node.exc is not None
    ]
    assert sorted(messages) == [
        "ValueError('animal source chronology context posture differs')",
        "ValueError('candidate-succession playback cannot ignore governed atlas edges')",
        "ValueError('candidate-succession playback requires explicit unavailable classification evidence')",
        "ValueError('static atlas manifest path does not match bundle ownership')",
        "ValueError(f'static atlas {field} contract is unavailable')",
        "ValueError(f'static atlas {field} identity is unavailable')",
    ]
