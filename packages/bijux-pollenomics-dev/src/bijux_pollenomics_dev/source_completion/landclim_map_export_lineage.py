"""Reconcile governed LandClim model cells with the published Nordic map transport."""

from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.modeled_context import build_modeled_context_manifest
from bijux_pollenomics.reporting.modeled_context.publication_projection import (
    project_modeled_context_layers,
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
PREFIX = (
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
)


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


def _map_manifest(page: str) -> dict[str, Any]:
    marker = "const MODELED_CONTEXT = "
    matches = [line for line in page.splitlines() if marker in line]
    _require(len(matches) == 1, "Nordic map model manifest binding changed")
    return cast(
        dict[str, Any],
        json.loads(matches[0].split(marker, 1)[1].removesuffix(";").strip()),
    )


def _published_features(repository: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    features: list[dict[str, Any]] = []
    paths: list[Path] = []
    for path in sorted((repository / CHUNKS).glob("nordic.atlas-nodes.*.js")):
        content = path.read_text()
        _require(
            content.startswith(PREFIX) and content.endswith(");\n"),
            f"Atlas chunk wrapper changed: {path.name}",
        )
        envelope = json.loads(content[len(PREFIX) : -3])
        if envelope["payload_encoding"] == "gzip_base64":
            payload = gzip.decompress(
                base64.b64decode(envelope["payload_gzip_base64"], validate=True)
            )
        else:
            payload = envelope["payload_json"].encode()
        _require(
            _digest(payload) == envelope["payload_sha256"],
            f"Atlas payload digest changed: {path.name}",
        )
        chunk = json.loads(payload)
        if chunk.get("layer_key") != "landclim-reveals-temporal-grid":
            continue
        paths.append(path)
        features.extend(chunk["features"])
    _require(bool(paths), "No published LandClim model shards")
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
    _require(
        _map_manifest(page) == manifest,
        "Published map model manifest differs from governed source",
    )
    _export_contract(page)
    projected = cast(
        list[dict[str, Any]],
        cast(dict[str, Any], project_modeled_context_layers([layer])[0]["geojson"])[
            "features"
        ],
    )
    expected = _by_id(projected)
    actual_features, shard_paths = _published_features(repository)
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
