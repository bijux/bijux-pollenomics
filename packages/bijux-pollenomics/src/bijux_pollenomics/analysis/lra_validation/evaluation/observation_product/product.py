"""Build the canonical model-free observation product from completed reads."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import cast

from ...contracts import canonical_json, manifest_sha256
from ..contracts import digest, refuse
from ..observation_sources import (
    HeldoutPollenCountSourceProduct,
    HeldoutPollenCountUnit,
    MeasuredVegetationSourceProduct,
    MeasuredVegetationUnit,
    ObservationSourceCompletionReceipt,
)
from .contracts import (
    AUTHENTICATED_OBSERVATION_PROFILE,
    AuthenticatedObservationAssignment,
    SourceUnit,
)

_FACTORY_TOKEN = object()


def _successful_products(
    completion: ObservationSourceCompletionReceipt,
) -> tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct]:
    if not isinstance(completion, ObservationSourceCompletionReceipt):
        refuse("Authenticated observations require a typed completion receipt")
    if completion.products is None:
        refuse("Authenticated observations require a successful source completion")
    vegetation, pollen = completion.products
    if not isinstance(vegetation, MeasuredVegetationSourceProduct) or not isinstance(
        pollen, HeldoutPollenCountSourceProduct
    ):
        refuse("Observation completion contains different typed products")
    return vegetation, pollen


def _unit_receipt(
    kind: str, product_sha256: str, unit: SourceUnit
) -> dict[str, object]:
    if isinstance(unit, MeasuredVegetationUnit):
        expected_kind = "independent_measured_vegetation"
        pollen: HeldoutPollenCountUnit | None = None
    elif isinstance(unit, HeldoutPollenCountUnit):
        expected_kind = "heldout_pollen_counts"
        pollen = unit
    else:
        refuse("Observation envelopes require an exact typed source unit")
    if kind != expected_kind:
        refuse("Observation envelope kind differs from its typed source unit")
    return {
        "observation_kind": kind,
        "target": (
            "vegetation_cover"
            if kind == "independent_measured_vegetation"
            else "pollen_composition"
        ),
        "observation_id": unit.observation_id,
        "record_id": unit.record_id,
        "site_id": unit.site_id,
        "group_id": unit.group_id,
        "block_id": unit.block_id,
        "bin_id": unit.bin_id,
        "source_reference_id": unit.source_reference_id,
        "source_sample_id": unit.source_sample_id,
        "source_row_id": unit.source_row_id,
        "source_product_sha256": product_sha256,
        "source_unit_sha256": unit.source_unit_sha256,
        "source_snapshot_sha256": unit.source_snapshot_sha256,
        "source_member_sha256": unit.source_member_sha256,
        "reviewed_taxon_mapping_sha256": unit.reviewed_taxon_mapping_sha256,
        "normalization_code_sha256": unit.normalization_code_sha256,
        "rights_evidence_sha256": unit.rights_evidence_sha256,
        "support": asdict(unit.support),
        "taxa": [taxon for taxon, _ in unit.values],
        "status": unit.status,
        "reason": unit.reason_code,
        "values": unit.values,
        "counting_effort": pollen.counting_effort if pollen else None,
        "all_zero_count": pollen.all_zero_count if pollen else None,
        "pollen_channel_input_id": pollen.pollen_channel_input_id if pollen else None,
        "pollen_channel_source_sha256": (
            pollen.pollen_channel_source_sha256 if pollen else None
        ),
    }


def _derive(
    completion: ObservationSourceCompletionReceipt,
) -> tuple[
    tuple[AuthenticatedObservationAssignment, ...],
    tuple[dict[str, object], ...],
]:
    vegetation, pollen = _successful_products(completion)
    products: dict[str, tuple[str, tuple[SourceUnit, ...]]] = {
        "independent_measured_vegetation": (
            vegetation.product_sha256,
            cast(tuple[SourceUnit, ...], vegetation.units),
        ),
        "heldout_pollen_counts": (
            pollen.product_sha256,
            cast(tuple[SourceUnit, ...], pollen.units),
        ),
    }
    units: dict[tuple[str, str], tuple[str, SourceUnit]] = {}
    source_receipts: list[dict[str, object]] = []
    for kind in sorted(products):
        product_sha256, typed_units = products[kind]
        for unit in typed_units:
            key = kind, unit.observation_id
            if key in units:
                refuse("Observation source unit denominator is duplicated")
            units[key] = product_sha256, unit
            source_receipts.append(_unit_receipt(kind, product_sha256, unit))
    assignments: list[AuthenticatedObservationAssignment] = []
    for planned in completion.start_receipt.plan.assignments:
        resolved = units.get((planned.observation_kind, planned.observation_id))
        if resolved is None:
            refuse("Observation assignment lacks its completed source unit")
        product_sha256, unit = resolved
        expected_kind = (
            "independent_measured_vegetation"
            if isinstance(unit, MeasuredVegetationUnit)
            else "heldout_pollen_counts"
        )
        if (
            expected_kind != planned.observation_kind
            or unit.record_id != planned.record_id
            or unit.source_reference_id != planned.source_reference_id
        ):
            refuse("Completed source unit ownership differs from its assignment")
        assignment = AuthenticatedObservationAssignment(
            planned.protocol_id,
            planned.cell_id,
            planned.fold_id,
            planned.record_id,
            planned.target,
            planned.observation_kind,
            planned.observation_id,
            planned.source_reference_id,
            product_sha256,
            unit.source_unit_sha256,
            unit.status,
            unit.reason_code,
        )
        if not assignment.matches_plan(planned):
            refuse("Authenticated observation differs from its access assignment")
        assignments.append(assignment)
    ordered = tuple(sorted(assignments, key=lambda value: value.key))
    if len({value.key for value in ordered}) != len(ordered):
        refuse("Authenticated observation assignments are duplicated")
    return ordered, tuple(source_receipts)


def _payload(
    completion: ObservationSourceCompletionReceipt,
) -> tuple[dict[str, object], tuple[AuthenticatedObservationAssignment, ...]]:
    vegetation, pollen = _successful_products(completion)
    assignments, source_units = _derive(completion)
    start = completion.start_receipt
    prediction = start.plan.prediction_product
    counts = {
        status: sum(value.status == status for value in assignments)
        for status in ("available", "missing", "refused")
    }
    return (
        {
            "schema_version": AUTHENTICATED_OBSERVATION_PROFILE,
            "prediction_product_sha256": prediction.product_sha256,
            "release_admission_sha256": prediction.release_admission_sha256,
            "scope_sha256": prediction.scope_sha256,
            "access_plan_sha256": start.plan.plan_sha256,
            "access_start_receipt_sha256": start.receipt_sha256,
            "source_completion_receipt_sha256": completion.receipt_sha256,
            "vegetation_product_sha256": vegetation.product_sha256,
            "pollen_product_sha256": pollen.product_sha256,
            "source_units": list(source_units),
            "assignments": [asdict(value) for value in assignments],
            "status_counts": counts,
            "empirical_evaluation_performed": False,
            "scientific_acceptance": "not_evaluated",
        },
        assignments,
    )


@dataclass(frozen=True, init=False)
class AuthenticatedObservationProduct:
    """Factory-only exact observation denominator over authenticated sources."""

    canonical_product_json: str
    product_sha256: str
    completion_receipt: ObservationSourceCompletionReceipt
    assignments: tuple[AuthenticatedObservationAssignment, ...]

    def __init__(
        self,
        canonical_product_json: str,
        product_sha256: str,
        completion_receipt: ObservationSourceCompletionReceipt,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            refuse("Authenticated observation products require the governed factory")
        expected, assignments = _payload(completion_receipt)
        try:
            loaded = json.loads(canonical_product_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed authenticated observation product: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != canonical_product_json
            or manifest_sha256(loaded) != digest(product_sha256)
            or canonical_json(loaded) != canonical_json(expected)
        ):
            refuse("Authenticated observation product bytes or parents differ")
        object.__setattr__(self, "canonical_product_json", canonical_product_json)
        object.__setattr__(self, "product_sha256", product_sha256)
        object.__setattr__(self, "completion_receipt", completion_receipt)
        object.__setattr__(self, "assignments", assignments)

    @property
    def prediction_product_sha256(self) -> str:
        return (
            self.completion_receipt.start_receipt.plan.prediction_product.product_sha256
        )


def build_authenticated_observation_product(
    completion_receipt: ObservationSourceCompletionReceipt,
) -> AuthenticatedObservationProduct:
    """Bind a successful completion receipt without accepting caller rows/maps."""
    payload, _ = _payload(completion_receipt)
    canonical = canonical_json(payload)
    return AuthenticatedObservationProduct(
        canonical,
        manifest_sha256(payload),
        completion_receipt,
        _factory_token=_FACTORY_TOKEN,
    )


def reopen_authenticated_observation_product(
    canonical_product_json: str,
    product_sha256: str,
    *,
    completion_receipt: ObservationSourceCompletionReceipt,
) -> AuthenticatedObservationProduct:
    """Replay exact product bytes against the successful completion parent."""
    return AuthenticatedObservationProduct(
        canonical_product_json,
        product_sha256,
        completion_receipt,
        _factory_token=_FACTORY_TOKEN,
    )


def source_unit_index(
    product: AuthenticatedObservationProduct,
) -> dict[tuple[str, str], SourceUnit]:
    """Return units only after replaying the combined product's canonical bytes."""
    reopened = reopen_authenticated_observation_product(
        product.canonical_product_json,
        product.product_sha256,
        completion_receipt=product.completion_receipt,
    )
    vegetation, pollen = _successful_products(reopened.completion_receipt)
    result: dict[tuple[str, str], SourceUnit] = {}
    for kind, units in (
        ("independent_measured_vegetation", vegetation.units),
        ("heldout_pollen_counts", pollen.units),
    ):
        for unit in units:
            result[kind, unit.observation_id] = unit
    return result
