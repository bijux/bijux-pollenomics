"""Small declared synthetic inputs; never an empirical review fixture."""

from __future__ import annotations

import hashlib
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
