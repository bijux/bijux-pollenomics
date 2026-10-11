"""Attach authenticated observations to the closed six-cell prediction ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import cast

from ...contracts import canonical_json, manifest_sha256
from ..contracts import EvaluationRow, digest, refuse
from ..observation_sources import HeldoutPollenCountUnit, MeasuredVegetationUnit
from ..prediction_product import SixCellPredictionProduct
from .contracts import (
    OBSERVED_SIX_CELL_PROFILE,
    ObservedRowAttachment,
    SourceUnit,
)
from .product import (
    AuthenticatedObservationProduct,
    reopen_authenticated_observation_product,
    source_unit_index,
)

_FACTORY_TOKEN = object()


def _prediction_receipts(
    prediction: SixCellPredictionProduct,
) -> tuple[dict[str, object], ...]:
    try:
        payload = json.loads(prediction.canonical_product_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed joined prediction parent: {exc}")
    receipts = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(receipts, list) or len(receipts) != len(
        prediction.outcome_free_rows
    ):
        refuse("Joined prediction receipt denominator differs")
    if any(not isinstance(value, dict) for value in receipts):
        refuse("Joined prediction row receipt is malformed")
    return tuple(cast(dict[str, object], value) for value in receipts)


def _attach(row: EvaluationRow, unit: SourceUnit) -> EvaluationRow:
    if row.status == "prediction_failed":
        return row
    if row.status != "predicted":
        refuse("Observed products do not admit excluded prediction parents")
    if unit.status != "available":
        return row
    if isinstance(unit, MeasuredVegetationUnit):
        kind = "independent_measured_vegetation"
    elif isinstance(unit, HeldoutPollenCountUnit):
        kind = "heldout_pollen_counts"
    else:
        refuse("Observed joins require an exact typed source unit")
    return replace(
        row,
        observation=cast(
            tuple[tuple[str, float | int | None], ...], tuple(unit.values)
        ),
        observation_reference_id=unit.source_reference_id,
        observation_kind=kind,
        observation_support=unit.support,
    )


def _attachment_receipt(value: ObservedRowAttachment) -> dict[str, object]:
    row = value.row
    return {
        "protocol_id": value.protocol_id,
        "cell_id": value.cell_id,
        "fold_id": row.fold_id,
        "record_id": row.record_id,
        "model_id": row.model_id,
        "experiment": row.experiment,
        "target": row.target,
        "prediction_status": value.prediction_status,
        "prediction_sha256": row.prediction_sha256,
        "observation_status": value.observation_status,
        "observation_reason": value.observation_reason,
        "observation_id": value.observation_id,
        "source_product_sha256": value.source_product_sha256,
        "source_unit_sha256": value.source_unit_sha256,
        "observation": row.observation,
        "observation_reference_id": row.observation_reference_id,
        "observation_kind": row.observation_kind,
        "observation_support": (
            asdict(row.observation_support) if row.observation_support else None
        ),
    }


def _derive_attachments(
    prediction: SixCellPredictionProduct,
    observations: AuthenticatedObservationProduct,
) -> tuple[ObservedRowAttachment, ...]:
    source_prediction = (
        observations.completion_receipt.start_receipt.plan.prediction_product
    )
    if (
        prediction.product_sha256 != observations.prediction_product_sha256
        or prediction != source_prediction
    ):
        refuse("Observed product parents name different prediction products")
    reopened = reopen_authenticated_observation_product(
        observations.canonical_product_json,
        observations.product_sha256,
        completion_receipt=observations.completion_receipt,
    )
    assignments = {value.key: value for value in reopened.assignments}
    if len(assignments) != len(reopened.assignments):
        refuse("Observed product assignments are duplicated")
    units = source_unit_index(reopened)
    attachments: list[ObservedRowAttachment] = []
    pair_counts: dict[tuple[str, str, str, str], int] = {}
    for receipt, parent in zip(
        _prediction_receipts(prediction), prediction.outcome_free_rows, strict=True
    ):
        key = (
            cast(str, receipt["protocol_id"]),
            cast(str, receipt["cell_id"]),
            parent.fold_id,
            parent.record_id,
        )
        assignment = assignments.get(key)
        if assignment is None:
            refuse("Prediction row lacks its model-free observation assignment")
        unit = units.get((assignment.observation_kind, assignment.observation_id))
        if unit is None or (
            unit.source_unit_sha256 != assignment.source_unit_sha256
            or unit.status != assignment.status
            or unit.reason_code != assignment.reason
        ):
            refuse("Observation assignment differs from its authenticated source unit")
        row = _attach(parent, unit)
        attachments.append(
            ObservedRowAttachment(
                key[0],
                key[1],
                row,
                parent.status,
                assignment.status,
                assignment.reason,
                assignment.observation_id,
                assignment.source_product_sha256,
                assignment.source_unit_sha256,
            )
        )
        pair_counts[key] = pair_counts.get(key, 0) + 1
    if set(pair_counts) != set(assignments) or any(
        count != 2 for count in pair_counts.values()
    ):
        refuse("Observed product comparison-pair denominator differs")
    result = tuple(attachments)
    if len({value.key for value in result}) != len(result):
        refuse("Observed product row attachments are duplicated")
    return result


def _payload(
    prediction: SixCellPredictionProduct,
    observations: AuthenticatedObservationProduct,
) -> tuple[dict[str, object], tuple[ObservedRowAttachment, ...]]:
    attachments = _derive_attachments(prediction, observations)
    counts = {
        status: sum(value.observation_status == status for value in attachments)
        for status in ("available", "missing", "refused")
    }
    protocol_ids = [protocol.protocol_id for protocol in prediction.protocols]
    return (
        {
            "schema_version": OBSERVED_SIX_CELL_PROFILE,
            "prediction_product_sha256": prediction.product_sha256,
            "authenticated_observation_product_sha256": observations.product_sha256,
            "release_admission_sha256": prediction.release_admission_sha256,
            "scope_sha256": prediction.scope_sha256,
            "protocols": protocol_ids,
            "row_attachments": [_attachment_receipt(value) for value in attachments],
            "observation_status_counts": counts,
            "empirical_evaluation_performed": False,
            "scientific_acceptance": "not_evaluated",
        },
        attachments,
    )


@dataclass(frozen=True, init=False)
class ObservedSixCellEvaluationProduct:
    """Factory-only joined ledger; it is not a score or acceptance result."""

    canonical_product_json: str
    product_sha256: str
    prediction_product: SixCellPredictionProduct
    observation_product: AuthenticatedObservationProduct
    attachments: tuple[ObservedRowAttachment, ...]

    def __init__(
        self,
        canonical_product_json: str,
        product_sha256: str,
        prediction_product: SixCellPredictionProduct,
        observation_product: AuthenticatedObservationProduct,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            refuse("Observed six-cell products require the governed join")
        expected, attachments = _payload(prediction_product, observation_product)
        try:
            loaded = json.loads(canonical_product_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed observed six-cell product: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != canonical_product_json
            or manifest_sha256(loaded) != digest(product_sha256)
            or canonical_json(loaded) != canonical_json(expected)
        ):
            refuse("Observed six-cell product bytes or parent join differ")
        object.__setattr__(self, "canonical_product_json", canonical_product_json)
        object.__setattr__(self, "product_sha256", product_sha256)
        object.__setattr__(self, "prediction_product", prediction_product)
        object.__setattr__(self, "observation_product", observation_product)
        object.__setattr__(self, "attachments", attachments)

    @property
    def rows(self) -> tuple[EvaluationRow, ...]:
        return tuple(value.row for value in self.attachments)


def build_observed_six_cell_product(
    prediction_product: SixCellPredictionProduct,
    authenticated_observations: AuthenticatedObservationProduct,
) -> ObservedSixCellEvaluationProduct:
    """Replay and attach the two canonical parents without caller-supplied rows."""
    if not isinstance(prediction_product, SixCellPredictionProduct) or not isinstance(
        authenticated_observations, AuthenticatedObservationProduct
    ):
        refuse("Observed joins require both typed canonical parent products")
    payload, _ = _payload(prediction_product, authenticated_observations)
    canonical = canonical_json(payload)
    return ObservedSixCellEvaluationProduct(
        canonical,
        manifest_sha256(payload),
        prediction_product,
        authenticated_observations,
        _factory_token=_FACTORY_TOKEN,
    )


def reopen_observed_six_cell_product(
    canonical_product_json: str,
    product_sha256: str,
    *,
    prediction_product: SixCellPredictionProduct,
    authenticated_observations: AuthenticatedObservationProduct,
) -> ObservedSixCellEvaluationProduct:
    """Replay the complete join from exact canonical parents."""
    return ObservedSixCellEvaluationProduct(
        canonical_product_json,
        product_sha256,
        prediction_product,
        authenticated_observations,
        _factory_token=_FACTORY_TOKEN,
    )
