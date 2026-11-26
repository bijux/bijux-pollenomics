"""Source-bound synthetic fixtures for SEAD retrieval tests."""

import json
from pathlib import Path
from typing import Any, cast

import pytest


@pytest.fixture(scope="module")
def synthetic_historical_sead_review() -> dict[str, Any]:
    """Project original decisions into review-shaped rows; not retained ledger bytes."""
    from bijux_pollenomics_dev.source_completion import sead_country_retrieval as owner

    root = Path(__file__).resolve().parents[4]
    decisions = json.loads((root / owner.RAW / "country-decisions.json").read_bytes())
    boundary = cast(dict[str, Any], json.loads((root / owner.BOUNDARY).read_bytes()))
    by_id = {int(row["site_id"]): row for row in decisions["decisions"]}
    for row in boundary["decisions"]:
        prior = by_id[int(row["source_record_id"].removeprefix("sead:site:"))]
        detail = prior["decision"]
        assigned = detail["decision_status"] == "assigned"
        row.update(
            {
                "country_decision_status": detail["decision_status"],
                "boundary_decision_status": detail["decision_status"],
                "decision_method": detail["decision_method"],
                "candidate_countries": detail["candidate_countries"],
                "boundary_artifact_digest": detail["boundary_artifact_digest"],
                "prior_country_decision_comparison": "agrees",
                "published_country": prior["governed_country_code"]
                if assigned
                else None,
                "derived_country_code": prior["governed_country_code"]
                if assigned
                else None,
                "review_requirement": "no_point_review_required"
                if assigned
                else "qualified_review_required",
                "qualified_review_status": "not_required" if assigned else "pending",
            }
        )
    return boundary
