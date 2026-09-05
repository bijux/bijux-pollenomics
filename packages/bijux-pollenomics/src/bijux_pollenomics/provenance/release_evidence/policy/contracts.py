"""Governed request, propagation, digest-alias, and gate policy validation."""

from __future__ import annotations

from collections.abc import Mapping, Set
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import _PropagationContractIdentity


def _parse_governed_request_ids(
    record: Mapping[str, object], known_required: Set[str]
) -> list[str]:
    from . import ReleaseEvidenceError, _require_unique, _string_items

    governed_request_artifact_ids = _string_items(
        record, "governed_request_artifact_ids"
    )
    if governed_request_artifact_ids != sorted(governed_request_artifact_ids):
        raise ReleaseEvidenceError("governed request artifact IDs must be sorted")
    _require_unique(governed_request_artifact_ids, "governed request artifact ID")
    if set(governed_request_artifact_ids) - known_required:
        raise ReleaseEvidenceError("governed request artifact IDs must be known")
    return governed_request_artifact_ids


def _parse_propagation_contract(
    record: Mapping[str, object],
) -> _PropagationContractIdentity:
    from . import (
        ReleaseEvidenceError,
        _PropagationContractIdentity,
        _mapping,
        _require_digest,
        _require_identity,
        _string_field,
    )

    contract_record = _mapping(
        record["propagation_contract"], "propagation contract identity"
    )
    if set(contract_record) != {
        "contract_id",
        "contract_version",
        "sha256",
        "default_scenario",
    }:
        raise ReleaseEvidenceError("propagation contract identity fields are invalid")
    default_scenario = _mapping(
        contract_record["default_scenario"], "default propagation scenario"
    )
    if set(default_scenario) != {
        "scenario_id",
        "maximum_distance_km",
        "maximum_lag_years",
    }:
        raise ReleaseEvidenceError("default propagation scenario fields are invalid")
    propagation_digest = _string_field(contract_record, "sha256")
    _require_digest(propagation_digest, "propagation contract digest")
    contract_id = _string_field(contract_record, "contract_id")
    contract_version = _string_field(contract_record, "contract_version")
    scenario_id = _string_field(default_scenario, "scenario_id")
    _require_identity(contract_id, "propagation contract ID")
    _require_identity(contract_version, "propagation contract version")
    _require_identity(scenario_id, "default propagation scenario ID")
    maximum_distance_km = default_scenario["maximum_distance_km"]
    maximum_lag_years = default_scenario["maximum_lag_years"]
    if (
        isinstance(maximum_distance_km, bool)
        or not isinstance(maximum_distance_km, (int, float))
        or isinstance(maximum_lag_years, bool)
        or not isinstance(maximum_lag_years, (int, float))
        or maximum_distance_km <= 0
        or maximum_lag_years <= 0
    ):
        raise ReleaseEvidenceError("default propagation thresholds are invalid")
    return _PropagationContractIdentity(
        contract_id=contract_id,
        contract_version=contract_version,
        output_digest=propagation_digest,
        scenario_id=scenario_id,
        maximum_distance_km=float(maximum_distance_km),
        maximum_lag_years=float(maximum_lag_years),
    )


def _parse_allowed_digest_aliases(
    record: Mapping[str, object], known_required: Set[str]
) -> set[frozenset[str]]:
    from . import ReleaseEvidenceError, _mapping_list, _string_items

    allowed_aliases: set[frozenset[str]] = set()
    for item in _mapping_list(record, "allowed_cross_role_digest_aliases"):
        if set(item) != {"artifact_identities"}:
            raise ReleaseEvidenceError("digest alias policy fields are invalid")
        identities = _string_items(item, "artifact_identities")
        if len(identities) != 2 or identities != sorted(identities):
            raise ReleaseEvidenceError(
                "digest alias policy requires two sorted artifact identities"
            )
        pair = frozenset(identities)
        if not pair <= known_required:
            raise ReleaseEvidenceError("digest alias policy names unknown artifacts")
        if pair in allowed_aliases:
            raise ReleaseEvidenceError("duplicate digest alias policy")
        allowed_aliases.add(pair)
    return allowed_aliases


def _parse_required_gate_ids(record: Mapping[str, object]) -> tuple[str, ...]:
    from . import (
        ReleaseEvidenceError,
        _require_identity,
        _require_unique,
        _string_items,
    )

    required_gate_ids = tuple(_string_items(record, "required_gate_ids"))
    if not required_gate_ids or list(required_gate_ids) != sorted(required_gate_ids):
        raise ReleaseEvidenceError("required gate IDs must be non-empty and sorted")
    _require_unique(required_gate_ids, "required gate ID")
    for gate_id in required_gate_ids:
        _require_identity(gate_id, "required gate ID")
    return required_gate_ids
