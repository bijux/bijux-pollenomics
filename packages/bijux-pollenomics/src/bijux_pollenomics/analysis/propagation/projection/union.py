"""Summarize exact lower-level edges and repeated endpoint observation sets."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from ..network import PhenomenonEvent, PropagationCandidate


def lower_level_union(
    rows: Sequence[PropagationCandidate], events: Mapping[str, PhenomenonEvent]
) -> dict[str, object]:
    """Keep per-signal edges while counting only exact repeated endpoint sets.

    Endpoint sets are bundled event support. They do not define individual
    source-observation/target-observation pairings. Partial overlaps and subset
    relationships remain distinct; no Cartesian scientific pairs are invented.
    """
    unique: dict[str, PropagationCandidate] = {}
    for row in rows:
        if row.resolution == "whole_pollen":
            continue
        previous = unique.get(row.edge_id)
        if previous is not None and previous != row:
            raise ValueError("conflicting lower-level rows share an edge identity")
        unique[row.edge_id] = row
    grouped: dict[
        tuple[str, tuple[str, ...], str, tuple[str, ...]], list[PropagationCandidate]
    ] = defaultdict(list)
    signal_counts: Counter[tuple[str, str]] = Counter()
    for edge_id in sorted(unique):
        row = unique[edge_id]
        source, target = events[row.source_event_id], events[row.target_event_id]
        grouped[
            (
                source.site_id,
                source.observation_ids,
                target.site_id,
                target.observation_ids,
            )
        ].append(row)
        signal_counts[(row.resolution, row.feature_key)] += 1
    records = [
        {
            "source_site_id": key[0],
            "source_observation_ids": list(key[1]),
            "target_site_id": key[2],
            "target_observation_ids": list(key[3]),
            "member_edge_ids": [row.edge_id for row in members],
            "member_edges": [
                {
                    "edge_id": row.edge_id,
                    "source_event_id": row.source_event_id,
                    "target_event_id": row.target_event_id,
                    "resolution": row.resolution,
                    "feature_key": row.feature_key,
                    "threshold_profile_id": row.threshold_profile_id,
                    "candidate_status": row.candidate_status,
                }
                for row in members
            ],
            "member_feature_edge_count": len(members),
        }
        for key, members in sorted(grouped.items())
    ]
    return {
        "schema_version": "propagation-lower-level-edge-union.v1",
        "record_count": len(records),
        "endpoint_set_relation_count": len(records),
        "feature_edge_count": len(unique),
        "feature_edge_ids": sorted(unique),
        "per_signal_edge_counts": [
            {"resolution": resolution, "feature_key": feature, "edge_count": count}
            for (resolution, feature), count in sorted(signal_counts.items())
        ],
        "records": records,
        "counting_basis": "Distinct ordered governed-site and complete endpoint observation-set relations; member edge IDs remain individually identifiable.",
        "overlap_posture": "Partial overlaps and subsets remain distinct; individual observation-pair lineage is unavailable and no Cartesian pairs are inferred.",
        "whole_assemblage_network_constructed": False,
        "route_interpretation_allowed": False,
    }
