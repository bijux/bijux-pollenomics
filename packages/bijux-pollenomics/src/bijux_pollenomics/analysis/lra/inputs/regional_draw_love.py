"""Versioned host contract for LOVE fed by authenticated regional-cover draws."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from ..engine.errors import LRARefusal
from ..publication_draws import read_multisite_regional_draw_source
from .schema import (
    BASIN,
    DIGEST,
    IDENTITY,
    INTERVAL,
    NONNEGATIVE,
    NUMBER,
    RING,
    _object,
)
from .validation import (
    ValidatedRequest,
    _evidence,
    _finite_json,
    _refuse,
    _temporal_and_denominators,
)

_PROFILE = "landclimii-2016-gpm-neutral-analytical-v1"

_SAMPLE = _object(
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
_LOCAL = _object(
    {
        "samples": {
            "type": "array",
            "items": _SAMPLE,
            "minItems": 1,
            "maxItems": 1,
        },
        "basin": BASIN,
    }
)
_PARAMETER = _object(
    {
        "taxon": IDENTITY,
        "fallspeed_m_s": {"type": "number", "minimum": 0.006, "maximum": 0.15},
        "ppe": {"type": "number", "exclusiveMinimum": 0},
        "ppe_sd": NONNEGATIVE,
    }
)
_EVIDENCE = _object(
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
                "draw_source_receipt",
            ]
        },
        "path": IDENTITY,
        "sha256": DIGEST,
    }
)

REGIONAL_DRAW_LOVE_REQUEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": (
        "https://bijux.io/bijux-pollenomics/schemas/"
        "lra-regional-draw-love-request.v1.json"
    ),
    **_object(
        {
            "schema_version": {"const": "lra-regional-draw-love-request.v1"},
            "purpose": {"const": "exploratory"},
            "data_kind": {"enum": ["synthetic", "source_observations"]},
            "method_profile": {"const": _PROFILE},
            "operation": {"const": "love"},
            "pollen_unit": {"const": "count"},
            "taxa": {
                "type": "array",
                "items": IDENTITY,
                "minItems": 1,
                "uniqueItems": True,
            },
            "local": _LOCAL,
            "regional_draw_source": _object(
                {
                    "directory": IDENTITY,
                    "bin_id": IDENTITY,
                    "expected_checksums_sha256": DIGEST,
                    "receipt_evidence_id": IDENTITY,
                    "cohort_disposition": {
                        "enum": [
                            "excluded_from_source",
                            "included_method_control",
                        ]
                    },
                }
            ),
            "parameters": {
                "type": "array",
                "items": _PARAMETER,
                "minItems": 1,
            },
            "rings": {"type": "array", "items": RING, "minItems": 1},
            "temporal_matching": _object(
                {
                    "rule": {"const": "declared_bin_stationarity"},
                    "decision_evidence_id": IDENTITY,
                    "bins": {
                        "type": "array",
                        "items": _object(
                            {
                                "bin_id": IDENTITY,
                                "younger_bp": NUMBER,
                                "older_bp": NUMBER,
                            }
                        ),
                        "minItems": 1,
                        "maxItems": 1,
                    },
                }
            ),
            "configuration": _object(
                {
                    "love": _object(
                        {
                            "max_ring": {"type": "integer", "minimum": 1},
                            "repeats": {"const": 1000},
                            "seed": {"type": "integer", "minimum": 0},
                            "stochastic": {"type": "boolean"},
                            "retain_samples": {"type": "boolean"},
                            "ppe_error": {"type": "boolean"},
                        }
                    )
                }
            ),
            "evidence": {"type": "array", "items": _EVIDENCE, "minItems": 1},
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
        }
    ),
}


def _receipt_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _invalid_receipt_constant(value: str) -> Any:
    raise ValueError(f"nonfinite value: {value}")


def _draw_source_receipt(
    payload: dict[str, Any], input_root: Path, roles: dict[str, str]
) -> None:
    declaration = payload["regional_draw_source"]
    evidence_id = declaration["receipt_evidence_id"]
    if roles.get(evidence_id) != "draw_source_receipt":
        _refuse(
            "invalid_regional_draw_source_receipt",
            "The declared receipt evidence must have the draw_source_receipt role",
        )
    item = next(row for row in payload["evidence"] if row["evidence_id"] == evidence_id)
    path = (input_root.resolve() / Path(item["path"])).resolve()
    try:
        receipt = json.loads(
            path.read_bytes(),
            object_pairs_hook=_receipt_pairs,
            parse_constant=_invalid_receipt_constant,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LRARefusal(
            "invalid_regional_draw_source_receipt",
            f"The declared draw-source receipt is not strict JSON: {exc}",
        ) from exc
    expected = {
        "schema_version": "regional-draw-source-receipt.v1",
        "bundle_directory": declaration["directory"],
        "checksums_sha256": declaration["expected_checksums_sha256"],
    }
    if receipt != expected:
        _refuse(
            "invalid_regional_draw_source_receipt",
            "The draw-source receipt must bind the selected bundle and checksum",
        )


def _draw_source(payload: dict[str, Any], input_root: Path) -> Any:
    declaration = payload["regional_draw_source"]
    relative = Path(declaration["directory"])
    root = input_root.resolve()
    if relative.is_absolute() or ".." in relative.parts:
        _refuse(
            "regional_draw_source_outside_root",
            declaration["directory"],
        )
    directory = root / relative
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            _refuse(
                "regional_draw_source_symlink",
                declaration["directory"],
            )
    source = read_multisite_regional_draw_source(
        directory,
        bin_id=declaration["bin_id"],
        expected_checksums_sha256=declaration["expected_checksums_sha256"],
    )
    taxa = tuple(payload["taxa"])
    if source.taxon_ids != taxa:
        _refuse(
            "regional_draw_taxon_mismatch",
            "Regional draw taxa must equal request taxa in exact order",
        )
    bin_record = payload["temporal_matching"]["bins"][0]
    if (
        source.bin_id != bin_record["bin_id"]
        or source.younger_bp != bin_record["younger_bp"]
        or source.older_bp != bin_record["older_bp"]
    ):
        _refuse(
            "regional_draw_time_mismatch",
            "Regional draw bin identity and typed BP bounds must match the request",
        )
    local_site = payload["local"]["samples"][0]["site_id"]
    actual_disposition = (
        "included_method_control"
        if local_site in source.regional_site_ids
        else "excluded_from_source"
    )
    if declaration["cohort_disposition"] != actual_disposition:
        _refuse(
            "regional_draw_cohort_mismatch",
            "Declared local/cohort disposition differs from authenticated source axes",
        )
    return source


def read_request_regional_draw_source(
    request: ValidatedRequest, *, input_root: Path
) -> Any:
    """Reauthenticate and return the source selected by a validated request."""
    return _draw_source(request.payload(), input_root)


def validate_regional_draw_love_request(
    payload: Mapping[str, object], *, input_root: Path
) -> ValidatedRequest:
    """Validate one local sample and its governed multi-site regional draws."""
    try:
        canonical = json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        copy = cast(dict[str, Any], json.loads(canonical))
    except (TypeError, ValueError) as exc:
        raise LRARefusal(
            "invalid_lra_json", "Request must contain finite JSON values"
        ) from exc
    errors = sorted(
        Draft202012Validator(REGIONAL_DRAW_LOVE_REQUEST_SCHEMA).iter_errors(copy),
        key=lambda error: str(error.path),
    )
    if errors:
        error = errors[0]
        _refuse(
            "invalid_lra_schema", f"{'/'.join(map(str, error.path))}: {error.message}"
        )
    _finite_json(copy)
    omissions = {
        "chronology",
        "basin_geometry",
        "parameter_domain",
        "spatial_model",
        "ppe_covariance",
    }
    if not omissions.issubset(copy["uncertainty_omissions"]):
        _refuse(
            "unreported_uncertainty_omission",
            "The current engine does not propagate every declared uncertainty source",
        )
    roles = _evidence(copy, input_root.resolve())
    _draw_source_receipt(copy, input_root, roles)
    local = copy["local"]
    sample = local["samples"][0]
    if local["basin"]["site_type"] != "lake":
        _refuse(
            "unsupported_local_basin_profile",
            "The adopted LOVE facade's local-basin profile is lake only",
        )
    if roles.get(local["basin"]["geometry_evidence_id"]) != "geometry":
        _refuse("invalid_geometry_lineage", "local")
    if (
        roles.get(sample["raw_evidence_id"]) != "raw_snapshot"
        or roles.get(sample["chronology_evidence_id"]) != "chronology"
    ):
        _refuse("invalid_sample_lineage", sample["sample_id"])
    if (
        len(sample["counts"]) != len(copy["taxa"])
        or not 0 < sum(sample["counts"]) <= 2**53
    ):
        _refuse("invalid_count_denominator", sample["sample_id"])
    if any(younger > older for younger, older in sample["age_support_bp"]):
        _refuse("reversed_age_interval", sample["sample_id"])
    if (
        isinstance(sample["coordinate"], int)
        and int(float(sample["coordinate"])) != sample["coordinate"]
    ):
        _refuse("inexact_pairing_coordinate", sample["sample_id"])
    _temporal_and_denominators(copy, roles)
    if [row["taxon"] for row in copy["parameters"]] != copy["taxa"]:
        _refuse(
            "parameter_taxon_mismatch",
            "Parameter rows must retain the exact regional-draw taxon order",
        )
    previous_outer = None
    for ring in copy["rings"]:
        if roles.get(ring["geometry_evidence_id"]) != "geometry":
            _refuse("invalid_ring_lineage", ring["geometry_evidence_id"])
        if ring["terrestrial_area_m2"] != ring["ring_area_m2"]:
            _refuse(
                "unsupported_analytical_land_mask",
                "Draw-fed analytical LOVE requires fully terrestrial rings",
            )
        if not ring["inner_m"] < ring["mean_m"] < ring["outer_m"] or (
            previous_outer is not None and ring["inner_m"] < previous_outer
        ):
            _refuse(
                "invalid_ring_geometry",
                "Rings must be ordered, nonoverlapping and have interior means",
            )
        previous_outer = ring["outer_m"]
    if copy["rings"][0]["inner_m"] <= local["basin"]["diameter_m"] / 2:
        _refuse(
            "invalid_analytical_ring_support",
            "Analytical LOVE rings must begin strictly beyond the local basin radius",
        )
    if copy["configuration"]["love"]["max_ring"] > len(copy["rings"]):
        _refuse(
            "invalid_local_ring_limit",
            "LOVE max_ring must lie within the supplied ring inventory",
        )
    _draw_source(copy, input_root)
    return ValidatedRequest(canonical, hashlib.sha256(canonical.encode()).hexdigest())
