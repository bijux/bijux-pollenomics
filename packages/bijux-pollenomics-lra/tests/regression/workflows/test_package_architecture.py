"""Host-standard ownership, discovery and engine schema boundaries."""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib

import jsonschema

from bijux_pollenomics_lra.api import (
    LoveConfig,
    OptimizedLoveProfile,
    extension_descriptor,
)
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
)
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.resources.schemas import load_schema


def test_named_domains_bound_source_size_and_dependency_direction(
    project_root: Path,
) -> None:
    source = project_root / "src/bijux_pollenomics_lra"
    assert not (source / "cli.py").exists()
    assert not (source / "integration.py").exists()
    for path in source.rglob("*.py"):
        assert len(path.read_text().splitlines()) <= 540, path
        if path.parent.name not in {"reconstruction", "dispersal", "optimization"}:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    part in (node.module or "").split(".")
                    for part in ("outputs", "workflows", "cli", "bijux_pollenomics")
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "to_csv",
                    "write_text",
                    "write_bytes",
                    "mkdir",
                }


def test_extension_descriptor_matches_packaged_registration(project_root: Path) -> None:
    descriptor = extension_descriptor()
    metadata = tomllib.loads((project_root / "pyproject.toml").read_text())
    target = metadata["project"]["entry-points"]["bijux_pollenomics.extensions"]["lra"]
    assert descriptor["extension_target"] == target
    assert descriptor["extension_group"] == "bijux_pollenomics.extensions"
    assert descriptor["extension_name"] == "lra"
    assert "scripts" not in metadata["project"]
    jsonschema.validate(descriptor, load_schema("extension-descriptor.schema.json"))


def test_named_love_capability_matches_validated_profile() -> None:
    profile = LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE
    assert (
        "lra.love.analytical.fall-speed-profile." + profile
        in extension_descriptor()["capabilities"]
    )
    config = LoveConfig(
        method="analytical",
        regional_basin_type="lake",
        regional_basin_diameter_m=300,
        local_basin_diameter_m=12.9,
        max_ring=1,
        distance_weighting="gpm neutral",
        fall_speed_profile=profile,
    )
    assert config.as_dict()["fall_speed_profile"] == profile


def test_optimized_revised_profile_is_publicly_discoverable() -> None:
    profile = OptimizedLoveProfile.RING_TAXON_PRESERVING.value
    capabilities = extension_descriptor()["capabilities"]
    assert "lra.love.optimized" in capabilities
    assert "lra.love.optimized." + profile in capabilities
    config = LoveConfig(
        method="optimized",
        regional_basin_type="lake",
        regional_basin_diameter_m=300,
        local_basin_diameter_m=12.9,
        max_ring=1,
        optimized_profile=profile,
    )
    assert config.as_dict()["optimized_profile"] == profile


def test_run_manifest_retains_actual_backend_and_valid_schema() -> None:
    manifest = build_manifest("test", {}, {}, stochastic=False, seed=None)
    assert manifest.runtime["numerical_backend"] == "python-numpy-scipy"
    jsonschema.validate(manifest.as_dict(), load_schema("run-manifest.schema.json"))
