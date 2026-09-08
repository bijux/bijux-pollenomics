"""Atlas evidence projection orchestration."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from pathlib import Path
from typing import cast

from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document.evidence import DETAIL_TAB_KEYS

from .constants import _NEOTOMA_LAYER_KEY, _SEAD_LAYER_KEYS, PROJECTION_SCHEMA_VERSION
from .io import _regular_absolute_directory, _required_text
from .models import MapEvidenceProjection
from .neotoma import _project_neotoma
from .records import _features, _is_unavailable, _tabs
from .sead import _project_sead


def build_map_evidence_projection(
    context_root: Path,
    point_layers: Sequence[MutableMapping[str, object]],
) -> MapEvidenceProjection:
    """Bind governed source evidence to map features through stable record IDs.

    The caller-owned point-layer dictionaries are annotated with source-qualified
    ``record_id`` values. Repeated chronology features for one SEAD site share its
    site detail record; the feature retains its own interval and native locator.
    """
    root = _regular_absolute_directory(context_root, "atlas context root")
    selected_layers = {
        _required_text(layer.get("key"), "point layer key"): layer
        for layer in point_layers
        if str(layer.get("key", "")).strip() in {_NEOTOMA_LAYER_KEY, *_SEAD_LAYER_KEYS}
    }
    records: list[dict[str, object]] = []
    source_accounting: dict[str, dict[str, object]] = {}
    projected_point_layers: list[dict[str, object]] = []

    neotoma_layer = selected_layers.get(_NEOTOMA_LAYER_KEY)
    if neotoma_layer is not None:
        (
            neotoma_records,
            neotoma_accounting,
            neotoma_source_layers,
        ) = _project_neotoma(root, neotoma_layer)
        records.extend(neotoma_records)
        source_accounting["neotoma"] = neotoma_accounting
        projected_point_layers.extend(neotoma_source_layers)

    sead_layers = [
        selected_layers[key]
        for key in sorted(_SEAD_LAYER_KEYS & selected_layers.keys())
    ]
    if sead_layers:
        sead_records, sead_accounting = _project_sead(root, sead_layers)
        records.extend(sead_records)
        source_accounting["sead"] = sead_accounting

    records.sort(key=lambda row: str(row["record_id"]))
    record_ids = [str(row["record_id"]) for row in records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("atlas evidence projection produced duplicate detail records")

    evidence_layers = [*selected_layers.values(), *projected_point_layers]
    relevant_features = [
        feature for layer in evidence_layers for feature in _features(layer)
    ]
    feature_record_ids = [
        _required_text(row.get("record_id"), "feature record_id")
        for row in relevant_features
    ]
    unmatched = sorted(set(feature_record_ids) - set(record_ids))
    unreferenced = sorted(set(record_ids) - set(feature_record_ids))
    if unmatched or unreferenced:
        raise ValueError(
            "atlas evidence projection does not reconcile; "
            f"unmatched_features={unmatched[:5]}, unreferenced_details={unreferenced[:5]}"
        )
    tab_counts = {
        tab: {
            "available": sum(
                1 for record in records if not _is_unavailable(_tabs(record)[tab])
            ),
            "unavailable": sum(
                1 for record in records if _is_unavailable(_tabs(record)[tab])
            ),
            "denominator": len(records),
        }
        for tab in DETAIL_TAB_KEYS
    }
    reconciliation: dict[str, object] = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "status": "reconciled",
        "source_layer_count": len(evidence_layers),
        "source_feature_count": len(relevant_features),
        "matched_feature_count": len(feature_record_ids),
        "detail_record_count": len(records),
        "unique_feature_record_id_count": len(set(feature_record_ids)),
        "repeated_feature_reference_count": len(feature_record_ids)
        - len(set(feature_record_ids)),
        "unmatched_feature_count": 0,
        "unreferenced_detail_count": 0,
        "tab_availability": tab_counts,
        "sources": source_accounting,
    }
    return MapEvidenceProjection(
        detail_records=tuple(cast(JsonObject, row) for row in records),
        reconciliation=reconciliation,
        point_layers=tuple(cast(JsonObject, row) for row in projected_point_layers),
    )
