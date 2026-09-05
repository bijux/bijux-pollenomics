"""Compatibility and topology contract for atlas bundle publication."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from bijux_pollenomics.reporting.bundles import atlas_bundle

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
        "workflow.py",
    ]
    assert len(modules) <= 10
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )


def test_manifest_ownership_refusal_has_one_reachable_raise() -> None:
    package_root = Path(atlas_bundle.__file__).parent
    messages = [
        ast.unparse(node.exc)
        for path in package_root.glob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Raise)
        if node.exc is not None
    ]
    assert messages == [
        "ValueError('static atlas manifest path does not match bundle ownership')"
    ]
