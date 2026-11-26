"""Stage context artifacts and build their publication layers."""

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
    SEAD_ARCHAEOLOGY_DISCOVERY_CSV,
    SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON,
    SEAD_ARCHAEOLOGY_DISCOVERY_JSON,
    SEAD_ARCHAEOLOGY_DISCOVERY_MARKDOWN,
)
from ...collection.sources.raa.inventory import decode_source_object
from ...core.geospatial.geojson import as_mapping
from ..map_publication import map_allows_context_layer
from .nordic_point_inputs import NordicPointInputs
from .nordic_polygon_inputs import NordicPolygonInputs
from .raa import (
    capture_raa_atlas_input_snapshot,
)
from .raa_native import NativeRegistryContextSnapshot
from .raa_native.publication import (
    build_native_registry_layer,
    publish_native_registry_context,
)
from .raa_staging import stage_raa_publication

__all__ = ["stage_context_point_layers", "stage_context_polygon_layers"]


def stage_context_point_layers(
    *,
    scope_key: str,
    context_root: Path,
    output_dir: Path,
    build_external_point_layer_fn: Callable[..., dict[str, object]],
    nordic_point_inputs: NordicPointInputs | None = None,
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external point layers into the bundle and return rendered layer configs."""
    if nordic_point_inputs is not None:
        if (
            scope_key != "nordic"
            or Path(context_root).absolute() != nordic_point_inputs.context_root
        ):
            raise ValueError("Nordic point capture requires its bound Nordic context")
        nordic_point_inputs.validate_temporal_presence()
    point_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []
    discovery_available = (
        True
        if nordic_point_inputs is not None
        else SEAD_ARCHAEOLOGY_DISCOVERY_GEOJSON.path_under(context_root).exists()
    )
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
        if nordic_point_inputs is not None:
            if layer_key not in nordic_point_inputs.buffers:
                raise ValueError("Nordic selected point layer differs")
            destination_path = nordic_point_inputs.stage(layer_key, output_dir)
            geojson = nordic_point_inputs.decode(layer_key)
        else:
            if not source_path.exists():
                continue
            destination_path = stage_context_artifact(
                source_path=source_path, output_dir=output_dir
            )
            geojson = load_context_geojson(destination_path)
        layer = build_external_point_layer_fn(geojson, source_path=destination_path)
        if nordic_point_inputs is not None and layer.get("key") != layer_key:
            raise ValueError("Nordic selected point layer identity differs")
        point_layers.append(layer)
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
    if nordic_point_inputs is not None:
        if len(point_layers) != len(nordic_point_inputs.buffers) or {
            layer.get("key") for layer in point_layers
        } != set(nordic_point_inputs.buffers):
            raise ValueError("Nordic selected point layer set differs")
        nordic_point_inputs.validate_staged(output_dir)
    return point_layers, extra_artifacts


def stage_context_polygon_layers(
    *,
    scope_key: str,
    context_root: Path | None,
    output_dir: Path,
    build_country_boundary_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_density_polygon_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_external_polygon_layer_fn: Callable[..., dict[str, object]],
    native_registry_context: NativeRegistryContextSnapshot | None = None,
    nordic_polygon_inputs: NordicPolygonInputs | None = None,
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external polygon layers into the bundle and return rendered layer configs."""
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []
    if nordic_polygon_inputs is not None and (
        context_root is None
        or scope_key != "nordic"
        or Path(context_root).absolute() != nordic_polygon_inputs.context_root
    ):
        raise ValueError("Nordic polygon capture requires its bound Nordic context")

    if context_root is None:
        if native_registry_context is not None and map_allows_context_layer(
            scope_key=scope_key, layer_key="raa-native-registry-cells"
        ):
            layer = build_native_registry_layer(native_registry_context)
            extra_artifacts.extend(
                publish_native_registry_context(
                    native_registry_context, output_dir=output_dir
                )
            )
            polygon_layers.append(layer)
        return polygon_layers, extra_artifacts

    if nordic_polygon_inputs is not None:
        selected = (
            ("country-boundaries", BOUNDARY_COLLECTION),
            ("landclim-reveals-temporal-grid", LANDCLIM_TEMPORAL_GRID_GEOJSON),
        )
        prepared = []
        for role, contract in selected:
            if not map_allows_context_layer(scope_key=scope_key, layer_key=role):
                raise ValueError("Nordic selected polygon layer is not allowed")
            destination_path = output_dir / contract.filename
            geojson = nordic_polygon_inputs.decode(role)
            layer = (
                build_country_boundary_layer_fn(geojson)
                if role == "country-boundaries"
                else build_external_polygon_layer_fn(
                    geojson, source_path=destination_path
                )
            )
            if layer.get("key") != role:
                raise ValueError("Nordic captured polygon layer identity differs")
            prepared.append((role, contract, layer))
        for role, contract, layer in prepared:
            destination_path = nordic_polygon_inputs.stage(role, output_dir)
            polygon_layers.append(layer)
            extra_artifacts.append((contract.label, destination_path.name))
        nordic_polygon_inputs.validate_staged(output_dir)

    if native_registry_context is not None and map_allows_context_layer(
        scope_key=scope_key, layer_key="raa-native-registry-cells"
    ):
        layer = build_native_registry_layer(native_registry_context)
        extra_artifacts.extend(
            publish_native_registry_context(
                native_registry_context, output_dir=output_dir
            )
        )
        polygon_layers.append(layer)
    boundary_path = BOUNDARY_COLLECTION.path_under(context_root)
    if (
        nordic_polygon_inputs is None
        and boundary_path.exists()
        and map_allows_context_layer(
            scope_key=scope_key,
            layer_key="country-boundaries",
        )
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
    if (
        nordic_polygon_inputs is None
        and landclim_grid_path.exists()
        and map_allows_context_layer(
            scope_key=scope_key,
            layer_key=landclim_layer_key,
        )
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

    raa_allowed = map_allows_context_layer(
        scope_key=scope_key, layer_key="raa-archaeology"
    )
    if raa_allowed:
        snapshot = capture_raa_atlas_input_snapshot(context_root)
        raa_status = snapshot.status()
        geometry_publication = raa_status.get("geometry_publication")
        with stage_raa_publication(
            snapshot=snapshot, output_dir=output_dir
        ) as publication:
            if (
                isinstance(geometry_publication, dict)
                and geometry_publication.get("default_enabled") is True
            ):
                if snapshot.density_bytes is None:
                    raise ValueError(
                        "RAÄ publication requires a captured density buffer"
                    )
                geojson = decode_source_object(snapshot.density_bytes.decode("utf-8"))
                layer = build_density_polygon_layer_fn(geojson)
                admitted = raa_status["atlas_input_status"] == "admitted"
                accounting = raa_status["density_count_accounting"]
                if not isinstance(accounting, dict):
                    raise ValueError(
                        "RAÄ context publication requires density accounting"
                    )
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
                    raise ValueError(
                        "RAÄ context publication requires authority reasons"
                    )
                layer.update(
                    {
                        "authority_status": raa_status["atlas_input_status"],
                        "source_authority_admitted": admitted,
                        "authority_reason_codes": list(authority_reason_codes),
                        "display_warning_codes": list(display_warning_codes),
                        "retained_surface_status": (
                            "current_authority"
                            if admitted
                            else "retained_historical_context"
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
            publication.validate()
            extra_artifacts.extend(publication.artifacts())

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
