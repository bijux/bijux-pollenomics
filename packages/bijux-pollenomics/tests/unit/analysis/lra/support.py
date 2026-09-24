"""Small declared synthetic inputs; never an empirical review fixture."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def request_fixture(root: Path, operation: str = "reveals") -> dict[str, Any]:
    evidence = []
    for role in (
        "raw_snapshot",
        "chronology",
        "geometry",
        "taxa",
        "parameters",
        "dependency_lock",
        "decision",
    ):
        data = f"synthetic test evidence for {role}\n".encode()
        (root / f"{role}.txt").write_bytes(data)
        evidence.append(
            {
                "evidence_id": role,
                "role": role,
                "path": f"{role}.txt",
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    regional: dict[str, Any] = {
        "samples": [
            {
                "sample_id": "regional-1",
                "site_id": "regional-site",
                "raw_evidence_id": "raw_snapshot",
                "chronology_evidence_id": "chronology",
                "bin_id": "test-bin",
                "age_type": "calendar_bp",
                "age_support_bp": [[5400, 5600]],
                "coordinate": 1,
                "counts": [60, 40],
            }
        ],
        "basin": {
            "site_type": "lake",
            "diameter_m": 300,
            "geometry_evidence_id": "geometry",
        },
    }
    result: dict[str, Any] = {
        "schema_version": "lra-request.v1",
        "purpose": "exploratory",
        "data_kind": "synthetic",
        "method_profile": "disqover-0.9.14-source-compatible",
        "operation": operation,
        "pollen_unit": "count",
        "taxa": ["Alnus", "Betula"],
        "regional": regional,
        "parameters": [
            {"taxon": taxon, "fallspeed_m_s": 0.024, "ppe": 4, "ppe_sd": 0}
            for taxon in ("Alnus", "Betula")
        ],
        "configuration": {"seed": 7, "reveals": {"iterations": 2, "stochastic": False}},
        "evidence": evidence,
        "temporal_matching": {
            "rule": "declared_bin_stationarity",
            "decision_evidence_id": "decision",
            "bins": [{"bin_id": "test-bin", "younger_bp": 5400, "older_bp": 5600}],
        },
        "versions": dict.fromkeys(
            ("taxonomy", "parameters", "geometry", "chronology", "binning"),
            "synthetic-v1",
        ),
        "uncertainty_omissions": [
            "chronology",
            "basin_geometry",
            "parameter_domain",
            "spatial_model",
            "ppe_covariance",
        ],
        "exclusions": [],
    }
    if operation != "reveals":
        result["local"] = {
            "samples": [
                {
                    **regional["samples"][0],
                    "sample_id": "local-1",
                    "site_id": "local-site",
                    "counts": [70, 30],
                }
            ],
            "basin": {
                "site_type": "lake",
                "diameter_m": 20,
                "geometry_evidence_id": "geometry",
            },
        }
        result["rings"] = [
            {
                "inner_m": 20,
                "outer_m": 200,
                "mean_m": 100,
                "ring_area_m2": math.pi * (200**2 - 20**2),
                "terrestrial_area_m2": math.pi * (200**2 - 20**2),
                "geometry_evidence_id": "geometry",
            }
        ]
        result["configuration"]["love"] = {
            "method": "analytical",
            "max_ring": 1,
            "repeats": 2,
            "stochastic": False,
        }
        if operation == "love":
            del result["configuration"]["reveals"]
    return result


def regional_draw_love_fixture(
    root: Path,
    *,
    bundle: Path,
    checksums_sha256: str,
    local_site_id: str = "local-site",
    cohort_disposition: str = "excluded_from_source",
) -> dict[str, Any]:
    """Return a synthetic draw-fed request with content-bound local evidence."""
    relative_bundle = bundle.relative_to(root).as_posix()
    evidence = []
    for role in (
        "raw_snapshot",
        "chronology",
        "geometry",
        "taxa",
        "parameters",
        "dependency_lock",
        "decision",
        "draw_source_receipt",
    ):
        data = (
            (
                json.dumps(
                    {
                        "schema_version": "regional-draw-source-receipt.v1",
                        "bundle_directory": relative_bundle,
                        "checksums_sha256": checksums_sha256,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
            if role == "draw_source_receipt"
            else f"synthetic regional-draw LOVE evidence for {role}\n".encode()
        )
        path = root / f"draw-{role}.txt"
        path.write_bytes(data)
        evidence.append(
            {
                "evidence_id": role,
                "role": role,
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    taxa = ["A", "B", "C"]
    ring_area = math.pi * (200**2 - 20**2)
    return {
        "schema_version": "lra-regional-draw-love-request.v1",
        "purpose": "exploratory",
        "data_kind": "synthetic",
        "method_profile": "landclimii-2016-gpm-neutral-analytical-v1",
        "operation": "love",
        "pollen_unit": "count",
        "taxa": taxa,
        "local": {
            "samples": [
                {
                    "sample_id": "local-sample",
                    "site_id": local_site_id,
                    "raw_evidence_id": "raw_snapshot",
                    "chronology_evidence_id": "chronology",
                    "bin_id": "recent",
                    "age_type": "calendar_bp",
                    "age_support_bp": [[0, 100]],
                    "coordinate": 1,
                    "counts": [40, 30, 30],
                }
            ],
            "basin": {
                "site_type": "lake",
                "diameter_m": 20,
                "geometry_evidence_id": "geometry",
            },
        },
        "regional_draw_source": {
            "directory": relative_bundle,
            "bin_id": "recent",
            "expected_checksums_sha256": checksums_sha256,
            "receipt_evidence_id": "draw_source_receipt",
            "cohort_disposition": cohort_disposition,
        },
        "parameters": [
            {"taxon": taxon, "fallspeed_m_s": 0.02, "ppe": 1, "ppe_sd": 0}
            for taxon in taxa
        ],
        "rings": [
            {
                "inner_m": 20,
                "outer_m": 200,
                "mean_m": 100,
                "ring_area_m2": ring_area,
                "terrestrial_area_m2": ring_area,
                "geometry_evidence_id": "geometry",
            }
        ],
        "temporal_matching": {
            "rule": "declared_bin_stationarity",
            "decision_evidence_id": "decision",
            "bins": [{"bin_id": "recent", "younger_bp": 0, "older_bp": 100}],
        },
        "configuration": {
            "love": {
                "max_ring": 1,
                "repeats": 1000,
                "seed": 7,
                "stochastic": False,
                "retain_samples": True,
                "ppe_error": False,
            }
        },
        "evidence": evidence,
        "versions": dict.fromkeys(
            ("taxonomy", "parameters", "geometry", "chronology", "binning"),
            "synthetic-v1",
        ),
        "uncertainty_omissions": [
            "chronology",
            "basin_geometry",
            "parameter_domain",
            "spatial_model",
            "ppe_covariance",
        ],
        "exclusions": [],
    }
