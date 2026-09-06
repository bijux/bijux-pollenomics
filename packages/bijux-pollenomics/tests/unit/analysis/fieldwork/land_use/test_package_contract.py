from __future__ import annotations

import inspect
from pathlib import Path

import bijux_pollenomics.analysis.fieldwork.land_use as land_use

EXPECTED_SIGNATURES = {
    "build_sweden_land_use_synthesis": "(*, context_root: 'Path', lake_report, human_localities, animal_localities) -> 'dict[str, object]'",
    "write_sweden_land_use_synthesis_json": "(path: 'Path', payload: 'dict[str, object]') -> 'None'",
    "write_sweden_land_use_synthesis_csv": "(path: 'Path', payload: 'dict[str, object]') -> 'None'",
    "render_sweden_land_use_synthesis_markdown": "(payload: 'dict[str, object]') -> 'str'",
    "_synthesis_targets": "(lake_report) -> 'tuple[_Target, ...]'",
    "_target_row": "(target: '_Target', *, lake_candidates, landclim_features: 'list[dict[str, object]]') -> 'dict[str, object]'",
    "_load_features": "(path: 'Path') -> 'list[dict[str, object]]'",
    "_target_landclim_features": "(target: '_Target', features: 'list[dict[str, object]]') -> 'list[dict[str, object]]'",
    "_polygon_contains": "(geometry, *, longitude: 'float', latitude: 'float') -> 'bool'",
    "_overlapping_geojson_context": "(*, target: '_Target', features, time_start_bp: 'int', time_end_bp: 'int') -> 'dict[str, int]'",
    "_overlapping_human_context": "(*, target: '_Target', localities, time_start_bp: 'int', time_end_bp: 'int') -> 'dict[str, int]'",
    "_overlapping_animal_context": "(*, target: '_Target', localities, time_start_bp: 'int', time_end_bp: 'int') -> 'dict[str, int]'",
    "_within_radius": "(target: '_Target', *, latitude: 'float', longitude: 'float') -> 'bool'",
    "_intervals_overlap": "(start_a: 'float | int | None', end_a: 'float | int | None', start_b: 'float | int | None', end_b: 'float | int | None') -> 'bool'",
    "_cross_proxy_posture": "(*, sead_count: 'int', human_count: 'int', animal_count: 'int') -> 'str'",
    "_number": "(value) -> 'float'",
}


def test_facade_preserves_every_monolith_function_signature() -> None:
    assert {
        name: str(inspect.signature(getattr(land_use, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_facade_preserves_public_exports_and_target_definition() -> None:
    assert land_use.__all__ == [
        "build_sweden_land_use_synthesis",
        "render_sweden_land_use_synthesis_markdown",
        "write_sweden_land_use_synthesis_csv",
        "write_sweden_land_use_synthesis_json",
    ]
    assert land_use._Target.__name__ == "_Target"
    assert tuple(inspect.signature(land_use._Target).parameters) == (
        "requested_name",
        "registry_name",
        "latitude",
        "longitude",
        "target_class",
        "lake_decision",
        "decision_reason",
        "coordinate_source",
    )


def test_land_use_package_has_small_intent_owned_modules() -> None:
    package_root = Path(land_use.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "context.py",
        "inputs.py",
        "interpretation.py",
        "models.py",
        "outputs.py",
        "quality.py",
        "spatial.py",
        "synthesis.py",
        "targets.py",
        "temporal.py",
    }
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )
