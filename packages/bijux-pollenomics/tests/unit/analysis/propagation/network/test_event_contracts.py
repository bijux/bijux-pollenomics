"""Event identity, publication, and admission contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PropagationCandidate,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
)
from bijux_pollenomics.analysis.propagation.network.codec import _event_manifest_digest

from .support import event


def test_source_native_event_id_is_stable_and_preserves_zero() -> None:
    first = event("zero", younger_bp=0, older_bp=0)
    second = event("zero", younger_bp=0, older_bp=0)

    assert first.event_id == second.event_id
    assert first.interval is not None
    assert first.interval.younger_bp == 0
    assert first.as_dict()["observation_ids"] == ["observation-zero"]


@pytest.mark.parametrize(
    "observations",
    (
        "AB",
        b"AB",
        bytearray(b"AB"),
        memoryview(b"AB"),
        None,
        1,
        {"observation": "source"},
        {"observation"},
        frozenset({"observation"}),
        iter(("observation",)),
    ),
)
def test_observation_identity_requires_an_array_container(
    observations: object,
) -> None:
    with pytest.raises(EventValidationError) as refused:
        replace(event("invalid-container"), observation_ids=observations)  # type: ignore[arg-type]
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("observations", ((), []))
def test_observation_identity_still_requires_a_nonempty_array(
    observations: object,
) -> None:
    with pytest.raises(EventValidationError) as refused:
        replace(event("empty-container"), observation_ids=observations)  # type: ignore[arg-type]
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize(
    "observations",
    ([None], [True], [1], [""], [" \t"], [b"AB"], [["nested"]], ["valid", None]),
)
def test_observation_identity_array_members_must_be_nonempty_strings(
    observations: object,
) -> None:
    with pytest.raises(EventValidationError) as refused:
        replace(event("invalid-member"), observation_ids=observations)  # type: ignore[arg-type]
    assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize(
    ("source_id", "target_id"),
    (("AB", "CD"), ("source-observation", "target-observation")),
)
def test_scalar_observation_ids_cannot_fabricate_or_conflate_network_support(
    source_id: str, target_id: str
) -> None:
    source = replace(event("source"), observation_ids=(source_id,), event_id="")
    target = replace(
        event("target", younger_bp=5500, older_bp=5500),
        observation_ids=(target_id,),
        event_id="",
    )
    pair = evaluate_propagation_pair(source, target)
    assert isinstance(pair, PropagationCandidate)
    assert pair.candidate_status == "definite_candidate"
    network = generate_propagation_network((source, target)).scenario_results[0]
    assert len(network.directed_candidates) == 1
    assert not network.refusals
    assert source.observation_ids == (source_id,)
    assert target.observation_ids == (target_id,)
    for baseline, scalar in ((source, source_id), (target, target_id)):
        with pytest.raises(EventValidationError) as refused:
            replace(baseline, observation_ids=scalar, event_id="")  # type: ignore[arg-type]
        assert refused.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("json_lists", (False, True))
def test_tuple_and_json_list_observations_keep_canonical_identity_and_pairs(
    json_lists: bool,
) -> None:
    source = replace(
        event("source"), observation_ids=("source-a", "source-b"), event_id=""
    )
    target = replace(
        event("target", younger_bp=5500, older_bp=5500),
        observation_ids=("target",),
        event_id="",
    )
    source_ids = [" source-b\t", "source-a", " source-a "]
    target_ids = [" target\n", "target"]
    source_before, target_before = list(source_ids), list(target_ids)
    source_values = source_ids if json_lists else tuple(source_ids)
    target_values = target_ids if json_lists else tuple(target_ids)
    normalized_source = replace(
        source,
        observation_ids=source_values,  # type: ignore[arg-type]
        event_id="",
    )
    normalized_target = replace(
        target,
        observation_ids=target_values,  # type: ignore[arg-type]
        event_id="",
    )
    assert normalized_source == source and normalized_target == target
    assert source_ids == source_before and target_ids == target_before
    assert normalized_source.as_dict()["observation_ids"] == ["source-a", "source-b"]
    assert normalized_target.as_dict()["observation_ids"] == ["target"]
    assert _event_manifest_digest((normalized_source, normalized_target)) == (
        _event_manifest_digest((source, target))
    )
    assert evaluate_propagation_pair(normalized_source, normalized_target) == (
        evaluate_propagation_pair(source, target)
    )
    assert (
        generate_propagation_network((normalized_source, normalized_target)).as_dict()
        == generate_propagation_network((source, target)).as_dict()
    )


def test_publication_schema_excludes_internal_identity_fields() -> None:
    baseline = event("identity")
    changed = replace(baseline, measurement_semantics_id="abundance.v1")

    assert baseline.as_dict() == changed.as_dict()
    assert _event_manifest_digest((baseline,)) != _event_manifest_digest((changed,))


@pytest.mark.parametrize(
    "overrides",
    (
        {"younger_bp": 100, "older_bp": 50},
        {"younger_bp": 100, "older_bp": None},
        {"younger_bp": -1, "older_bp": 50},
        {"subject_granularity": "site_midpoint"},
        {"feature_key": "taxon:"},
    ),
)
def test_invalid_or_presentation_level_events_are_refused(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(EventValidationError) as refusal:
        event("invalid", **overrides)  # type: ignore[arg-type]

    assert refusal.value.reason_code == "invalid_event_schema"


@pytest.mark.parametrize("field", ("preaggregation_valid", "role_membership_explicit"))
@pytest.mark.parametrize("value", ("false", "true", 0, 1, None, [], {}, [False]))
@pytest.mark.parametrize("role", (False, True))
def test_nonboolean_admission_flags_are_refused(
    field: str, value: object, role: bool
) -> None:
    template = (
        event("flags", resolution="ecological_role", feature_key="role:crop")
        if role
        else event("flags")
    )
    with pytest.raises(
        EventValidationError, match=f"{field} must be a boolean"
    ) as error:
        if field == "preaggregation_valid":
            replace(template, preaggregation_valid=value)  # type: ignore[arg-type]
        else:
            replace(template, role_membership_explicit=value)  # type: ignore[arg-type]
    assert error.value.reason_code == "invalid_event_schema"


def test_valid_boolean_flags_preserve_publication_and_pair_refusal() -> None:
    baseline = event("source")
    explicit = replace(
        baseline, preaggregation_valid=True, role_membership_explicit=False
    )
    assert explicit == baseline
    assert baseline.preaggregation_valid is True
    assert baseline.role_membership_explicit is False
    invalid_preaggregation = replace(baseline, preaggregation_valid=False)
    assert invalid_preaggregation.preaggregation_valid is False
    assert invalid_preaggregation.event_id == baseline.event_id
    assert invalid_preaggregation.as_dict() == baseline.as_dict()
    assert _event_manifest_digest((invalid_preaggregation,)) != _event_manifest_digest(
        (baseline,)
    )
    target = event("target", younger_bp=5500, older_bp=5500)
    accepted = evaluate_propagation_pair(baseline, target)
    refused = evaluate_propagation_pair(invalid_preaggregation, target)
    assert isinstance(accepted, PropagationCandidate)
    assert accepted.candidate_status == "definite_candidate"
    assert isinstance(refused, PropagationPairRefusal)
    assert refused.reason_code == "invalid_preaggregation"


def test_ecological_role_still_requires_explicit_true_membership() -> None:
    source = event("source", resolution="ecological_role", feature_key="role:crop")
    target = event(
        "target",
        resolution="ecological_role",
        feature_key="role:crop",
        younger_bp=5500,
        older_bp=5500,
    )
    assert source.role_membership_explicit is True
    with pytest.raises(
        EventValidationError, match="membership must be explicit"
    ) as error:
        replace(source, role_membership_explicit=False)
    assert error.value.reason_code == "invalid_event_schema"
    accepted = evaluate_propagation_pair(source, target)
    assert isinstance(accepted, PropagationCandidate)
    assert accepted.candidate_status == "definite_candidate"
