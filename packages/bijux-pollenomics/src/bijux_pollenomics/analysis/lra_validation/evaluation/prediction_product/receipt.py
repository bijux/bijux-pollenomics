"""Validate the canonical six-cell matrix and its outcome-free row receipts."""

from __future__ import annotations

from typing import cast

from ...contracts import required_identity
from ...experiments.configuration import (
    FITTED_METHOD,
    LOCAL_METHOD,
    TRAINING_MEAN_METHOD,
)
from ..contracts import (
    AcceptanceCell,
    EvaluationRow,
    EvaluationScope,
    SourceModelIdentity,
    digest,
    refuse,
    validate_frozen_prediction,
)
from ..release import FinalEvaluationProtocol, ProtocolId

PREDICTION_PRODUCT_PROFILE = "pollenomics-six-cell-prediction-product.v1"

_PROTOCOLS: tuple[ProtocolId, ...] = ("grouped_outer", "spatial_block")
_CELLS = (
    ("local_pollen_available", "vegetation_cover"),
    ("all_target_pollen_withheld", "vegetation_cover"),
    ("all_target_pollen_withheld", "pollen_composition"),
)
_PRODUCT_KEYS = frozenset(
    {
        "schema_version",
        "engineering_prediction_product",
        "empirical_evaluation_performed",
        "scientific_acceptance",
        "release_admission_sha256",
        "scope_sha256",
        "protocols",
        "rows",
    }
)
_PROTOCOL_KEYS = frozenset(
    {
        "protocol_id",
        "scope_split_sha256",
        "split_manifest_sha256",
        "policy_sha256",
        "retained_products",
        "cells",
    }
)
_PRODUCT_IDENTITY_KEYS = frozenset(
    {
        "local_predictions_sha256",
        "withheld_predictions_sha256",
        "conditional_uncertainty_sha256",
    }
)
_CELL_KEYS = frozenset(
    {
        "cell_id",
        "experiment",
        "target",
        "model_id",
        "baseline_id",
        "interval_profile_id",
        "units",
    }
)
_ROW_KEYS = frozenset(
    {
        "protocol_id",
        "cell_id",
        "fold_id",
        "record_id",
        "model_id",
        "experiment",
        "target",
        "status",
        "reason",
        "prediction_sha256",
        "prediction_manifest_json",
    }
)


def protocol_index(
    protocols: tuple[FinalEvaluationProtocol, ...],
) -> dict[ProtocolId, FinalEvaluationProtocol]:
    if not isinstance(protocols, tuple) or any(
        not isinstance(value, FinalEvaluationProtocol) for value in protocols
    ):
        refuse("Prediction products require exact typed release protocols")
    indexed = {value.protocol_id: value for value in protocols}
    if len(indexed) != 2 or set(indexed) != set(_PROTOCOLS):
        refuse("Prediction products require grouped-outer and spatial-block protocols")
    return indexed


def cell_index(
    protocol: FinalEvaluationProtocol,
) -> dict[tuple[str, str], AcceptanceCell]:
    cells: dict[tuple[str, str], AcceptanceCell] = {
        (value.experiment, value.target): value for value in protocol.policy.cells
    }
    if len(cells) != len(_CELLS) or set(cells) != set(_CELLS):
        refuse("Prediction product policy does not contain the exact three cells")
    for combination, cell in cells.items():
        model = (
            LOCAL_METHOD
            if combination[0] == "local_pollen_available"
            else FITTED_METHOD
        )
        if (
            cell.model_id != model
            or cell.baseline_id != TRAINING_MEAN_METHOD
            or cell.subgroup != "all"
        ):
            refuse(
                "Prediction product cells require governed paired methods and all sites"
            )
    return cells


def units(
    protocol_id: ProtocolId, scope: EvaluationScope
) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for fold in scope.folds:
        if protocol_id == "grouped_outer" and len(fold.test_record_ids) != 1:
            refuse("Grouped-outer prediction products require singleton test folds")
        values.extend((fold.fold_id, record_id) for record_id in fold.test_record_ids)
    return tuple(sorted(values))


def _expected_source_kind(row: EvaluationRow) -> str:
    if row.model_id == LOCAL_METHOD:
        return "local_pollen_assimilation"
    if row.model_id == FITTED_METHOD:
        return "fitted_spatial"
    if row.model_id == TRAINING_MEAN_METHOD:
        return "admitted_reconstruction_training_mean"
    return refuse("Prediction product row uses an unsupported model identity")


