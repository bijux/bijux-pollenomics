"""Compare one explicit candidate with authenticated published LandClim targets.

This module reports an exact, typed outer join and candidate-minus-reference
residuals.  It does not apply tolerances, convert units, or certify a model
rerun, scientific accuracy, or independent vegetation agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Literal

from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    LandClimPublishedEstimateInventory,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory.contracts import (
    EVIDENCE_ROLE,
    VALUE_UNIT,
)

SCHEMA_VERSION = "essd-published-estimate-comparison.v1"
COMPARISON_ROLE = "published_reconstruction_comparison_only"

KeyMembership = Literal["shared", "reference_only", "candidate_only"]


class PublishedEstimateComparisonError(ValueError):
    """Raised when comparison inputs do not satisfy the exact join contract."""


def _require_identifier(value: str, name: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise PublishedEstimateComparisonError(
            f"{name} must be a non-empty, whitespace-exact string"
        )


def _require_value(value: Decimal | None, name: str) -> None:
    if value is None:
        return
    if type(value) is not Decimal or not value.is_finite():
        raise PublishedEstimateComparisonError(
            f"{name} must be a finite Decimal or null"
        )


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


@dataclass(frozen=True, order=True, slots=True)
class PublishedEstimateKey:
    """An explicit published-product comparison key."""

    grid: str
    window: str
    feature: str

    def __post_init__(self) -> None:
        _require_identifier(self.grid, "grid")
        _require_identifier(self.window, "window")
        _require_identifier(self.feature, "feature")

    def payload(self) -> dict[str, str]:
        """Return the key without normalization or alias inference."""
        return {
            "grid": self.grid,
            "window": self.window,
            "feature": self.feature,
        }


@dataclass(frozen=True, slots=True)
class PublishedEstimateValue:
    """One candidate or reference mean/SE pair; null and zero stay distinct."""

    key: PublishedEstimateKey
    mean: Decimal | None
    standard_error: Decimal | None

    def __post_init__(self) -> None:
        if type(self.key) is not PublishedEstimateKey:
            raise PublishedEstimateComparisonError(
                "comparison row key must be a PublishedEstimateKey"
            )
        _require_value(self.mean, "mean")
        _require_value(self.standard_error, "standard_error")

    def payload(self) -> dict[str, object]:
        """Return canonical, lossless decimal strings and explicit nulls."""
        return {
            "key": self.key.payload(),
            "mean": _decimal(self.mean),
            "standard_error": _decimal(self.standard_error),
        }


@dataclass(frozen=True, slots=True)
class PublishedEstimateCandidate:
    """An explicitly named, content-addressed candidate projection."""

    candidate_id: str
    value_unit: str
    rows: tuple[PublishedEstimateValue, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.candidate_id, "candidate_id")
        _require_identifier(self.value_unit, "value_unit")
        if type(self.rows) is not tuple:
            raise PublishedEstimateComparisonError(
                "candidate rows must be an immutable tuple"
            )
        _row_map("candidate", self.rows)

    def payload(self) -> dict[str, object]:
        """Return an order-independent candidate-input projection."""
        return {
            "schema_version": "essd-published-estimate-candidate.v1",
            "candidate_id": self.candidate_id,
            "value_unit": self.value_unit,
            "rows": [row.payload() for row in _ordered_rows(self.rows)],
        }

    @property
    def canonical_bytes(self) -> bytes:
        """Return deterministic bytes for the exact candidate projection."""
        return _canonical_bytes(self.payload())

    @property
    def sha256(self) -> str:
        """Return the content hash of the ordered candidate projection."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class MetricDenominators:
    """Partition the shared-key denominator for one reported metric."""

    numeric_pairs: int
    both_null: int
    null_disagreements: int

    def payload(self) -> dict[str, int]:
        """Return mutually exclusive shared-key counts."""
        return {
            "numeric_pairs": self.numeric_pairs,
            "both_null": self.both_null,
            "null_disagreements": self.null_disagreements,
        }


@dataclass(frozen=True, slots=True)
class ComparisonDenominators:
    """Expose every outer-join and metric-specific denominator."""

    reference_keys: int
    candidate_keys: int
    union_keys: int
    shared_keys: int
    reference_only_keys: int
    candidate_only_keys: int
    mean: MetricDenominators
    standard_error: MetricDenominators

    def payload(self) -> dict[str, object]:
        """Return exact comparison denominators without a pass threshold."""
        return {
            "reference_keys": self.reference_keys,
            "candidate_keys": self.candidate_keys,
            "union_keys": self.union_keys,
            "shared_keys": self.shared_keys,
            "reference_only_keys": self.reference_only_keys,
            "candidate_only_keys": self.candidate_only_keys,
            "mean": self.mean.payload(),
            "standard_error": self.standard_error.payload(),
        }


