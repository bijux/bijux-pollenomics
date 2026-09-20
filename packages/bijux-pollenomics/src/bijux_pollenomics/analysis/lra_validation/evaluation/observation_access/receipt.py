"""Persist the first outcome-access instant before any outcome-bearing read."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
from typing import cast

from ...contracts import canonical_json, manifest_sha256
from ..contracts import digest, refuse
from ..policy import timestamp, validate_evaluation_policy
from ..prediction_product import SixCellPredictionProduct
from .plan import ObservationAccessPlan, reopen_observation_access_plan

OUTCOME_ACCESS_START_PROFILE = "pollenomics-outcome-access-start.v1"

_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "access_plan_sha256",
        "prediction_product_sha256",
        "release_admission_sha256",
        "scope_sha256",
        "access_started_at_utc",
        "protocols",
        "policy_revalidated_at_access_start",
        "outcome_bytes_read",
        "actual_outcome_reads",
        "historical_human_nonaccess_authenticated",
        "historical_access_limitation",
        "empirical_evaluation_performed",
        "scientific_acceptance",
    }
)
_PROTOCOL_KEYS = frozenset({"protocol_id", "policy_sha256"})
_RECEIPT_FACTORY_TOKEN = object()


def _utc_now() -> datetime:
    """Return the internally captured start instant; tests may replace this clock."""
    return datetime.now(UTC)


def _protocol_payloads(
    product: SixCellPredictionProduct,
) -> list[dict[str, str]]:
    return [
        {
            "protocol_id": protocol.protocol_id,
            "policy_sha256": protocol.policy.policy_sha256,
        }
        for protocol in product.protocols
    ]


def _revalidate_policy_chronology(
    product: SixCellPredictionProduct, started: datetime
) -> None:
    for protocol in product.protocols:
        try:
            payload = json.loads(protocol.policy.canonical_policy_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed policy at outcome-access boundary: {exc}")
        if not isinstance(payload, dict):
            refuse("Outcome-access policy payload must be an object")
        revalidated = validate_evaluation_policy(
            cast(dict[str, object], payload),
            scope=protocol.scope,
            first_test_access_at=started,
        )
        if revalidated != replace(protocol.policy, first_test_access_at=started):
            refuse("Policy differs when revalidated at the exact access instant")


def _validate_prediction_chronology(
    product: SixCellPredictionProduct, started: datetime
) -> None:
    for row in product.outcome_free_rows:
        if row.status != "predicted":
            continue
        frozen = row.prediction_frozen_at
        if (
            not isinstance(frozen, datetime)
            or frozen.utcoffset() is None
            or frozen >= started
        ):
            refuse("Every successful prediction must freeze before outcome access")


def _validate_receipt_payload(
    payload: dict[str, object],
    *,
    plan: ObservationAccessPlan,
    started: datetime,
) -> None:
    product = plan.prediction_product
    if frozenset(payload) != _RECEIPT_KEYS or (
        payload.get("schema_version") != OUTCOME_ACCESS_START_PROFILE
        or payload.get("status") != "started"
        or payload.get("access_plan_sha256") != plan.plan_sha256
        or payload.get("prediction_product_sha256") != product.product_sha256
        or payload.get("release_admission_sha256") != product.release_admission_sha256
        or payload.get("scope_sha256") != product.scope_sha256
        or payload.get("policy_revalidated_at_access_start") is not True
        or payload.get("outcome_bytes_read") is not False
        or payload.get("actual_outcome_reads") != []
        or payload.get("historical_human_nonaccess_authenticated") is not False
        or payload.get("historical_access_limitation")
        != "process_order_only_prior_human_access_not_authenticated"
        or payload.get("empirical_evaluation_performed") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
    ):
        refuse("Outcome-access start receipt identity or claim boundary differs")
    protocols = payload.get("protocols")
    if not isinstance(protocols, list) or protocols != _protocol_payloads(product):
        refuse("Outcome-access receipt policy identities differ")
    if any(
        not isinstance(value, dict) or frozenset(value) != _PROTOCOL_KEYS
        for value in protocols
    ):
        refuse("Outcome-access receipt protocol fields differ")
    encoded = payload.get("access_started_at_utc")
    parsed = timestamp(encoded)
    if (
        parsed != started
        or parsed.utcoffset() != UTC.utcoffset(parsed)
        or encoded != started.isoformat()
    ):
        refuse("Outcome-access receipt timestamp differs from its typed instant")


@dataclass(frozen=True, init=False)
class OutcomeAccessStartReceipt:
    """Durable started/no-reads receipt; never a historical non-access claim."""

    canonical_receipt_json: str
    receipt_sha256: str
    access_started_at_utc: datetime
    plan: ObservationAccessPlan

    def __init__(
        self,
        canonical_receipt_json: str,
        receipt_sha256: str,
        access_started_at_utc: datetime,
        plan: ObservationAccessPlan,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _RECEIPT_FACTORY_TOKEN:
            refuse("Outcome-access receipts require the governed producer")
        object.__setattr__(self, "canonical_receipt_json", canonical_receipt_json)
        object.__setattr__(self, "receipt_sha256", receipt_sha256)
        object.__setattr__(self, "access_started_at_utc", access_started_at_utc)
        object.__setattr__(self, "plan", plan)
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ObservationAccessPlan):
            refuse("Outcome-access receipt requires a typed access plan")
        try:
            loaded = json.loads(self.canonical_receipt_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed outcome-access receipt: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != self.canonical_receipt_json
            or manifest_sha256(loaded) != digest(self.receipt_sha256)
        ):
            refuse("Outcome-access receipt canonical bytes or identity differ")
        _validate_receipt_payload(
            cast(dict[str, object], loaded),
            plan=self.plan,
            started=self.access_started_at_utc,
        )
        _revalidate_policy_chronology(
            self.plan.prediction_product, self.access_started_at_utc
        )
        _validate_prediction_chronology(
            self.plan.prediction_product, self.access_started_at_utc
        )


def _receipt_payload(
    plan: ObservationAccessPlan, started: datetime
) -> dict[str, object]:
    product = plan.prediction_product
    return {
        "schema_version": OUTCOME_ACCESS_START_PROFILE,
        "status": "started",
        "access_plan_sha256": plan.plan_sha256,
        "prediction_product_sha256": product.product_sha256,
        "release_admission_sha256": product.release_admission_sha256,
        "scope_sha256": product.scope_sha256,
        "access_started_at_utc": started.isoformat(),
        "protocols": _protocol_payloads(product),
        "policy_revalidated_at_access_start": True,
        "outcome_bytes_read": False,
        "actual_outcome_reads": [],
        "historical_human_nonaccess_authenticated": False,
        "historical_access_limitation": (
            "process_order_only_prior_human_access_not_authenticated"
        ),
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
    }


def _fsync_directory(path: Path) -> None:
    try:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        refuse(f"Cannot fsync outcome-access receipt directory: {exc}")


def _publish_exclusive(destination: Path, content: bytes) -> None:
    if not isinstance(destination, Path) or not destination.is_absolute():
        refuse("Outcome-access receipt destination must be an absolute typed path")
    parent = destination.parent
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=parent
        )
    except OSError as exc:
        refuse(f"Cannot create outcome-access receipt: {exc}")
    temporary = Path(temporary_name)
    linked = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError:
            refuse("Outcome-access start receipt already exists")
        linked = True
        _fsync_directory(parent)
    except OSError as exc:
        refuse(f"Cannot durably publish outcome-access receipt: {exc}")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        if linked:
            _fsync_directory(parent)


def start_outcome_access(
    plan: ObservationAccessPlan,
    *,
    destination: Path,
) -> OutcomeAccessStartReceipt:
    """Persist the exclusive start receipt before any outcome-bearing read."""
    if not isinstance(plan, ObservationAccessPlan):
        refuse("Outcome access requires a typed canonical plan")
    checked = reopen_observation_access_plan(
        plan.canonical_plan_json,
        plan.plan_sha256,
        prediction_product=plan.prediction_product,
        sources=plan.sources,
    )
    if checked != plan:
        refuse("Outcome access plan differs from its reopened canonical form")
    started = _utc_now()
    if started.utcoffset() != UTC.utcoffset(started):
        refuse("Outcome-access producer clock must return UTC")
    _revalidate_policy_chronology(plan.prediction_product, started)
    _validate_prediction_chronology(plan.prediction_product, started)
    payload = _receipt_payload(plan, started)
    canonical = canonical_json(payload)
    receipt = OutcomeAccessStartReceipt(
        canonical,
        manifest_sha256(payload),
        started,
        plan,
        _factory_token=_RECEIPT_FACTORY_TOKEN,
    )
    _publish_exclusive(destination, (canonical + "\n").encode("utf-8"))
    return receipt


def reopen_outcome_access_start_receipt(
    path: Path,
    *,
    plan: ObservationAccessPlan,
    expected_receipt_sha256: str,
) -> OutcomeAccessStartReceipt:
    """Read and validate only the durable start receipt, never an outcome source."""
    if not isinstance(path, Path):
        refuse("Outcome-access receipt requires a typed path")
    try:
        content = path.read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        refuse(f"Cannot read outcome-access receipt: {exc}")
    if not text.endswith("\n") or text.count("\n") != 1:
        refuse("Outcome-access receipt must contain one canonical JSON line")
    canonical = text[:-1]
    try:
        loaded = json.loads(canonical)
    except json.JSONDecodeError as exc:
        refuse(f"Malformed persisted outcome-access receipt: {exc}")
    if not isinstance(loaded, dict):
        refuse("Persisted outcome-access receipt must be an object")
    started = timestamp(loaded.get("access_started_at_utc"))
    return OutcomeAccessStartReceipt(
        canonical,
        digest(expected_receipt_sha256),
        started,
        plan,
        _factory_token=_RECEIPT_FACTORY_TOKEN,
    )
