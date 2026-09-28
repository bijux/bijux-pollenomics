"""Render a source-bound PANGAEA 937075 atlas for panel browser checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
from typing import Any, cast

from bijux_pollenomics.reporting.geography import build_published_geography_plan
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
from bijux_pollenomics_dev.ci.atlas_browser.context_frame_candidate import (
    collect_retained_features,
    record_digest,
)

COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
LAYER_KEY = "landclim-reveals-temporal-grid"
METRICS = ("ET", "ST", "OL", "AL")


def panel_rows(csv_bytes: bytes, report: dict[str, Any]) -> list[dict[str, str]]:
    """Validate the retained panel inventory before using it as a browser oracle."""
    if hashlib.sha256(csv_bytes).hexdigest() != report["csv_sha256"]:
        raise ValueError("modeled panel CSV digest mismatch")
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode())))
    if len(rows) != report["row_count"] or len(rows) != 400:
        raise ValueError("modeled panel row count mismatch")
    keys = {(row["country"], row["source_window"], row["metric_key"]) for row in rows}
    if len(keys) != len(rows) or {row["metric_key"] for row in rows} != set(METRICS):
        raise ValueError("modeled panel key topology mismatch")
    return rows


def generate_modeled_panel_candidate(
    repository: Path, destination: Path
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
        raw = path.read_bytes()
        key = path.resolve().relative_to(repository).as_posix()
        digest = hashlib.sha256(raw).hexdigest()
        if key in inputs and inputs[key] != digest:
            raise ValueError("source input mutated during rendering")
        inputs[key] = digest
        return raw

    panel_root = repository / "docs/report/regions/nordic/landclim-modeled-panels"
    panel_report = json.loads(read(panel_root / "report.json"))
    rows = panel_rows(read(panel_root / "panels.csv"), panel_report)
    normalized_path = repository / panel_report["inputs"][0]["path"]
    normalized_bytes = read(normalized_path)
    if (
        hashlib.sha256(normalized_bytes).hexdigest()
        != panel_report["inputs"][0]["sha256"]
    ):
        raise ValueError("modeled panel normalized source digest mismatch")
    raw_taxonomy = repository / panel_report["inputs"][1]["path"]
    if (
        hashlib.sha256(read(raw_taxonomy)).hexdigest()
        != panel_report["inputs"][1]["sha256"]
    ):
        raise ValueError("modeled panel source taxonomy digest mismatch")
    read(Path(__file__))
    read(
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/context_frame_candidate.py"
    )

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
        raw = read(retained / row["path"])
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("retained atlas chunk digest mismatch")
        return decode_chunk_script(
            raw,
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
    retained_features = [
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
    source_by_id = {
        feature["properties"]["record_id"]: feature
        for feature in json.loads(normalized_bytes)["features"]
        if feature["properties"]["dataset_id"] == "937075"
    }
    raw_features = [
        source_by_id[feature["properties"]["record_id"]]
        for feature in retained_features
    ]
    layer = {
        key: value
        for key, value in source_layer.items()
        if key not in {"static_feature_count", "static_facets"}
    }
    layer.update(
        geojson={"type": "FeatureCollection", "features": raw_features},
        count=len(raw_features),
    )
    projected = project_modeled_context_layers([layer])
    if record_digest(
        cast(dict[str, Any], projected[0]["geojson"])["features"]
    ) != record_digest(retained_features):
        raise ValueError("source projection differs from retained published features")
    manifest = build_modeled_context_manifest([layer])
    if manifest.get("status") != "available" or len(retained_features) != 1875:
        raise ValueError("populated modeled context manifest is inconsistent")

    destination.mkdir(parents=True)
    assets = write_static_atlas_assets(
        destination,
        slug="modeled-panel-source",
        version="retained-pangaea-panel-context",
        point_layers=[],
        polygon_layers=projected,
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
        "Retained PANGAEA modeled panels",
        "retained-pangaea-panel-context",
        "2026-09-28",
        COUNTRIES,
        policy,
        [],
        [layer],
        "./_map_assets",
        static_assets=assets,
    )
    (destination / "index.html").write_text(document)
    package = repository / "packages/bijux-pollenomics/src/bijux_pollenomics"
    for domain in ("reporting", "core"):
        for path in sorted((package / domain).rglob("*")):
            if path.is_file() and path.suffix in {".py", ".html", ".js"}:
                read(path)
    map_assets = package / "reporting/assets/map"
    shutil.copytree(map_assets, destination / "_map_assets")
    for path in sorted(map_assets.rglob("*")):
        if path.is_file():
            read(path)
    for key, digest in inputs.items():
        if hashlib.sha256((repository / key).read_bytes()).hexdigest() != digest:
            raise ValueError("frozen source input mutated during rendering")
    receipt = {
        "schema_version": "atlas-modeled-panel-candidate.v1",
        "inputs_sha256": inputs,
        "source_atlas_build_id": source_manifest["build_id"],
        "source_feature_count": len(retained_features),
        "source_feature_sha256": record_digest(retained_features),
        "source_features_equal": True,
        "manifest": manifest,
        "panel_rows": len(rows),
        "panel_csv_sha256": panel_report["csv_sha256"],
        "scientific_admission": False,
        "numerical_execution": "none; render retained modeled source records only",
    }
    (destination / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    result = generate_modeled_panel_candidate(args.repository, args.destination)
    print(
        json.dumps(
            {
                "source_features": result["source_feature_count"],
                "panel_rows": result["panel_rows"],
            }
        )
    )


if __name__ == "__main__":
    main()
