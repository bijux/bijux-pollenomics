from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma import refresh_review

EXPECTED_SIGNATURES = {
    "build_neotoma_refresh_baseline": "(*, raw_archive_root: 'Path', relational_root: 'Path', compact_geojson_path: 'Path', lineage_path: 'Path', raw_public_root: 'str' = 'data/neotoma/raw/neotoma_pollen_dataset_downloads', relational_public_root: 'str' = 'data/neotoma/relational', compact_public_path: 'str' = 'data/neotoma/normalized/nordic_pollen_sites.geojson', lineage_public_path: 'str' = 'data/neotoma/review/compact_relational_lineage.json') -> 'dict[str, object]'",
    "build_neotoma_refresh_review": "(prior: 'Mapping[str, object] | None', candidate: 'Mapping[str, object] | None', *, explanations: 'Mapping[str, str] | None' = None, missing_reasons: 'list[str] | None' = None) -> 'dict[str, object]'",
    "write_neotoma_refresh_baseline": "(output_path: 'Path', *, raw_archive_root: 'Path', relational_root: 'Path', compact_geojson_path: 'Path', lineage_path: 'Path') -> 'Path'",
    "write_neotoma_refresh_review": "(output_path: 'Path', *, baseline_path: 'Path', raw_archive_root: 'Path', relational_root: 'Path', compact_geojson_path: 'Path', lineage_path: 'Path', explanations: 'Mapping[str, str] | None' = None, markdown_path: 'Path | None' = None) -> 'Path'",
    "render_neotoma_refresh_review_markdown": "(payload: 'Mapping[str, object]') -> 'str'",
    "_collect_changes": "(changes: 'list[dict[str, object]]', *, section: 'str', prior: 'Mapping[str, object]', candidate: 'Mapping[str, object]', explanations: 'Mapping[str, str]', prefix: 'str' = '') -> 'None'",
    "_change_kind": "(*, section: 'str', prior: 'object', candidate: 'object') -> 'str'",
    "_validate_baseline": "(value: 'Mapping[str, object]', label: 'str') -> 'None'",
    "_optional_baseline_id": "(value: 'Mapping[str, object] | None') -> 'str | None'",
    "_write_atomic": "(path: 'Path', content: 'bytes') -> 'None'",
    "_read_regular_file": "(path: 'Path') -> 'bytes'",
    "_json_object": "(content: 'bytes', label: 'str') -> 'dict[str, object]'",
    "_mapping": "(value: 'object', label: 'str') -> 'Mapping[str, object]'",
    "_required_text": "(value: 'object', label: 'str') -> 'str'",
    "_non_negative_integer": "(value: 'object', label: 'str') -> 'int'",
    "_safe_filename": "(value: 'str') -> 'str'",
    "_safe_public_path": "(value: 'str') -> 'str'",
    "_canonical_json": "(payload: 'object') -> 'bytes'",
}


def test_facade_preserves_every_monolith_signature() -> None:
    assert {
        name: str(inspect.signature(getattr(refresh_review, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_facade_preserves_exports_and_schema_constants() -> None:
    assert refresh_review.__all__ == [
        "build_neotoma_refresh_baseline",
        "build_neotoma_refresh_review",
        "render_neotoma_refresh_review_markdown",
        "write_neotoma_refresh_baseline",
        "write_neotoma_refresh_review",
    ]
    namespace = vars(refresh_review)
    assert namespace["BASELINE_SCHEMA_VERSION"] == "neotoma-refresh-baseline.v1"
    assert namespace["REFRESH_REVIEW_SCHEMA_VERSION"] == "neotoma-refresh-review.v1"


def test_package_has_small_intent_owned_modules() -> None:
    package_root = Path(refresh_review.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "baseline.py",
        "comparison.py",
        "constants.py",
        "operations_api.py",
        "serialization.py",
        "validation.py",
        "validation_api.py",
    }
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )
