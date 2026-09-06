from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ...core.geospatial.geojson import JsonObject

DETAIL_TAB_KEYS = (
    "overview",
    "samples",
    "chronology",
    "pollen_composition",
    "relation",
    "classification",
    "provenance",
)
SCIENTIFIC_RESOLUTIONS = ("whole", "group", "subgroup", "role", "taxon")
_CUE_REGISTRY = ("circle", "square", "triangle", "diamond", "cross", "ring")
_COLOR_REGISTRY = (
    "#2563eb",
    "#0f766e",
    "#b45309",
    "#be123c",
    "#7c3aed",
    "#0369a1",
    "#4d7c0f",
    "#c2410c",
)
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


@dataclass(frozen=True)
class AtlasEvidence:
    detail_records: tuple[JsonObject, ...]
    edge_records: tuple[JsonObject, ...]
    scientific_signals: tuple[JsonObject, ...]
    sequence_records: tuple[JsonObject, ...]


def normalize_atlas_evidence(
    *,
    detail_records: Sequence[JsonObject] | None,
    scientific_signals: Sequence[JsonObject] | None,
    edge_records: Sequence[JsonObject] | None,
    sequence_records: Sequence[JsonObject] | None,
) -> AtlasEvidence:
    """Validate optional governed atlas evidence and return deterministic rows."""
    signals = _normalize_signals(scientific_signals or ())
    signal_ids = {str(row["signal_id"]) for row in signals}
    return AtlasEvidence(
        detail_records=tuple(_normalize_details(detail_records or ())),
        scientific_signals=tuple(signals),
        edge_records=tuple(_normalize_edges(edge_records or (), signal_ids)),
        sequence_records=tuple(
            _normalize_sequences(sequence_records or (), signal_ids)
        ),
    )


def validate_feature_signal_references(
    point_layers: Sequence[JsonObject], scientific_signals: Sequence[JsonObject]
) -> None:
    """Fail closed when a scientific feature names an unaccepted signal."""
    accepted = {str(row["signal_id"]) for row in scientific_signals}
    for layer in point_layers:
        raw_features = layer.get("features")
        if not isinstance(raw_features, list):
            continue
        for feature in raw_features:
            if not isinstance(feature, dict):
                continue
            references = feature.get("scientific_signal_ids", [])
            if references is None:
                references = []
            if not isinstance(references, list) or any(
                not isinstance(value, str) or not value.strip() for value in references
            ):
                raise ValueError(
                    "atlas scientific_signal_ids must be a list of stable identifiers"
                )
            unknown = set(references) - accepted
            if unknown:
                raise ValueError(
                    "atlas feature references unaccepted scientific signals: "
                    + ", ".join(sorted(unknown))
                )


