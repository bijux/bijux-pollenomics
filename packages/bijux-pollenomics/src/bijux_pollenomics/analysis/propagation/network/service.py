"""Indexed, exhaustive, and sensitivity network orchestration."""

from __future__ import annotations
from collections import defaultdict
from collections.abc import Sequence
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
)

from .codec import _deduplicate_events, _event_manifest_digest
from .errors import EventValidationError
from .evaluation import evaluate_propagation_pair
from .models import (
    PhenomenonEvent,
    PropagationCandidate,
    PropagationNetworkResult,
    PropagationPairRefusal,
    PropagationScenarioResult,
)
from .pairs import (
    _build_refusal,
    _exhaustive_pair_rows,
    _indexed_pair_rows,
    _preindexed_refusals,
)
from .reconciliation import _build_reconciliation, _universe_key
from .scenarios import PROPAGATION_SENSITIVITY_SCENARIOS


def generate_propagation_network(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario] = (DEFAULT_PROPAGATION_SCENARIO,),
) -> PropagationNetworkResult:
    """Generate deterministic scenario results through a latitude-band index."""
    return _generate_network(events, scenarios=scenarios, indexed=True)


def generate_propagation_network_exhaustive(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario] = (DEFAULT_PROPAGATION_SCENARIO,),
) -> PropagationNetworkResult:
    """Reference implementation for tests; do not use at Nordic production scale."""
    return _generate_network(events, scenarios=scenarios, indexed=False)


def run_propagation_sensitivity(
    events: Sequence[PhenomenonEvent],
) -> PropagationNetworkResult:
    """Execute every declared rectangular distance/lag sensitivity scenario."""
    return generate_propagation_network(
        events,
        scenarios=PROPAGATION_SENSITIVITY_SCENARIOS,
    )


def _generate_network(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario],
    indexed: bool,
) -> PropagationNetworkResult:
    unique_events, duplicate_count = _deduplicate_events(events)
    build_ids = {event.build_id for event in unique_events}
    if len(build_ids) > 1:
        raise EventValidationError(
            "invalid_event_schema", "all events in one network require one build_id"
        )
    unique_scenarios = {scenario.scenario_id: scenario for scenario in scenarios}
    if len(unique_scenarios) != len(scenarios):
        raise ValueError("scenario_id values must be unique")
    ordered_scenarios = tuple(unique_scenarios[key] for key in sorted(unique_scenarios))
    pollen_events = tuple(
        event for event in unique_events if event.evidence_domain == "pollen_context"
    )
    excluded_non_pollen_events = tuple(
        event for event in unique_events if event.evidence_domain != "pollen_context"
    )
    manifest_digest = _event_manifest_digest(pollen_events)
    results = tuple(
        _generate_scenario(
            unique_events,
            scenario=scenario,
            event_manifest_digest=manifest_digest,
            indexed=indexed,
        )
        for scenario in ordered_scenarios
    )
    return PropagationNetworkResult(
        event_manifest_digest=manifest_digest,
        events=pollen_events,
        excluded_non_pollen_events=excluded_non_pollen_events,
        scenario_results=results,
        duplicate_input_event_count=duplicate_count,
    )


def _generate_scenario(
    events: tuple[PhenomenonEvent, ...],
    *,
    scenario: CandidatePropagationScenario,
    event_manifest_digest: str,
    indexed: bool,
) -> PropagationScenarioResult:
    pollen_events = tuple(
        event for event in events if event.evidence_domain == "pollen_context"
    )
    universes: dict[tuple[str, ...], list[PhenomenonEvent]] = defaultdict(list)
    for event in pollen_events:
        universes[_universe_key(event)].append(event)
    evaluated: dict[tuple[str, str], PropagationCandidate] = {}
    refusals: dict[tuple[str, str], PropagationPairRefusal] = {}
    for universe_key in sorted(universes):
        universe = tuple(
            sorted(universes[universe_key], key=lambda event: event.event_id)
        )
        for source, target, reason in _preindexed_refusals(universe):
            pair_key = (source.event_id, target.event_id)
            refusals[pair_key] = _build_refusal(source, target, scenario, reason)
        pair_rows = (
            _indexed_pair_rows(universe, scenario.maximum_distance_km)
            if indexed
            else _exhaustive_pair_rows(universe, scenario.maximum_distance_km)
        )
        for source, target in pair_rows:
            pair_key = (source.event_id, target.event_id)
            if pair_key in refusals:
                continue
            row = evaluate_propagation_pair(
                source,
                target,
                scenario=scenario,
                event_manifest_digest=event_manifest_digest,
            )
            if isinstance(row, PropagationPairRefusal):
                refusals[pair_key] = row
            else:
                evaluated[pair_key] = row
    evaluated_rows = tuple(
        sorted(
            evaluated.values(),
            key=lambda row: (row.source_event_id, row.target_event_id),
        )
    )
    refusal_rows = tuple(
        sorted(
            refusals.values(),
            key=lambda row: (row.source_event_id, row.target_event_id),
        )
    )
    return PropagationScenarioResult(
        scenario=scenario,
        evaluated_pairs=evaluated_rows,
        refusals=refusal_rows,
        reconciliation=_build_reconciliation(
            events,
            pollen_events,
            evaluated_rows,
            refusal_rows,
        ),
    )
