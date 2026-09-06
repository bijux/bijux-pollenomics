"""Closed source relations for atlas-projection tests."""

from __future__ import annotations

import json

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
    SourceNodeDerivationResult,
    derive_neotoma_source_chronology_nodes,
)
from bijux_pollenomics.reporting.source_chronology import (
    SourceChronologyAtlasProjection,
    build_source_chronology_atlas_projection,
)

SNAPSHOT = "sha256:" + "a" * 64
BUILD = "sha256:" + "b" * 64
SITE_ID = "site-SE"
DETAIL_ID = f"neotoma:site:{SITE_ID}"


def source_result() -> SourceNodeDerivationResult:
    """Derive all three publication levels from one admitted observation."""
    sample_id = "sample-SE"
    variable_id = "variable-1"
    return derive_neotoma_source_chronology_nodes(
        observations=[
            {
                "observation_id": "observation-1",
                "sample_id": sample_id,
                "site_id": SITE_ID,
                "variable_id": variable_id,
                "country_code": "SE",
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
                "source_element_type": "pollen",
                "detection_status": "reported_value",
                "source_value": 3,
                "source_unit": "NISP",
                "source_taxon_id": 1,
                "source_reported_name": "Abies",
                "source_ecological_group": "TRSH",
            }
        ],
        samples=[
            {
                "sample_id": sample_id,
                "site_id": SITE_ID,
                "country_code": "SE",
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
            }
        ],
        sites=[
            {
                "site_id": SITE_ID,
                "country_code": "SE",
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
                "source_payload": {
                    "geography": json.dumps(
                        {"type": "Point", "coordinates": [18.0, 59.0]}
                    )
                },
            }
        ],
        variables=[
            {
                "variable_id": variable_id,
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
                "source_taxon_id": 1,
                "source_reported_name": "Abies",
                "source_units": ["NISP"],
                "source_semantics": [
                    {
                        "source_element_type": "pollen",
                        "source_ecological_group": "TRSH",
                    }
                ],
            }
        ],
        chronologies=[
            {
                "chronology_claim_id": "claim-SE",
                "source_record_id": sample_id,
                "site_id": SITE_ID,
                "country_code": "SE",
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
                "is_default_chronology": True,
                "chronology_id": "chronology-SE",
                "chronology_name": "Source chronology",
                "comparability_status": "comparable",
                "younger_bp": 100,
                "older_bp": 125,
                "admission_reason": None,
                "refusal_reason": None,
                "provenance_record_id": SNAPSHOT,
            }
        ],
        context=SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        ),
    )


def projection() -> tuple[SourceNodeDerivationResult, SourceChronologyAtlasProjection]:
    """Build the canonical synthetic atlas projection."""
    result = source_result()
    return result, build_source_chronology_atlas_projection(
        result,
        detail_record_ids={DETAIL_ID},
    )


__all__ = ["BUILD", "DETAIL_ID", "SITE_ID", "SNAPSHOT", "projection", "source_result"]
