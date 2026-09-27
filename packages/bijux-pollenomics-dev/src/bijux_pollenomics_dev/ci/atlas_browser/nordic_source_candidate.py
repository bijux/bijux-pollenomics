"""Produce eight authenticated retained source contexts for Nordic browser replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

SOURCE_SELECTION = {
    "Denmark": {"neotoma-pollen": "neotoma:site:27349", "sead-sites": "sead:site:3797"},
    "Finland": {"neotoma-pollen": "neotoma:site:2966", "sead-sites": "sead:site:5070"},
    "Norway": {"neotoma-pollen": "neotoma:site:26128", "sead-sites": "sead:site:5119"},
    "Sweden": {"neotoma-pollen": "neotoma:site:12", "sead-sites": "sead:site:6468"},
}


def digest(value: Any) -> str:
    """Identify the exact retained JSON record without dependence on key ordering."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def generate_nordic_source_candidate(
    repository: Path, destination: Path
) -> dict[str, Any]:
    repository, destination = repository.resolve(), destination.resolve()
    if not destination.is_relative_to(repository / "artifacts"):
        raise ValueError("candidate must be generated under repository artifacts")
    if destination.exists():
        raise ValueError("candidate destination must be absent")
    retained = repository / "docs/report/regions/nordic"
    inputs: dict[str, str] = {}

    def read(path: Path) -> bytes:
        if path.is_symlink() or not path.is_file():
            raise ValueError("source input must be a regular file")
        payload = path.read_bytes()
        key, checksum = (
            path.relative_to(repository).as_posix(),
            hashlib.sha256(payload).hexdigest(),
        )
        if key in inputs and inputs[key] != checksum:
            raise ValueError("source input mutated during generation")
        inputs[key] = checksum
        return payload

    reporting = (
        repository / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting"
    )
    for path in sorted((reporting / "map_document").rglob("*")):
        if path.is_file() and path.suffix in {".py", ".html", ".js"}:
            read(path)
    for path in (
        reporting / "geography.py",
        reporting / "map_publication.py",
        Path(__file__).resolve(),
    ):
        if path.is_relative_to(repository) and path.is_file():
            read(path)
    bootstrap = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        read(retained / "nordic_map.html").decode(),
        re.S,
    )
    if bootstrap is None:
        raise ValueError("retained atlas bootstrap is absent")
    manifest = json.loads(bootstrap.group(1))
    inventory = normalize_asset_inventory(manifest["assets"])

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
    indexes = decode_index_bundle(
        chunk(next(row for row in inventory if row["domain"] == "indexes"))
    )
    layers, details, summaries = [], [], []
    for layer_key in ("neotoma-pollen", "sead-sites"):
        source_layer = next(
            entry["layer"]
            for entry in provenance["layers"]
            if entry["layer"]["key"] == layer_key
        )
        features = []
        for country, selections in SOURCE_SELECTION.items():
            record_id = selections[layer_key]
            matches = []
            for row in inventory:
                if (
                    row["domain"] == "nodes"
                    and row["layer_key"] == layer_key
                    and row["country_keys"] == [country]
                ):
                    matches.extend(
                        feature
                        for feature in chunk(row)["features"]
                        if feature["record_id"] == record_id
                    )
            if len(matches) != 1:
                raise ValueError("source site identity is missing or duplicated")
            feature = matches[0]
            key = indexes["detail_record_asset_keys"][record_id]
            detail_matches = [
                record
                for record in chunk(
                    next(row for row in inventory if row["asset_key"] == key)
                )["records"]
                if record["record_id"] == record_id
            ]
            if len(detail_matches) != 1:
                raise ValueError("source detail identity is missing or duplicated")
            detail = detail_matches[0]
            features.append(feature)
            details.append(detail)
            summaries.append(
                {
                    "country": country,
                    "layer_key": layer_key,
                    "record_id": record_id,
                    "feature_identity": f"evidence:{feature['evidence_row_id']}",
                    "title": feature["title"],
                    "feature_sha256": digest(feature),
                    "detail_record_sha256": digest(detail),
                    "chronology": detail["tabs"]["chronology"],
                    "source_provenance": detail["tabs"]["provenance"],
                    "classification": detail["tabs"]["classification"],
                    "relation": detail["tabs"]["relation"],
                }
            )
        layer = {
            key: value
            for key, value in source_layer.items()
            if key not in {"static_feature_count", "static_facets"}
        }
        layer.update(features=features, count=len(features), default_enabled=True)
        layer["coverage_label"] = (
            "One exact retained source site per Nordic country; geographic context only."
        )
        layers.append(layer)
    destination.mkdir(parents=True)
    assets = write_static_atlas_assets(
        destination,
        slug="nordic-source",
        version="retained-source-context",
        point_layers=layers,
        polygon_layers=[],
        detail_records=details,
        scientific_signals=provenance["scientific_signals"],
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                tuple(SOURCE_SELECTION)
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    document = render_multi_country_map_html(
        "Nordic retained source contexts",
        "retained-source-context",
        "2026-09-27",
        tuple(SOURCE_SELECTION),
        policy,
        layers,
        [],
        "./_map_assets",
        static_assets=assets,
    )
    (destination / "index.html").write_text(document)
    map_assets = reporting / "assets/map"
    for path in sorted(map_assets.rglob("*")):
        if path.is_file():
            read(path)
    shutil.copytree(map_assets, destination / "_map_assets")
    # Authenticate the writer output against the selected source records as well.
    emitted_details, emitted_features = {}, {}
    for row in normalize_asset_inventory(assets.manifest["assets"]):
        if row["domain"] not in {"details", "nodes"}:
            continue
        payload = decode_chunk_script(
            (destination / row["path"]).read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row.get("decoded_byte_count"),
        )
        for record in payload.get("records", []):
            emitted_details[record["record_id"]] = digest(record)
        for feature in payload.get("features", []):
            emitted_features[feature["record_id"]] = digest(feature)
    for record in summaries:
        if (
            emitted_details.get(record["record_id"]) != record["detail_record_sha256"]
            or emitted_features.get(record["record_id"]) != record["feature_sha256"]
        ):
            raise ValueError("candidate changed a retained source record")
    for path, checksum in inputs.items():
        if hashlib.sha256((repository / path).read_bytes()).hexdigest() != checksum:
            raise ValueError("frozen source input mutated during generation")
    receipt = {
        "schema_version": "atlas-nordic-retained-source-candidate.v1",
        "source_atlas_build_id": manifest["build_id"],
        "candidate_build_id": assets.manifest["build_id"],
        "inputs_sha256": inputs,
        "source_records": summaries,
        "countries": list(SOURCE_SELECTION),
        "selected_source_record_equality": True,
        "scientific_posture": "retained source display only; no accepted classifications or propagation edges; preserve unresolved/refused/context-only claims",
    }
    (destination / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    receipt = generate_nordic_source_candidate(args.repository, args.destination)
    print(
        json.dumps(
            {
                "candidate_build_id": receipt["candidate_build_id"],
                "record_count": len(receipt["source_records"]),
            }
        )
    )


if __name__ == "__main__":
    main()
