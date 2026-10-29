"""Exact publication-owned node references and raw endpoint coordinate views."""

from collections.abc import Mapping, Sequence

from ..serialization import canonical_json

EDGE_SCHEMA = "atlas-edges-chunk.v2"


def edge_endpoint_geometry(
    records: Sequence[Mapping[str, object]],
    nodes: Mapping[str, Mapping[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Retain source positions and raw coordinates for every endpoint representation."""
    endpoints: set[str] = set()
    for record in records:
        for field in ("source_record_id", "target_record_id"):
            value = record.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError("Edge endpoint record identity is invalid")
            endpoints.add(value)
    found: dict[str, list[dict[str, object]]] = {record: [] for record in endpoints}
    for asset_key, payload in sorted(nodes.items()):
        if payload.get("layer_kind") != "point":
            continue
        features, positions = payload.get("features"), payload.get("feature_indexes")
        if (
            not isinstance(features, list)
            or not isinstance(positions, list)
            or len(features) != len(positions)
            or any(type(position) is not int or position < 0 for position in positions)
            or len(set(positions)) != len(positions)
        ):
            raise ValueError("Edge endpoint node feature positions are invalid")
        for position, feature in sorted(zip(positions, features, strict=True)):
            if not isinstance(feature, Mapping):
                raise ValueError("Edge endpoint node feature is invalid")
            record_id = feature.get("record_id")
            if isinstance(record_id, str) and record_id in found:
                found[record_id].append(
                    {
                        "asset_key": asset_key,
                        "feature_index": position,
                        "latitude": feature.get("latitude"),
                        "longitude": feature.get("longitude"),
                    }
                )
    if any(not references for references in found.values()):
        raise ValueError("Governed edge endpoint has no published point node")
    return {record: found[record] for record in sorted(found)}


def edge_endpoint_assets(
    records: Sequence[Mapping[str, object]],
    nodes: Mapping[str, Mapping[str, object]],
) -> dict[str, list[str]]:
    """Retain all exact point-node asset references without changing record IDs."""
    return {
        record: sorted({str(reference["asset_key"]) for reference in references})
        for record, references in edge_endpoint_geometry(records, nodes).items()
    }


def validate_edge_endpoint_assets(
    payload: Mapping[str, object],
    nodes: Mapping[str, Mapping[str, object]],
) -> None:
    """Reject incomplete/foreign hints while preserving the explicit legacy schema."""
    if payload.get("schema_version") == "atlas-edges-chunk.v1":
        if "endpoint_node_assets" in payload or "endpoint_node_geometry" in payload:
            raise ValueError("Legacy edge payload cannot declare endpoint assets")
        return
    if payload.get("schema_version") != EDGE_SCHEMA:
        raise ValueError("Edge asset discovery schema is unsupported")
    records = payload.get("records")
    if not isinstance(records, list) or any(
        not isinstance(record, Mapping) for record in records
    ):
        raise ValueError("Edge asset discovery records are invalid")
    if payload.get("endpoint_node_assets") != edge_endpoint_assets(
        records, nodes
    ) or canonical_json(payload.get("endpoint_node_geometry")) != canonical_json(
        edge_endpoint_geometry(records, nodes)
    ):
        raise ValueError(
            "Edge endpoint assets or geometry differ from published point nodes"
        )
