"""Render retained modeled and signed native frames without numerical execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Literal, cast

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.lra_products.api import render_lra_report
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy
from bijux_pollenomics.reporting.modeled_context import build_modeled_context_manifest
from bijux_pollenomics.reporting.modeled_context.publication_projection import (
    project_modeled_context_layers,
)

COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
LAYER_KEY = "landclim-reveals-temporal-grid"
PROFILE: Literal["calendar-bp1950-signed.v1"] = "calendar-bp1950-signed.v1"


def record_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def collect_retained_features(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Country-sharded chunk overlaps must preserve one identical source feature."""
    indexed: dict[int, dict[str, Any]] = {}
    for payload in payloads:
        for index, feature in zip(
            payload["feature_indexes"], payload["features"], strict=True
        ):
            if index in indexed and record_digest(indexed[index]) != record_digest(
                feature
            ):
                raise ValueError(
                    "retained feature index has conflicting source records"
                )
            indexed[index] = feature
    return [indexed[index] for index in sorted(indexed)]


def generate_context_frame_candidates(
    repository: Path,
    destination: Path,
    native_product: Path,
    native_geometry: Path,
    product_manifest_sha256: str,
    geometry_sha256: str,
) -> dict[str, Any]:
    repository, destination = repository.resolve(), destination.resolve()
    if not destination.is_relative_to(repository / "artifacts"):
        raise ValueError("candidate must be generated under repository artifacts")
    if destination.exists():
        raise ValueError("candidate destination must be absent")
    inputs: dict[str, str] = {}

    def read(path: Path) -> bytes:
        if path.is_symlink() or not path.is_file():
            raise ValueError("source input must be a regular file")
        payload = path.read_bytes()
        key, checksum = (
            path.resolve().relative_to(repository).as_posix(),
            hashlib.sha256(payload).hexdigest(),
        )
        if key in inputs and inputs[key] != checksum:
            raise ValueError("source input mutated during generation")
        inputs[key] = checksum
        return payload

    if (
        hashlib.sha256(read(native_product / "manifest.json")).hexdigest()
        != product_manifest_sha256
        or hashlib.sha256(read(native_geometry)).hexdigest() != geometry_sha256
    ):
        raise ValueError("native input digest mismatch")
    for path in sorted(native_product.rglob("*")):
        if path.is_file():
            read(path)
    package = repository / "packages/bijux-pollenomics/src/bijux_pollenomics"
    for domain in ("reporting", "analysis/lra", "core"):
        for path in sorted((package / domain).rglob("*")):
            if path.is_file() and path.suffix in {".py", ".html", ".js"}:
                read(path)
    for dependency_root in (
        repository / "packages/bijux-pollenomics-lra/src",
        repository / "configs/scientific-contracts",
    ):
        for path in sorted(dependency_root.rglob("*")):
            if path.is_file() and path.suffix in {".py", ".json", ".yaml"}:
                read(path)
    if Path(__file__).resolve().is_relative_to(repository):
        read(Path(__file__).resolve())
    retained = repository / "docs/report/regions/nordic"
    html = read(retained / "nordic_map.html").decode()
    bootstrap = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if bootstrap is None:
        raise ValueError("retained atlas bootstrap is absent")
    source_manifest = json.loads(bootstrap.group(1))
    inventory = cast(
        list[dict[str, Any]], normalize_asset_inventory(source_manifest["assets"])
    )

    def chunk(row: dict[str, Any]) -> dict[str, Any]:
        payload = read(retained / row["path"])
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError("retained atlas chunk digest mismatch")
        return decode_chunk_script(
            payload,
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row.get("decoded_byte_count"),
        )

    provenance = chunk(next(row for row in inventory if row["domain"] == "provenance"))
    source_layer = next(
        entry["layer"]
        for entry in provenance["layers"]
        if entry["layer"]["key"] == LAYER_KEY
    )
    features = [
        feature
        for feature in collect_retained_features(
            [
                chunk(row)
                for row in inventory
                if row.get("layer_key") == LAYER_KEY and row["domain"] == "nodes"
            ]
        )
        if feature["properties"]["dataset_id"] == "937075"
    ]
    normalized = json.loads(
        read(
            repository
            / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
        )
    )
    source_by_id = {
        feature["properties"]["record_id"]: feature
        for feature in normalized["features"]
    }
    raw_features = [
        source_by_id[feature["properties"]["record_id"]] for feature in features
    ]
    layer = {
        key: value
        for key, value in source_layer.items()
        if key not in {"static_feature_count", "static_facets"}
    }
    layer.update(
        geojson={"type": "FeatureCollection", "features": raw_features},
        count=len(features),
    )
    projected_layers = project_modeled_context_layers([layer])
    if record_digest(
        cast(dict[str, Any], projected_layers[0]["geojson"])["features"]
    ) != record_digest(features):
        raise ValueError(
            "normalized source projection differs from retained published features"
        )
    modeled = build_modeled_context_manifest([layer])
    if modeled.get("status") != "available" or modeled.get("feature_count") != len(
        features
    ):
        raise ValueError("populated modeled context manifest is inconsistent")
    destination.mkdir(parents=True)
    modeled_root = destination / "modeled"
    modeled_root.mkdir()
    assets = write_static_atlas_assets(
        modeled_root,
        slug="modeled-source",
        version="retained-pangaea-context",
        point_layers=[],
        polygon_layers=projected_layers,
        scientific_signals=provenance["scientific_signals"],
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(COUNTRIES).regional_scopes
            if scope.key == "nordic"
        )
    )
    document = render_multi_country_map_html(
        "Retained PANGAEA modeled context",
        "retained-pangaea-context",
        "2026-09-28",
        COUNTRIES,
        policy,
        [],
        [layer],
        "./_map_assets",
        static_assets=assets,
    )
    (modeled_root / "index.html").write_text(document)
    map_assets = package / "reporting/assets/map"
    for path in sorted(map_assets.rglob("*")):
        if path.is_file():
            read(path)
    shutil.copytree(map_assets, modeled_root / "_map_assets")
    emitted_payloads = []
    for row in cast(
        list[dict[str, Any]], normalize_asset_inventory(assets.manifest["assets"])
    ):
        if row.get("layer_key") != LAYER_KEY or row["domain"] != "nodes":
            continue
        emitted_payloads.append(
            decode_chunk_script(
                (modeled_root / row["path"]).read_bytes(),
                expected_asset_key=row["asset_key"],
                expected_payload_sha256=row["payload_sha256"],
                expected_payload_encoding=row["payload_encoding"],
                expected_decoded_byte_count=row.get("decoded_byte_count"),
            )
        )
    emitted = collect_retained_features(emitted_payloads)
    if record_digest(emitted) != record_digest(features):
        raise ValueError("modeled candidate changed retained source features")
    native_root = destination / "native"
    render_lra_report(
        native_product,
        expected_manifest_sha256=product_manifest_sha256,
        geometry_path=native_geometry,
        expected_geometry_sha256=geometry_sha256,
        destination=native_root,
        temporal_profile=PROFILE,
    )
    view = json.loads((native_root / "native-view.json").read_bytes())
    native_manifest = json.loads((native_root / "manifest.json").read_bytes())
    for input_relative, checksum in inputs.items():
        if (
            hashlib.sha256((repository / input_relative).read_bytes()).hexdigest()
            != checksum
        ):
            raise ValueError("frozen source input mutated during generation")
    receipt = {
        "schema_version": "atlas-retained-context-frame-candidate.v1",
        "inputs_sha256": inputs,
        "source_atlas_build_id": source_manifest["build_id"],
        "modeled": {
            "build_id": assets.manifest["build_id"],
            "source_feature_count": len(features),
            "source_feature_sha256": record_digest(features),
            "source_features_equal": True,
            "manifest": modeled,
        },
        "native": {
            "product_manifest_sha256": product_manifest_sha256,
            "geometry_sha256": geometry_sha256,
            "native_view_sha256": native_manifest["native_view_sha256"],
            "row_count": len(view["rows"]),
            "missing_value_count": sum(
                row["native_value"] is None for row in view["rows"]
            ),
            "temporal_profile": PROFILE,
            "data_kind": view["data_kind"],
            "scientific_acceptance": view["scientific_acceptance"],
            "publication_authorized": native_manifest["publication_authorized"],
            "posterior_draw_channel": "unavailable_in_retained_paired_view",
        },
        "numerical_execution": "none; render existing retained products only",
    }
    (destination / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "destination", "native-product", "native-geometry"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--product-manifest-sha256", required=True)
    parser.add_argument("--geometry-sha256", required=True)
    args = parser.parse_args()
    receipt = generate_context_frame_candidates(
        args.repository,
        args.destination,
        args.native_product,
        args.native_geometry,
        args.product_manifest_sha256,
        args.geometry_sha256,
    )
    print(
        json.dumps(
            {
                "modeled_source_records": receipt["modeled"]["source_feature_count"],
                "native_rows": receipt["native"]["row_count"],
                "native_view_sha256": receipt["native"]["native_view_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
