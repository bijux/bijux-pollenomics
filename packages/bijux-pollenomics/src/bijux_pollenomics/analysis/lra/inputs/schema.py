"""Versioned exploratory request schema; scientific admission is a separate gate."""

from __future__ import annotations

from typing import Any


def _object(
    properties: dict[str, Any], required: tuple[str, ...] | None = None
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties if required is None else required),
        "additionalProperties": False,
    }


IDENTITY = {"type": "string", "minLength": 1, "pattern": r"^\S(?:.*\S)?$"}
NUMBER = {"type": "number"}
NONNEGATIVE = {"type": "number", "minimum": 0}
DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
INTERVAL = {"type": "array", "items": NUMBER, "minItems": 2, "maxItems": 2}
SAMPLE = _object(
    {
        "sample_id": IDENTITY,
        "site_id": IDENTITY,
        "raw_evidence_id": IDENTITY,
        "chronology_evidence_id": IDENTITY,
        "bin_id": IDENTITY,
        "age_type": {"enum": ["calendar_bp", "calibrated_bp"]},
        "age_support_bp": {"type": "array", "items": INTERVAL, "minItems": 1},
        "coordinate": NUMBER,
        "counts": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "integer", "minimum": 0},
        },
    }
)
BASIN = _object(
    {
        "site_type": {"enum": ["lake", "peatland"]},
        "diameter_m": {"type": "number", "exclusiveMinimum": 0},
        "geometry_evidence_id": IDENTITY,
    }
)
POLLEN = _object(
    {
        "samples": {"type": "array", "items": SAMPLE, "minItems": 1},
        "basin": BASIN,
    }
)
PARAMETER = _object(
    {
        "taxon": IDENTITY,
        "fallspeed_m_s": {"type": "number", "minimum": 0.01, "maximum": 0.15},
        "ppe": {"type": "number", "exclusiveMinimum": 0},
        "ppe_sd": NONNEGATIVE,
    }
)
EVIDENCE = _object(
    {
        "evidence_id": IDENTITY,
        "role": {
            "enum": [
                "raw_snapshot",
                "chronology",
                "geometry",
                "taxa",
                "parameters",
                "dependency_lock",
                "decision",
            ]
        },
        "path": IDENTITY,
        "sha256": DIGEST,
    }
)
RING = _object(
    {
        "inner_m": NONNEGATIVE,
        "outer_m": NONNEGATIVE,
        "mean_m": NONNEGATIVE,
        "ring_area_m2": {"type": "number", "exclusiveMinimum": 0},
        "terrestrial_area_m2": NONNEGATIVE,
        "geometry_evidence_id": IDENTITY,
    }
)

REQUEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://bijux.io/bijux-pollenomics/schemas/lra-request.v1.json",
    **_object(
        {
            "schema_version": {"const": "lra-request.v1"},
            "purpose": {"const": "exploratory"},
            "data_kind": {"enum": ["synthetic", "source_observations"]},
            "method_profile": {
                "enum": ["disqover-0.9.14-source-compatible", "ring-taxon-preserving"]
            },
            "operation": {"enum": ["reveals", "love", "lra", "series"]},
            "pollen_unit": {"const": "count"},
            "taxa": {
                "type": "array",
                "items": IDENTITY,
                "minItems": 1,
                "uniqueItems": True,
            },
            "regional": POLLEN,
            "local": POLLEN,
            "parameters": {"type": "array", "items": PARAMETER, "minItems": 1},
            "rings": {"type": "array", "items": RING, "minItems": 1},
            "temporal_matching": _object(
                {
                    "rule": {"const": "declared_bin_stationarity"},
                    "decision_evidence_id": IDENTITY,
                    "bins": {
                        "type": "array",
                        "minItems": 1,
                        "items": _object(
                            {
                                "bin_id": IDENTITY,
                                "younger_bp": NUMBER,
                                "older_bp": NUMBER,
                            }
                        ),
                    },
                }
            ),
            "configuration": _object(
                {
                    "reveals": {"type": "object"},
                    "love": {"type": "object"},
                    "seed": {"type": "integer", "minimum": 0},
                    "couple_regional_draws": {"type": "boolean"},
                },
                (),
            ),
            "evidence": {"type": "array", "items": EVIDENCE, "minItems": 1},
            "versions": _object(
                {
                    "taxonomy": IDENTITY,
                    "parameters": IDENTITY,
                    "geometry": IDENTITY,
                    "chronology": IDENTITY,
                    "binning": IDENTITY,
                }
            ),
            "uncertainty_omissions": {
                "type": "array",
                "items": IDENTITY,
                "uniqueItems": True,
            },
            "exclusions": {
                "type": "array",
                "items": _object({"sample_id": IDENTITY, "reason_code": IDENTITY}),
            },
        },
        (
            "schema_version",
            "purpose",
            "data_kind",
            "method_profile",
            "operation",
            "pollen_unit",
            "taxa",
            "regional",
            "temporal_matching",
            "parameters",
            "configuration",
            "evidence",
            "versions",
            "uncertainty_omissions",
            "exclusions",
        ),
    ),
}
