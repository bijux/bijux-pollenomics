"""Validate normalized SEAD lineage against its historical source authority."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
)

from .contract import (
    SEAD_NORMALIZED_LINEAGE_INPUTS,
    SEAD_NORMALIZED_LINEAGE_PATH,
    file_sha256,
    historical_country_membership,
)


def validate_normalized_lineage(
    data_root: Path, *, lineage_bytes: bytes | None = None
) -> None:
    """Bind every normalized map source to the admitted acquisition identity."""
    if lineage_bytes is None:
        lineage = json_object(data_root / SEAD_NORMALIZED_LINEAGE_PATH)
    else:
        lineage = json.loads(lineage_bytes)
        if not isinstance(lineage, dict):
            raise ValueError("SEAD normalized lineage must be an object")
    version = lineage.get("schema_version")
    if version not in {
        "sead-normalized-surface-lineage.v1",
        "sead-normalized-surface-lineage.v2",
    }:
        raise ValueError("SEAD normalized lineage schema differs")
    if (
        version == "sead-normalized-surface-lineage.v2"
        and lineage.get("country_membership") != historical_country_membership()
    ):
        raise ValueError("SEAD normalized lineage country membership differs")
    if version == "sead-normalized-surface-lineage.v2":
        inputs = lineage.get("refresh_input_sha256")
        required = {
            "boundary/raw/source_manifest.json",
            "boundary/raw/sweden.geojson",
            "boundary/raw/norway.geojson",
            "boundary/raw/finland.geojson",
            "boundary/raw/denmark.geojson",
            "boundary/normalized/nordic_country_boundaries.geojson",
            "evidence/evidence_materialization_manifest.json",
            "context/raa_density",
        }
        if not isinstance(inputs, dict) or not required.issubset(inputs):
            raise ValueError("SEAD normalized lineage refresh inputs are incomplete")
        if (
            inputs["boundary/normalized/nordic_country_boundaries.geojson"]
            != SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST.removeprefix("sha256:")
            or inputs["evidence/evidence_materialization_manifest.json"]
            != SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256
        ):
            raise ValueError("SEAD normalized lineage refresh input authority differs")
        for key, value in inputs.items():
            if key == "context/raa_density" and value is None:
                continue
            if (
                not isinstance(key, str)
                or not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError(
                    "SEAD normalized lineage refresh input digest is invalid"
                )
    for field in (
        "source_run_id",
        "build_id",
        "acquisition_manifest_sha256",
        "parent_admission_sha256",
        "acquisition_bundle_sha256",
    ):
        value = lineage.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"SEAD normalized lineage {field} is missing")
    expected = {
        str(path.relative_to("sead")): file_sha256(data_root / path)
        for path in SEAD_NORMALIZED_LINEAGE_INPUTS
    }
    if lineage.get("normalized_surface_sha256") != expected:
        raise ValueError("SEAD normalized lineage surface hashes differ")
    review_lineage = json_object(data_root / "sead/review/temporal_review.json").get(
        "lineage"
    )
    shared_fields = (
        "source_run_id",
        "build_id",
        "acquisition_manifest_sha256",
        "parent_admission_sha256",
    )
    if review_lineage != {field: lineage[field] for field in shared_fields}:
        raise ValueError("SEAD normalized and review lineage differ")


def json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(  # noqa: TRY004 - malformed contract payload
            f"SEAD candidate JSON root is invalid: {path.name}"
        )
    return value
