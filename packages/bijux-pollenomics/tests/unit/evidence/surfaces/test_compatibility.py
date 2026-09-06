"""Compatibility and ownership checks for atlas-evidence surfaces."""

from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.evidence import surfaces

_LEGACY_DEFINITIONS = {
    "build_atlas_evidence_surface",
    "_build_human_species_row",
    "_build_nonhuman_species_rows",
    "_contribution_role_for",
    "_interaction_posture_for",
    "_chronology_posture_for",
    "_geography_posture_for",
    "_rationale_for",
    "_build_atlas_layers",
    "_build_country_profiles",
    "_build_refusals",
}


def test_facade_preserves_the_legacy_surface_contract() -> None:
    assert surfaces.__all__ == ["build_atlas_evidence_surface"]
    assert vars(surfaces).keys() >= _LEGACY_DEFINITIONS
    assert str(inspect.signature(surfaces.build_atlas_evidence_surface)) == (
        "(*, countries: 'tuple[str, ...]', "
        "human_localities: 'Iterable[AdnaLocalitySummary]', "
        "animal_localities: 'Iterable[AdnaLocalitySummary]' = (), "
        "context_points: 'Iterable[ContextPointRecord]', "
        "include_tracked_nonhuman_review: 'bool' = True) -> 'AtlasEvidenceSurface'"
    )


def test_package_modules_are_bounded_and_named_by_evidence_intent() -> None:
    package_root = Path(surfaces.__file__).parent
    modules = {
        module.name: len(module.read_text(encoding="utf-8").splitlines())
        for module in package_root.glob("*.py")
    }

    assert set(modules) == {
        "__init__.py",
        "countries.py",
        "layers.py",
        "posture.py",
        "refusals.py",
        "species.py",
    }
    assert max(modules.values()) <= 220
