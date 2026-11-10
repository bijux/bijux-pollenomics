"""Reconcile governed LandClim model cells with the published Nordic map transport."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.map_document.render import (
    _FixedJsonBindings,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.modeled_context import build_modeled_context_manifest
from bijux_pollenomics.reporting.modeled_context.publication_projection import (
    project_modeled_context_layers,
)
from bijux_pollenomics_dev.ci.atlas_browser.candidate_files import regular_bytes
from bijux_pollenomics_dev.ci.atlas_browser.published_runtime import (
    read_published_runtime,
)

SOURCE = Path("data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson")
MAP = Path("docs/report/regions/nordic/nordic_map.html")
CHUNKS = Path("docs/report/regions/nordic")
OVERLAP = Path("docs/report/source-relations/rootsi-landclim-overlap/report.json")
NEOTOMA = Path(
    "docs/report/source-relations/neotoma/landclim-site-identity/report.json"
)
SWEDISH_LINEAGE = Path("docs/report/countries/sweden/pollen-model-lineage/report.json")
SEAD_CONTEXT = Path(
    "docs/report/countries/sweden/observed-pollen-trajectory/report.json"
)
RECEIPT = Path("data/landclim/raw/landclim_sources.json")
ARCHIVE = Path("data/landclim/raw/landclim_ii_reveals_results.zip")
FIELDS = (
    "country",
    "source_window",
    "younger_bp",
    "older_bp",
    "cell_count",
    "high_count",
    "low_count",
    "no_pollen_data_count",
    "metric_count",
    "paired_numeric_count",
    "null_pair_count",
    "selected_features_sha256",
)
ASSETS = CHUNKS / "nordic_map_assets.json"
_LAYER_KEY = "landclim-reveals-temporal-grid"


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _identity(repository: Path, path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(content),
        "sha256": _digest(content),
    }


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _map_manifest(page: str, *, script: str | None = None) -> dict[str, Any]:
    if script is not None:
        parser = _FixedJsonBindings()
        parser.feed(page)
        parser.close()
        bindings = parser.bindings["atlas-modeled-context-binding"]
        _require(
            len(bindings) == 1
            and bindings[0] is not None
            and "const MODELED_CONTEXT = JSON.parse(document.getElementById('atlas-modeled-context-binding').textContent);"
            in script,
            "Published modeled-context JSON binding differs",
        )
        value = json.loads("".join(cast(list[str], bindings[0])))
        _require(isinstance(value, dict), "Published modeled context is not an object")
        return cast(dict[str, Any], value)
    marker = "const MODELED_CONTEXT = "
    matches = [line for line in page.splitlines() if marker in line]
    _require(len(matches) == 1, "Nordic map model manifest binding changed")
    return cast(
        dict[str, Any],
        json.loads(matches[0].split(marker, 1)[1].removesuffix(";").strip()),
    )


def _published_path(repository: Path, name: str) -> Path:
    _require(
        bool(name)
        and Path(name).name == name
        and name not in {".", ".."}
        and "\\" not in name
        and "\x00" not in name,
        "Published asset path is not a confined basename",
    )
    return repository / CHUNKS / name


def _published_script(repository: Path, page: str) -> tuple[str, list[Path]]:
    """Use the shared authenticated executable graph and preserve inline inputs."""
    manifest = json.loads(regular_bytes(repository / ASSETS))
    runtime = read_published_runtime(
        repository / MAP, repository / ASSETS, page, manifest
    )
    return runtime.script, list(runtime.paths)


def _published_features(
    repository: Path, projected: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[Path]]:
    manifest = json.loads(regular_bytes(repository / ASSETS))
    rows = [
        row
        for row in normalize_asset_inventory(manifest["assets"])
        if row["domain"] == "nodes" and row.get("layer_key") == _LAYER_KEY
    ]
    _require(bool(rows), "No published LandClim model shards")
    expected_count = len(projected)
    _require(
        sum(cast(int, row["record_count"]) for row in rows) == expected_count,
        "Published LandClim declared count differs from source",
    )
    features: list[dict[str, Any]] = []
    paths: list[Path] = []
    indexes: set[int] = set()
    layer_indexes = {row["layer_index"] for row in rows}
    _require(len(layer_indexes) == 1, "LandClim layer identity differs")
    for row in rows:
        path = _published_path(repository, cast(str, row["path"]))
        body = regular_bytes(path)
        _require(
            len(body) == row["byte_count"] and _digest(body) == row["sha256"],
            f"Atlas physical identity changed: {path.name}",
        )
        chunk = decode_chunk_script(
            body,
            expected_asset_key=cast(str, row["asset_key"]),
            expected_payload_sha256=cast(str, row["payload_sha256"]),
            expected_payload_encoding=cast(str, row["payload_encoding"]),
            expected_decoded_byte_count=cast(int, row["decoded_byte_count"]),
        )
        _require(
            chunk.get("schema_version") == manifest["compatibility"]["node_schema"]
            and chunk.get("build_id") == manifest["build_id"]
            and chunk.get("layer_key") == _LAYER_KEY
            and chunk.get("layer_index") == row["layer_index"]
            and chunk.get("layer_kind") == row["layer_kind"] == "polygon",
            "Published LandClim node identity differs",
        )
        raw_features = chunk.get("features")
        raw_indexes = chunk.get("feature_indexes")
        _require(
            isinstance(raw_features, list)
            and isinstance(raw_indexes, list)
            and len(raw_features) == len(raw_indexes) == row["record_count"],
            "Published LandClim node cardinality differs",
        )
        for index, feature in zip(
            cast(list[object], raw_indexes),
            cast(list[Any], raw_features),
            strict=True,
        ):
            _require(
                type(index) is int
                and 0 <= index < expected_count
                and index not in indexes
                and isinstance(feature, dict)
                and feature.get("type") == "Feature"
                and isinstance(feature.get("properties"), dict)
                and feature == projected[index],
                "Published LandClim feature membership differs",
            )
            indexes.add(cast(int, index))
            features.append(feature)
        paths.append(path)
    _require(indexes == set(range(expected_count)), "LandClim index coverage differs")
    return features, paths


def _by_id(features: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed = {str(feature["properties"]["record_id"]): feature for feature in features}
    _require(len(indexed) == len(features), "Duplicate LandClim map record identity")
    return indexed


def _export_contract(page: str) -> None:
    # These are the actual published selectors and serializer, not a parallel export.
    required = (
        "function modeledContextFrameFeatures()",
        "properties.time_label === sourceWindow.label",
        "activeCountries.has(properties.country)",
        "function modeledContextFrameGeoJson()",
        "reconstruction_values: Object.fromEntries",
        "standard_errors: Object.fromEntries",
        "schema_version: MODELED_CONTEXT.download_schema_version",
        "evidence_role: 'context_only'",
        "propagation_use_allowed: false",
        "interpolation_allowed: false",
        "function downloadModeledContextFrame()",
        "modeledContextDownload.addEventListener('click', downloadModeledContextFrame)",
    )
    _require(
        all(part in page for part in required),
        "Published modeled export selector or identity contract changed",
    )


def _source_geometry(repository: Path, features: list[dict[str, Any]]) -> int:
    """Bind derived one-degree polygons to every archived grid center."""
    selected = {
        str(feature["properties"]["parent_grid_record_id"]) for feature in features
    }
    centers: dict[str, tuple[float, float]] = {}
    with ZipFile(repository / ARCHIVE) as archive:
        members = sorted(
            name
            for name in archive.namelist()
            if name.startswith("LANDCLIMII.RV.means.JUN2021/TW")
            and name.endswith(".RV.estimates.jun21.csv")
        )
        _require(len(members) == 25, "Published source window inventory changed")
        for name in members:
            with archive.open(name) as raw:
                for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")):
                    grid_id = row["LCGRID_ID"]
                    if grid_id not in selected:
                        continue
                    center = (float(row["lonDD"]), float(row["latDD"]))
                    _require(
                        grid_id not in centers or centers[grid_id] == center,
                        f"Published source grid center changed: {grid_id}",
                    )
                    centers[grid_id] = center
    _require(set(centers) == selected, "Published source grid centers are incomplete")
    for feature in features:
        grid_id = str(feature["properties"]["parent_grid_record_id"])
        longitude, latitude = centers[grid_id]
        expected = [
            [longitude - 0.5, latitude - 0.5],
            [longitude + 0.5, latitude - 0.5],
            [longitude + 0.5, latitude + 0.5],
            [longitude - 0.5, latitude + 0.5],
            [longitude - 0.5, latitude - 0.5],
        ]
        _require(
            feature["geometry"] == {"type": "Polygon", "coordinates": [expected]},
            f"Derived cell polygon differs from source center: {grid_id}",
        )
    return len(centers)


def derive(repository: Path) -> tuple[dict[str, object], bytes]:
    """Check every static map cell and every four-country source-window slice."""
    repository = repository.resolve()
    source_path, map_path = repository / SOURCE, repository / MAP
    source = json.loads(source_path.read_text())
    _require(
        "crs" not in source
        and all(
            "crs" not in feature and "crs" not in feature["properties"]
            for feature in source["features"]
        ),
        "LandClim normalized CRS declaration changed; review explicit CRS",
    )
    source_features = source["features"]
    layer = build_external_polygon_layer(source, source_path=source_path)
    manifest = cast(dict[str, Any], build_modeled_context_manifest([layer]))
    page = map_path.read_text()
    script, runtime_paths = _published_script(repository, page)
    _require(
        _map_manifest(page, script=script) == manifest
        if runtime_paths
        else _map_manifest(script) == manifest,
        "Published map model manifest differs from governed source",
    )
    _export_contract(script)
    projected = cast(
        list[dict[str, Any]],
        cast(dict[str, Any], project_modeled_context_layers([layer])[0]["geojson"])[
            "features"
        ],
    )
    expected = _by_id(projected)
    actual_features, shard_paths = _published_features(repository, projected)
    actual = _by_id(actual_features)
    _require(
        set(expected) == set(actual),
        "Published LandClim cell/window identity inventory differs",
    )
    for record_id, feature in expected.items():
        _require(
            feature == actual[record_id],
            f"Published LandClim feature differs: {record_id}",
        )
    _require(
        len(expected) == len(source_features) == 2515,
        "LandClim temporal model denominator changed",
    )
    model = [
        feature
        for feature in actual_features
        if feature["properties"].get("dataset_id") == "937075"
    ]
    _require(len(model) == 1875, "PANGAEA 937075 map denominator changed")
    metric_keys = {
        metric["key"]
        for family in manifest["metric_families"]
        for metric in family["metrics"]
    }
    _require(
        len(metric_keys) == manifest["metric_count"] == 47,
        "Source model metric inventory changed",
    )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for feature in model:
        properties = feature["properties"]
        _require(
            properties["value_unit"] == manifest["value_unit"], "Map model unit changed"
        )
        _require(
            properties["source_url"] == manifest["dataset_doi"], "Map model DOI changed"
        )
        _require(
            properties["temporal_semantics"]["evidence_class"]
            == "modeled_vegetation_time_window",
            "Map evidence class changed",
        )
        values, errors = (
            properties["reconstruction_values"],
            properties["standard_errors"],
        )
        _require(
            set(values) == set(errors) == metric_keys, "Map estimate/SE keys differ"
        )
        if properties["quality_class"] == "no_pollen_data":
            _require(
                all(values[key] is None and errors[key] is None for key in metric_keys),
                "No-pollen placeholder exported numerically",
            )
        else:
            _require(
                all(
                    isinstance(values[key], (float, int))
                    and isinstance(errors[key], (float, int))
                    for key in metric_keys
                ),
                "Map estimate/SE pair missing",
            )
        grouped[(properties["country"], properties["time_label"])].append(feature)
    rows: list[dict[str, Any]] = []
    for window in manifest["windows_oldest_to_present"]:
        for country, expected_count in manifest["country_cell_counts"].items():
            selected = sorted(
                grouped[(country, window["label"])],
                key=lambda feature: feature["properties"]["record_id"],
            )
            _require(
                len(selected) == expected_count,
                "Published country/window source count changed",
            )
            counts = Counter(
                feature["properties"]["quality_class"] for feature in selected
            )
            _require(
                dict(counts)
                == {
                    key: count
                    for key, count in window["country_quality_class_counts"][
                        country
                    ].items()
                    if count
                },
                "Country/window quality counts changed",
            )
            rows.append(
                {
                    "country": country,
                    "source_window": window["label"],
                    "younger_bp": window["time_start_bp"],
                    "older_bp": window["time_end_bp"],
                    "cell_count": len(selected),
                    "high_count": counts["high"],
                    "low_count": counts["low"],
                    "no_pollen_data_count": counts["no_pollen_data"],
                    "metric_count": len(metric_keys),
                    "paired_numeric_count": (counts["high"] + counts["low"])
                    * len(metric_keys),
                    "null_pair_count": counts["no_pollen_data"] * len(metric_keys),
                    "selected_features_sha256": _digest(_canonical(selected)),
                }
            )
    _require(len(rows) == 100, "Four-country window inventory changed")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = buffer.getvalue().encode()
    overlap = json.loads((repository / OVERLAP).read_text())
    neotoma = json.loads((repository / NEOTOMA).read_text())
    swedish_lineage = json.loads((repository / SWEDISH_LINEAGE).read_text())
    sead_context = json.loads((repository / SEAD_CONTEXT).read_text())
    receipt = json.loads((repository / RECEIPT).read_text())
    _require(
        overlap["admission"]["grid_window_contributor_lineage_resolved"] is False,
        "Rootsi contributor posture changed",
    )
    _require(
        overlap["admission"]["independent_vegetation_ground_truth"] is False,
        "Rootsi independence posture changed",
    )
    _require(
        neotoma["identity_admitted"] == 0, "Neotoma physical-site decision changed"
    )
    _require(
        swedish_lineage["matched_site_count"] == 3
        and swedish_lineage["targets_sharing_bus_boke_grid"] == 5,
        "Swedish pollen/model candidate overlap changed",
    )
    _require(
        sead_context["source_roles"]["sead"]
        == "independent dated site-location context only, not land-use magnitude",
        "SEAD evidence role changed",
    )
    archive_receipts = [
        asset
        for asset in receipt["assets"]
        if asset["dataset_id"] == "937075" and asset["filename"] == ARCHIVE.name
    ]
    _require(len(archive_receipts) == 1, "LandClim source archive receipt absent")
    archive_identity = _identity(repository, repository / ARCHIVE)
    _require(
        archive_identity["sha256"] == archive_receipts[0]["sha256"]
        and archive_identity["bytes"] == archive_receipts[0]["size_bytes"],
        "LandClim source archive differs from receipt",
    )
    source_centers = _source_geometry(repository, model)
    report: dict[str, object] = {
        "schema_version": "landclim-map-export-lineage.v1",
        "status": "source_to_static_transport_verified",
        "dataset_id": manifest["dataset_id"],
        "dataset_doi": manifest["dataset_doi"],
        "method_citation": manifest["method_citation"],
        "method_doi": manifest["method_doi"],
        "evidence_role": "modeled_context_not_observed_vegetation",
        "scenario_identity": "published_PANGAEA_937075_REVEALS_reconstruction;no_alternative_scenario_asserted",
        "source_metric_families": [
            {"key": family["key"], "metric_count": family["metric_count"]}
            for family in manifest["metric_families"]
        ],
        "source_class_boundary": "ET_ST_OL_source_land_cover_types;AL_source_PFT_component_of_OL",
        "value_unit": manifest["value_unit"],
        "time_basis": "discrete_published_BP_windows",
        "geometry_crs": "not_explicit_in_normalized_geojson_or_download_contract",
        "source_coordinate_policy_url": "https://wiki.pangaea.de/wiki/Geocode",
        "geojson_coordinate_specification_url": "https://www.rfc-editor.org/rfc/rfc7946#section-4",
        "source_center_coordinate_interpretation": "WGS84_by_PANGAEA_geocode_policy;archive_CSV_has_no_CRS_field",
        "derived_polygon_semantics": "one_degree_square_about_source_lonDD_latDD_center",
        "source_grid_center_count": source_centers,
        "source_mean_member_count": 25,
        "derived_polygon_match_count": len(model),
        "source_feature_count": len(source_features),
        "published_feature_count": len(actual),
        "modeled_cell_window_count": len(model),
        "metric_count": len(metric_keys),
        "estimate_standard_error_pair_count": manifest[
            "estimate_standard_error_pair_count"
        ],
        "country_window_slice_count": len(rows),
        "numeric_pair_count": sum(int(row["paired_numeric_count"]) for row in rows),
        "null_pair_count": sum(int(row["null_pair_count"]) for row in rows),
        "rootsi_candidate_pair_count": overlap["denominators"][
            "unique_metadata_candidate_pairs"
        ],
        "rootsi_grid_window_contributor_identity_resolved": False,
        "neotoma_swedish_same_name_candidates": neotoma["same_name_candidates"],
        "neotoma_swedish_physical_identity_admitted": neotoma["identity_admitted"],
        "swedish_neotoma_landclim_site_metadata_candidates": swedish_lineage[
            "matched_site_count"
        ],
        "swedish_synthesis_targets_sharing_bus_boke_grid": swedish_lineage[
            "targets_sharing_bus_boke_grid"
        ],
        "sead_evidence_role": sead_context["source_roles"]["sead"],
        "sead_grid_window_contributor_identity_resolved": False,
        "independent_corroboration_admitted": False,
        "inputs": [
            _identity(repository, path)
            for path in (
                source_path,
                map_path,
                repository / ASSETS,
                *runtime_paths,
                repository / OVERLAP,
                repository / NEOTOMA,
                repository / SWEDISH_LINEAGE,
                repository / SEAD_CONTEXT,
                repository / RECEIPT,
            )
        ]
        + [archive_identity],
        "published_landclim_shards": [
            _identity(repository, path) for path in shard_paths
        ],
        "rows_csv_sha256": _digest(csv_bytes),
    }
    return report, csv_bytes


def main() -> None:
    """Write the bounded audit to an absent repository artifacts directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository, output = args.repository.resolve(), args.output.resolve()
    _require(
        not output.exists() and output.is_relative_to(repository / "artifacts"),
        "Absent repository artifact destination required",
    )
    report, csv_bytes = derive(repository)
    output.mkdir(parents=True)
    (output / "rows.csv").write_bytes(csv_bytes)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
