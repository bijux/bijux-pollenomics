"""Publish source-bound Nordic LandClim model panels and uncertainty ranges."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.modeled_context import build_modeled_context_manifest
from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_COUNTRY_CELL_COUNTS,
    PANGAEA_DATASET_DOI,
)

SOURCE = Path("data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson")
MAPPING = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")
METRICS = (
    ("ET", "Evergreen trees", "source_land_cover_type"),
    ("ST", "Summer-green trees", "source_land_cover_type"),
    ("OL", "Open land", "source_land_cover_type"),
    ("AL", "Agricultural land - cereals", "source_pft_component_of_open_land"),
)
FIELDS = (
    "country",
    "source_window",
    "younger_bp",
    "older_bp",
    "metric_key",
    "source_label",
    "source_class",
    "cell_count",
    "modeled_count",
    "high_quality_count",
    "low_quality_count",
    "no_pollen_data_count",
    "minimum_estimate_percent",
    "maximum_estimate_percent",
    "minimum_standard_error_percent",
    "maximum_standard_error_percent",
)


def _identity(path: Path, repository: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _range(values: list[float]) -> tuple[str, str]:
    if not values:
        return "", ""
    return format(min(values), ".12g"), format(max(values), ".12g")


def _require_source_labels(mapping_path: Path) -> None:
    with mapping_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    land_cover_labels = {
        row["Land-cover types (LCTs)"] for row in rows if row["Land-cover types (LCTs)"]
    }
    if land_cover_labels != {
        "Evergreen trees (ET)",
        "Summer-green trees (ST)",
        "Open land (OL)",
    }:
        raise ValueError("PANGAEA land-cover source labels changed")
    if not any(
        row["PFT"] == "AL" and row["PFT definition"] == "Agricultural land - cereals"
        for row in rows
    ):
        raise ValueError("PANGAEA agricultural PFT source label changed")


def derive(
    geojson: dict[str, Any], manifest: dict[str, Any]
) -> list[dict[str, object]]:
    """Summarize only usable modeled rows, without aggregating uncertainty."""
    if manifest.get("status") != "available" or manifest.get("dataset_id") != "937075":
        raise ValueError("Complete PANGAEA 937075 model manifest required")
    families = {
        family["key"]: {metric["key"]: metric for metric in family["metrics"]}
        for family in manifest["metric_families"]
    }
    for key, label, source_class in METRICS:
        family = "source_pft_codes" if key == "AL" else "source_land_cover_types"
        metric = families[family].get(key)
        if metric is None or metric["definition"] != label:
            raise ValueError(f"Source metric label changed: {key}")
        if key == "AL" and source_class != "source_pft_component_of_open_land":
            raise ValueError("Agricultural PFT must remain a component of open land")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for feature in geojson["features"]:
        properties = feature["properties"]
        if properties.get("dataset_id") == "937075":
            groups[(properties["country"], properties["time_label"])].append(properties)
    rows: list[dict[str, object]] = []
    for window in manifest["windows_oldest_to_present"]:
        for country, expected_count in PANGAEA_COUNTRY_CELL_COUNTS.items():
            members = groups[(country, window["label"])]
            if len(members) != expected_count:
                raise ValueError("Modeled country/window inventory changed")
            usable = [
                member
                for member in members
                if member["quality_class"] != "no_pollen_data"
            ]
            high_count = sum(member["quality_class"] == "high" for member in members)
            low_count = sum(member["quality_class"] == "low" for member in members)
            absent_count = expected_count - len(usable)
            if (high_count, low_count, absent_count) != tuple(
                window["country_quality_class_counts"][country][quality]
                for quality in ("high", "low", "no_pollen_data")
            ):
                raise ValueError("Modeled country/window quality inventory changed")
            for key, label, source_class in METRICS:
                estimates = [
                    float(member["reconstruction_values"][key]) for member in usable
                ]
                errors = [float(member["standard_errors"][key]) for member in usable]
                estimate_min, estimate_max = _range(estimates)
                error_min, error_max = _range(errors)
                rows.append(
                    {
                        "country": country,
                        "source_window": window["label"],
                        "younger_bp": window["time_start_bp"],
                        "older_bp": window["time_end_bp"],
                        "metric_key": key,
                        "source_label": label,
                        "source_class": source_class,
                        "cell_count": expected_count,
                        "modeled_count": len(usable),
                        "high_quality_count": high_count,
                        "low_quality_count": low_count,
                        "no_pollen_data_count": absent_count,
                        "minimum_estimate_percent": estimate_min,
                        "maximum_estimate_percent": estimate_max,
                        "minimum_standard_error_percent": error_min,
                        "maximum_standard_error_percent": error_max,
                    }
                )
    if len(rows) != 25 * 4 * len(METRICS):
        raise ValueError("Modeled panel inventory is incomplete")
    return rows


def run(repository: Path, output: Path) -> Path:
    """Write a deterministic review under a new repository artifact directory."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    source_path, mapping_path = repository / SOURCE, repository / MAPPING
    _require_source_labels(mapping_path)
    source = json.loads(source_path.read_text())
    layer = build_external_polygon_layer(source, source_path=source_path)
    manifest = cast(dict[str, Any], build_modeled_context_manifest([layer]))
    rows = derive(source, manifest)
    output.mkdir(parents=True)
    with (output / "panels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": "landclim-modeled-panels.v1",
        "source": PANGAEA_DATASET_DOI,
        "evidence_role": "modeled_context",
        "unit": "percentage_cover",
        "aggregation": "cellwise_minimum_maximum_only;standard_errors_not_pooled",
        "inputs": [
            _identity(source_path, repository),
            _identity(mapping_path, repository),
        ],
        "window_count": len(manifest["windows_oldest_to_present"]),
        "country_count": len(PANGAEA_COUNTRY_CELL_COUNTS),
        "panel_count": len(METRICS),
        "row_count": len(rows),
        "source_cell_window_count": manifest["feature_count"],
        "no_pollen_data_cell_window_count": manifest["quality_class_counts"][
            "no_pollen_data"
        ],
        "csv_sha256": hashlib.sha256((output / "panels.csv").read_bytes()).hexdigest(),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.repository, args.output))


if __name__ == "__main__":
    main()
