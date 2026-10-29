"""Publication-owned substring postings and exact source representation membership."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

from .....core.geospatial.geojson import JsonObject
from ...temporal_admission import feature_temporal_admission

SEARCH_ABI = "atlas-substring-postings.v1"
SEARCH_KIND = "text_search_index"


def _string(value: object) -> str:
    """Predict JavaScript string coercion; the viewer detects any runtime difference."""
    if value is None or value is False or value == 0 or value == "":
        return ""
    if value is True:
        return "true"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ",".join(_string(item) for item in value)
    if isinstance(value, Mapping):
        return "[object Object]"
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return str(int(value))
    return str(value)


def search_text(
    layer: Mapping[str, object], feature: Mapping[str, object], profile: str | None
) -> str:
    """Retain the five original fields; no tokenization, accent folding or ranking."""
    status, interval = feature_temporal_admission(feature, temporal_profile=profile)
    time = ""
    if status != "refused":
        if feature.get("time_label"):
            time = _string(feature["time_label"])
        elif interval is not None:
            a, b = (
                str(int(value)) if float(value).is_integer() else str(value)
                for value in interval
            )
            time = f"{a} BP" if a == b else f"{a}-{b} BP"
    return " ".join(
        [_string(feature.get(key)) for key in ("title", "subtitle", "country")]
        + [_string(layer.get("label")), time]
    ).lower()


def grams(text: str) -> set[str]:
    """Use hexadecimal UTF-16 units so surrogate units never enter UTF-8 keys."""
    raw = text.encode("utf-16-le", errors="surrogatepass")
    units = [
        f"{int.from_bytes(raw[i : i + 2], 'little'):04x}" for i in range(0, len(raw), 2)
    ]
    return {
        "".join(units[i : i + size])
        for size in (1, 2, 3)
        for i in range(len(units) - size + 1)
    }


def build_search_index(
    point_layers: Sequence[JsonObject], *, temporal_profile: str | None = None
) -> dict[str, object]:
    """Publish one representation per original layer/feature position, even repeated IDs."""
    rows: dict[str, object] = {}
    postings: dict[str, list[str]] = {}
    for layer_index, layer in enumerate(point_layers):
        features = layer.get("features")
        if not isinstance(features, list):
            continue
        for position, feature in enumerate(features):
            if not isinstance(feature, dict):
                raise ValueError("Search feature must be a source object")
            key = f"d:{layer_index}:{position}"
            text = search_text(layer, feature, temporal_profile)
            rows[key] = {
                "layer_index": layer_index,
                "feature_index": position,
                "layer_key": layer.get("key"),
                "record_id": feature.get("record_id"),
                "text": text,
            }
            for gram in sorted(grams(text)):
                postings.setdefault("p:" + gram, []).append(key)
    rows.update({key: sorted(value) for key, value in postings.items()})
    return dict(sorted(rows.items()))


def validate_search_index(rows: object) -> None:
    """Refuse missing/extra posting references, duplicates and foreign document forms."""
    if not isinstance(rows, Mapping):
        raise ValueError("Search index must be an object")
    expected: dict[str, list[str]] = {}
    for key, row in rows.items():
        if not isinstance(key, str):
            raise ValueError("Search reference must be text")
        if key.startswith("p:"):
            continue
        if (
            not isinstance(row, Mapping)
            or set(row)
            != {"layer_index", "feature_index", "layer_key", "record_id", "text"}
            or type(row["layer_index"]) is not int
            or row["layer_index"] < 0
            or type(row["feature_index"]) is not int
            or row["feature_index"] < 0
            or not isinstance(row["layer_key"], str)
            or not row["layer_key"]
            or not isinstance(row["text"], str)
            or key != f"d:{row['layer_index']}:{row['feature_index']}"
        ):
            raise ValueError("Search document identity is invalid")
        for gram in grams(row["text"]):
            expected.setdefault("p:" + gram, []).append(key)
    actual = {key: value for key, value in rows.items() if str(key).startswith("p:")}
    if actual != {key: sorted(value) for key, value in expected.items()}:
        raise ValueError("Search postings are incomplete, duplicated or foreign")


def validate_search_membership(
    payloads: Mapping[str, Mapping[str, object]],
    indexes: Mapping[str, object],
    profile: str | None,
) -> None:
    """Join the complete index to actual published node positions and layer metadata."""
    if "search_index_abi" not in indexes:
        if SEARCH_KIND in indexes:
            raise ValueError("Undeclared search index")
        return
    if indexes["search_index_abi"] != SEARCH_ABI:
        raise ValueError("Unsupported search ABI")
    layers: dict[int, JsonObject] = {}
    counts: dict[int, int] = {}
    for payload in payloads.values():
        if not str(payload.get("schema_version", "")).startswith(
            "atlas-provenance-chunk."
        ):
            continue
        raw_layers = payload.get("layers")
        if not isinstance(raw_layers, list):
            raise ValueError("Search provenance layers are invalid")
        for item in raw_layers:
            if not isinstance(item, Mapping):
                raise ValueError("Search provenance layer is invalid")
            if item.get("layer_kind") != "point":
                continue
            i, layer, count = (
                item.get("layer_index"),
                item.get("layer"),
                item.get("feature_count"),
            )
            if (
                type(i) is not int
                or i < 0
                or i in layers
                or not isinstance(layer, dict)
                or type(count) is not int
                or count < 0
            ):
                raise ValueError("Search layer membership is invalid")
            layers[i] = dict(layer)
            counts[i] = count
    features: dict[int, dict[int, JsonObject]] = {key: {} for key in layers}
    for payload in payloads.values():
        if (
            not str(payload.get("schema_version", "")).startswith("atlas-node-chunk.")
            or payload.get("layer_kind") != "point"
        ):
            continue
        i = payload.get("layer_index")
        if (
            type(i) is not int
            or i not in layers
            or payload.get("layer_key") != layers[i].get("key")
        ):
            raise ValueError("Foreign search node layer")
        bodies, positions = payload.get("features"), payload.get("feature_indexes")
        if (
            not isinstance(bodies, list)
            or not isinstance(positions, list)
            or len(bodies) != len(positions)
        ):
            raise ValueError("Search node shape is invalid")
        for body, position in zip(bodies, positions, strict=True):
            if (
                type(position) is not int
                or position < 0
                or position in features[i]
                or not isinstance(body, dict)
            ):
                raise ValueError("Search node position is invalid")
            features[i][position] = body
    if sorted(layers) != list(range(len(layers))):
        raise ValueError("Search layer positions are incomplete")
    ordered = []
    for i in sorted(layers):
        if sorted(features[i]) != list(range(counts[i])):
            raise ValueError("Search feature positions are incomplete")
        ordered.append(
            {**layers[i], "features": [features[i][j] for j in range(counts[i])]}
        )
    expected = build_search_index(ordered, temporal_profile=profile)
    if indexes.get(SEARCH_KIND) != expected:
        raise ValueError("Search index differs from actual published representations")
