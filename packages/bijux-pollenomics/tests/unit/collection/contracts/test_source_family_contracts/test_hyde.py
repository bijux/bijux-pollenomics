"""Missing native HYDE evidence cannot be promoted by generic file presence."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.capabilities import (
    build_source_capability_contract_payload,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contract_payload,
    build_source_family_contracts,
    build_source_family_state_matrix_payload,
)

from .support import _object, _rows


def test_hyde_release_and_prohibited_interpretations_are_explicit() -> None:
    families = build_source_family_contract_payload()
    capabilities = build_source_capability_contract_payload()
    assert families["source_release_by_key"] == {"hyde": "3.5"}
    assert capabilities["source_release_by_key"] == {"hyde": "3.5"}
    assert "hyde" not in _object(capabilities["normative_contract"])["source_keys"]
    profile = next(
        row for row in _rows(capabilities["sources"]) if row["source_key"] == "hyde"
    )
    assert profile["evidence_class"] == "modelled_land_use_context"
    assert profile["support_by_dimension"]["pollen_propagation_event"] == "unsupported"
    assert profile["support_by_dimension"]["crop_cereal_resolution"] == "unsupported"
    assert profile["support_by_dimension"]["quantitative_observation"] == "partial"
    assert (
        "HYDE modeled land use is independently measured vegetation truth"
        in profile["prohibited_claims"]
    )
    assert profile["human_review_required"] is True


def test_absent_hyde_keeps_unknown_denominators_and_separate_statuses(
    tmp_path: Path,
) -> None:
    payload = build_source_family_state_matrix_payload(
        tmp_path / "data", counts={"hyde_admitted_cell_count": 9000}
    )
    row = next(row for row in _rows(payload["rows"]) if row["source_key"] == "hyde")
    assert row["raw_status"] == row["normalized_status"] == "missing"
    assert row["authority_status"] == "refused"
    assert row["publication_posture"] == "refused_not_publication_ready"
    assert row["coverage_metrics"] == {
        "hyde_admitted_cell_count": None,
        "hyde_admitted_country_count": None,
    }
    assert "unavailable_governed_coverage_metrics" in row["blocking_reasons"]
    assert "zero_coverage_metrics" not in row["blocking_reasons"]


def test_self_asserted_hyde_json_cannot_satisfy_native_capabilities(
    tmp_path: Path,
) -> None:
    contract = next(
        c for c in build_source_family_contracts() if c.source_key == "hyde"
    )
    capabilities = build_source_capability_contract_payload()
    profile = next(
        row for row in _rows(capabilities["sources"]) if row["source_key"] == "hyde"
    )
    paths = {
        p for values in profile["evidence_paths_by_dimension"].values() for p in values
    }
    for layer in (
        contract.raw_layer,
        contract.normalized_layer,
        contract.reviewed_layer,
        contract.published_layer,
    ):
        paths.update(layer.example_artifacts)
    for path in paths:
        file = tmp_path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            json.dumps(
                {
                    "schema_version": "hyde-native.v1",
                    "source_release": "3.5",
                    "release_status": "accepted",
                    "reviewer_id": "self-assertion",
                    "row_count": 1,
                    "rows": [{"cell_count": 9999}],
                }
            )
        )
    payload = build_source_family_state_matrix_payload(tmp_path / "data", counts={})
    row = next(row for row in _rows(payload["rows"]) if row["source_key"] == "hyde")
    assert row["raw_status"] == row["normalized_status"] == "present"
    assert row["authority_status"] == "refused"
    assert row["publication_posture"] == "refused_not_publication_ready"
    audit = [
        r
        for r in _rows(_object(payload["capability_materialization_audit"])["rows"])
        if r["source_key"] == "hyde"
    ]
    assert len(audit) == 17
    for capability in audit:
        assert capability["present_evidence_paths"] == ()
        assert capability["materialization"] == (
            "not_applicable" if capability["support"] == "unsupported" else "missing"
        )