def validate_row(
    row: EvaluationRow,
    *,
    protocol_id: ProtocolId,
    cell: AcceptanceCell,
    scope: EvaluationScope,
) -> None:
    if not isinstance(row, EvaluationRow):
        refuse("Prediction products require typed evaluation rows")
    if (
        row.experiment != cell.experiment
        or row.target != cell.target
        or row.model_id not in {cell.model_id, cell.baseline_id}
        or row.observation is not None
        or row.observation_reference_id is not None
        or row.observation_kind is not None
        or row.observation_support is not None
    ):
        refuse("Prediction product row cell, method or outcome-free boundary differs")
    if row.status == "prediction_failed":
        if (
            not isinstance(row.reason, str)
            or not row.reason.strip()
            or row.prediction is not None
            or row.prediction_sha256 is not None
            or row.prediction_manifest_json is not None
            or row.fitted_model_sha256 is not None
            or row.prediction_frozen_at is not None
            or row.fit_input_ids
            or row.interval is not None
            or row.observed_pollen is not None
            or row.source_model is not None
        ):
            refuse("Failed prediction terminals must remain value-free")
        return
    if row.status != "predicted" or row.prediction is None or row.reason is not None:
        refuse("Prediction product terminals must be predicted or value-free failures")
    if validate_frozen_prediction(row) != "pollenomics-evaluation-prediction.v2":
        refuse("Six-cell products require canonical v2 prediction envelopes")
    if (
        not isinstance(row.source_model, SourceModelIdentity)
        or row.source_model.kind != _expected_source_kind(row)
        or len(dict(row.prediction)) != len(row.prediction)
        or set(dict(row.prediction)) != set(scope.taxa)
    ):
        refuse("Predicted rows require the exact typed source and taxon denominator")
    if row.target == "pollen_composition":
        if (
            row.interval is None
            or row.interval.profile_id != cell.interval_profile_id
            or row.interval.uncertainty_kind != "predictive_observation"
            or row.interval.propagated_sources != ("observation_process",)
        ):
            refuse("Pollen predictions require the policy-bound observation interval")
    elif row.interval is not None:
        refuse("Vegetation prediction rows cannot invent an interval")
    if row.experiment == "local_pollen_available":
        if (row.model_id == LOCAL_METHOD) != (row.observed_pollen is not None):
            refuse("Only the local assimilation row may retain target pollen")
        if (
            row.observed_pollen is not None
            and row.observed_pollen.record_id != row.record_id
        ):
            refuse("Local observed pollen belongs to a different target")
    elif row.observed_pollen is not None:
        refuse("All-target-withheld rows cannot retain target pollen")
    if protocol_id == "spatial_block" and row.fold_id == "":
        refuse("Spatial-block rows require an explicit fold identity")


def row_receipt(
    protocol_id: ProtocolId, cell_id: str, row: EvaluationRow
) -> dict[str, object]:
    return {
        "protocol_id": protocol_id,
        "cell_id": cell_id,
        "fold_id": row.fold_id,
        "record_id": row.record_id,
        "model_id": row.model_id,
        "experiment": row.experiment,
        "target": row.target,
        "status": row.status,
        "reason": row.reason,
        "prediction_sha256": row.prediction_sha256,
        "prediction_manifest_json": row.prediction_manifest_json,
    }


