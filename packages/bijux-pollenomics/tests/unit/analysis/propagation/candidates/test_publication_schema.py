"""Normative candidate publication rejects contradictory directional marks."""

from __future__ import annotations

import json

from jsonschema import Draft202012Validator
import pytest

from bijux_pollenomics.analysis.propagation.network import (
    PropagationCandidate,
    evaluate_propagation_pair,
)
from tests.support.repository import REPOSITORY_ROOT

from ..network.support import event


@pytest.mark.parametrize(
    ("status", "allowed"),
    [
        pytest.param("indeterminate_order", False, id="PROP-015"),
        pytest.param("definite_candidate", True, id="PROP-016-definite"),
        pytest.param("possible_candidate", True, id="PROP-016-possible"),
        pytest.param("unresolved", False, id="PROP-017-unresolved"),
        pytest.param("excluded_spatial", False, id="PROP-017-spatial"),
        pytest.param("excluded_temporal_nonpositive", False, id="PROP-017-nonpositive"),
        pytest.param("excluded_temporal_too_large", False, id="PROP-017-too-large"),
    ],
)
def test_candidate_schema_requires_directional_mark_to_match_declared_status(
    status: str, allowed: bool
) -> None:
    candidate = evaluate_propagation_pair(
        event("source"),
        event("target", younger_bp=5500, older_bp=5500, longitude=13.01),
    )
    assert isinstance(candidate, PropagationCandidate)
    row = json.loads(json.dumps(candidate.as_dict()))
    # Isolate the publication invariant from temporal classification: valid
    # declared statuses must have their own consistent directional posture.
    row.update(candidate_status=status, directional_arrow_allowed=allowed)
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "configs/scientific-contracts/propagation-candidate.schema.json"
        ).read_bytes()
    )
    validator = Draft202012Validator(schema)
    assert validator.is_valid(row)
    row["directional_arrow_allowed"] = not allowed
    errors = list(validator.iter_errors(row))
    assert errors
    assert any(
        list(error.path) == ["directional_arrow_allowed"] and error.validator == "const"
        for error in errors
    )
    assert not validator.is_valid(row)
