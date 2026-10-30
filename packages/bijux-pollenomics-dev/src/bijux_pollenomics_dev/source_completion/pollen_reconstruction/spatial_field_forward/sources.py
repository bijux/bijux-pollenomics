"""Authenticate the three source cores, parameters, centres and geometry facts."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.intake.workbooks import read_xlsx_sheet_rows

from ..swedish_static_basin.reconstruction import parameter_vectors
from ..swedish_static_basin.sources import read_bound

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/spatial-field-forward/protocol.json"
)
RAW = "data/neotoma/raw/neotoma_pollen_dataset_downloads/"
POLICY = "neotoma/dataset-19913/2026-10-26T185139Z/"
PUBLICATIONS = "neotoma/publication-links/2026-09-29/"
AXIS = ("Betula", "Ulmus")
FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)


def require(value: object, reason: str) -> None:
    """Refuse source/model ambiguity without substituting an input."""
    if not value:
        raise ValueError(reason)


def bound_inputs(
    repository: Path, source_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Read exact source-owned buffers; write no raw-data copy."""
    public = {
        name: read_bound(repository, name, identity)
        for name, identity in protocol["repository_files"].items()
    }
    original = {
        name: read_bound(source_root, name, identity)
        for name, identity in protocol["source_store_files"].items()
    }
    return public, original


def named_chronology(unit: dict[str, Any], chronology_id: int) -> dict[str, Any]:
    """Bind one explicit native model independently of individual sample ages."""
    selected: list[dict[str, Any]] = [
        value["chronology"]
        for value in unit["chronologies"]
        if value["chronology"]["chronologyid"] == chronology_id
    ]
    require(
        len(selected) == 1
        and selected[0]["chronology"]["modelagetype"]
        == "Calibrated radiocarbon years BP",
        "Named chronology is not a unique calibrated BP source model",
    )
    return selected[0]


def load_sources(repository: Path, source_root: Path) -> dict[str, Any]:
    """Bind original normalized payloads and current use/attribution evidence."""
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    require(
        protocol["projected_axis"] == list(AXIS)
        and protocol["families"] == list(FAMILIES),
        "Frozen axes/families differ",
    )
    require(
        protocol["window_edges_native_bp"] == list(range(2700, 5701, 500))
        and len(protocol["cores"]) == 3,
        "Frozen window/place population differs",
    )
    public, original = bound_inputs(repository, source_root, protocol)
    baseline = json.loads(public["data/neotoma/review/relational_baseline.json"])[
        "input_artifacts"
    ]["raw_archive"]
    require(
        protocol["repository_files"][RAW + "manifest.json"]["sha256"]
        == baseline["manifest_sha256"],
        "Retained source archive authority differs",
    )
    for core in protocol["cores"]:
        require(
            protocol["repository_files"][RAW + core["part"]]["sha256"]
            == baseline["part_sha256"][core["part"]],
            "Retained native part authority differs",
        )
    metadata_path = repository / "data/landclim/raw/landclim_ii_site_metadata.xlsx"
    metadata = read_xlsx_sheet_rows(metadata_path, "LANDCLIMII metadata file")
    require(
        ["siteradius", "radius of the site in meters"]
        in read_xlsx_sheet_rows(metadata_path, "readme"),
        "Source radius unit definition differs",
    )
    centres = json.loads(
        gzip.decompress(
            public[
                "docs/report/regions/nordic/author-target-pollen/inputs/metadata-DK.json.gz"
            ]
        )
    )
    denmark = next(
        s["coordinate"] for s in centres["sites"] if s["site_id"] == "neotoma:site:3432"
    )
    requested = {c["dataset_id"]: c for c in protocol["cores"]}
    cores = {}
    for name in sorted({c["part"] for c in requested.values()}):
        document = json.loads(public[RAW + name])
        for record in document["rows"]:
            site = record["site"]
            unit = site["collectionunit"]
            dataset = unit["dataset"]
            did = dataset["datasetid"]
            if did not in requested:
                continue
            declared = requested[did]
            require(
                did not in cores
                and (site["siteid"], unit["collectionunitid"], unit["handle"])
                == (
                    declared["site_id"],
                    declared["collection_unit_id"],
                    declared["id"],
                ),
                "Native core/place identity differs",
            )
            row = dict(
                zip(metadata[0], metadata[declared["metadata_row"] - 1], strict=True)
            )
            require(
                row["csvfilename"] == declared["metadata_code"]
                and row["siteType"] == "lake"
                and float(row["siteradius"]) == declared["radius_m"],
                "Source geometry fact differs",
            )
            geometry = json.loads(site["geography"])
            require(
                geometry["crs"]["properties"]["name"] == "EPSG:4326",
                "Native coordinate reference differs",
            )
            centre = declared["analysis_centre_lon_lat"]
            require(
                geometry["type"] == ("Polygon" if did == 4446 else "Point"),
                "Native geometry type differs",
            )
            require(
                centre == [denmark["longitude"], denmark["latitude"]]
                if did == 4446
                else centre == geometry["coordinates"][:2],
                "Fixed analysis centre differs",
            )
            require(
                unit["gpslocation"]["latitude"] is None
                and unit["gpslocation"]["longitude"] is None,
                "Core GPS source changed; do not silently replace the declared centre",
            )
            require(
                dataset["database"] == "European Pollen Database",
                "Constituent source attribution differs",
            )
            cores[did] = {
                "declaration": declared,
                "site": site,
                "selected_chronology": named_chronology(
                    unit, declared["chronology_id"]
                ),
            }
        del document
    require(set(cores) == set(requested), "Declared native core missing")
    policies = json.loads(original[POLICY + "capture-manifest.json"])
    require(policies["status"] == "complete", "Current policy capture incomplete")
    policy_records = [
        r for r in policies["records"] if r["role"] in {"neotoma_policy", "epd_policy"}
    ]
    require(
        len(policy_records) == 2
        and all(r["http_status"] == 200 and r["body_complete"] for r in policy_records),
        "Current public policy evidence differs",
    )
    publications = json.loads(original[PUBLICATIONS + "capture-manifest.json"])
    attribution = []
    for did, core in cores.items():
        captured = [r for r in publications["responses"] if r["dataset_id"] == did]
        require(
            len(captured) == 1
            and captured[0]["http_status"] == 200
            and captured[0]["sha256"]
            == protocol["source_store_files"][PUBLICATIONS + captured[0]["path"]][
                "sha256"
            ],
            "Qualified publication metadata identity differs",
        )
        body = json.loads(original[PUBLICATIONS + captured[0]["path"]])
        require(body["status"] == "success", "Publication metadata source refused")
        dataset = core["site"]["collectionunit"]["dataset"]
        attribution.append(
            {
                "dataset_id": did,
                "native_dois": dataset["doi"],
                "original_investigators": dataset["datasetpi"],
                "publication_metadata": body["data"],
            }
        )
    ppe, sd, fall = parameter_vectors(repository, list(AXIS))
    return {
        "protocol": protocol,
        "cores": cores,
        "ppe": ppe.tolist(),
        "published_sd": sd.tolist(),
        "fall": fall.tolist(),
        "attribution": attribution,
        "policy_urls": [r["requested_url"] for r in policy_records],
        "input_sha256": {
            **{
                f"repository/{k}": v["sha256"]
                for k, v in protocol["repository_files"].items()
            },
            **{
                f"source-store/{k}": v["sha256"]
                for k, v in protocol["source_store_files"].items()
            },
        },
    }
