"""Render a bounded source-owned drawer candidate from authenticated atlas chunks."""

from __future__ import annotations

import argparse
from collections import Counter
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

SITE_IDS = ("neotoma:site:12", "neotoma:site:3009")


def generate_source_detail_candidate(
    repository: Path, destination: Path
) -> dict[str, Any]:
    """Preserve two literal source records and their refusal/chronology support."""
    repository = repository.resolve()
    destination = destination.resolve()
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
        digest = hashlib.sha256(payload).hexdigest()
        key = path.relative_to(repository).as_posix()
        if key in inputs and inputs[key] != digest:
            raise ValueError("source input mutated during generation")
        inputs[key] = digest
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
        if path.is_file() and path.is_relative_to(repository):
            read(path)
    html = read(retained / "nordic_map.html").decode("utf-8")
    bootstrap = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if bootstrap is None:
        raise ValueError("retained atlas bootstrap is absent")
    manifest = json.loads(bootstrap.group(1))
    inventory = normalize_asset_inventory(manifest["assets"])

    def chunk(row: dict[str, Any]) -> dict[str, Any]:
        path = retained / row["path"]
        payload = read(path)
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
    source_layer = next(
        entry["layer"]
        for entry in provenance["layers"]
        if entry["layer"]["key"] == "neotoma-pollen"
    )
    features: list[dict[str, Any]] = []
    for row in inventory:
        if (
            row["domain"] == "nodes"
            and row["layer_key"] == "neotoma-pollen"
            and row["country_keys"] == ["Sweden"]
        ):
            features.extend(
                feature
                for feature in chunk(row)["features"]
                if feature["record_id"] in SITE_IDS
            )
    by_id = {feature["record_id"]: feature for feature in features}
    if set(by_id) != set(SITE_IDS) or len(features) != len(SITE_IDS):
        raise ValueError("source site identity is missing or duplicated")
    details = []
    asset_keys = indexes["detail_record_asset_keys"]
    if not isinstance(asset_keys, dict):
        raise ValueError("retained detail asset index is invalid")
    for site_id in SITE_IDS:
        key = asset_keys[site_id]
        payload = chunk(next(row for row in inventory if row["asset_key"] == key))
        matches = [
            record for record in payload["records"] if record["record_id"] == site_id
        ]
        if len(matches) != 1:
            raise ValueError("source detail identity is missing or duplicated")
        details.append(matches[0])
    layer = dict(source_layer)
    for key in ("static_feature_count", "static_facets"):
        layer.pop(key, None)
    layer.update(features=[by_id[site] for site in SITE_IDS], count=len(SITE_IDS))
    layer["coverage_label"] = (
        "Two retained source-owned Neotoma records selected for drawer verification."
    )
    destination.mkdir(parents=True)
    assets = write_static_atlas_assets(
        destination,
        slug="source-detail",
        version="retained-neotoma",
        point_layers=[layer],
        polygon_layers=[],
        detail_records=details,
        scientific_signals=provenance["scientific_signals"],
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(("Sweden",)).regional_scopes
            if scope.key == "nordic"
        )
    )
    document = render_multi_country_map_html(
        "Retained Neotoma source details",
        "retained-neotoma",
        "2026-09-27",
        ("Sweden",),
        policy,
        [layer],
        [],
        "./_map_assets",
        static_assets=assets,
    )
    (destination / "index.html").write_text(document, encoding="utf-8")
    map_assets = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"
    )
    for path in sorted(map_assets.rglob("*")):
        if path.is_file():
            read(path)
    shutil.copytree(map_assets, destination / "_map_assets")
    source_summaries = []
    for detail in details:
        tabs = detail["tabs"]
        chronology = tabs["chronology"]
        statuses = Counter(
            tuple(
                row[chronology["fields"].index(field)]
                for field in ("calibration_status", "comparability_status")
            )
            for row in chronology["records"]
        )
        source_summaries.append(
            {
                "record_id": detail["record_id"],
                "sample_count": tabs["samples"]["samples"]["record_count"],
                "chronology_claim_count": chronology["record_count"],
                "chronology_status_counts": [
                    {
                        "calibration": status[0],
                        "comparability": status[1],
                        "count": count,
                    }
                    for status, count in sorted(statuses.items())
                ],
                "observation_count": tabs["pollen_composition"]["record_count"],
                "source_provenance": tabs["provenance"],
                "detail_record_sha256": hashlib.sha256(
                    json.dumps(detail, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            }
        )
    receipt = {
        "schema_version": "atlas-retained-source-detail-candidate.v1",
        "source_atlas_build_id": manifest["build_id"],
        "inputs_sha256": inputs,
        "source_records": source_summaries,
        "candidate_build_id": assets.manifest["build_id"],
        "candidate_document_sha256": hashlib.sha256(document.encode()).hexdigest(),
        "scientific_posture": "source_owned_site_context; preserve chronology refusals; no reviewed classification or propagation claim",
    }
    for input_path, digest in inputs.items():
        if hashlib.sha256((repository / input_path).read_bytes()).hexdigest() != digest:
            raise ValueError("frozen source input mutated during generation")
    expectations = {
        "fixture_kind": "retained_source_owned_neotoma_site_context",
        "query": by_id[SITE_IDS[0]]["title"],
        "title": by_id[SITE_IDS[0]]["title"],
        "next_title": by_id[SITE_IDS[1]]["title"],
        "next_detail_status": "available",
        "sample_count": source_summaries[0]["sample_count"],
        "sample_table_path": "samples.samples",
        "chronology_text": "Calibrated radiocarbon years BP",
        "composition_text": "NISP",
        "composition_record": (
            details[0]["tabs"]["pollen_composition"]
            .get("identifier_prefixes", {})
            .get("sample_id", "")
            + str(
                details[0]["tabs"]["pollen_composition"]["records"][0][
                    details[0]["tabs"]["pollen_composition"]["fields"].index(
                        "sample_id"
                    )
                ]
            )
        ),
        "provenance_text": details[0]["tabs"]["provenance"]["record_locator"],
        "provenance_build": details[0]["tabs"]["provenance"]["build_id"],
    }
    composition = details[0]["tabs"]["pollen_composition"]
    expectations["first_observation"] = {
        field: (
            composition.get("identifier_prefixes", {}).get(field, "") + str(value)
            if field in composition.get("identifier_prefixes", {}) and value is not None
            else value
        )
        for field, value in zip(
            composition["fields"], composition["records"][0], strict=True
        )
    }
    (destination / "expectations.json").write_text(
        json.dumps(expectations, indent=2) + "\n"
    )
    (destination / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    receipt = generate_source_detail_candidate(args.repository, args.destination)
    print(
        json.dumps(
            {
                "candidate_build_id": receipt["candidate_build_id"],
                "source_records": receipt["source_records"],
            }
        )
    )


if __name__ == "__main__":
    main()
