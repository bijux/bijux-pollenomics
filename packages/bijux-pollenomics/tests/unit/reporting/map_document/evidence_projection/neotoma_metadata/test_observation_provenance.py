"""Optional compact qualifiers preserve missingness without changing source rows."""

from collections.abc import Iterator
from copy import deepcopy

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma_metadata.observations import (
    observation_variable_provenance,
)


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"variableid": None}, {"symmetry": [None, {"literal": "unknown"}]}],
)
def test_optional_provenance_retains_absence_null_and_owned_values(
    payload: object,
) -> None:
    row = {"observation_id": "generated:observation", "source_payload": payload}
    original = deepcopy(row)
    result = list(observation_variable_provenance([row]))
    assert row == original
    assert result[0]["source_payload"] == payload
    assert result[0]["source_variable_provenance"] == payload
    if isinstance(payload, dict):
        assert result[0]["source_variable_provenance"] is not payload


def test_missing_source_payload_is_explicitly_unavailable() -> None:
    row = {"observation_id": "generated:observation"}
    result = list(observation_variable_provenance([row]))
    assert result == [{**row, "source_variable_provenance": None}]
    assert "source_payload" not in row


def test_provenance_yields_one_owned_row_without_consuming_later_sources() -> None:
    observed: list[str] = []
    native = {"symmetry": [{"literal": "reported"}]}

    def rows() -> Iterator[dict[str, object]]:
        observed.append("first")
        yield {"site_id": "generated:site", "source_payload": native}
        observed.append("second")
        yield {"site_id": "generated:site", "source_payload": {"variableid": 2}}

    projected = observation_variable_provenance(rows())
    assert observed == []
    first = next(projected)
    assert observed == ["first"]
    provenance = first["source_variable_provenance"]
    assert isinstance(provenance, dict)
    symmetry = provenance["symmetry"]
    assert isinstance(symmetry, list)
    symmetry[0]["literal"] = "changed display copy"
    assert native == {"symmetry": [{"literal": "reported"}]}
    second = next(projected)
    assert observed == ["first", "second"]
    assert second["source_variable_provenance"] == {"variableid": 2}
