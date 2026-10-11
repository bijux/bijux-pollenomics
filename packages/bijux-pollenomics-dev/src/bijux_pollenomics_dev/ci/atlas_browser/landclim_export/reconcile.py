"""Reconcile a real Nordic map download with pinned LandClim model cells."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, cast
from zipfile import ZipFile

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.modeled_context.publication_projection import (
    project_modeled_context_layers,
)


def digest(content: bytes) -> str:
    """Hash the exact source bytes used to bind artifact custody."""
    return hashlib.sha256(content).hexdigest()


def canonical(value: object) -> bytes:
    """Encode deterministic JSON bytes for content-bound custody."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def require(condition: bool, message: str) -> None:
    """Refuse a violated source or artifact custody invariant."""
    if not condition:
        raise ValueError(message)


def reconcile(repository: Path, artifact: Path, browser: Path) -> dict[str, object]:
    """Validate browser controls, completed download, source values, and map lineage."""
    repository = repository.resolve()
    artifact = artifact.resolve()
    require(
        artifact.is_relative_to(repository / "artifacts"), "artifact outside repository"
    )
    lineage_root = (
        repository / "docs/report/source-relations/landclim/map-export-lineage"
    )
    lineage = json.loads((lineage_root / "report.json").read_text())
    map_content = (
        repository / "docs/report/regions/nordic/nordic_map.html"
    ).read_text()
    manifest_line = [
        line for line in map_content.splitlines() if "const MODELED_CONTEXT = " in line
    ]
    require(len(manifest_line) == 1, "map model manifest unavailable")
    manifest = json.loads(
        manifest_line[0]
        .split("const MODELED_CONTEXT = ", 1)[1]
        .removesuffix(";")
        .strip()
    )
    families = {
        family["key"]: {metric["key"] for metric in family["metrics"]}
        for family in manifest["metric_families"]
    }
    require(
        {key: len(value) for key, value in families.items()}
        == {"exact_taxa": 31, "source_pft_codes": 13, "source_land_cover_types": 3},
        "source class inventory differs",
    )
    require(
        families["source_land_cover_types"] == {"ET", "ST", "OL"}
        and "AL" in families["source_pft_codes"],
        "source class boundary differs",
    )
    for entry in lineage["inputs"]:
        if entry["path"] in {
            "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
            "docs/report/regions/nordic/nordic_map.html",
        }:
            content = (repository / entry["path"]).read_bytes()
            require(
                len(content) == entry["bytes"] and digest(content) == entry["sha256"],
                f"pinned input changed: {entry['path']}",
            )
    rows_content = (lineage_root / "rows.csv").read_bytes()
    require(
        digest(rows_content) == lineage["rows_csv_sha256"],
        "pinned country/window ledger changed",
    )
    rows = list(csv.DictReader(rows_content.decode().splitlines()))
    selected_rows = [
        row
        for row in rows
        if row["source_window"] == "0-100 BP"
        and row["country"] in {"Denmark", "Sweden"}
    ]
    require(len(selected_rows) == 2, "selected ledger rows unavailable")
    source_path = (
        repository
        / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
    )
    source = json.loads(source_path.read_bytes())
    layer = build_external_polygon_layer(source, source_path=source_path)
    projected_layer = cast(
        dict[str, Any], project_modeled_context_layers([layer])[0]["geojson"]
    )
    projected = cast(list[dict[str, Any]], projected_layer["features"])
    expected = {
        feature["properties"]["record_id"]: feature
        for feature in projected
        if feature["properties"].get("dataset_id") == "937075"
        and feature["properties"].get("time_label") == "0-100 BP"
        and feature["properties"].get("country") in {"Denmark", "Sweden"}
    }
    require(len(expected) == 32, "normalized selected denominator changed")
    archive_path = repository / "data/landclim/raw/landclim_ii_reveals_results.zip"
    archive_identity = next(
        entry
        for entry in lineage["inputs"]
        if entry["path"] == "data/landclim/raw/landclim_ii_reveals_results.zip"
    )
    require(
        digest(archive_path.read_bytes()) == archive_identity["sha256"],
        "source archive changed",
    )
    with ZipFile(archive_path) as archive:
        member = "LANDCLIMII.RV.means.JUN2021/TW25.RV.estimates.jun21.csv"
        raw_centers = {
            row["LCGRID_ID"]: (float(row["lonDD"]), float(row["latDD"]))
            for row in csv.DictReader(archive.read(member).decode().splitlines())
            if row["lonDD"] != "#N/A" and row["latDD"] != "#N/A"
        }

    observation = json.loads((artifact / "browser-observation.json").read_bytes())
    require(
        observation["control_state"]["selected_countries"] == ["Denmark", "Sweden"],
        "browser country controls differ",
    )
    require(
        observation["control_state"]["source_window"].startswith("0-100 BP ·"),
        "browser window control differs",
    )
    require(
        observation["control_state"]["modeled_toggle_pressed"] == "true",
        "browser modeled panel inactive",
    )
    require(
        observation["visible_state"].startswith(
            "32 visible cells · 3/32 explicitly have no pollen data"
        ),
        "browser visible state differs",
    )
    filename = observation["download_filename"]
    require(
        filename == "pangaea-937075-ol-0-100-bp.geojson",
        "browser download filename differs",
    )
    raw = (artifact / "downloads" / filename).read_bytes()
    require(len(raw) == observation["download_bytes"], "download byte count differs")
    events = observation["download_events"]
    starts = [
        event["params"]
        for event in events
        if event["method"] == "Browser.downloadWillBegin"
    ]
    require(
        len(starts) == 1 and starts[0]["suggestedFilename"] == filename,
        "browser download begin event absent",
    )
    completes = [
        event["params"]
        for event in events
        if event["method"] == "Browser.downloadProgress"
        and event["params"].get("state") == "completed"
    ]
    require(
        len(completes) == 1
        and completes[0]["guid"] == starts[0]["guid"]
        and completes[0]["receivedBytes"] == len(raw),
        "browser download completion event absent",
    )
    payload = json.loads(raw)
    require(
        payload["type"] == "FeatureCollection"
        and payload["schema_version"] == "modeled-context-visible-frame.v3",
        "download schema differs",
    )
    metadata = payload["modeled_context"]
    require(
        "scenario" not in metadata and "scenario_id" not in metadata,
        "download scenario contract changed",
    )
    require(
        metadata["dataset_id"] == lineage["dataset_id"]
        and metadata["dataset_doi"] == lineage["dataset_doi"],
        "model source citation differs",
    )
    require(
        metadata["method_citation"] == lineage["method_citation"]
        and metadata["method_doi"] == lineage["method_doi"],
        "method citation differs",
    )
    require(
        metadata["metric_family_key"] == "source_land_cover_types"
        and metadata["metric_key"] == "OL",
        "selected source class differs",
    )
    require(
        metadata["value_unit"] == lineage["value_unit"] == "percentage_cover",
        "model unit differs",
    )
    require(
        metadata["source_window"]["label"] == "0-100 BP"
        and metadata["source_window"]["time_start_bp"] == 0
        and metadata["source_window"]["time_end_bp"] == 100,
        "source time window differs",
    )
    require(
        metadata["country_counts"] == {"Denmark": 6, "Sweden": 26},
        "download country counts differ",
    )
    require(
        metadata["quality_class_counts"]
        == {"high": 15, "low": 14, "no_pollen_data": 3},
        "download quality counts differ",
    )
    require(
        metadata["quality_class_count_denominator"] == 32,
        "download quality denominator differs",
    )
    require(
        metadata["evidence_role"] == "context_only"
        and metadata["propagation_use_allowed"] is False
        and metadata["interpolation_allowed"] is False,
        "model evidence role differs",
    )
    require(
        metadata["no_pollen_data_display_posture"] == "null_not_zero",
        "null posture differs",
    )
    require(
        metadata["metric_count_denominator"] == lineage["metric_count"] == 47,
        "metric denominator differs",
    )
    require(
        metadata["estimate_standard_error_pair_count_denominator"]
        == lineage["estimate_standard_error_pair_count"],
        "pair denominator differs",
    )
    features = payload["features"]
    actual = {feature["properties"]["record_id"]: feature for feature in features}
    require(
        len(features) == len(actual) == len(expected),
        "download record ID inventory differs",
    )
    require(
        set(actual) == set(expected), "download record IDs differ from normalized map"
    )
    for record_id in sorted(expected):
        require(
            actual[record_id] == expected[record_id],
            f"download feature differs from normalized map: {record_id}",
        )
    metric_keys = set(next(iter(features))["properties"]["reconstruction_values"])
    require(len(metric_keys) == 47, "download metric keys differ")
    quality: Counter[str] = Counter()
    numeric_pairs = null_pairs = zero_estimates = zero_standard_errors = 0
    for feature in features:
        props = feature["properties"]
        require(
            props["dataset_id"] == "937075"
            and props["country"] in {"Denmark", "Sweden"},
            "feature source/country differs",
        )
        require(
            props["time_label"] == "0-100 BP"
            and props["time_start_bp"] == 0
            and props["time_end_bp"] == 100,
            "feature time window differs",
        )
        require(
            props["source_url"] == lineage["dataset_doi"]
            and props["value_unit"] == "percentage_cover",
            "feature provenance differs",
        )
        require(
            props["temporal_semantics"]["evidence_class"]
            == "modeled_vegetation_time_window",
            "feature source class differs",
        )
        center = raw_centers.get(str(props["parent_grid_record_id"]))
        if center is None:
            raise ValueError("download grid ID absent from published source centers")
        longitude, latitude = center
        expected_ring = [
            [longitude - 0.5, latitude - 0.5],
            [longitude + 0.5, latitude - 0.5],
            [longitude + 0.5, latitude + 0.5],
            [longitude - 0.5, latitude + 0.5],
            [longitude - 0.5, latitude - 0.5],
        ]
        require(
            feature["geometry"] == {"type": "Polygon", "coordinates": [expected_ring]},
            "derived polygon differs from published source center",
        )
        values, errors = props["reconstruction_values"], props["standard_errors"]
        require(
            set(values) == set(errors) == metric_keys,
            "estimate/SE key topology differs",
        )
        quality[props["quality_class"]] += 1
        for key in metric_keys:
            estimate, error = values[key], errors[key]
            require((estimate is None) == (error is None), "estimate/SE pair mismatch")
            if estimate is None:
                require(
                    props["quality_class"] == "no_pollen_data",
                    "null outside unavailable model cell",
                )
                null_pairs += 1
            else:
                require(
                    type(estimate) in {int, float} and type(error) in {int, float},
                    "non-numeric model pair",
                )
                require(
                    props["quality_class"] != "no_pollen_data",
                    "unavailable model cell exported numerically",
                )
                numeric_pairs += 1
                zero_estimates += estimate == 0
                zero_standard_errors += error == 0
    for row in selected_rows:
        selected = sorted(
            (
                feature
                for feature in features
                if feature["properties"]["country"] == row["country"]
            ),
            key=lambda feature: feature["properties"]["record_id"],
        )
        require(
            len(selected) == int(row["cell_count"]),
            f"ledger cell count differs: {row['country']}",
        )
        # JavaScript JSON.stringify omits integral float suffixes (8.0 -> 8).
        # The ledger hashes parsed static map numbers; compare its projection
        # after exact parsed-value equality with the browser download.
        projected_selected = sorted(
            (
                feature
                for feature in expected.values()
                if feature["properties"]["country"] == row["country"]
            ),
            key=lambda feature: feature["properties"]["record_id"],
        )
        require(
            digest(canonical(projected_selected)) == row["selected_features_sha256"],
            f"ledger feature digest differs: {row['country']}",
        )
        by_quality = Counter(
            feature["properties"]["quality_class"] for feature in selected
        )
        for quality_class in ("high", "low", "no_pollen_data"):
            require(
                by_quality[quality_class] == int(row[f"{quality_class}_count"]),
                f"ledger quality count differs: {row['country']}",
            )
    require(
        numeric_pairs == sum(int(row["paired_numeric_count"]) for row in selected_rows),
        "ledger numeric pairs differ",
    )
    require(
        null_pairs == sum(int(row["null_pair_count"]) for row in selected_rows),
        "ledger null pairs differ",
    )
    require(
        sum(quality.values()) == 32 and quality["no_pollen_data"] == 3,
        "download quality tally differs",
    )
    require(
        "crs" not in payload and all("crs" not in feature for feature in features),
        "unexpected explicit CRS changed",
    )
    browser_version = subprocess.check_output(
        [str(browser), "--version"], text=True
    ).strip()
    return {
        "schema_version": "landclim-browser-export.v1",
        "status": "executed_browser_download_reconciled",
        "reference_product_head": "555ef191dbd8fe3672b30e2c60dbb9ad790c0e0d",
        "browser": browser_version,
        "download_filename": filename,
        "download_bytes": len(raw),
        "download_sha256": digest(raw),
        "download_completed_event": True,
        "source_window": {"label": "0-100 BP", "younger_bp": 0, "older_bp": 100},
        "countries": {"Denmark": 6, "Sweden": 26},
        "feature_count": len(features),
        "record_ids_exactly_match_normalized_projection": True,
        "all_parsed_feature_properties_and_geometry_match_normalized_projection": True,
        "normalized_projection_feature_digests_match_pinned_ledger": True,
        "download_number_lexemes_may_differ_from_ledger": True,
        "metric_count": len(metric_keys),
        "source_metric_family_counts": {
            key: len(value) for key, value in families.items()
        },
        "metric_keys_match_between_estimates_and_standard_errors": True,
        "numeric_pair_count": numeric_pairs,
        "null_pair_count": null_pairs,
        "numeric_zero_estimate_count": zero_estimates,
        "numeric_zero_standard_error_count": zero_standard_errors,
        "quality_class_counts": dict(sorted(quality.items())),
        "source_class_boundary": lineage["source_class_boundary"],
        "dataset_doi": metadata["dataset_doi"],
        "method_citation": metadata["method_citation"],
        "method_doi": metadata["method_doi"],
        "scenario_identity": lineage["scenario_identity"],
        "download_has_explicit_scenario_field": False,
        "evidence_role": metadata["evidence_role"],
        "propagation_use_allowed": False,
        "interpolation_allowed": False,
        "geometry_crs": "not_explicit_in_download;coordinate_interpretation_requires_source_policy_and_geojson_spec",
        "download_polygons_are_one_degree_squares_on_published_source_centers": True,
        "published_source_centers_verified": len(features),
        "pinned_lineage_report_sha256": digest(
            (lineage_root / "report.json").read_bytes()
        ),
        "pinned_normalized_geojson_sha256": next(
            entry["sha256"]
            for entry in lineage["inputs"]
            if entry["path"]
            == "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
        ),
        "pinned_map_html_sha256": next(
            entry["sha256"]
            for entry in lineage["inputs"]
            if entry["path"] == "docs/report/regions/nordic/nordic_map.html"
        ),
        "pinned_ledger_sha256": lineage["rows_csv_sha256"],
    }


def main() -> None:
    """Reconcile pinned LandClim sources with the retained browser export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = reconcile(arguments.repository, arguments.artifact, arguments.browser)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "feature_count",
                    "numeric_pair_count",
                    "null_pair_count",
                    "download_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
