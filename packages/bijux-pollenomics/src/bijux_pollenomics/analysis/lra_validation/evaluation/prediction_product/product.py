"""Mint the closed, outcome-free six-cell prediction product."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

from ...contracts import canonical_json, manifest_sha256
from ..block_local_rows import adapt_authenticated_spatial_block_local_vegetation_rows
from ..block_products.rows import (
    adapt_authenticated_spatial_block_withheld_pollen_rows,
    adapt_authenticated_spatial_block_withheld_vegetation_rows,
)
from ..contracts import EvaluationRow, digest, refuse
from ..grouped_local_rows import adapt_authenticated_grouped_local_vegetation_rows
from ..grouped_products.rows import (
    adapt_authenticated_grouped_withheld_pollen_rows,
    adapt_authenticated_grouped_withheld_vegetation_rows,
)
from ..release import (
    FinalEvaluationProtocol,
    FinalEvaluationReleaseAdmission,
    ProtocolId,
    admit_final_evaluation_release,
)
from .receipt import (
    PREDICTION_PRODUCT_PROFILE,
    _CELLS,
    _PROTOCOLS,
    cell_index,
    cell_payload,
    ordered_cell_rows,
    protocol_index,
    row_receipt,
    units,
    validate_payload,
)

_FACTORY_TOKEN = object()


@dataclass(frozen=True)
class RetainedProductLocator:
    """One retained product location plus its caller-pinned mismatch guard."""

    path: Path
    expected_manifest_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            refuse("Retained products require typed filesystem paths")
        object.__setattr__(
            self,
            "expected_manifest_sha256",
            digest(self.expected_manifest_sha256),
        )


@dataclass(frozen=True)
class ProtocolProductLocators:
    """Fixed three-product input schema for one resampling protocol."""

    local_predictions: RetainedProductLocator
    withheld_predictions: RetainedProductLocator
    conditional_uncertainty: RetainedProductLocator

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, RetainedProductLocator)
            for value in (
                self.local_predictions,
                self.withheld_predictions,
                self.conditional_uncertainty,
            )
        ):
            refuse("Each protocol requires exact typed product locators")

    def _authenticated_identities_after_adapter_reads(self) -> dict[str, str]:
        """Name pins as authenticated only after every fixed adapter has succeeded."""
        return {
            "local_predictions_sha256": self.local_predictions.expected_manifest_sha256,
            "withheld_predictions_sha256": (
                self.withheld_predictions.expected_manifest_sha256
            ),
            "conditional_uncertainty_sha256": (
                self.conditional_uncertainty.expected_manifest_sha256
            ),
        }


@dataclass(frozen=True)
class SixCellProductLocators:
    """Closed locator schema; mappings and caller-selected adapters are not accepted."""

    grouped_outer: ProtocolProductLocators
    spatial_block: ProtocolProductLocators

    def __post_init__(self) -> None:
        if not isinstance(
            self.grouped_outer, ProtocolProductLocators
        ) or not isinstance(self.spatial_block, ProtocolProductLocators):
            refuse("Six-cell products require both typed protocol locator sets")


@dataclass(frozen=True, init=False)
class SixCellPredictionProduct:
    """Factory-only immutable six-cell ledger; not empirical acceptance."""

    canonical_product_json: str
    product_sha256: str
    release_admission_sha256: str
    scope_sha256: str
    protocols: tuple[FinalEvaluationProtocol, ...]
    outcome_free_rows: tuple[EvaluationRow, ...]

    def __init__(
        self,
        canonical_product_json: str,
        product_sha256: str,
        release_admission_sha256: str,
        scope_sha256: str,
        protocols: tuple[FinalEvaluationProtocol, ...],
        outcome_free_rows: tuple[EvaluationRow, ...],
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            refuse("Six-cell prediction products require the governed factory")
        object.__setattr__(self, "canonical_product_json", canonical_product_json)
        object.__setattr__(self, "product_sha256", product_sha256)
        object.__setattr__(self, "release_admission_sha256", release_admission_sha256)
        object.__setattr__(self, "scope_sha256", scope_sha256)
        object.__setattr__(self, "protocols", protocols)
        object.__setattr__(self, "outcome_free_rows", tuple(outcome_free_rows))
        self.__post_init__()

    def __post_init__(self) -> None:
        try:
            loaded = json.loads(self.canonical_product_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed prediction product receipt: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != self.canonical_product_json
            or manifest_sha256(loaded) != digest(self.product_sha256)
        ):
            refuse("Prediction product canonical bytes or identity differ")
        payload = cast(dict[str, object], loaded)
        if payload.get("release_admission_sha256") != digest(
            self.release_admission_sha256
        ) or payload.get("scope_sha256") != digest(self.scope_sha256):
            refuse("Prediction product typed identities differ from its receipt")
        indexed = protocol_index(self.protocols)
        regenerated = admit_final_evaluation_release(
            tuple(indexed[key] for key in _PROTOCOLS)
        )
        if regenerated.admission_sha256 != self.release_admission_sha256:
            refuse("Prediction product protocols differ from release admission")
        validate_payload(payload, self.outcome_free_rows, indexed)

    def rows_for(self, protocol_id: ProtocolId) -> tuple[EvaluationRow, ...]:
        """Return one protocol ledger without consulting retained paths."""
        if protocol_id not in _PROTOCOLS:
            refuse("Unknown prediction-product protocol")
        payload = cast(dict[str, object], json.loads(self.canonical_product_json))
        receipts = cast(list[dict[str, object]], payload["rows"])
        return tuple(
            row
            for receipt, row in zip(receipts, self.outcome_free_rows, strict=True)
            if receipt["protocol_id"] == protocol_id
        )


def _adapter_rows(
    protocol_id: ProtocolId,
    protocol: FinalEvaluationProtocol,
    locators: ProtocolProductLocators,
) -> dict[tuple[str, str], tuple[EvaluationRow, ...]]:
    local = locators.local_predictions
    withheld = locators.withheld_predictions
    uncertainty = locators.conditional_uncertainty
    scope = protocol.scope
    if protocol_id == "grouped_outer":
        return {
            _CELLS[0]: adapt_authenticated_grouped_local_vegetation_rows(
                local.path,
                expected_local_manifest_sha256=local.expected_manifest_sha256,
                baseline_predictions=withheld.path,
                expected_baseline_manifest_sha256=withheld.expected_manifest_sha256,
                scope=scope,
            ),
            _CELLS[1]: adapt_authenticated_grouped_withheld_vegetation_rows(
                withheld.path,
                expected_manifest_sha256=withheld.expected_manifest_sha256,
                scope=scope,
            ),
            _CELLS[2]: adapt_authenticated_grouped_withheld_pollen_rows(
                withheld.path,
                expected_prediction_manifest_sha256=withheld.expected_manifest_sha256,
                uncertainty=uncertainty.path,
                expected_uncertainty_manifest_sha256=(
                    uncertainty.expected_manifest_sha256
                ),
                scope=scope,
            ),
        }
    return {
        _CELLS[0]: adapt_authenticated_spatial_block_local_vegetation_rows(
            local.path,
            expected_local_manifest_sha256=local.expected_manifest_sha256,
            baseline_predictions=withheld.path,
            expected_baseline_manifest_sha256=withheld.expected_manifest_sha256,
            scope=scope,
        ),
        _CELLS[1]: adapt_authenticated_spatial_block_withheld_vegetation_rows(
            withheld.path,
            expected_manifest_sha256=withheld.expected_manifest_sha256,
            scope=scope,
        ),
        _CELLS[2]: adapt_authenticated_spatial_block_withheld_pollen_rows(
            withheld.path,
            expected_prediction_manifest_sha256=withheld.expected_manifest_sha256,
            uncertainty=uncertainty.path,
            expected_uncertainty_manifest_sha256=uncertainty.expected_manifest_sha256,
            scope=scope,
        ),
    }


def build_six_cell_prediction_product(
    release_admission: FinalEvaluationReleaseAdmission,
    *,
    protocols: tuple[FinalEvaluationProtocol, ...],
    locators: SixCellProductLocators,
) -> SixCellPredictionProduct:
    """Authenticate and freeze the fixed six-cell matrix before outcome access."""
    if not isinstance(release_admission, FinalEvaluationReleaseAdmission):
        refuse("A governed final-release admission is required")
    if not isinstance(locators, SixCellProductLocators):
        refuse("Prediction products require the fixed typed locator schema")
    indexed = protocol_index(protocols)
    ordered_protocols = tuple(indexed[key] for key in _PROTOCOLS)
    regenerated = admit_final_evaluation_release(ordered_protocols)
    if regenerated != release_admission:
        refuse("Release admission differs from regenerated protocol bytes")
    protocol_payloads: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    frozen_rows: list[EvaluationRow] = []
    locator_index = {
        "grouped_outer": locators.grouped_outer,
        "spatial_block": locators.spatial_block,
    }
    for protocol_id in _PROTOCOLS:
        protocol = indexed[protocol_id]
        cells = cell_index(protocol)
        selected_locators = locator_index[protocol_id]
        adapted = _adapter_rows(protocol_id, protocol, selected_locators)
        cell_payloads: list[dict[str, object]] = []
        for combination in _CELLS:
            cell = cells[combination]
            cell_units = units(protocol_id, protocol.scope)
            ordered = ordered_cell_rows(
                adapted[combination],
                protocol_id=protocol_id,
                cell=cell,
                scope=protocol.scope,
            )
            cell_payloads.append(cell_payload(cell, cell_units))
            for row in ordered:
                receipt_rows.append(row_receipt(protocol_id, cell.cell_id, row))
                frozen_rows.append(row)
        protocol_payloads.append(
            {
                "protocol_id": protocol_id,
                "scope_split_sha256": protocol.scope.split_sha256,
                "split_manifest_sha256": protocol.split_manifest_sha256,
                "policy_sha256": protocol.policy.policy_sha256,
                "retained_products": (
                    selected_locators._authenticated_identities_after_adapter_reads()
                ),
                "cells": cell_payloads,
            }
        )
    payload = {
        "schema_version": PREDICTION_PRODUCT_PROFILE,
        "engineering_prediction_product": "authenticated",
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "release_admission_sha256": release_admission.admission_sha256,
        "scope_sha256": ordered_protocols[0].scope.scope_sha256,
        "protocols": protocol_payloads,
        "rows": receipt_rows,
    }
    canonical = canonical_json(payload)
    return SixCellPredictionProduct(
        canonical,
        manifest_sha256(payload),
        release_admission.admission_sha256,
        ordered_protocols[0].scope.scope_sha256,
        ordered_protocols,
        tuple(frozen_rows),
        _factory_token=_FACTORY_TOKEN,
    )