def _normalize_signals(rows: Sequence[JsonObject]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        signal_id = _required_text(row, "signal_id", "scientific signal")
        feature_key = _required_text(row, "feature_key", "scientific signal")
        label = _required_text(row, "label", "scientific signal")
        resolution = _required_text(row, "resolution", "scientific signal")
        if resolution not in SCIENTIFIC_RESOLUTIONS:
            raise ValueError(
                f"atlas scientific signal {signal_id} resolution is invalid"
            )
        if row.get("status") != "accepted":
            raise ValueError(
                f"atlas scientific signal {signal_id} is not accepted for publication"
            )
        color = row.get("color")
        if color is not None and (
            not isinstance(color, str) or not _HEX_COLOR.fullmatch(color)
        ):
            raise ValueError(f"atlas scientific signal {signal_id} color is invalid")
        cue = row.get("non_color_cue")
        if cue is not None and cue not in _CUE_REGISTRY:
            raise ValueError(
                f"atlas scientific signal {signal_id} non-color cue is invalid"
            )
        normalized.append(
            {
                **dict(row),
                "signal_id": signal_id,
                "feature_key": feature_key,
                "label": label,
                "resolution": resolution,
            }
        )
    normalized.sort(key=lambda item: str(item["signal_id"]))
    _require_unique(normalized, "signal_id", "scientific signal")
    signal_ids = {str(row["signal_id"]) for row in normalized}
    for index, row in enumerate(normalized):
        signal_id = str(row["signal_id"])
        parent = row.get("parent_signal_id")
        if parent is not None and (
            not isinstance(parent, str) or parent not in signal_ids
        ):
            raise ValueError(
                f"atlas scientific signal {signal_id} parent is not accepted"
            )
        row["color"] = str(
            row.get("color") or _COLOR_REGISTRY[index % len(_COLOR_REGISTRY)]
        )
        row["non_color_cue"] = str(row.get("non_color_cue") or _stable_cue(signal_id))
    return normalized


def _normalize_details(rows: Sequence[JsonObject]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        record_id = _required_text(row, "record_id", "detail record")
        raw_tabs = row.get("tabs")
        if not isinstance(raw_tabs, Mapping):
            raise ValueError(f"atlas detail record {record_id} tabs are missing")
        tabs: dict[str, object] = {}
        for tab in DETAIL_TAB_KEYS:
            value = raw_tabs.get(tab)
            tabs[tab] = (
                value
                if value is not None
                else {
                    "status": "unavailable",
                    "reason_code": f"{tab}_evidence_not_available",
                }
            )
        normalized.append({**dict(row), "record_id": record_id, "tabs": tabs})
    normalized.sort(key=lambda item: str(item["record_id"]))
    _require_unique(normalized, "record_id", "detail record")
    return normalized


def _normalize_edges(
    rows: Sequence[JsonObject], signal_ids: set[str]
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        edge_id = _required_text(row, "edge_id", "edge")
        signal_id = _required_text(row, "signal_id", "edge")
        if signal_id not in signal_ids:
            raise ValueError(f"atlas edge {edge_id} signal is not accepted")
        source_country = _required_text(row, "source_country", "edge")
        target_country = _required_text(row, "target_country", "edge")
        normalized.append(
            {
                **dict(row),
                "edge_id": edge_id,
                "signal_id": signal_id,
                "source_record_id": _required_text(row, "source_record_id", "edge"),
                "target_record_id": _required_text(row, "target_record_id", "edge"),
                "source_country": source_country,
                "target_country": target_country,
                "cross_border": source_country != target_country,
            }
        )
    normalized.sort(key=lambda item: str(item["edge_id"]))
    _require_unique(normalized, "edge_id", "edge")
    return normalized


def _normalize_sequences(
    rows: Sequence[JsonObject], signal_ids: set[str]
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        sequence_id = _required_text(row, "sequence_id", "sequence")
        signal_id = _required_text(row, "signal_id", "sequence")
        if signal_id not in signal_ids:
            raise ValueError(f"atlas sequence {sequence_id} signal is not accepted")
        record_ids = row.get("record_ids")
        if (
            not isinstance(record_ids, list)
            or not record_ids
            or any(
                not isinstance(value, str) or not value.strip() for value in record_ids
            )
        ):
            raise ValueError(f"atlas sequence {sequence_id} record_ids are invalid")
        normalized.append(
            {
                **dict(row),
                "sequence_id": sequence_id,
                "signal_id": signal_id,
                "record_ids": list(record_ids),
            }
        )
    normalized.sort(key=lambda item: str(item["sequence_id"]))
    _require_unique(normalized, "sequence_id", "sequence")
    return normalized


def _required_text(row: Mapping[str, object], key: str, domain: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"atlas {domain} {key} is missing")
    return value.strip()


def _require_unique(
    rows: Sequence[Mapping[str, object]], key: str, domain: str
) -> None:
    values = [str(row[key]) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"atlas {domain} identifiers are duplicated")


def _stable_cue(signal_id: str) -> str:
    digest = hashlib.sha256(signal_id.encode("utf-8")).digest()
    return _CUE_REGISTRY[digest[0] % len(_CUE_REGISTRY)]


__all__ = [
    "DETAIL_TAB_KEYS",
    "SCIENTIFIC_RESOLUTIONS",
    "AtlasEvidence",
    "normalize_atlas_evidence",
    "validate_feature_signal_references",
]
