"""Explicitly synthetic source and externally supplied review fixtures."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.raa.density_membership import (
    build_raa_density_membership,
)
from bijux_pollenomics.collection.sources.raa.outputs import (
    build_raa_density_geojson,
    build_raa_inventory_summary,
    count_raa_features,
)
from tests.support.context_data.boundaries import write_synthetic_boundary_manifest

REVIEW_INPUT_PATHS = {
    "raw_inventory": "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
    "raw_summary": "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
    "normalized_metadata": "raa/normalized/sweden_archaeology_layer.json",
    "normalized_density": "raa/normalized/sweden_archaeology_density.geojson",
    "membership_ledger": "raa/derived/sweden_archaeology_density_membership.json",
    "boundary_manifest": "boundaries/raw/source_manifest.json",
    "sweden_boundary": "boundaries/raw/sweden.geojson",
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False))


def read_json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def geometry(
    west: int = 17, south: int = 56, east: int = 20, north: int = 59
) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def grid_cell(longitude: int, latitude: int, count: object) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": geometry(longitude, latitude, longitude + 1, latitude + 1),
        "properties": {"count": count},
    }


def inventory(statuses: list[str] | None = None) -> dict[str, Any]:
    labels = statuses if statuses is not None else ["Fornlämning", "Möjlig fornlämning"]
    return {
        "type": "FeatureCollection",
        "numberMatched": len(labels),
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18.2, 57.2]},
                "properties": {
                    "lamningsnummer": "A" if index == 0 else f"B{index}",
                    "antikvariskbedomningtyp_namn": status,
                },
            }
            for index, status in enumerate(labels)
        ],
    }


def write_synthetic_review(root: Path, *, reviewer_id: str = "reviewer-1") -> None:
    """Model a supplied review of exact test bytes, never an actual human approval."""
    ledger = read_json(root / REVIEW_INPUT_PATHS["membership_ledger"])
    receipts = {}
    for role, relative in REVIEW_INPUT_PATHS.items():
        raw = (root / relative).read_bytes()
        receipts[role] = {
            "path": relative,
            "sha256": sha256(raw).hexdigest(),
            "byte_count": len(raw),
        }
    write_json(
        root / "raa/review/spatiotemporal_review.json",
        {
            "schema_version": "raa-density-review-v1",
            "selection_policy": ledger["selection_policy"],
            "release_status": "accepted",
            "reviewer_id": reviewer_id,
            "input_artifacts": receipts,
        },
    )


def write_authority_fixture(
    root: Path,
    *,
    source: dict[str, Any] | None = None,
    boundary: dict[str, Any] | None = None,
    reviewer_id: str = "reviewer-1",
) -> None:
    """Write only generated native records, boundaries and a synthetic review stub."""
    source = inventory() if source is None else source
    boundary = (
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADM0_A3": "SWE"},
                    "geometry": geometry(),
                }
            ],
        }
        if boundary is None
        else boundary
    )
    for country, code in [
        ("sweden", "SWE"),
        ("norway", "NOR"),
        ("denmark", "DNK"),
        ("finland", "FIN"),
    ]:
        payload = json.loads(json.dumps(boundary))
        for feature in payload["features"]:
            feature["properties"]["ADM0_A3"] = code
        write_json(root / f"boundaries/raw/{country}.geojson", payload)
    write_synthetic_boundary_manifest(root / "boundaries/raw")
    write_json(root / REVIEW_INPUT_PATHS["raw_inventory"], source)
    write_json(
        root / REVIEW_INPUT_PATHS["raw_summary"], build_raa_inventory_summary(source)
    )
    density = build_raa_density_geojson(
        feature_inventory=source, sweden_boundary=boundary
    )
    write_json(root / REVIEW_INPUT_PATHS["normalized_density"], density)
    write_json(
        root / REVIEW_INPUT_PATHS["normalized_metadata"],
        {
            "counts": {
                "all_published_sites": count_raa_features(source),
                "fornlamning": count_raa_features(
                    source, heritage_statuses={"Fornlämning"}
                ),
                "fornlamning_or_possible": count_raa_features(
                    source, heritage_statuses={"Fornlämning", "Möjlig fornlämning"}
                ),
            },
            "density_feature_count": len(cast(list[object], density["features"])),
        },
    )
    ledger = build_raa_density_membership(
        feature_inventory=source, sweden_boundary=boundary
    )
    raw = (root / REVIEW_INPUT_PATHS["raw_inventory"]).read_bytes()
    ledger["raw_inventory_identity"] = {
        "path": "raw/publicerade_lamningar_centrumpunkt.geojson",
        "sha256": sha256(raw).hexdigest(),
        "byte_count": len(raw),
    }
    write_json(root / REVIEW_INPUT_PATHS["membership_ledger"], ledger)
    write_synthetic_review(root, reviewer_id=reviewer_id)
