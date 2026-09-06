"""Facade compatibility and topology tests for animal locality reporting."""

import inspect
from pathlib import Path

from bijux_pollenomics.reporting.adna import animal_localities

_LEGACY_DEFINITIONS = {
    "AnimalAtlasBundle",
    "load_tracked_animal_localities",
    "build_tracked_animal_atlas_bundle",
    "_load_dataset_review",
    "_load_review_lookup",
    "_build_point_feature",
    "_write_feature_collection",
    "_warning_rows_for",
    "_layer_group_for",
    "_animal_scope_for",
    "_layer_description_for",
    "_layer_style_for",
    "_temporal_semantics_for",
    "_alpha",
    "_optional_str",
    "_write_animal_atlas_evidence_csv",
    "_write_animal_atlas_evidence_json",
    "_write_animal_point_traceability_json",
}


def test_facade_preserves_legacy_symbols_and_public_contract() -> None:
    assert set(animal_localities.__all__) == {
        "AnimalAtlasBundle",
        "build_tracked_animal_atlas_bundle",
        "load_tracked_animal_localities",
    }
    assert set(vars(animal_localities)) >= _LEGACY_DEFINITIONS
    assert str(
        inspect.signature(animal_localities.build_tracked_animal_atlas_bundle)
    ) == (
        "(*, data_root: 'Path', output_dir: 'Path', atlas_slug: 'str', "
        "geography_scope: 'GeographicScope | None' = None) -> 'AnimalAtlasBundle'"
    )


def test_package_modules_are_bounded_and_named_by_reporting_intent() -> None:
    root = Path(animal_localities.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in root.glob("*.py")
    }

    assert set(modules) == {
        "__init__.py",
        "assembly.py",
        "features.py",
        "layers.py",
        "model.py",
        "publication.py",
        "review.py",
    }
    assert max(modules.values()) <= 250
