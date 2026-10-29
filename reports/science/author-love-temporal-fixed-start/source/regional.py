"""Reuse exact deterministic regional stages across local-request identities."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

Json = dict[str, Any]
SOURCE_EPOCH = "d60500153ff589db3b93c38fe3bddde46c2994a9"
INPUT_EPOCH = "d863e6c939fab8eed3e53c4dc01c52953bc2434a"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def stage_identity(payload: Json) -> str:
    """Exclude only channels which cannot enter the regional stage."""
    if payload["configuration"]["reveals"]["stochastic"] is not False:
        raise ValueError("Only the declared deterministic regional handoff is reusable")
    return digest(
        {k: payload[k] for k in ("taxa", "parameters", "regional")}
        | {
            "configuration": {
                "seed": payload["configuration"]["seed"],
                "reveals": payload["configuration"]["reveals"],
            }
        }
    )


def saved_fraction(raw: bytes, taxa: list[str], coordinate: float) -> list[float]:
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    expected = {"Distance.weighting", "Basin.type", "coordinate"} | {
        taxon + "." + statistic
        for taxon in taxa
        for statistic in ("mean", "median", "q10", "q90", "sd")
    }
    if len(rows) != 1 or set(rows[0]) != expected or len(taxa) != 30:
        raise ValueError("Complete single-sample thirty-taxon regional table required")
    row = rows[0]
    if (
        row["Distance.weighting"] != "gpm neutral"
        or row["Basin.type"] != "lake"
        or float(row["coordinate"]) != coordinate
    ):
        raise ValueError("Original regional sample/transport/basin metadata differs")
    percent = [float(row[taxon + ".mean"]) for taxon in taxa]
    for taxon, value in zip(taxa, percent, strict=True):
        if (
            not math.isfinite(value)
            or not 0 <= value <= 100
            or abs(value * 1000 - round(value * 1000)) > 1e-8
            or any(
                float(row[taxon + "." + k]) != value for k in ("median", "q10", "q90")
            )
            or float(row[taxon + ".sd"]) != 0
        ):
            raise ValueError(
                "Identical deterministic three-decimal-percent draws required"
            )
    if abs(math.fsum(percent) - 100) > 30 * 0.0005 + 1e-10:
        raise ValueError("Source-rounded regional percent mass differs")
    return [value / 100 for value in percent]


def load(
    repository: Path, temporal: Json, topology: Json, window: int, authority_pin: Json
) -> tuple[dict[str, list[float]], Json]:
    """Bind saved stages to the admitted original requests, including local refusals."""
    read = temporal["read"]
    authority = json.loads(read(repository, authority_pin))
    if (
        authority.get("schema_version")
        != "author-love-temporal-development-output-authority.v1"
        or authority.get("candidate") != SOURCE_EPOCH
        or authority.get("input_epoch") != INPUT_EPOCH
        or authority.get("approved") is not True
        or type(authority.get("actual_exit")) is not int
        or authority["actual_exit"] != 0
        or authority.get("scientific_saved_products_admitted") is not True
    ):
        raise ValueError("Admitted original temporal uniform products required")
    for key in ("observation", "observer_execution", "observer_source_review"):
        proof = json.loads(read(repository, authority[key]))
        if key == "observation" and any(
            proof.get(k) != authority.get(k)
            for k in ("jobs", "products", "summaries", "cache_product_manifests")
        ):
            raise ValueError("Original temporal authority differs from its observation")
        if key == "observer_execution" and proof.get("actual_exit") != 0:
            raise ValueError("Original temporal saved-output execution zero required")
        if key == "observer_source_review" and proof.get("approved") is not True:
            raise ValueError("Original temporal saved-output source review required")
    batch = json.loads(
        read(repository, authority["products"][str(window)]["batch-result.json"])
    )
    numeric = topology["numeric"]
    rows = batch["items"]
    if (
        len(rows) != len(numeric)
        or len({row["request_sha256"] for row in rows}) != len(rows)
        or {row["request_sha256"] for row in rows} != set(numeric)
    ):
        raise ValueError("Exact original unique temporal request population required")
    available: dict[str, Json] = {}
    read_inputs = [
        authority_pin,
        *[
            authority[k]
            for k in ("observation", "observer_execution", "observer_source_review")
        ],
        authority["products"][str(window)]["batch-result.json"],
    ]
    refused = []
    for row in rows:
        checksum = row["request_sha256"]
        if row["item_status"] == "refused":
            if row["error"]["reason_code"] != "optimizer_nonconvergence":
                raise ValueError("Unknown original request refusal")
            refused.append(checksum)
            continue
        if row["item_status"] != "completed":
            raise ValueError("Incomplete original temporal population")
        payload = numeric[checksum].payload()
        source = authority["cache_product_manifests"][str(window)][checksum]
        directory = temporal["location"](repository, row["product"]["directory"])
        if (
            temporal["location"](repository, source["path"])
            != directory / "manifest.json"
            or source["sha256"] != row["product"]["manifest_sha256"]
        ):
            raise ValueError("Actual completed product/manifest lineage differs")
        manifest = json.loads(read(repository, source))
        read_inputs.append(source)
        if manifest["request_sha256"] != checksum:
            raise ValueError("Original numerical request identity differs")
        bodies = {}
        refs = {}
        for relative in (
            "numerical/regional_reveals/reconstruction.csv",
            "numerical/regional_reveals/run_manifest.json",
        ):
            path = directory / relative
            ref = {
                "path": str(path),
                "sha256": manifest["files"][relative],
                "bytes": path.stat().st_size,
            }
            bodies[relative] = read(repository, ref)
            refs[relative] = ref
            read_inputs.append(ref)
        stage = json.loads(bodies["numerical/regional_reveals/run_manifest.json"])
        configuration = stage["parameters"]
        if configuration != {
            "basin_diameter_m": payload["regional"]["basin"]["diameter_m"],
            "basin_type": "lake",
            "distance_weighting": "gpm neutral",
            "equation": "Sugita-2007-B1",
            "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
            "iterations": 2,
            "paired_pollen_draws": False,
            "paired_ppe_draws": False,
            "region_cutoff_m": 100000.0,
            "retain_samples": True,
            "seed": 1201125462,
            "stochastic": False,
        }:
            raise ValueError(
                "Exact deterministic regional child configuration required"
            )
        regional = saved_fraction(
            bodies["numerical/regional_reveals/reconstruction.csv"],
            payload["taxa"],
            payload["regional"]["samples"][0]["coordinate"],
        )
        key = stage_identity(payload)
        if key in available and (
            available[key]["raw_fraction"] != regional
            or available[key]["regional_inputs"] != stage["inputs"]
            or available[key]["csv_sha256"]
            != refs["numerical/regional_reveals/reconstruction.csv"]["sha256"]
        ):
            raise ValueError("Equivalent saved deterministic regional stages disagree")
        available.setdefault(
            key,
            {
                "source_request_sha256": checksum,
                "product_manifest": source,
                "stage_files": refs,
                "raw_fraction": regional,
                "regional_inputs": stage["inputs"],
                "csv_sha256": refs["numerical/regional_reveals/reconstruction.csv"][
                    "sha256"
                ],
            },
        )
    regional_by_request = {}
    aliases = []
    for checksum, item in sorted(numeric.items()):
        key = stage_identity(item.payload())
        if key not in available:
            raise ValueError(
                "No authenticated regional stage for this request; no implicit recomputation"
            )
        source = available[key]
        regional_by_request[checksum] = source["raw_fraction"]
        aliases.append(
            {
                "request_sha256": checksum,
                "regional_stage_sha256": key,
                "source_request_sha256": source["source_request_sha256"],
            }
        )
    return regional_by_request, {
        "original_source_epoch": SOURCE_EPOCH,
        "input_epoch": INPUT_EPOCH,
        "original_authority": authority_pin,
        "original_refused_requests": refused,
        "stage_sources": available,
        "request_aliases": aliases,
        "read_inputs": read_inputs,
        "new_REVEALS_calls": 0,
        "qualification": "Source-identical deterministic two-draw REVEALS: mean equals each identically rounded first coupled draw; raw fractions unchanged. Local failed products are not invented or reused.",
    }
