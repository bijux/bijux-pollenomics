"""Typed source relations for chronology-node tests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
    SourceNodeDerivationResult,
    derive_neotoma_source_chronology_nodes,
)

SNAPSHOT = "sha256:" + "a" * 64
BUILD = "sha256:" + "b" * 64


def source_rows(
    *,
    country: str = "SE",
    observation_id: str = "observation-1",
    source_value: object = 3,
    source_code: object = "TRSH",
    taxon_id: object = 1,
    taxon_name: object = "Abies",
    default: bool = True,
    status: str = "comparable",
    younger_bp: object = 100,
    older_bp: object = 125,
    admission_reason: str | None = None,
) -> dict[str, list[dict[str, object]]]:
    site_id = f"site-{country}"
    sample_id = f"sample-{country}"
    variable_id = f"variable-{taxon_id}"
    observation: dict[str, object] = {
        "observation_id": observation_id,
        "sample_id": sample_id,
        "site_id": site_id,
        "variable_id": variable_id,
        "country_code": country,
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
        "source_element_type": "pollen",
        "detection_status": "reported_value",
        "source_value": source_value,
        "source_unit": "NISP",
        "source_taxon_id": taxon_id,
        "source_reported_name": taxon_name,
        "source_ecological_group": source_code,
    }
    variable: dict[str, object] = {
        "variable_id": variable_id,
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
        "source_taxon_id": taxon_id,
        "source_reported_name": taxon_name,
        "source_units": ["NISP"],
        "source_semantics": [
            {
                "source_element_type": "pollen",
                "source_ecological_group": source_code,
            }
        ],
    }
    site: dict[str, object] = {
        "site_id": site_id,
        "country_code": country,
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
        "source_payload": {
            "geography": json.dumps({"type": "Point", "coordinates": [18.0, 59.0]})
        },
    }
    sample: dict[str, object] = {
        "sample_id": sample_id,
        "site_id": site_id,
        "country_code": country,
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
    }
    claim: dict[str, object] = {
        "chronology_claim_id": f"claim-{country}-{observation_id}",
        "source_record_id": sample_id,
        "site_id": site_id,
        "country_code": country,
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
        "is_default_chronology": default,
        "comparability_status": status,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "admission_reason": admission_reason,
        "refusal_reason": None,
        "provenance_record_id": SNAPSHOT,
    }
    return {
        "observations": [observation],
        "samples": [sample],
        "sites": [site],
        "variables": [variable],
        "chronologies": [claim],
    }


def derive(
    rows: Mapping[str, Sequence[Mapping[str, object]]],
) -> SourceNodeDerivationResult:
    """Derive nodes from a closed source fixture."""
    return derive_neotoma_source_chronology_nodes(
        observations=rows["observations"],
        samples=rows["samples"],
        sites=rows["sites"],
        variables=rows["variables"],
        chronologies=rows["chronologies"],
        context=SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        ),
    )


__all__ = ["BUILD", "SNAPSHOT", "derive", "source_rows"]