@dataclass(frozen=True, slots=True)
class PublishedEstimateComparisonRow:
    """One outer-join row with candidate-minus-reference residuals."""

    key: PublishedEstimateKey
    membership: KeyMembership
    reference_mean: Decimal | None
    candidate_mean: Decimal | None
    mean_residual: Decimal | None
    mean_null_disagreement: bool
    reference_standard_error: Decimal | None
    candidate_standard_error: Decimal | None
    standard_error_residual: Decimal | None
    standard_error_null_disagreement: bool

    def payload(self) -> dict[str, object]:
        """Return a row whose missing side is distinct from a present null."""
        return {
            "key": self.key.payload(),
            "membership": self.membership,
            "reference_mean": _decimal(self.reference_mean),
            "candidate_mean": _decimal(self.candidate_mean),
            "mean_residual": _decimal(self.mean_residual),
            "mean_null_disagreement": self.mean_null_disagreement,
            "reference_standard_error": _decimal(self.reference_standard_error),
            "candidate_standard_error": _decimal(self.candidate_standard_error),
            "standard_error_residual": _decimal(self.standard_error_residual),
            "standard_error_null_disagreement": (self.standard_error_null_disagreement),
        }


@dataclass(frozen=True, slots=True)
class PublishedEstimateComparison:
    """A hash-bound comparison product with deliberately bounded claims."""

    candidate_id: str
    reference_input_sha256: str
    candidate_input_sha256: str
    value_unit: str
    denominators: ComparisonDenominators
    rows: tuple[PublishedEstimateComparisonRow, ...]

    def payload(self) -> dict[str, object]:
        """Return the deterministic comparison and explicit non-claims."""
        return {
            "schema_version": SCHEMA_VERSION,
            "comparison_role": COMPARISON_ROLE,
            "candidate_id": self.candidate_id,
            "value_unit": self.value_unit,
            "inputs": {
                "reference": {
                    "sha256": self.reference_input_sha256,
                    "evidence_role": EVIDENCE_ROLE,
                },
                "candidate": {"sha256": self.candidate_input_sha256},
            },
            "residual_definition": "candidate_minus_reference",
            "denominators": self.denominators.payload(),
            "rows": [row.payload() for row in self.rows],
            "claims": {
                "historical_raw_inputs_recovered": False,
                "original_r_execution": False,
                "whole_paper_reproduction_certified": False,
                "independent_measured_vegetation_accuracy": False,
                "scientifically_accepted": False,
                "scientific_acceptance": "not_evaluated",
            },
        }

    @property
    def canonical_bytes(self) -> bytes:
        """Return deterministic bytes for the complete comparison product."""
        return _canonical_bytes(self.payload())

    @property
    def sha256(self) -> str:
        """Return the complete comparison-product hash."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def _ordered_rows(
    rows: tuple[PublishedEstimateValue, ...],
) -> tuple[PublishedEstimateValue, ...]:
    return tuple(sorted(rows, key=lambda row: row.key))


def _row_map(
    side: str, rows: tuple[PublishedEstimateValue, ...]
) -> dict[PublishedEstimateKey, PublishedEstimateValue]:
    mapped: dict[PublishedEstimateKey, PublishedEstimateValue] = {}
    for row in rows:
        if type(row) is not PublishedEstimateValue:
            raise PublishedEstimateComparisonError(
                f"{side} rows must contain PublishedEstimateValue instances"
            )
        if row.key in mapped:
            raise PublishedEstimateComparisonError(
                f"duplicate {side} comparison key: {row.key}"
            )
        mapped[row.key] = row
    return mapped


def _reference_rows(
    inventory: LandClimPublishedEstimateInventory,
) -> tuple[PublishedEstimateValue, ...]:
    rows: list[PublishedEstimateValue] = []
    for record in inventory.records:
        for estimate in record.estimates:
            rows.append(
                PublishedEstimateValue(
                    key=PublishedEstimateKey(
                        grid=record.cell_id,
                        window=record.time_window,
                        feature=estimate.variable,
                    ),
                    mean=estimate.mean,
                    standard_error=estimate.standard_error,
                )
            )
    return tuple(rows)


def _metric_denominators(
    pairs: tuple[tuple[Decimal | None, Decimal | None], ...],
) -> MetricDenominators:
    numeric = sum(
        reference is not None and candidate is not None
        for reference, candidate in pairs
    )
    both_null = sum(
        reference is None and candidate is None for reference, candidate in pairs
    )
    null_disagreements = len(pairs) - numeric - both_null
    return MetricDenominators(numeric, both_null, null_disagreements)


def _residual(candidate: Decimal | None, reference: Decimal | None) -> Decimal | None:
    if candidate is None or reference is None:
        return None
    least_exponent = min(
        int(candidate.as_tuple().exponent),
        int(reference.as_tuple().exponent),
    )
    required_precision = max(
        1,
        max(candidate.adjusted(), reference.adjusted()) - least_exponent + 2,
    )
    with localcontext() as context:
        context.prec = required_precision
        return candidate - reference


def _compare_rows(
    reference_rows: tuple[PublishedEstimateValue, ...],
    candidate: PublishedEstimateCandidate,
    *,
    reference_input_sha256: str,
) -> PublishedEstimateComparison:
    reference = _row_map("reference", reference_rows)
    candidate_rows = _row_map("candidate", candidate.rows)
    shared_keys = set(reference) & set(candidate_rows)
    rows: list[PublishedEstimateComparisonRow] = []
    mean_pairs: list[tuple[Decimal | None, Decimal | None]] = []
    standard_error_pairs: list[tuple[Decimal | None, Decimal | None]] = []
    for key in sorted(set(reference) | set(candidate_rows)):
        reference_value = reference.get(key)
        candidate_value = candidate_rows.get(key)
        if reference_value is None:
            membership: KeyMembership = "candidate_only"
        elif candidate_value is None:
            membership = "reference_only"
        else:
            membership = "shared"
        reference_mean = None if reference_value is None else reference_value.mean
        candidate_mean = None if candidate_value is None else candidate_value.mean
        reference_se = (
            None if reference_value is None else reference_value.standard_error
        )
        candidate_se = (
            None if candidate_value is None else candidate_value.standard_error
        )
        shared = membership == "shared"
        if shared:
            mean_pairs.append((reference_mean, candidate_mean))
            standard_error_pairs.append((reference_se, candidate_se))
        rows.append(
            PublishedEstimateComparisonRow(
                key=key,
                membership=membership,
                reference_mean=reference_mean,
                candidate_mean=candidate_mean,
                mean_residual=(
                    _residual(candidate_mean, reference_mean) if shared else None
                ),
                mean_null_disagreement=(
                    shared and ((reference_mean is None) != (candidate_mean is None))
                ),
                reference_standard_error=reference_se,
                candidate_standard_error=candidate_se,
                standard_error_residual=(
                    _residual(candidate_se, reference_se) if shared else None
                ),
                standard_error_null_disagreement=(
                    shared and ((reference_se is None) != (candidate_se is None))
                ),
            )
        )
    reference_only = set(reference) - set(candidate_rows)
    candidate_only = set(candidate_rows) - set(reference)
    denominators = ComparisonDenominators(
        reference_keys=len(reference),
        candidate_keys=len(candidate_rows),
        union_keys=len(rows),
        shared_keys=len(shared_keys),
        reference_only_keys=len(reference_only),
        candidate_only_keys=len(candidate_only),
        mean=_metric_denominators(tuple(mean_pairs)),
        standard_error=_metric_denominators(tuple(standard_error_pairs)),
    )
    return PublishedEstimateComparison(
        candidate_id=candidate.candidate_id,
        reference_input_sha256=reference_input_sha256,
        candidate_input_sha256=candidate.sha256,
        value_unit=VALUE_UNIT,
        denominators=denominators,
        rows=tuple(rows),
    )


def compare_published_estimates(
    reference: LandClimPublishedEstimateInventory,
    candidate: PublishedEstimateCandidate,
) -> PublishedEstimateComparison:
    """Outer-join a candidate with authenticated percentage-cover targets.

    Residuals are exact ``candidate - reference`` Decimal operations only when
    both values are present.  No tolerance or interpretation is applied.
    """
    if type(reference) is not LandClimPublishedEstimateInventory:
        raise PublishedEstimateComparisonError(
            "reference must be an authenticated LandClim published inventory"
        )
    if reference.evidence_role != EVIDENCE_ROLE or reference.value_unit != VALUE_UNIT:
        raise PublishedEstimateComparisonError(
            "reference evidence role or percentage-cover unit changed"
        )
    if candidate.value_unit != VALUE_UNIT:
        raise PublishedEstimateComparisonError(
            "candidate and reference units must both be percentage_cover; "
            "implicit conversion is forbidden"
        )
    return _compare_rows(
        _reference_rows(reference),
        candidate,
        reference_input_sha256=reference.sha256,
    )