def ordered_cell_rows(
    rows: tuple[EvaluationRow, ...],
    *,
    protocol_id: ProtocolId,
    cell: AcceptanceCell,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    if not isinstance(rows, tuple):
        refuse("Governed adapters must return immutable row tuples")
    expected = {
        (fold_id, record_id, model_id)
        for fold_id, record_id in units(protocol_id, scope)
        for model_id in (cell.model_id, cell.baseline_id)
    }
    indexed = {(row.fold_id, row.record_id, row.model_id): row for row in rows}
    if len(indexed) != len(rows) or set(indexed) != expected:
        refuse("Adapter output differs from the exact cell terminal denominator")
    ordered = tuple(indexed[key] for key in sorted(expected))
    for row in ordered:
        validate_row(row, protocol_id=protocol_id, cell=cell, scope=scope)
    for fold_id, record_id in units(protocol_id, scope):
        pair = [
            indexed[(fold_id, record_id, method)]
            for method in (cell.model_id, cell.baseline_id)
        ]
        predicted = [row for row in pair if row.status == "predicted"]
        kinds = {cast(SourceModelIdentity, row.source_model).kind for row in predicted}
        if len(predicted) == 2 and len(kinds) != 2:
            refuse("Paired predictions require distinct authenticated source kinds")
    return ordered


def cell_payload(
    cell: AcceptanceCell, cell_units: tuple[tuple[str, str], ...]
) -> dict[str, object]:
    return {
        "cell_id": cell.cell_id,
        "experiment": cell.experiment,
        "target": cell.target,
        "model_id": cell.model_id,
        "baseline_id": cell.baseline_id,
        "interval_profile_id": cell.interval_profile_id,
        "units": cell_units,
    }


def validate_payload(
    payload: dict[str, object],
    rows: tuple[EvaluationRow, ...],
    protocols_by_id: dict[ProtocolId, FinalEvaluationProtocol],
) -> None:
    if frozenset(payload) != _PRODUCT_KEYS or (
        payload.get("schema_version") != PREDICTION_PRODUCT_PROFILE
        or payload.get("engineering_prediction_product") != "authenticated"
        or payload.get("empirical_evaluation_performed") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
    ):
        refuse("Prediction product receipt schema or claim boundary differs")
    digest(cast(str, payload.get("release_admission_sha256")))
    digest(cast(str, payload.get("scope_sha256")))
    protocol_rows = payload.get("protocols")
    receipts = payload.get("rows")
    if not isinstance(protocol_rows, list) or not isinstance(receipts, list):
        refuse("Prediction product protocols and rows must be arrays")
    expected: list[tuple[str, str, str, str, str, str, str]] = []
    if len(protocol_rows) != len(_PROTOCOLS):
        refuse("Prediction product protocol matrix is incomplete")
    for index, protocol_id in enumerate(_PROTOCOLS):
        protocol = protocol_rows[index]
        typed = protocols_by_id[protocol_id]
        if not isinstance(protocol, dict) or frozenset(protocol) != _PROTOCOL_KEYS:
            refuse("Prediction product protocol receipt fields differ")
        identities = protocol.get("retained_products")
        cells = protocol.get("cells")
        if (
            protocol.get("protocol_id") != protocol_id
            or protocol.get("scope_split_sha256") != typed.scope.split_sha256
            or protocol.get("split_manifest_sha256") != typed.split_manifest_sha256
            or protocol.get("policy_sha256") != typed.policy.policy_sha256
            or not isinstance(identities, dict)
            or frozenset(identities) != _PRODUCT_IDENTITY_KEYS
            or any(not isinstance(value, str) for value in identities.values())
            or not isinstance(cells, list)
            or len(cells) != len(_CELLS)
        ):
            refuse("Prediction product protocol identity or cell matrix differs")
        for value in identities.values():
            digest(value)
        typed_cells = cell_index(typed)
        typed_units = units(protocol_id, typed.scope)
        for combination, cell in zip(_CELLS, cells, strict=True):
            if not isinstance(cell, dict) or frozenset(cell) != _CELL_KEYS:
                refuse("Prediction product cell receipt fields differ")
            if (cell.get("experiment"), cell.get("target")) != combination:
                refuse("Prediction product cell ordering or identity differs")
            typed_cell = typed_cells[combination]
            if any(
                cell.get(field) != getattr(typed_cell, field)
                for field in (
                    "cell_id",
                    "model_id",
                    "baseline_id",
                    "interval_profile_id",
                )
            ):
                refuse("Prediction product cell differs from its typed policy")
            cell_units = cell.get("units")
            if not isinstance(cell_units, list) or not cell_units:
                refuse("Prediction product cell denominator is missing")
            parsed_units: list[tuple[str, str]] = []
            for unit in cell_units:
                if (
                    not isinstance(unit, list)
                    or len(unit) != 2
                    or any(not isinstance(item, str) or not item for item in unit)
                ):
                    refuse("Prediction product unit identity is malformed")
                parsed_units.append((unit[0], unit[1]))
            if parsed_units != sorted(set(parsed_units)):
                refuse("Prediction product units must be unique and canonical")
            if tuple(parsed_units) != typed_units:
                refuse("Prediction product units differ from its typed scope")
            model_id = required_identity(cast(str, cell.get("model_id")))
            baseline_id = required_identity(cast(str, cell.get("baseline_id")))
            cell_id = required_identity(cast(str, cell.get("cell_id")))
            expected.extend(
                (
                    protocol_id,
                    cell_id,
                    fold_id,
                    record_id,
                    method,
                    cast(str, combination[0]),
                    cast(str, combination[1]),
                )
                for fold_id, record_id in parsed_units
                for method in sorted((model_id, baseline_id))
            )
    if len(receipts) != len(rows) or len(expected) != len(rows):
        refuse("Prediction product row denominator differs from its receipt")
    for expected_key, receipt, row in zip(expected, receipts, rows, strict=True):
        if not isinstance(receipt, dict) or frozenset(receipt) != _ROW_KEYS:
            refuse("Prediction product row receipt fields differ")
        key = (
            receipt.get("protocol_id"),
            receipt.get("cell_id"),
            receipt.get("fold_id"),
            receipt.get("record_id"),
            receipt.get("model_id"),
            receipt.get("experiment"),
            receipt.get("target"),
        )
        if key != expected_key or receipt != row_receipt(
            cast(ProtocolId, key[0]), cast(str, key[1]), row
        ):
            refuse("Prediction product row bytes or ordered identity differ")
        protocol_id = cast(ProtocolId, receipt["protocol_id"])
        typed_protocol = protocols_by_id[protocol_id]
        typed_cell = cell_index(typed_protocol)[
            (cast(str, receipt["experiment"]), cast(str, receipt["target"]))
        ]
        validate_row(
            row,
            protocol_id=protocol_id,
            cell=typed_cell,
            scope=typed_protocol.scope,
        )
