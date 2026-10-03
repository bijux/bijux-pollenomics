"""Missing source axes survive publication and refuse every oriented pair."""

from __future__ import annotations

from dataclasses import replace
import json
from typing import Literal

from jsonschema import Draft202012Validator
import pytest

from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PropagationCandidate,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
)
from tests.support.repository import SCIENTIFIC_CONTRACTS_ROOT

from .support import event


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    ((None, 13.191), (55.7047, None), (None, None), (None, 0.0), (0.0, None)),
)
@pytest.mark.parametrize("endpoint", ("source", "target"))
@pytest.mark.parametrize("indexed", (True, False))
def test_missing_axis_preserves_source_and_refuses_both_pair_directions(
    latitude: float | None,
    longitude: float | None,
    endpoint: str,
    indexed: bool,
) -> None:
    source = event("source", country_code="SE")
    target = event("target", country_code="DK", younger_bp=5500, older_bp=5500)
    incomplete = replace(
        source if endpoint == "source" else target,
        latitude=latitude,
        longitude=longitude,
        coordinate_quality="reported",
    )
    if endpoint == "source":
        source = incomplete
    else:
        target = incomplete
    published = json.loads(json.dumps(incomplete.as_dict(), allow_nan=False))
    assert published["latitude"] == latitude
    assert published["longitude"] == longitude
    assert not incomplete.has_valid_coordinates
    schema = json.loads(
        (SCIENTIFIC_CONTRACTS_ROOT / "phenomenon-event.schema.json").read_bytes()
    )
    Draft202012Validator(schema).validate(published)
    for first, second in ((source, target), (target, source)):
        refusal = evaluate_propagation_pair(first, second)
        assert isinstance(refusal, PropagationPairRefusal)
        assert refusal.reason_code == "invalid_or_missing_coordinate"
        assert (refusal.source_event_id, refusal.target_event_id) == (
            first.event_id,
            second.event_id,
        )
        assert json.loads(json.dumps(refusal.as_dict())) == refusal.as_dict()
    generate = (
        generate_propagation_network
        if indexed
        else generate_propagation_network_exhaustive
    )
    network = generate((source, target))
    result = network.scenario_results[0]
    assert set(network.events) == {source, target}
    assert not result.evaluated_pairs and not result.directed_candidates
    assert {
        (row.source_event_id, row.target_event_id, row.reason_code)
        for row in result.refusals
    } == {
        (source.event_id, target.event_id, "invalid_or_missing_coordinate"),
        (target.event_id, source.event_id, "invalid_or_missing_coordinate"),
    }
    assert len({row.pair_id for row in result.refusals}) == 2
    reconciliation = result.reconciliation
    assert reconciliation.input_event_count == reconciliation.eligible_event_count == 2
    assert reconciliation.evaluated_pair_count == 0
    assert reconciliation.refused_pair_count == 2
    assert reconciliation.connected_component_count == 0
    assert sum(dict(reconciliation.status_counts).values()) == 0
    countries = dict(reconciliation.ordered_country_pair_counts)
    assert dict(countries["SE-DK"])["refused"] == 1
    assert dict(countries["DK-SE"])["refused"] == 1
    assert sum(sum(dict(counts).values()) for counts in countries.values()) == 2
    assert network.duplicate_input_event_count == 0


@pytest.mark.parametrize("axis", ("latitude", "longitude"))
@pytest.mark.parametrize("missing_opposite", (True, False))
@pytest.mark.parametrize(
    "value", (True, False, float("nan"), float("inf"), -float("inf"), "55.0")
)
def test_present_malformed_axis_is_refused_even_when_the_other_axis_is_missing(
    axis: Literal["latitude", "longitude"],
    missing_opposite: bool,
    value: object,
) -> None:
    valid = event("invalid-axis")
    latitude: object = None if missing_opposite else valid.latitude
    longitude: object = None if missing_opposite else valid.longitude
    if axis == "latitude":
        latitude = value
    else:
        longitude = value
    with pytest.raises(EventValidationError) as refused:
        replace(valid, latitude=latitude, longitude=longitude)  # type: ignore[arg-type]
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    ((91.0, 13.191), (-91.0, None), (55.0, 181.0), (None, -181.0), (120.0, 55.0)),
)
def test_out_of_range_or_demonstrably_reversed_axes_refuse_before_pair_evaluation(
    latitude: float | None, longitude: float | None
) -> None:
    with pytest.raises(EventValidationError) as refused:
        event("outside-range", latitude=latitude, longitude=longitude)
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("latitude", (-90.0, 0.0, 90.0))
@pytest.mark.parametrize("longitude", (-180.0, 0.0, 180.0))
def test_valid_complete_coordinate_boundaries_keep_finite_zero_distance(
    latitude: float, longitude: float
) -> None:
    source = event("boundary-source", latitude=latitude, longitude=longitude)
    target = event(
        "boundary-target",
        latitude=latitude,
        longitude=longitude,
        younger_bp=5500,
        older_bp=5500,
    )
    result = evaluate_propagation_pair(source, target)
    assert source.has_valid_coordinates and target.has_valid_coordinates
    assert isinstance(result, PropagationCandidate)
    assert result.distance_km_unrounded == 0.0
    assert result.shared_location
    assert result.candidate_status == "definite_candidate"


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    ((True, None), (None, False), (91, None), (None, 181), ("55", None)),
)
def test_public_schema_retains_numeric_type_and_range_guards(
    latitude: object, longitude: object
) -> None:
    schema = json.loads(
        (SCIENTIFIC_CONTRACTS_ROOT / "phenomenon-event.schema.json").read_bytes()
    )
    published = replace(
        event("schema-invalid"), coordinate_quality="reported"
    ).as_dict()
    published.update(latitude=latitude, longitude=longitude)
    assert not Draft202012Validator(schema).is_valid(published)
