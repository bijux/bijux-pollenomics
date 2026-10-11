"""Persist fixed-order observation source completion or failure receipts."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
from typing import cast

from ...contracts import ValidationRefusal, canonical_json, manifest_sha256
from ..contracts import Support, digest, refuse
from ..observation_access import OutcomeAccessStartReceipt
from .binding import bind_products_to_start
from .contracts import (
    _PRODUCT_FACTORY_TOKEN,
    HeldoutPollenCountSourceProduct,
    HeldoutPollenCountUnit,
    MeasuredVegetationSourceProduct,
    MeasuredVegetationUnit,
    UnitStatus,
)
from .reading import (
    _read_heldout_pollen_source,
    _read_measured_vegetation_source,
    _read_source_bytes,
    governed_reader_code_sha256,
)

OBSERVATION_SOURCE_COMPLETION_PROFILE = "pollenomics-observation-source-completion.v1"

_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "start_receipt_sha256",
        "access_plan_sha256",
        "prediction_product_sha256",
        "scope_sha256",
        "access_started_at_utc",
        "completed_at_utc",
        "actual_outcome_reads",
        "outcome_bytes_read",
        "products",
        "failure",
        "empirical_evaluation_performed",
        "scientific_acceptance",
        "historical_human_nonaccess_authenticated",
    }
)
_READ_KEYS = frozenset({"source_kind", "path", "source_sha256", "bytes"})
_PRODUCT_KEYS = frozenset({"canonical_product_json", "product_sha256"})
_FAILURE_KEYS = frozenset({"reason_code", "detail"})
_RECEIPT_FACTORY_TOKEN = object()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _product_payload(
    vegetation: MeasuredVegetationSourceProduct,
    pollen: HeldoutPollenCountSourceProduct,
) -> dict[str, dict[str, str]]:
    return {
        "independent_measured_vegetation": {
            "canonical_product_json": vegetation.canonical_product_json,
            "product_sha256": vegetation.product_sha256,
        },
        "heldout_pollen_counts": {
            "canonical_product_json": pollen.canonical_product_json,
            "product_sha256": pollen.product_sha256,
        },
    }


def _support(value: object) -> Support:
    if not isinstance(value, dict):
        refuse("Observation source support must be an exact object")
    try:
        return Support(**value)
    except (TypeError, ValueError) as exc:
        refuse(f"Malformed observation source support: {exc}")


def _vegetation_unit(value: dict[str, object]) -> MeasuredVegetationUnit:
    values = tuple(
        (cast(str, item[0]), cast(float | None, item[1]))
        for item in cast(list[list[object]], value["values"])
    )
    return MeasuredVegetationUnit(
        observation_id=cast(str, value["observation_id"]),
        record_id=cast(str, value["record_id"]),
        site_id=cast(str, value["site_id"]),
        group_id=cast(str, value["group_id"]),
        block_id=cast(str, value["block_id"]),
        bin_id=cast(str, value["bin_id"]),
        source_reference_id=cast(str, value["source_reference_id"]),
        source_sample_id=cast(str, value["source_sample_id"]),
        source_row_id=cast(str, value["source_row_id"]),
        source_snapshot_sha256=cast(str, value["source_snapshot_sha256"]),
        source_member_sha256=cast(str, value["source_member_sha256"]),
        reviewed_taxon_mapping_sha256=cast(str, value["reviewed_taxon_mapping_sha256"]),
        normalization_code_sha256=cast(str, value["normalization_code_sha256"]),
        rights_evidence_sha256=cast(str, value["rights_evidence_sha256"]),
        source_unit_sha256=cast(str, value["source_unit_sha256"]),
        support=_support(value["support"]),
        status=cast(UnitStatus, value["status"]),
        reason_code=cast(str | None, value["reason_code"]),
        values=values,
    )


def _pollen_unit(value: dict[str, object]) -> HeldoutPollenCountUnit:
    values = tuple(
        (cast(str, item[0]), cast(int | None, item[1]))
        for item in cast(list[list[object]], value["values"])
    )
    return HeldoutPollenCountUnit(
        observation_id=cast(str, value["observation_id"]),
        record_id=cast(str, value["record_id"]),
        site_id=cast(str, value["site_id"]),
        group_id=cast(str, value["group_id"]),
        block_id=cast(str, value["block_id"]),
        bin_id=cast(str, value["bin_id"]),
        source_reference_id=cast(str, value["source_reference_id"]),
        source_sample_id=cast(str, value["source_sample_id"]),
        source_row_id=cast(str, value["source_row_id"]),
        source_snapshot_sha256=cast(str, value["source_snapshot_sha256"]),
        source_member_sha256=cast(str, value["source_member_sha256"]),
        reviewed_taxon_mapping_sha256=cast(str, value["reviewed_taxon_mapping_sha256"]),
        normalization_code_sha256=cast(str, value["normalization_code_sha256"]),
        rights_evidence_sha256=cast(str, value["rights_evidence_sha256"]),
        source_unit_sha256=cast(str, value["source_unit_sha256"]),
        pollen_channel_input_id=cast(str, value["pollen_channel_input_id"]),
        pollen_channel_source_sha256=cast(str, value["pollen_channel_source_sha256"]),
        support=_support(value["support"]),
        status=cast(UnitStatus, value["status"]),
        reason_code=cast(str | None, value["reason_code"]),
        counting_effort=cast(int | None, value["counting_effort"]),
        all_zero_count=cast(bool, value["all_zero_count"]),
        values=values,
    )


def _reopen_vegetation_product(
    canonical: str, product_sha256: str
) -> MeasuredVegetationSourceProduct:
    loaded = cast(dict[str, object], json.loads(canonical))
    units = tuple(
        _vegetation_unit(value)
        for value in cast(list[dict[str, object]], loaded["units"])
    )
    return MeasuredVegetationSourceProduct(
        canonical, product_sha256, units, _factory_token=_PRODUCT_FACTORY_TOKEN
    )


def _reopen_pollen_product(
    canonical: str, product_sha256: str
) -> HeldoutPollenCountSourceProduct:
    loaded = cast(dict[str, object], json.loads(canonical))
    units = tuple(
        _pollen_unit(value) for value in cast(list[dict[str, object]], loaded["units"])
    )
    return HeldoutPollenCountSourceProduct(
        canonical, product_sha256, units, _factory_token=_PRODUCT_FACTORY_TOKEN
    )


def _validate_products(
    value: object,
) -> tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "independent_measured_vegetation",
        "heldout_pollen_counts",
    }:
        refuse("Observation completion source products differ")
    vegetation = value["independent_measured_vegetation"]
    pollen = value["heldout_pollen_counts"]
    if any(
        not isinstance(item, dict) or frozenset(item) != _PRODUCT_KEYS
        for item in (vegetation, pollen)
    ):
        refuse("Observation completion product fields differ")
    try:
        return (
            _reopen_vegetation_product(
                cast(str, vegetation["canonical_product_json"]),
                cast(str, vegetation["product_sha256"]),
            ),
            _reopen_pollen_product(
                cast(str, pollen["canonical_product_json"]),
                cast(str, pollen["product_sha256"]),
            ),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        refuse(f"Malformed embedded observation source product: {exc}")


def _validate_payload(
    payload: dict[str, object],
    *,
    start: OutcomeAccessStartReceipt,
    completed_at: datetime,
) -> tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct] | None:
    status = payload.get("status")
    reads = payload.get("actual_outcome_reads")
    failure = payload.get("failure")
    if frozenset(payload) != _RECEIPT_KEYS or (
        payload.get("schema_version") != OBSERVATION_SOURCE_COMPLETION_PROFILE
        or status not in {"completed", "failed"}
        or payload.get("start_receipt_sha256") != start.receipt_sha256
        or payload.get("access_plan_sha256") != start.plan.plan_sha256
        or payload.get("prediction_product_sha256")
        != start.plan.prediction_product.product_sha256
        or payload.get("scope_sha256") != start.plan.prediction_product.scope_sha256
        or payload.get("access_started_at_utc")
        != start.access_started_at_utc.isoformat()
        or payload.get("completed_at_utc") != completed_at.isoformat()
        or not isinstance(reads, list)
        or any(
            not isinstance(value, dict) or frozenset(value) != _READ_KEYS
            for value in reads
        )
        or payload.get("outcome_bytes_read") is not bool(reads)
        or payload.get("empirical_evaluation_performed") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("historical_human_nonaccess_authenticated") is not False
        or completed_at.utcoffset() != UTC.utcoffset(completed_at)
        or completed_at <= start.access_started_at_utc
    ):
        refuse("Observation completion receipt identity or claim boundary differs")
    kinds = [cast(dict[str, object], value)["source_kind"] for value in reads]
    if (
        kinds
        != [
            "independent_measured_vegetation",
            "heldout_pollen_counts",
        ][: len(kinds)]
    ):
        refuse("Observation sources were not read in the fixed planned order")
    paths = (start.plan.sources.vegetation.path, start.plan.sources.pollen.path)
    for raw_read, path in zip(reads, paths, strict=False):
        read = cast(dict[str, object], raw_read)
        byte_count = read.get("bytes")
        digest(cast(str, read.get("source_sha256")))
        if (
            read.get("path") != str(path)
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count < 0
        ):
            refuse("Observation completion actual-read identity differs")
    products = _validate_products(payload.get("products"))
    if status == "completed":
        if len(reads) != 2 or products is None or failure is not None:
            refuse("Completed observation source receipt is incomplete")
        bind_products_to_start(products, start, reads)
    elif (
        products is not None
        or not isinstance(failure, dict)
        or frozenset(failure) != _FAILURE_KEYS
        or any(not isinstance(failure.get(key), str) for key in _FAILURE_KEYS)
    ):
        refuse("Failed observation source receipt lacks its exact refusal")
    return products


@dataclass(frozen=True, init=False)
class ObservationSourceCompletionReceipt:
    """Canonical fixed-order completion; it is not an evaluation result."""

    canonical_receipt_json: str
    receipt_sha256: str
    completed_at_utc: datetime
    start_receipt: OutcomeAccessStartReceipt
    products: (
        tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct] | None
    )

    def __init__(
        self,
        canonical_receipt_json: str,
        receipt_sha256: str,
        completed_at_utc: datetime,
        start_receipt: OutcomeAccessStartReceipt,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _RECEIPT_FACTORY_TOKEN:
            refuse("Observation completion receipts require the governed producer")
        object.__setattr__(self, "canonical_receipt_json", canonical_receipt_json)
        object.__setattr__(self, "receipt_sha256", receipt_sha256)
        object.__setattr__(self, "completed_at_utc", completed_at_utc)
        object.__setattr__(self, "start_receipt", start_receipt)
        try:
            loaded = json.loads(canonical_receipt_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed observation completion receipt: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != canonical_receipt_json
            or manifest_sha256(loaded) != digest(receipt_sha256)
        ):
            refuse("Observation completion receipt canonical bytes differ")
        products = _validate_payload(
            cast(dict[str, object], loaded),
            start=start_receipt,
            completed_at=completed_at_utc,
        )
        object.__setattr__(self, "products", products)


def _publish_exclusive(destination: Path, content: bytes) -> None:
    if not isinstance(destination, Path) or not destination.is_absolute():
        refuse("Observation completion destination must be an absolute typed path")
    if not destination.parent.is_dir() or destination.exists():
        refuse(
            "Observation completion destination must be new in an existing directory"
        )
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
    except OSError as exc:
        refuse(f"Cannot create observation completion receipt: {exc}")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination, follow_symlinks=False)
        directory = os.open(
            destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileExistsError:
        refuse("Observation completion receipt already exists")
    except OSError as exc:
        refuse(f"Cannot durably publish observation completion receipt: {exc}")
    finally:
        with suppress(FileNotFoundError):
            temporary.unlink()


def _receipt(
    start: OutcomeAccessStartReceipt,
    destination: Path,
    reads: list[dict[str, object]],
    *,
    products: (
        tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct] | None
    ),
    failure: ValidationRefusal | None,
) -> ObservationSourceCompletionReceipt:
    completed = _utc_now()
    payload = {
        "schema_version": OBSERVATION_SOURCE_COMPLETION_PROFILE,
        "status": "completed" if failure is None else "failed",
        "start_receipt_sha256": start.receipt_sha256,
        "access_plan_sha256": start.plan.plan_sha256,
        "prediction_product_sha256": start.plan.prediction_product.product_sha256,
        "scope_sha256": start.plan.prediction_product.scope_sha256,
        "access_started_at_utc": start.access_started_at_utc.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "actual_outcome_reads": reads,
        "outcome_bytes_read": bool(reads),
        "products": None
        if products is None
        else _product_payload(products[0], products[1]),
        "failure": None
        if failure is None
        else {"reason_code": failure.reason_code, "detail": str(failure)},
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "historical_human_nonaccess_authenticated": False,
    }
    canonical = canonical_json(payload)
    receipt = ObservationSourceCompletionReceipt(
        canonical,
        manifest_sha256(payload),
        completed,
        start,
        _factory_token=_RECEIPT_FACTORY_TOKEN,
    )
    _publish_exclusive(destination, (canonical + "\n").encode("utf-8"))
    return receipt


def read_observation_source_products(
    start_receipt: OutcomeAccessStartReceipt,
    *,
    completion_destination: Path,
) -> ObservationSourceCompletionReceipt:
    """Read only both planned paths, in fixed order, after a durable start."""
    if not isinstance(start_receipt, OutcomeAccessStartReceipt):
        refuse("Observation source reads require a governed access-start receipt")
    if (
        not isinstance(completion_destination, Path)
        or not completion_destination.is_absolute()
        or not completion_destination.parent.is_dir()
        or completion_destination.exists()
    ):
        refuse("Observation completion destination must be new and writable")
    reads: list[dict[str, object]] = []
    try:
        expected_code = governed_reader_code_sha256()
        sources = start_receipt.plan.sources
        if (
            sources.vegetation.reader_code_sha256 != expected_code
            or sources.pollen.reader_code_sha256 != expected_code
        ):
            refuse("Observation access plan names a different governed reader code")
        vegetation_read = _read_source_bytes(
            sources.vegetation.path,
            source_kind="independent_measured_vegetation",
        )
        reads.append(vegetation_read.receipt())
        vegetation = _read_measured_vegetation_source(vegetation_read, start_receipt)
        pollen_read = _read_source_bytes(
            sources.pollen.path, source_kind="heldout_pollen_counts"
        )
        reads.append(pollen_read.receipt())
        pollen = _read_heldout_pollen_source(pollen_read, start_receipt)
    except ValidationRefusal as exc:
        _receipt(
            start_receipt,
            completion_destination,
            reads,
            products=None,
            failure=exc,
        )
        raise
    return _receipt(
        start_receipt,
        completion_destination,
        reads,
        products=(vegetation, pollen),
        failure=None,
    )


def reopen_observation_source_completion_receipt(
    path: Path,
    *,
    start_receipt: OutcomeAccessStartReceipt,
    expected_receipt_sha256: str,
) -> ObservationSourceCompletionReceipt:
    """Reopen persisted products without reading either outcome path again."""
    if not isinstance(path, Path):
        refuse("Observation completion receipt requires a typed path")
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        refuse(f"Cannot read observation completion receipt: {exc}")
    if not text.endswith("\n") or text.count("\n") != 1:
        refuse("Observation completion receipt must be one canonical JSON line")
    canonical = text[:-1]
    try:
        value = json.loads(canonical)
    except json.JSONDecodeError as exc:
        refuse(f"Malformed persisted observation completion: {exc}")
    if not isinstance(value, dict):
        refuse("Persisted observation completion must be an object")
    try:
        completed = datetime.fromisoformat(cast(str, value.get("completed_at_utc")))
    except (TypeError, ValueError) as exc:
        refuse(f"Malformed observation completion timestamp: {exc}")
    return ObservationSourceCompletionReceipt(
        canonical,
        digest(expected_receipt_sha256),
        completed,
        start_receipt,
        _factory_token=_RECEIPT_FACTORY_TOKEN,
    )
