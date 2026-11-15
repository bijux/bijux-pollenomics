"""Reconcile source-facet routes against their actual native node buffers."""

from collections.abc import Mapping, Sequence
from typing import Any

from ..serialization import canonical_json
from .partition import native_taxon

SCHEMA = "atlas-source-facet-routing.v1"


def _facet_key(level: str, feature: Mapping[str, Any]) -> str:
    if level == "source_taxon":
        return str(native_taxon(feature.get("source_taxon_id")))
    value = feature.get("source_ecological_code")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Source facet literal ecological code is invalid")
    return value


def source_facet_routes(
    metadata: Sequence[Mapping[str, Any]],
    payloads: Mapping[str, Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Each source feature contributes once to its exact literal facet's route."""
    result: dict[int, dict[str, Any]] = {}
    for item in metadata:
        layer = item["layer"]
        level = layer.get("node_level")
        if layer.get("semantic_role") != "source_chronology_context" or level not in {
            "source_taxon",
            "source_ecological_code",
        }:
            continue
        field = "source_taxa" if level == "source_taxon" else "source_ecological_codes"
        declared = layer.get("facet_metadata", {}).get(field)
        if not isinstance(declared, list):
            raise ValueError("Source facet declaration is unavailable")
        routes: dict[str, dict[str, Any]] = {}
        for facet in declared:
            key = (
                str(native_taxon(facet.get("source_taxon_id")))
                if level == "source_taxon"
                else facet.get("value")
            )
            if not isinstance(key, str) or not key.strip() or key in routes:
                raise ValueError(
                    "Source facet declaration identity is invalid or repeated"
                )
            routes[key] = {"asset_keys": [], "record_count": 0}
        seen = set()
        for asset_key, payload in payloads.items():
            if payload["layer_index"] != item["layer_index"]:
                continue
            if payload["layer_key"] != layer["key"] or payload["layer_kind"] != "point":
                raise ValueError("Source facet node layer ownership differs")
            features, positions = payload["features"], payload["feature_indexes"]
            if len(features) != len(positions):
                raise ValueError("Source facet node positions are incomplete")
            members = set()
            for position, feature in zip(positions, features, strict=True):
                if type(position) is not int or position < 0 or position in seen:
                    raise ValueError("Source facet node identity repeats")
                seen.add(position)
                key = _facet_key(level, feature)
                if key not in routes:
                    raise ValueError(
                        "Source facet native node is absent from its declaration"
                    )
                routes[key]["record_count"] += 1
                members.add(key)
            for key in members:
                routes[key]["asset_keys"].append(asset_key)
        for facet in declared:
            key = (
                str(native_taxon(facet.get("source_taxon_id")))
                if level == "source_taxon"
                else facet["value"]
            )
            if (
                type(facet.get("node_count")) is not int
                or routes[key]["record_count"] != facet["node_count"]
            ):
                raise ValueError(
                    "Source facet route count differs from declared native nodes"
                )
        for route in routes.values():
            route["asset_keys"].sort()
        result[item["layer_index"]] = {
            "schema_version": SCHEMA,
            "node_level": level,
            "facets": dict(sorted(routes.items())),
        }
    return result


def bind_source_facet_routes(
    metadata: Sequence[dict[str, Any]], payloads: Mapping[str, Mapping[str, Any]]
) -> bool:
    """Bind routing before the build digest; payload membership remains unchanged."""
    routes = source_facet_routes(metadata, payloads)
    for item in metadata:
        if item["layer_index"] in routes:
            item["layer"]["static_source_facets"] = routes[item["layer_index"]]
    return bool(routes)


def validate_source_facet_routes(
    metadata: Sequence[Mapping[str, Any]],
    payloads: Mapping[str, Mapping[str, Any]],
    *,
    required: bool = False,
) -> None:
    """An optional legacy route may be absent; every declared route must be complete."""
    if not required:
        if any("static_source_facets" in item["layer"] for item in metadata):
            raise ValueError("Source facet routing is undeclared")
        return
    expected = source_facet_routes(metadata, payloads)
    for item in metadata:
        if canonical_json(item["layer"].get("static_source_facets")) != canonical_json(
            expected.get(item["layer_index"])
        ):
            raise ValueError("Source facet routing differs from actual node buffers")
