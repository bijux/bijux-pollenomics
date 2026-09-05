"""Required source-reconciliation policy validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import _RequiredReconciliation


def _parse_required_reconciliations(
    record: Mapping[str, object],
) -> tuple[_RequiredReconciliation, ...]:
    from . import (
        Literal,
        ReleaseEvidenceError,
        _RequiredReconciliation,
        _mapping,
        _mapping_list,
        _require_identity,
        _require_unique,
        _string_field,
        cast,
    )

    required: list[_RequiredReconciliation] = []
    for item in _mapping_list(record, "required_reconciliations"):
        if set(item) != {
            "source",
            "entity",
            "dimension",
            "scope_values",
            "derivation_adapter",
            "derivation_metric",
            "unavailable_status",
            "unavailable_reason_code",
        }:
            raise ReleaseEvidenceError(
                "required reconciliation policy fields are invalid"
            )
        source = _string_field(item, "source")
        entity = _string_field(item, "entity")
        dimension = _string_field(item, "dimension")
        derivation_adapter = _string_field(item, "derivation_adapter")
        derivation_metric = _string_field(item, "derivation_metric")
        unavailable_status = _string_field(item, "unavailable_status")
        unavailable_reason_code = _string_field(item, "unavailable_reason_code")
        if dimension not in {"country", "scope"}:
            raise ReleaseEvidenceError("invalid required reconciliation dimension")
        if derivation_adapter not in {
            "classification_observation_memberships",
            "country_coverage",
            "neotoma_relational_reconciliation",
            "propagation_primary_reconciliation",
            "sead_chronology_claims",
            "unavailable",
        }:
            raise ReleaseEvidenceError("invalid reconciliation derivation adapter")
        if unavailable_status not in {"unavailable", "refused"}:
            raise ReleaseEvidenceError("invalid reconciliation unavailable status")
        _require_identity(derivation_metric, "reconciliation derivation metric")
        _require_identity(
            unavailable_reason_code, "reconciliation unavailable reason code"
        )
        raw_scope_values = _mapping(item["scope_values"], "scope values")
        scope_values: list[tuple[str, tuple[str, ...]]] = []
        for key, values in sorted(raw_scope_values.items()):
            if (
                not isinstance(key, str)
                or not isinstance(values, list)
                or any(not isinstance(value, str) for value in values)
            ):
                raise ReleaseEvidenceError("scope values must be string arrays")
            typed_values = tuple(cast(list[str], values))
            if not typed_values or list(typed_values) != sorted(typed_values):
                raise ReleaseEvidenceError("scope values must be non-empty and sorted")
            _require_unique(typed_values, "scope value")
            scope_values.append((key, typed_values))
        if dimension == "country" and scope_values:
            raise ReleaseEvidenceError("country requirement cannot define scope values")
        if dimension == "scope" and not scope_values:
            raise ReleaseEvidenceError("scope requirement must define scope values")
        _require_identity(source, "required reconciliation source")
        _require_identity(entity, "required reconciliation entity")
        required.append(
            _RequiredReconciliation(
                source=source,
                entity=entity,
                dimension=cast(Literal["country", "scope"], dimension),
                scope_values=tuple(scope_values),
                derivation_adapter=derivation_adapter,
                derivation_metric=derivation_metric,
                unavailable_status=cast(
                    Literal["unavailable", "refused"], unavailable_status
                ),
                unavailable_reason_code=unavailable_reason_code,
            )
        )
    if not required:
        raise ReleaseEvidenceError("required reconciliation policy must not be empty")
    _require_unique(
        (f"{item.source}\0{item.entity}" for item in required),
        "required reconciliation",
    )
    if [(item.source, item.entity) for item in required] != sorted(
        (item.source, item.entity) for item in required
    ):
        raise ReleaseEvidenceError("required reconciliations must be sorted")
    return tuple(required)
