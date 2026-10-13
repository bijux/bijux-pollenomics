"""Select and project maintained propagation results without readmitting evidence."""

from __future__ import annotations

from ..network import PropagationNetworkResult
from ..network.codec import _event_manifest_digest
from .geojson import candidate_geojson
from .selection import PropagationSelection
from .union import lower_level_union


def project_propagation_network(
    network: PropagationNetworkResult,
    *,
    selection: PropagationSelection | None = None,
) -> dict[str, dict[str, object]]:
    """Produce separately directional, indeterminate, and lower-level union views.

    This consumes generated network results. It does not admit classifications,
    change event or chronology eligibility, or authorize scientific publication.
    """
    if selection is None:
        selection = PropagationSelection()
    events = {event.event_id: event for event in network.events}
    if len(events) != len(network.events) or any(
        event.evidence_domain != "pollen_context" for event in network.events
    ):
        raise ValueError("projection requires unique governed pollen events")
    if _event_manifest_digest(network.events) != network.event_manifest_digest:
        raise ValueError("projection event manifest does not match its input events")
    scenarios = [
        row
        for row in network.scenario_results
        if row.scenario.scenario_id == selection.scenario_id
    ]
    if len(scenarios) != 1:
        raise ValueError("projection requires one matching scenario")
    result = scenarios[0]
    if len({row.edge_id for row in result.evaluated_pairs}) != len(
        result.evaluated_pairs
    ):
        raise ValueError("projection candidate edge identities must be unique")
    for row in result.evaluated_pairs:
        source, target = (
            events.get(row.source_event_id),
            events.get(row.target_event_id),
        )
        if source is None or target is None:
            raise ValueError("projection candidate references an unavailable event")
        if (
            row.source_site_id,
            row.target_site_id,
            row.source_country_code,
            row.target_country_code,
            row.resolution,
            row.feature_key,
            row.scenario_id,
            row.event_manifest_digest,
        ) != (
            source.site_id,
            target.site_id,
            source.country_code,
            target.country_code,
            source.resolution,
            source.feature_key,
            selection.scenario_id,
            network.event_manifest_digest,
        ) or (target.resolution, target.feature_key) != (
            source.resolution,
            source.feature_key,
        ):
            raise ValueError(
                "projection candidate conflicts with governed endpoint identity"
            )
        if row.candidate_status not in {
            "definite_candidate",
            "possible_candidate",
            "indeterminate_order",
            "unresolved",
            "excluded_spatial",
            "excluded_temporal_nonpositive",
            "excluded_temporal_too_large",
        }:
            raise ValueError("projection candidate status is not governed")
        if (
            row.cross_border is not (source.country_code != target.country_code)
            or row.threshold_profile_id != source.threshold_profile_id
            or source.threshold_profile_id != target.threshold_profile_id
        ):
            raise ValueError(
                "projection candidate country or threshold profile is inconsistent"
            )
        directional = row.candidate_status in {
            "definite_candidate",
            "possible_candidate",
        }
        if (
            row.directional_arrow_allowed is not directional
            or row.route_interpretation_allowed is not False
            or row.map_geometry_role != "endpoint_connection_only"
        ):
            raise ValueError("projection candidate has invalid arrow or route posture")
    selected = [
        row
        for row in result.evaluated_pairs
        if selection.matches(events[row.source_event_id], events[row.target_event_id])
    ]
    directed = sorted(
        (
            row
            for row in selected
            if row.candidate_status in {"definite_candidate", "possible_candidate"}
        ),
        key=lambda row: row.edge_id,
    )
    indeterminate = sorted(
        (row for row in selected if row.candidate_status == "indeterminate_order"),
        key=lambda row: row.edge_id,
    )
    metadata = {
        "build_id": network.events[0].build_id if network.events else None,
        "event_manifest_digest": network.event_manifest_digest,
        "selection": selection.as_dict(),
        "source_evaluated_pair_count": len(result.evaluated_pairs),
        "source_refused_pair_count": len(result.refusals),
        "source_refusals": [row.as_dict() for row in result.refusals],
        "excluded_non_pollen_event_count": len(network.excluded_non_pollen_events),
        "selected_evaluated_pair_count": len(selected),
        "scientific_publication_authorized": False,
        "assumptions": "Projection only; original event admission, candidate statuses, exact distance, lag bounds and refusal ledger remain authoritative.",
    }
    return {
        "directed_candidates.geojson": {
            **metadata,
            **candidate_geojson(directed, events, directional=True),
        },
        "indeterminate_pairs.geojson": {
            **metadata,
            **candidate_geojson(indeterminate, events, directional=False),
        },
        "lower_level_edge_union.json": {
            **metadata,
            **lower_level_union(directed, events),
        },
    }
