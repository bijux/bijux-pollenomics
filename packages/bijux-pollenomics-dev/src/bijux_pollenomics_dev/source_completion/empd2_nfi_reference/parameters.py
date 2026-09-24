"""Authenticate exact LRA taxon, PPE, and fall-speed parameter rows."""

from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json

from .projection import digest, identities, identity, sha_identity

_MANIFEST_KEYS = {
    "schema_version",
    "pollen_source_sha256",
    "accepted_taxon_ids",
    "ppe_reference_taxon",
    "rows",
}
_ROW_KEYS = {
    "taxon_id",
    "accepted_taxon_name",
    "accepted_taxon_rank",
    "lra_model_taxon_id",
    "ppe_binding",
    "fall_speed_binding",
    "evidence_reference_ids",
    "parameter_row_sha256",
}
_BINDING_KEYS = {
    "parameter_record_id",
    "parameter_record_sha256",
    "parameter_candidate_id",
    "parameter_candidate_sha256",
    "source_value_text",
    "source_value",
    "source_units",
    "source_uncertainty_text",
    "source_uncertainty_value",
    "normalized_value",
    "normalized_units",
    "normalization_profile",
    "reference_taxon",
    "applicability_domain",
    "normalization_rationale",
}


def _positive(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return result


def _binding(value: object, kind: str) -> None:
    if not isinstance(value, dict) or set(value) != _BINDING_KEYS:
        raise ValueError(f"{kind} binding fields differ from the exact schema")
    binding = cast(dict[str, Any], value)
    for field in (
        "parameter_record_id",
        "parameter_candidate_id",
        "source_value_text",
        "source_units",
        "normalization_profile",
        "applicability_domain",
        "normalization_rationale",
    ):
        identity(binding[field], f"{kind} {field}")
    for field in ("parameter_record_sha256", "parameter_candidate_sha256"):
        sha_identity(binding[field], f"{kind} {field}")
    source_value = _positive(binding["source_value"], f"{kind} source value")
    normalized_value = _positive(
        binding["normalized_value"], f"{kind} normalized value"
    )
    try:
        parsed_source_text = float(binding["source_value_text"])
    except ValueError as exc:
        raise ValueError(f"{kind} source text is not numeric") from exc
    if not math.isfinite(parsed_source_text) or parsed_source_text != source_value:
        raise ValueError(f"{kind} source text differs from its numeric value")
    uncertainty = binding["source_uncertainty_value"]
    uncertainty_text = binding["source_uncertainty_text"]
    if uncertainty is None:
        if uncertainty_text is not None:
            raise ValueError(f"{kind} uncertainty text lacks a numeric value")
    elif (
        isinstance(uncertainty, bool)
        or not isinstance(uncertainty, (int, float))
        or not math.isfinite(float(uncertainty))
        or uncertainty < 0
    ):
        raise ValueError(f"{kind} uncertainty must be finite and nonnegative")
    else:
        identity(uncertainty_text, f"{kind} uncertainty text")
        try:
            parsed_uncertainty = float(uncertainty_text)
        except ValueError as exc:
            raise ValueError(f"{kind} uncertainty text is not numeric") from exc
        if parsed_uncertainty != float(uncertainty):
            raise ValueError(f"{kind} uncertainty text differs from its value")
    if kind == "ppe":
        identity(binding["reference_taxon"], "PPE reference taxon")
        if (
            binding["source_units"] != "relative_to_reference_taxon"
            or binding["normalized_units"] != "dimensionless_pollen_productivity"
            or binding["normalization_profile"]
            != "identity-relative-ppe-to-dimensionless.v1"
            or normalized_value != source_value
        ):
            raise ValueError("PPE normalized units are unsupported")
    elif (
        binding["reference_taxon"] is not None
        or binding["source_units"] != "m/s"
        or binding["normalized_units"] != "m/s"
        or binding["normalization_profile"] != "identity-m-per-second.v1"
        or normalized_value != source_value
    ):
        raise ValueError("fall-speed normalization is unsupported")


def authenticated_parameter_manifest(
    content: bytes,
    pinned_sha256: str,
    projection: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Bind exact parameter values and units to the receipt content digest."""
    pinned = sha_identity(pinned_sha256, "taxon_parameter_manifest_sha256")
    if sha256(content).hexdigest() != pinned:
        raise ValueError("taxon parameter bytes differ from the external trust anchor")
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("taxon parameter manifest is not canonical JSON") from exc
    accepted = receipt["accepted_taxon_ids"]
    reference_taxon = (
        identity(raw.get("ppe_reference_taxon"), "PPE reference taxon")
        if isinstance(raw, dict)
        else ""
    )
    if (
        not isinstance(raw, dict)
        or set(raw) != _MANIFEST_KEYS
        or canonical_json(raw).encode() != content
        or raw.get("schema_version") != "empd2-lra-taxon-parameters.v1"
        or raw.get("pollen_source_sha256")
        != projection["source_identities"]["empd2_source"]
        or raw.get("accepted_taxon_ids") != accepted
        or reference_taxon not in accepted
        or pinned != receipt["parameter_binding_sha256"]
    ):
        raise ValueError("taxon parameter manifest differs from the pinned receipt")
    rows = raw.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("taxon parameter rows must be an object array")
    mapped: dict[str, dict[str, Any]] = {}
    for row in cast(list[dict[str, Any]], rows):
        if set(row) != _ROW_KEYS:
            raise ValueError("taxon parameter row fields differ from the exact schema")
        taxon = identity(row["taxon_id"], "parameter taxon")
        if taxon in mapped or row["lra_model_taxon_id"] != taxon:
            raise ValueError("taxon parameter identity is duplicated or inconsistent")
        identity(row["accepted_taxon_name"], "accepted taxon name")
        if row["accepted_taxon_rank"] != "genus":
            raise ValueError("accepted parameter taxa must have genus rank")
        _binding(row["ppe_binding"], "ppe")
        if row["ppe_binding"]["reference_taxon"] != reference_taxon:
            raise ValueError("PPE bindings do not share the manifest reference taxon")
        _binding(row["fall_speed_binding"], "fall_speed")
        identities(row["evidence_reference_ids"], "parameter evidence")
        payload = {
            key: item for key, item in row.items() if key != "parameter_row_sha256"
        }
        if sha_identity(row["parameter_row_sha256"], "parameter_row_sha256") != digest(
            payload
        ):
            raise ValueError("taxon parameter row digest differs from exact values")
        mapped[taxon] = row
    if list(mapped) != accepted:
        raise ValueError("taxon parameter rows do not close the accepted denominator")
    return mapped
