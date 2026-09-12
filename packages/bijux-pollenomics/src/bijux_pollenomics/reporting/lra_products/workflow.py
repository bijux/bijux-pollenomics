"""Build a local exploratory report through the existing shared atlas renderer."""

from __future__ import annotations

from dataclasses import replace
from html import escape
import os
from pathlib import Path
import tempfile
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaValidationError

from ...analysis.lra.api import read_lra_product
from ...analysis.lra.inputs.schema import REQUEST_SCHEMA
from ...core.geospatial.geojson import JsonObject
from ...core.owned_tree import publish_new_output_tree
from ..map_document import render_multi_country_map_html
from ..map_document.static_assets import write_static_atlas_assets
from ..rendering.artifacts import copy_map_assets
from ..scope_policy import MAP_SCOPE_POLICIES
from .contracts import (
    LRAPresentation,
    LRAPresentationRefusal,
    bound_bytes,
    canonical,
    digest,
    json_object,
)
from .downloads import capture_product, write_downloads
from .geometry import validate_geometry
from .projection import project_sites
from .tables import input_rows, model_rows, numerical_tables


def _report(
    manifest: dict[str, Any],
    request: dict[str, Any],
    rows: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    sites: list[dict[str, Any]],
    *,
    map_available: bool,
) -> str:
    def text(value: object) -> str:
        return escape(str(value), quote=True)

    estimates = "".join(
        "<tr>"
        + "".join(
            f"<td>{text(row[key] if row[key] is not None else 'N/A')}</td>"
            for key in (
                "role",
                "site_id",
                "taxon",
                "statistic",
                "native_value",
                "native_unit",
            )
        )
        + "</tr>"
        for row in rows
    )
    statuses = "".join(
        f"<li>{text(site['role'])} / {text(site['site_id'])}: {text(site['map_status'])}"
        f" {text(', '.join(site['reason_codes']))}</li>"
        for site in sites
    )
    source_tables = "".join(
        f"<details><summary>{text(table['member'])} ({table['data_row_count']} rows)</summary>"
        f"<pre>{text(canonical({'header': table['header'], 'rows': table['rows']}).decode())}</pre></details>"
        for table in tables
    )
    links = [
        ("product.zip", "Exact original product archive"),
        ("product/manifest.json", "Original product manifest"),
        ("manifest.json", "Presentation identities and all file hashes"),
        ("model-estimates.json", "Native estimates and full row lineage (JSON)"),
        ("model-estimates.csv", "Native estimates (CSV)"),
        ("numerical-tables.json", "All numerical CSV cells and source locators"),
        ("input-pollen.json", "Input pollen counts and source identities"),
        ("display-geometry.json", "Display geometry declaration"),
        ("site-accounting.json", "Mapped and refused sites"),
    ]
    downloads = "".join(
        f'<li><a href="{path}">{label}</a></li>' for path, label in links
    )
    return (
        (
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>Exploratory LRA report</title><main><h1>Exploratory LRA report</h1>"
            f"<p>Data kind: {text(request['data_kind'])}. Scientific acceptance: not evaluated. "
            "This local report does not authorize publication.</p>"
            "<p>Model estimates and input pollen are separate evidence roles. Display anchors "
            "are not regional footprints or geographic ring estimates. No propagation arrows, "
            "accepted classifications or empirical accuracy metrics are produced.</p>"
        )
        + (
            '<p><a href="map.html">Open synthetic display-anchor map</a></p>'
            if map_available
            else "<p>Map unavailable; all numerical values remain below and in downloads.</p>"
        )
        + (
            "<p>Advanced model/taxon/site selections and selected-frame downloads "
            "are unavailable in this report profile. Downloads retain all rows.</p>"
            "<h2>Native estimates</h2><p>REVEALS cover: percent. LOVE cover: fraction. "
            "Values retain original CSV decimal text; N/A remains missing. q10/q90 are method "
            "quantiles, not total uncertainty or held-out predictive intervals.</p>"
            "<table><thead><tr><th>Role</th><th>Site</th><th>Taxon</th><th>Statistic</th>"
            "<th>Value</th><th>Native unit</th></tr></thead><tbody>"
            + estimates
            + "</tbody></table>"
            "<h2>Map accounting</h2><ul>" + statuses + "</ul>"
            "<h2>Downloads</h2><ul>" + downloads + "</ul>"
            "<h2>Request, source lineage, exclusions and uncertainty omissions</h2><pre>"
            + text(canonical(request).decode())
            + "</pre>"
            "<h2>Product metadata</h2><pre>"
            + text(canonical(manifest).decode())
            + "</pre>"
            "<h2>Complete original numerical CSV content</h2>"
            + source_tables
            + "</main></html>"
        )
    )


def _map(stage: Path, layers: list[dict[str, Any]]) -> str | None:
    if not layers:
        return None
    assets = write_static_atlas_assets(
        stage,
        slug="lra-exploratory",
        version="presentation-v1",
        point_layers=layers,
        polygon_layers=[],
    )
    policy = replace(
        MAP_SCOPE_POLICIES["custom"],
        default_basemap="none",
        eyebrow_label="Exploratory synthetic model anchors",
        summary="Declared synthetic display anchors; no actual site geometry, land-cover truth or propagation is established.",
    )
    copy_map_assets(stage)
    render_layers: list[JsonObject] = [dict(layer) for layer in layers]
    document = render_multi_country_map_html(
        title="Exploratory synthetic LRA anchors",
        version="presentation-v1",
        generated_on="Source identities in the accompanying report",
        countries=(),
        policy=policy,
        point_layers=render_layers,
        polygon_layers=[],
        asset_base_path="_map_assets",
        static_assets=assets,
    )
    (stage / "map.html").write_text(document)
    return str(assets.manifest["build_id"])


