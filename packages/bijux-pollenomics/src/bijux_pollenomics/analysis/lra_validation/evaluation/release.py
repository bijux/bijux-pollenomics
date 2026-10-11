"""Release admission for the complete, prospectively frozen evaluation matrix."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
from typing import Literal, cast

from ..contracts import SiteRecord, canonical_json, manifest_sha256
from ..splits import split_manifest
from .cohort import ReviewedCohortAdmission, validate_cohort_admission
from .contracts import EvaluationPolicy, EvaluationScope, digest, refuse
from .policy import validate_evaluation_policy

FINAL_EVALUATION_RELEASE_PROFILE = "pollenomics-final-evaluation-release.v1"

ProtocolId = Literal["grouped_outer", "spatial_block"]

_PROTOCOL_SPLIT_KINDS: dict[ProtocolId, str] = {
    "grouped_outer": "leave_one_site_group_out",
    "spatial_block": "predefined_block",
}
_REQUIRED_CELLS = frozenset(
    {
        ("local_pollen_available", "vegetation_cover"),
        ("all_target_pollen_withheld", "vegetation_cover"),
        ("all_target_pollen_withheld", "pollen_composition"),
    }
)
_SPLIT_MANIFEST_KEYS = frozenset({"schema_version", "split_kind", "records", "folds"})
_SPLIT_RECORD_KEYS = frozenset({"record_id", "site_id", "identity_keys", "block_id"})
_RELEASE_KEYS = frozenset(
    {
        "profile",
        "engineering_admission",
        "empirical_evaluation_performed",
        "scientific_acceptance",
        "scope_sha256",
        "cohort_admission_sha256",
        "required_matrix",
        "protocols",
    }
)
_PROTOCOL_KEYS = frozenset(
    {
        "protocol_id",
        "split_kind",
        "scope_sha256",
        "cohort_admission_sha256",
        "scope_split_sha256",
        "split_manifest_sha256",
        "policy_sha256",
        "cells",
    }
)
_CELL_KEYS = frozenset(
    {
        "cell_id",
        "experiment",
        "target",
        "model_id",
        "baseline_id",
        "subgroup",
        "maximum_mae_pp",
        "minimum_baseline_improvement_pp",
        "minimum_sites",
        "minimum_blocks",
        "maximum_prediction_failure_fraction",
        "maximum_exclusion_fraction",
        "nominal_predictive_coverage",
        "coverage_tolerance",
        "interval_profile_id",
    }
)
_RELEASE_FACTORY_TOKEN = object()


def _required_matrix() -> list[dict[str, str]]:
    return [
        {"experiment": experiment, "target": target}
        for experiment, target in sorted(_REQUIRED_CELLS)
    ]


def _validate_receipt_payload(payload: dict[str, object]) -> None:
    if frozenset(payload) != _RELEASE_KEYS:
        refuse("Release admission receipt fields differ from the exact schema")
    if (
        payload.get("profile") != FINAL_EVALUATION_RELEASE_PROFILE
        or payload.get("engineering_admission") != "admitted"
        or payload.get("empirical_evaluation_performed") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
        or canonical_json(payload.get("required_matrix"))
        != canonical_json(_required_matrix())
    ):
        refuse("Release admission receipt claim boundary or matrix differs")
    scope_sha256 = payload.get("scope_sha256")
    cohort_admission_sha256 = payload.get("cohort_admission_sha256")
    if not isinstance(scope_sha256, str):
        refuse("Release admission receipt scope identity is missing")
    digest(scope_sha256)
    if not isinstance(cohort_admission_sha256, str):
        refuse("Release admission cohort identity is missing")
    digest(cohort_admission_sha256)
    protocols = payload.get("protocols")
    if not isinstance(protocols, list) or len(protocols) != len(_PROTOCOL_SPLIT_KINDS):
        refuse("Release admission receipt protocols are incomplete")
    for index, (protocol_id, split_kind) in enumerate(_PROTOCOL_SPLIT_KINDS.items()):
        protocol = protocols[index]
        if not isinstance(protocol, dict) or frozenset(protocol) != _PROTOCOL_KEYS:
            refuse("Release admission protocol fields differ from the exact schema")
        if (
            protocol.get("protocol_id") != protocol_id
            or protocol.get("split_kind") != split_kind
            or protocol.get("scope_sha256") != scope_sha256
            or protocol.get("cohort_admission_sha256") != cohort_admission_sha256
        ):
            refuse("Release admission protocol identity or scope differs")
        for key in (
            "scope_split_sha256",
            "split_manifest_sha256",
            "policy_sha256",
        ):
            value = protocol.get(key)
            if not isinstance(value, str):
                refuse("Release admission protocol digest is missing")
            digest(value)
        cells = protocol.get("cells")
        if not isinstance(cells, list) or len(cells) != len(_REQUIRED_CELLS):
            refuse("Release admission protocol cell matrix is incomplete")
        combinations: set[tuple[object, object]] = set()
        identities: set[object] = set()
        for cell in cells:
            if not isinstance(cell, dict) or frozenset(cell) != _CELL_KEYS:
                refuse("Release admission cell fields differ from the exact schema")
            for key in (
                "cell_id",
                "model_id",
                "baseline_id",
                "subgroup",
                "interval_profile_id",
            ):
                if not isinstance(cell.get(key), str) or not cell[key]:
                    refuse("Release admission cell identity is malformed")
            combinations.add((cell.get("experiment"), cell.get("target")))
            identities.add(cell.get("cell_id"))
        if combinations != _REQUIRED_CELLS or len(identities) != len(cells):
            refuse("Release admission cell identities or combinations differ")


@dataclass(frozen=True)
class FinalEvaluationProtocol:
    """One generic evaluator policy bound to its complete canonical split payload."""

    protocol_id: ProtocolId
    scope: EvaluationScope
    cohort_admission: ReviewedCohortAdmission
    policy: EvaluationPolicy
    canonical_split_manifest_json: str
    split_manifest_sha256: str


@dataclass(frozen=True, init=False)
class FinalEvaluationReleaseAdmission:
    """Engineering admission receipt; never an empirical or scientific decision."""

    canonical_admission_json: str
    admission_sha256: str

    def __init__(
        self,
        canonical_admission_json: str,
        admission_sha256: str,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _RELEASE_FACTORY_TOKEN:
            refuse("Release admission receipts must come from the governed factory")
        object.__setattr__(self, "canonical_admission_json", canonical_admission_json)
        object.__setattr__(self, "admission_sha256", admission_sha256)
        self.__post_init__()

    def __post_init__(self) -> None:
        try:
            payload = json.loads(self.canonical_admission_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed release admission receipt: {exc}")
        if (
            not isinstance(payload, dict)
            or canonical_json(payload) != self.canonical_admission_json
            or manifest_sha256(payload) != digest(self.admission_sha256)
        ):
            refuse("Release admission receipt identity differs")
        _validate_receipt_payload(cast(dict[str, object], payload))


def _policy_cells(
    policy: EvaluationPolicy, scope: EvaluationScope
) -> list[dict[str, object]]:
    if not isinstance(policy, EvaluationPolicy):
        refuse("Release protocols require a validated EvaluationPolicy")
    try:
        payload = json.loads(policy.canonical_policy_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed canonical evaluation policy: {exc}")
    if (
        not isinstance(payload, dict)
        or canonical_json(payload) != policy.canonical_policy_json
    ):
        refuse("Evaluation policy must retain exact canonical JSON")
    if manifest_sha256(payload) != digest(policy.policy_sha256):
        refuse("Evaluation policy digest differs from its canonical payload")
    revalidated = validate_evaluation_policy(
        cast(Mapping[str, object], payload),
        scope=scope,
        first_test_access_at=policy.first_test_access_at,
    )
    if revalidated != policy:
        refuse("Evaluation policy object differs from its revalidated payload")
    combinations = {(cell.experiment, cell.target) for cell in policy.cells}
    if len(policy.cells) != len(_REQUIRED_CELLS) or combinations != _REQUIRED_CELLS:
        refuse(
            "Each release protocol requires exactly local-pollen vegetation and "
            "all-target-withheld vegetation plus pollen cells"
        )
    return [cast(dict[str, object], asdict(cell)) for cell in policy.cells]


def _split_payload(
    protocol: FinalEvaluationProtocol,
    *,
    expected_kind: str,
) -> dict[str, object]:
    if not isinstance(protocol.scope, EvaluationScope):
        refuse("Release protocols require a typed EvaluationScope")
    if not isinstance(protocol.canonical_split_manifest_json, str):
        refuse("Canonical split manifest JSON is required")
    try:
        loaded = json.loads(protocol.canonical_split_manifest_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed canonical split manifest: {exc}")
    if (
        not isinstance(loaded, dict)
        or frozenset(loaded) != _SPLIT_MANIFEST_KEYS
        or canonical_json(loaded) != protocol.canonical_split_manifest_json
    ):
        refuse("Split manifest must use the exact canonical v1 payload")
    payload = cast(dict[str, object], loaded)
    if (
        payload["schema_version"] != "lra-site-splits.v1"
        or payload["split_kind"] != expected_kind
    ):
        refuse("Split manifest kind does not match its required release protocol")
    if manifest_sha256(payload) != digest(protocol.split_manifest_sha256):
        refuse("Split manifest digest differs from its exact canonical payload")
    records_value = payload["records"]
    folds_value = payload["folds"]
    if not isinstance(records_value, list) or not isinstance(folds_value, list):
        refuse("Split manifest records and folds must be arrays")
    records: list[SiteRecord] = []
    for value in records_value:
        if not isinstance(value, dict) or frozenset(value) != _SPLIT_RECORD_KEYS:
            refuse("Split manifest record fields differ from the canonical schema")
        row = cast(dict[str, object], value)
        identity_keys = row["identity_keys"]
        if not isinstance(identity_keys, list) or any(
            not isinstance(item, str) for item in identity_keys
        ):
            refuse("Split manifest identity keys must be an explicit string array")
        if (
            not isinstance(row["record_id"], str)
            or not isinstance(row["site_id"], str)
            or (row["block_id"] is not None and not isinstance(row["block_id"], str))
        ):
            refuse("Split manifest record identities are malformed")
        records.append(
            SiteRecord(
                row["record_id"],
                row["site_id"],
                tuple(identity_keys),
                row["block_id"],
            )
        )
    sites = {site.record_id: site for site in protocol.scope.sites}
    if set(sites) != {record.record_id for record in records} or any(
        record.site_id != sites[record.record_id].site_id
        or record.block_id != sites[record.record_id].block_id
        for record in records
    ):
        refuse("Split manifest record universe differs from the evaluation scope")
    scope_folds = [fold.as_dict() for fold in protocol.scope.folds]
    if canonical_json(folds_value) != canonical_json(scope_folds):
        refuse("Split manifest folds differ from the evaluation scope")
    if expected_kind == "predefined_block":
        for fold in protocol.scope.folds:
            training_blocks = {
                sites[record_id].block_id for record_id in fold.train_record_ids
            }
            test_blocks = {
                sites[record_id].block_id for record_id in fold.test_record_ids
            }
            if training_blocks & test_blocks:
                refuse("Spatial-block folds must be train/test block-exclusive")
    regenerated = split_manifest(records, by_block=expected_kind == "predefined_block")
    if canonical_json(payload) != canonical_json(regenerated):
        refuse("Split manifest is not the canonical deterministic protocol output")
    return payload


def admit_final_evaluation_release(
    protocols: tuple[FinalEvaluationProtocol, ...],
) -> FinalEvaluationReleaseAdmission:
    """Admit only the exact six-cell, two-protocol engineering release matrix.

    This boundary binds cohort, policy and split identities before empirical
    scoring. Reviewer authority remains explicitly unauthenticated, and this
    boundary evaluates neither outcomes nor accuracy.
    """
    if not isinstance(protocols, tuple) or any(
        not isinstance(item, FinalEvaluationProtocol) for item in protocols
    ):
        refuse("Release protocols must be an explicit typed tuple")
    if len(protocols) != len(_PROTOCOL_SPLIT_KINDS):
        refuse(
            "Final release requires exactly grouped-outer and spatial-block protocols"
        )
    indexed = {item.protocol_id: item for item in protocols}
    if len(indexed) != len(protocols) or set(indexed) != set(_PROTOCOL_SPLIT_KINDS):
        refuse("Final release protocol identities are missing or duplicated")
    admitted: list[dict[str, object]] = []
    record_payloads: list[object] = []
    scope_hashes: set[str] = set()
    cohort_admission_hashes: set[str] = set()
    for protocol_id in ("grouped_outer", "spatial_block"):
        protocol = indexed[protocol_id]
        expected_kind = _PROTOCOL_SPLIT_KINDS[protocol_id]
        split_payload = _split_payload(protocol, expected_kind=expected_kind)
        validate_cohort_admission(protocol.cohort_admission, scope=protocol.scope)
        cells = _policy_cells(protocol.policy, protocol.scope)
        record_payloads.append(split_payload["records"])
        scope_hashes.add(protocol.scope.scope_sha256)
        cohort_admission_hashes.add(protocol.cohort_admission.admission_sha256)
        admitted.append(
            {
                "protocol_id": protocol_id,
                "split_kind": expected_kind,
                "scope_sha256": protocol.scope.scope_sha256,
                "cohort_admission_sha256": (protocol.cohort_admission.admission_sha256),
                "scope_split_sha256": protocol.scope.split_sha256,
                "split_manifest_sha256": protocol.split_manifest_sha256,
                "policy_sha256": protocol.policy.policy_sha256,
                "cells": cells,
            }
        )
    if (
        len(scope_hashes) != 1
        or len(cohort_admission_hashes) != 1
        or canonical_json(record_payloads[0]) != canonical_json(record_payloads[1])
    ):
        refuse(
            "Both release protocols must use the same cohort admission, frozen site "
            "and alias universe"
        )
    payload = {
        "profile": FINAL_EVALUATION_RELEASE_PROFILE,
        "engineering_admission": "admitted",
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "scope_sha256": next(iter(scope_hashes)),
        "cohort_admission_sha256": next(iter(cohort_admission_hashes)),
        "required_matrix": _required_matrix(),
        "protocols": admitted,
    }
    canonical = canonical_json(payload)
    return FinalEvaluationReleaseAdmission(
        canonical,
        manifest_sha256(payload),
        _factory_token=_RELEASE_FACTORY_TOKEN,
    )
