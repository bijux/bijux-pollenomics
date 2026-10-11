from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import shutil

from ...collection.contracts.artifacts import (
    ATLAS_POINT_ARTIFACTS,
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
    RAA_DENSITY_GEOJSON,
    RAA_LAYER_METADATA,
    SEAD_ARCHAEOLOGY_DISCOVERY_CSV,
    SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON,
    SEAD_ARCHAEOLOGY_DISCOVERY_JSON,
    SEAD_ARCHAEOLOGY_DISCOVERY_MARKDOWN,
)
from ...core.files import write_json
from ...core.geospatial.geojson import as_mapping
from ..map_publication import map_allows_context_layer
from .raa import (
    RAA_ATLAS_INPUT_STATUS_FILENAME,
    RAA_ATLAS_INPUT_STATUS_LABEL,
    build_raa_atlas_input_status,
)

__all__ = ["stage_context_point_layers", "stage_context_polygon_layers"]


def stage_context_point_layers(
    *,
    scope_key: str,
    context_root: Path,
    output_dir: Path,
    build_external_point_layer_fn: Callable[..., dict[str, object]],
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external point layers into the bundle and return rendered layer configs."""
    point_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []
    discovery_available = SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON.path_under(
        context_root
    ).exists()
    superseded_sead_filenames = {
        "nordic_temporal_evidence.geojson",
    }
    for contract in ATLAS_POINT_ARTIFACTS:
        if discovery_available and contract.filename in superseded_sead_filenames:
            continue
        layer_key = _layer_key_for_point_contract(contract.filename)
        if not map_allows_context_layer(scope_key=scope_key, layer_key=layer_key):
            continue
        source_path = contract.path_under(context_root)
        if not source_path.exists():
            continue
        destination_path = stage_context_artifact(
            source_path=source_path, output_dir=output_dir
        )
        geojson = load_context_geojson(destination_path)
        point_layers.append(
            build_external_point_layer_fn(geojson, source_path=destination_path)
        )
        extra_artifacts.append((contract.label, destination_path.name))
        if contract is SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON:
            for companion in (
                SEAD_ARCHAEOLOGY_DISCOVERY_JSON,
                SEAD_ARCHAEOLOGY_DISCOVERY_CSV,
                SEAD_ARCHAEOLOGY_DISCOVERY_MARKDOWN,
            ):
                companion_path = companion.path_under(context_root)
                if not companion_path.exists():
                    continue
                staged_companion = stage_context_artifact(
                    source_path=companion_path, output_dir=output_dir
                )
                extra_artifacts.append((companion.label, staged_companion.name))
    return point_layers, extra_artifacts


def stage_context_polygon_layers(
    *,
    scope_key: str,
    context_root: Path,
    output_dir: Path,
    build_country_boundary_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_density_polygon_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_external_polygon_layer_fn: Callable[..., dict[str, object]],
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external polygon layers into the bundle and return rendered layer configs."""
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    boundary_path = BOUNDARY_COLLECTION.path_under(context_root)
    if boundary_path.exists() and map_allows_context_layer(
        scope_key=scope_key,
        layer_key="country-boundaries",
    ):
        destination_path = stage_context_artifact(
            source_path=boundary_path, output_dir=output_dir
        )
        polygon_layers.append(
            build_country_boundary_layer_fn(load_context_geojson(destination_path))
        )
        extra_artifacts.append((BOUNDARY_COLLECTION.label, destination_path.name))

    temporal_landclim_grid_path = LANDCLIM_TEMPORAL_GRID_GEOJSON.path_under(
        context_root
    )
    landclim_grid_contract = (
        LANDCLIM_TEMPORAL_GRID_GEOJSON
        if temporal_landclim_grid_path.exists()
        else LANDCLIM_GRID_GEOJSON
    )
    landclim_grid_path = landclim_grid_contract.path_under(context_root)
    landclim_layer_key = (
        "landclim-reveals-temporal-grid"
        if landclim_grid_contract is LANDCLIM_TEMPORAL_GRID_GEOJSON
        else "landclim-reveals-grid"
    )
    if landclim_grid_path.exists() and map_allows_context_layer(
        scope_key=scope_key,
        layer_key=landclim_layer_key,
    ):
        destination_path = stage_context_artifact(
            source_path=landclim_grid_path, output_dir=output_dir
        )
        polygon_layers.append(
            build_external_polygon_layer_fn(
                load_context_geojson(destination_path), source_path=destination_path
            )
        )
        extra_artifacts.append((landclim_grid_contract.label, destination_path.name))

    archaeology_path = RAA_LAYER_METADATA.path_under(context_root)
    if archaeology_path.exists() and map_allows_context_layer(
        scope_key=scope_key,
        layer_key="raa-layer-metadata",
    ):
        destination_path = stage_context_artifact(
            source_path=archaeology_path, output_dir=output_dir
        )
        extra_artifacts.append((RAA_LAYER_METADATA.label, destination_path.name))

    archaeology_density_path = RAA_DENSITY_GEOJSON.path_under(context_root)
    raa_allowed = map_allows_context_layer(
        scope_key=scope_key,
        layer_key="raa-archaeology",
    )
    raa_status = build_raa_atlas_input_status(context_root) if raa_allowed else None
    if raa_allowed:
        raa_status_path = output_dir / RAA_ATLAS_INPUT_STATUS_FILENAME
        write_json(raa_status_path, raa_status)
        extra_artifacts.append((RAA_ATLAS_INPUT_STATUS_LABEL, raa_status_path.name))
    geometry_publication = (
        raa_status.get("geometry_publication") if isinstance(raa_status, dict) else None
    )
    publish_context = bool(
        isinstance(geometry_publication, dict)
        and geometry_publication.get("default_enabled") is True
        and archaeology_density_path.is_file()
    )
    if publish_context:
        if not isinstance(geometry_publication, dict):
            raise ValueError("RAÄ context publication requires geometry posture")
        destination_path = stage_context_artifact(
            source_path=archaeology_density_path, output_dir=output_dir
        )
        layer = build_density_polygon_layer_fn(load_context_geojson(destination_path))
        if raa_status is None:
            raise ValueError("RAÄ context publication requires an input status")
        admitted = raa_status["atlas_input_status"] == "admitted"
        accounting = raa_status["density_count_accounting"]
        if not isinstance(accounting, dict):
            raise ValueError("RAÄ context publication requires density accounting")
        density_sum = accounting["density_cell_count_sum"]
        metadata_count = accounting["metadata_fornlamning_count"]
        display_warning_codes = geometry_publication.get("warning_codes")
        authority_reason_codes = raa_status.get("reason_codes")
        if not isinstance(display_warning_codes, list) or any(
            not isinstance(code, str) for code in display_warning_codes
        ):
            raise ValueError("RAÄ context publication requires warning codes")
        if not isinstance(authority_reason_codes, list) or any(
            not isinstance(code, str) for code in authority_reason_codes
        ):
            raise ValueError("RAÄ context publication requires authority reasons")
        layer.update(
            {
                "authority_status": raa_status["atlas_input_status"],
                "source_authority_admitted": admitted,
                "authority_reason_codes": list(authority_reason_codes),
                "display_warning_codes": list(display_warning_codes),
                "retained_surface_status": (
                    "current_authority" if admitted else "retained_historical_context"
                ),
                "density_count_accounting": dict(accounting),
                "density_value_label": (
                    "Governed source records"
                    if admitted
                    else "Retained cell count (unreconciled)"
                ),
                "density_count_label": (
                    "Governed Swedish RAÄ source records in one-degree cells."
                    if admitted
                    else "Retained Swedish one-degree cell values: "
                    f"{density_sum:,} summed cell counts versus "
                    f"{metadata_count:,} metadata Fornlämning; display only, "
                    "source authority refused."
                ),
                "description": (
                    layer["description"]
                    if admitted
                    else "Retained RAÄ archaeology density from the v0.1.8 "
                    "surface, displayed as degraded historical context while "
                    "raw-inventory reconciliation, count reconciliation and "
                    "qualified review remain unavailable."
                ),
            }
        )
        polygon_layers.append(layer)
        extra_artifacts.append((RAA_DENSITY_GEOJSON.label, destination_path.name))

    return polygon_layers, extra_artifacts


def stage_context_artifact(*, source_path: Path, output_dir: Path) -> Path:
    """Copy one context artifact into the atlas bundle and return the staged path."""
    destination_path = output_dir / source_path.name
    shutil.copyfile(source_path, destination_path)
    return destination_path


def load_context_geojson(path: Path) -> dict[str, object]:
    """Load one staged GeoJSON artifact."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = as_mapping(payload)
    if mapping is None:
        raise ValueError(f"Context GeoJSON must be a JSON object: {path}")
    return {str(key): value for key, value in mapping.items()}


def _layer_key_for_point_contract(filename: str) -> str:
    if filename == "nordic_pollen_site_sequences.geojson":
        return "landclim-sites"
    if filename == "nordic_pollen_sites.geojson":
        return "neotoma-pollen"
    if filename == "nordic_environmental_sites.geojson":
        return "sead-sites"
    if filename == "nordic_temporal_evidence.geojson":
        return "sead-temporal-evidence"
    if filename == "sweden_archaeology_site_discovery.geojson":
        return "sweden-archaeology-site-discovery"
    raise ValueError(f"Unhandled point artifact contract filename: {filename}")
