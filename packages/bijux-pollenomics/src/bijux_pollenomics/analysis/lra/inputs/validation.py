"""Refuse ambiguous units, pairing, geometry and unbound source identities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, NoReturn, cast

from jsonschema import Draft202012Validator

from ..engine.errors import LRARefusal
from .schema import REQUEST_SCHEMA


@dataclass(frozen=True)
class ValidatedRequest:
    """Immutable canonical request after structural and source-byte verification."""

    canonical_json: str
    sha256: str

    def payload(self) -> dict[str, Any]:
        """Return a new copy so a consumer cannot mutate the accepted request."""
        return cast(dict[str, Any], json.loads(self.canonical_json))


def _refuse(reason: str, detail: str) -> NoReturn:
    raise LRARefusal(reason, detail)


def _finite_json(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            valid = isfinite(float(value))
        except OverflowError:
            valid = False
        if not valid:
            _refuse("invalid_lra_number", "Numeric inputs must fit finite binary64")
    elif isinstance(value, dict):
        for child in value.values():
            _finite_json(child)
    elif isinstance(value, list):
        for child in value:
            _finite_json(child)


def _evidence(payload: dict[str, Any], root: Path) -> dict[str, str]:
    roles = {}
    for item in payload["evidence"]:
        identity = item["evidence_id"]
        if identity in roles:
            _refuse("duplicate_evidence_id", identity)
        relative = Path(item["path"])
        source = (root / relative).resolve()
        if relative.is_absolute() or not source.is_relative_to(root):
            _refuse("evidence_path_outside_root", item["path"])
        try:
            with source.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
        except OSError as exc:
            raise LRARefusal("evidence_unavailable", f"{identity}: {exc}") from exc
        if digest != item["sha256"]:
            _refuse("evidence_digest_mismatch", identity)
        roles[identity] = item["role"]
    needed = {
        "raw_snapshot",
        "chronology",
        "geometry",
        "taxa",
        "parameters",
        "dependency_lock",
        "decision",
    }
    if missing := needed - set(roles.values()):
        _refuse("missing_evidence_role", ", ".join(sorted(missing)))
    return roles


def _pollen(payload: dict[str, Any], roles: dict[str, str]) -> None:
    identities: set[str] = set()
    local = payload.get("local")
    if payload["operation"] == "reveals":
        if local is not None or "rings" in payload:
            _refuse(
                "unused_lra_input", "REVEALS does not consume local pollen or rings"
            )
    elif local is None or "rings" not in payload:
        _refuse(
            "missing_local_input",
            "LOVE and paired workflows require local pollen and rings",
        )
    coordinates: dict[str, dict[float, str]] = {}
    for role in ("regional", "local"):
        if role not in payload:
            continue
        block = payload[role]
        if roles.get(block["basin"]["geometry_evidence_id"]) != "geometry":
            _refuse("invalid_geometry_lineage", role)
        if len({row["site_id"] for row in block["samples"]}) != 1:
            _refuse(
                "unsupported_multisite_profile",
                "This source-compatible workflow accepts one measured basin per series",
            )
        coordinates[role] = {}
        for row in block["samples"]:
            if row["sample_id"] in identities:
                _refuse("duplicate_sample_id", row["sample_id"])
            identities.add(row["sample_id"])
            if (
                roles.get(row["raw_evidence_id"]) != "raw_snapshot"
                or roles.get(row["chronology_evidence_id"]) != "chronology"
            ):
                _refuse("invalid_sample_lineage", row["sample_id"])
            if (
                len(row["counts"]) != len(payload["taxa"])
                or not 0 < sum(row["counts"]) <= 2**53
            ):
                _refuse("invalid_count_denominator", row["sample_id"])
            if any(younger > older for younger, older in row["age_support_bp"]):
                _refuse("reversed_age_interval", row["sample_id"])
            key = row["coordinate"]
            if isinstance(key, int) and int(float(key)) != key:
                _refuse("inexact_pairing_coordinate", row["sample_id"])
            key = float(key)
            if key in coordinates[role]:
                _refuse("duplicate_pairing_coordinate", role)
            coordinates[role][key] = row["bin_id"]
        if payload["operation"] in {"love", "lra"} and len(block["samples"]) != 1:
            _refuse("invalid_sample_count", "Use series for multiple paired samples")
    if local is not None and coordinates["regional"] != coordinates["local"]:
        _refuse(
            "incompatible_time_pairing",
            "Local and regional coordinates and bin identities must match exactly",
        )
    if (
        local is not None
        and local["samples"][0]["site_id"]
        == payload["regional"]["samples"][0]["site_id"]
    ):
        _refuse(
            "overlapping_regional_local_site",
            "Local and regional backgrounds must identify distinct sites",
        )


def _temporal_and_denominators(payload: dict[str, Any], roles: dict[str, str]) -> None:
    matching = payload["temporal_matching"]
    if roles.get(matching["decision_evidence_id"]) != "decision":
        _refuse(
            "invalid_temporal_decision",
            "Bin-stationarity assumption needs an explicit decision reference",
        )
    bins = {row["bin_id"]: row for row in matching["bins"]}
    if len(bins) != len(matching["bins"]) or any(
        row["younger_bp"] > row["older_bp"] for row in bins.values()
    ):
        _refuse(
            "invalid_time_bins",
            "Time bins must have unique identities and ordered BP bounds",
        )
    samples = [
        row
        for role in ("regional", "local")
        if role in payload
        for row in payload[role]["samples"]
    ]
    used_bins = {row["bin_id"] for row in samples}
    if used_bins != set(bins):
        _refuse(
            "time_bin_inventory_mismatch",
            "Declare exactly the time bins consumed by the selected samples",
        )
    for row in samples:
        bounds = bins[row["bin_id"]]
        if any(
            younger < bounds["younger_bp"] or older > bounds["older_bp"]
            for younger, older in row["age_support_bp"]
        ):
            _refuse("sample_outside_declared_bin", row["sample_id"])
    included = {row["sample_id"] for row in samples}
    exclusions = [row["sample_id"] for row in payload["exclusions"]]
    if len(set(exclusions)) != len(exclusions) or included & set(exclusions):
        _refuse(
            "contradictory_sample_denominator",
            "Included and excluded sample IDs must be disjoint, without duplicate exclusions",
        )


def _method_profile(payload: dict[str, Any]) -> None:
    """Bind the public method label to the exact configured LOVE equations."""
    love = payload["configuration"].get("love", {})
    revised = payload["method_profile"] == "ring-taxon-preserving"
    selected = love.get("optimized_profile") == "ring-taxon-preserving"
    if revised != selected or (
        revised
        and (
            payload["operation"] not in {"love", "lra", "series"}
            or love.get("method") != "optimized"
        )
    ):
        _refuse(
            "method_profile_configuration_mismatch",
            "The request method profile must match optimized LOVE configuration",
        )

    if any(row["fallspeed_m_s"] < 0.01 for row in payload["parameters"]):
        named = "landclimii-2016-gpm-neutral-analytical-v1"
        required = (
            ("reveals", "love")
            if payload["operation"] in {"lra", "series"}
            else (payload["operation"],)
        )
        for method in required:
            config = payload["configuration"].get(method, {})
            if (
                config.get("fall_speed_profile") != named
                or config.get("distance_weighting") != "gpm neutral"
                or (method == "love" and config.get("method") != "analytical")
            ):
                _refuse(
                    "unsupported_fall_speed_profile",
                    "Fall speeds below 0.01 m/s require the named LandClim II gpm-neutral analytical profile",
                )


def validate_request(
    payload: Mapping[str, object], *, input_root: Path
) -> ValidatedRequest:
    """Validate an exploratory input contract without claiming scientific review.

    Numeric coordinates are pairing keys, never inferred ages or sample IDs.
    Source age support and its type remain separate, including disjoint intervals.
    Referenced review files are content-bound; authenticity and scientific approval
    remain the release evidence gate's responsibility.
    """
    try:
        canonical = json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        copy = json.loads(canonical)
    except (TypeError, ValueError) as exc:
        raise LRARefusal(
            "invalid_lra_json", "Request must contain finite JSON values"
        ) from exc
    errors = sorted(
        Draft202012Validator(REQUEST_SCHEMA).iter_errors(copy),
        key=lambda error: str(error.path),
    )
    if errors:
        error = errors[0]
        _refuse(
            "invalid_lra_schema", f"{'/'.join(map(str, error.path))}: {error.message}"
        )
    _method_profile(copy)
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
            "The current engine does not propagate chronology, basin geometry, parameter-domain, spatial-model or PPE covariance uncertainty",
        )
    roles = _evidence(copy, input_root.resolve())
    _pollen(copy, roles)
    _temporal_and_denominators(copy, roles)
    parameters = [row["taxon"] for row in copy["parameters"]]
    if len(parameters) != len(set(parameters)) or set(parameters) != set(copy["taxa"]):
        _refuse(
            "parameter_taxon_mismatch",
            "Parameters must cover the exact retained taxon denominator once",
        )
    previous_outer = None
    for ring in copy.get("rings", []):
        if roles.get(ring["geometry_evidence_id"]) != "geometry":
            _refuse("invalid_ring_lineage", ring["geometry_evidence_id"])
        if ring["terrestrial_area_m2"] > ring["ring_area_m2"]:
            _refuse(
                "terrestrial_area_exceeds_ring",
                "Terrestrial area cannot exceed its ring area",
            )
        if not ring["inner_m"] < ring["mean_m"] < ring["outer_m"] or (
            previous_outer is not None and ring["inner_m"] < previous_outer
        ):
            _refuse(
                "invalid_ring_geometry",
                "Rings must be ordered, nonoverlapping and have interior mean distances",
            )
        previous_outer = ring["outer_m"]
    if (
        "local" in copy
        and copy["rings"][0]["inner_m"] < copy["local"]["basin"]["diameter_m"] / 2
    ):
        _refuse(
            "ring_inside_basin", "Terrestrial rings cannot begin inside the local basin"
        )
    return ValidatedRequest(canonical, hashlib.sha256(canonical.encode()).hexdigest())