def render_lra_report(
    product_directory: Path,
    *,
    expected_manifest_sha256: str,
    geometry_path: Path,
    expected_geometry_sha256: str,
    destination: Path,
) -> LRAPresentation:
    """Render verified saved bytes without loading or running the numerical engine.

    Only synthetic paired/single nonnegative-bin geometry is mapped. Other cases
    retain original values/downloads and explicit site refusals. Existing outputs
    are never replaced; failed staging directories remain available for diagnosis.
    """
    destination = destination.absolute()
    product_directory = product_directory.absolute()
    geometry_path = geometry_path.absolute()
    # Check visible spelling before lexical normalization: resolving a symlink
    # would conceal the unsupported alias even when followed by a dot segment.
    for path in (destination, product_directory, geometry_path):
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise LRAPresentationRefusal("invalid_presentation_output", str(path))
    destination = Path(os.path.abspath(destination))
    product_directory = Path(os.path.abspath(product_directory))
    geometry_path = Path(os.path.abspath(geometry_path))
    if (
        destination == Path(destination.anchor)
        or any(parent.is_symlink() for parent in (destination, *destination.parents))
        or destination.is_relative_to(product_directory)
    ):
        raise LRAPresentationRefusal("invalid_presentation_output", str(destination))
    try:
        manifest, product = capture_product(product_directory, expected_manifest_sha256)
        geometry_bytes = bound_bytes(geometry_path, expected_geometry_sha256)
        request = json_object(product["request.json"])
        Draft202012Validator(REQUEST_SCHEMA).validate(request)
        geometry = validate_geometry(
            json_object(geometry_bytes),
            manifest,
            request,
            product_manifest_sha256=expected_manifest_sha256,
        )
        tables = numerical_tables(product)
        rows = model_rows(tables, request, request_sha256=manifest["request_sha256"])
        observations = input_rows(request)
        layers, sites = project_sites(
            request,
            manifest,
            rows,
            geometry,
            product_sha256=expected_manifest_sha256,
            geometry_sha256=expected_geometry_sha256,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.pending-", dir=destination.parent
            )
        )
        write_downloads(stage, product, rows, tables, observations)
        (stage / "display-geometry.json").write_bytes(geometry_bytes)
        (stage / "site-accounting.json").write_bytes(canonical(sites))
        (stage / "model-layers.json").write_bytes(canonical(layers))
        map_build_id = _map(stage, layers)
        (stage / "index.html").write_text(
            _report(manifest, request, rows, tables, sites, map_available=bool(layers))
        )
        read_lra_product(
            stage / "product", expected_manifest_sha256=expected_manifest_sha256
        )
        mapped = sum(site["map_status"] == "synthetic_anchor" for site in sites)
        payload = {
            "schema_version": "lra-presentation.v1",
            "status": "generated_exploratory",
            "scientific_acceptance": "not_evaluated",
            "publication_authorized": False,
            "purpose": request["purpose"],
            "data_kind": request["data_kind"],
            "operation": request["operation"],
            "product_manifest_sha256": expected_manifest_sha256,
            "request_sha256": manifest["request_sha256"],
            "scientific_content_sha256": manifest["scientific_content_sha256"],
            "display_geometry_sha256": expected_geometry_sha256,
            "download_selection": "complete_product_and_all_rows_no_interactive_subset",
            "map_build_id": map_build_id,
            "capabilities": {
                "native_selection_filters": False,
                "browser_acceptance": False,
                "regional_footprint": False,
                "geographic_ring_values": False,
                "validation_metrics": False,
                "propagation": False,
            },
            "table_projection_status": "paired_native_rows"
            if request["operation"] == "lra"
            else "unsupported_operation_original_tables_retained",
            "counts": {
                "requested_sites": len(sites),
                "mapped_sites": mapped,
                "refused_sites": len(sites) - mapped,
                "model_rows": len(rows),
                "missing_model_values": sum(
                    row["native_value"] is None for row in rows
                ),
                "input_pollen_rows": len(observations),
                "numerical_csv_files": len(tables),
                "numerical_csv_data_rows": sum(
                    table["data_row_count"] for table in tables
                ),
                "numerical_csv_cells": sum(table["cell_count"] for table in tables),
                "excluded_request_records": len(request["exclusions"]),
            },
            "files": {
                path.relative_to(stage).as_posix(): digest(path.read_bytes())
                for path in sorted(stage.rglob("*"))
                if path.is_file()
            },
        }
        encoded = canonical(payload)
        (stage / "manifest.json").write_bytes(encoded)
        # Check input closure after all projections; a concurrent edit cannot be
        # silently incorporated into a report carrying the previous identity.
        capture_product(product_directory, expected_manifest_sha256)
        bound_bytes(geometry_path, expected_geometry_sha256)
        for path in stage.rglob("*"):
            if path.is_file():
                with path.open("rb") as stream:
                    os.fsync(stream.fileno())
        publish_new_output_tree(
            final_output_root=destination, staging_output_root=stage
        )
        return LRAPresentation(
            destination,
            digest(encoded),
            expected_manifest_sha256,
            expected_geometry_sha256,
            mapped,
            len(sites) - mapped,
        )
    except LRAPresentationRefusal:
        raise
    except FileExistsError as exc:
        raise LRAPresentationRefusal(
            "presentation_output_exists", str(destination)
        ) from exc
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        OverflowError,
        SchemaValidationError,
    ) as exc:
        raise LRAPresentationRefusal("invalid_lra_presentation", str(exc)) from exc
