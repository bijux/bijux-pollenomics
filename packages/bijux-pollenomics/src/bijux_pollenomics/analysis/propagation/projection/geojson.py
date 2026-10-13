"""Preserve exact governed candidate properties in endpoint-only GeoJSON."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..network import PhenomenonEvent, PropagationCandidate


def candidate_geojson(
    rows: Sequence[PropagationCandidate],
    events: Mapping[str, PhenomenonEvent],
    *,
    directional: bool,
) -> dict[str, object]:
    """Export evaluated rows without inferring a route or changing uncertainty."""
    features = []
    for row in rows:
        if row.directional_arrow_allowed is not directional:
            raise ValueError("candidate arrow posture does not match its export layer")
        source, target = events[row.source_event_id], events[row.target_event_id]
        if None in (
            source.longitude,
            source.latitude,
            target.longitude,
            target.latitude,
        ):
            raise ValueError("export endpoints require governed coordinates")
        features.append(
            {
                "type": "Feature",
                "id": row.edge_id,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [source.longitude, source.latitude],
                        [target.longitude, target.latitude],
                    ],
                },
                "properties": {
                    **row.as_dict(),
                    "source_observation_ids": list(source.observation_ids),
                    "target_observation_ids": list(target.observation_ids),
                    "source_event": source.as_dict(),
                    "target_event": target.as_dict(),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "record_count": len(features),
        "features": features,
        "directional_arrow_allowed": directional,
        "route_interpretation_allowed": False,
        "map_geometry_role": "endpoint_connection_only",
        "geometry_interpretation": "Endpoint connection only; not a sampled WGS84 geodesic or an inferred movement route.",
        "endpoint_order_semantics": "Stored evaluation orientation; indeterminate endpoints do not assert chronological direction.",
    }
