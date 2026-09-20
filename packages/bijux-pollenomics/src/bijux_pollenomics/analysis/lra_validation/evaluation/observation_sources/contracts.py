"""Factory-only products for separately authenticated observation sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, cast

from ...contracts import (
    canonical_json,
    finite_number,
    manifest_sha256,
    required_identity,
)
from ..contracts import EvaluationSite, Support, digest, refuse
from ..observation_access import OutcomeAccessStartReceipt
from ..release import FinalEvaluationProtocol
from .product_validation import validate_product

MEASURED_VEGETATION_SOURCE_PROFILE = "pollenomics-measured-vegetation-source-product.v1"
HELDOUT_POLLEN_SOURCE_PROFILE = "pollenomics-heldout-pollen-source-product.v1"
UnitStatus = Literal["available", "missing", "refused"]
VegetationValue = tuple[str, float | None]
PollenValue = tuple[str, int | None]
_PRODUCT_FACTORY_TOKEN = object()


def _identity_fields(values: tuple[str, ...]) -> None:
    for value in values:
        required_identity(value)


def _expected_sites(
    receipt: OutcomeAccessStartReceipt, kind: str
) -> dict[str, EvaluationSite]:
    protocols: dict[str, FinalEvaluationProtocol] = {
        protocol.protocol_id: protocol
        for protocol in receipt.plan.prediction_product.protocols
    }
    expected: dict[str, EvaluationSite] = {}
    for assignment in receipt.plan.assignments:
        if assignment.observation_kind != kind:
            continue
        protocol = protocols.get(assignment.protocol_id)
        site = (
            None
            if protocol is None
            else next(
                (
                    value
                    for value in protocol.scope.sites
                    if value.record_id == assignment.record_id
                ),
                None,
            )
        )
        if site is None:
            refuse("Observation assignment has no exact frozen scope site")
        expected_observation = (
            site.vegetation_observation_id
            if kind == "independent_measured_vegetation"
            else site.pollen_observation_id
        )
        if assignment.observation_id != expected_observation:
            refuse("Observation assignment names a different scope outcome")
        if (
            assignment.observation_id in expected
            and expected[assignment.observation_id] != site
        ):
            refuse("Observation ownership differs between release protocols")
        expected[assignment.observation_id] = site
    if not expected:
        refuse("Observation source has no planned units")
    return expected


def _terminal(status: UnitStatus, reason_code: str | None) -> None:
    if status not in {"available", "missing", "refused"}:
        refuse("Observation source unit has an unsupported status")
    if (status == "available") != (reason_code is None):
        refuse("Observation source status and reason differ")
    if reason_code is not None:
        required_identity(reason_code)


def _taxon_values(values: tuple[tuple[str, object], ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        refuse("Observation source requires an explicit taxon denominator")
    taxa: list[str] = []
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            refuse("Observation source taxon values require exact pairs")
        taxa.append(required_identity(item[0]))
    if taxa != sorted(set(taxa)):
        refuse("Observation source unit taxa must be sorted and unique")
    return tuple(taxa)


def _unit_provenance(
    source: dict[str, object], row: dict[str, object]
) -> tuple[str, str, str, str, str, str]:
    values = (
        cast(str, source["source_snapshot_sha256"]),
        cast(str, source["source_member_sha256"]),
        cast(str, source["taxon_mapping_sha256"]),
        cast(str, source["normalization_code_sha256"]),
        cast(str, source["rights_evidence_sha256"]),
    )
    for value in values:
        digest(value)
    identity = manifest_sha256(
        {
            "source_payload_sha256": manifest_sha256(source),
            "observation_id": row["observation_id"],
            "source_row_id": row["source_row_id"],
        }
    )
    return (*values, identity)


@dataclass(frozen=True)
class MeasuredVegetationUnit:
    """One measured vegetation outcome with exact ownership and support."""

    observation_id: str
    record_id: str
    site_id: str
    group_id: str
    block_id: str
    bin_id: str
    source_reference_id: str
    source_sample_id: str
    source_row_id: str
    source_snapshot_sha256: str
    source_member_sha256: str
    reviewed_taxon_mapping_sha256: str
    normalization_code_sha256: str
    rights_evidence_sha256: str
    source_unit_sha256: str
    support: Support
    status: UnitStatus
    reason_code: str | None
    values: tuple[VegetationValue, ...]

    def __post_init__(self) -> None:
        _identity_fields(
            (
                self.observation_id,
                self.record_id,
                self.site_id,
                self.group_id,
                self.block_id,
                self.bin_id,
                self.source_reference_id,
                self.source_sample_id,
                self.source_row_id,
            )
        )
        if not isinstance(self.support, Support):
            refuse("Measured vegetation requires typed support")
        for provenance_digest in (
            self.source_snapshot_sha256,
            self.source_member_sha256,
            self.reviewed_taxon_mapping_sha256,
            self.normalization_code_sha256,
            self.rights_evidence_sha256,
            self.source_unit_sha256,
        ):
            digest(provenance_digest)
        _terminal(self.status, self.reason_code)
        _taxon_values(cast(tuple[tuple[str, object], ...], self.values))
        numbers: list[float | None] = []
        for _, observation_value in self.values:
            if observation_value is None:
                numbers.append(None)
                continue
            number = finite_number(observation_value)
            if not 0 <= number <= 1:
                refuse("Measured vegetation fractions must lie in [0,1]")
            numbers.append(number)
        known_total = sum(value for value in numbers if value is not None)
        if (
            (
                self.status == "available"
                and (None in numbers or abs(known_total - 1) > 1e-9)
            )
            or (self.status == "missing" and None not in numbers)
            or (
                self.status == "refused" and any(value is not None for value in numbers)
            )
            or known_total > 1 + 1e-9
        ):
            refuse("Measured vegetation values and terminal status differ")


@dataclass(frozen=True)
class HeldoutPollenCountUnit:
    """One withheld pollen outcome, preserving counts and counting effort."""

    observation_id: str
    record_id: str
    site_id: str
    group_id: str
    block_id: str
    bin_id: str
    source_reference_id: str
    source_sample_id: str
    source_row_id: str
    source_snapshot_sha256: str
    source_member_sha256: str
    reviewed_taxon_mapping_sha256: str
    normalization_code_sha256: str
    rights_evidence_sha256: str
    source_unit_sha256: str
    pollen_channel_input_id: str
    pollen_channel_source_sha256: str
    support: Support
    status: UnitStatus
    reason_code: str | None
    counting_effort: int | None
    all_zero_count: bool
    values: tuple[PollenValue, ...]

    def __post_init__(self) -> None:
        _identity_fields(
            (
                self.observation_id,
                self.record_id,
                self.site_id,
                self.group_id,
                self.block_id,
                self.bin_id,
                self.source_reference_id,
                self.source_sample_id,
                self.source_row_id,
                self.pollen_channel_input_id,
            )
        )
        for provenance_digest in (
            self.source_snapshot_sha256,
            self.source_member_sha256,
            self.reviewed_taxon_mapping_sha256,
            self.normalization_code_sha256,
            self.rights_evidence_sha256,
            self.source_unit_sha256,
            self.pollen_channel_source_sha256,
        ):
            digest(provenance_digest)
        if not isinstance(self.support, Support):
            refuse("Held-out pollen requires typed support")
        _terminal(self.status, self.reason_code)
        if self.counting_effort is not None and (
            isinstance(self.counting_effort, bool)
            or not isinstance(self.counting_effort, int)
            or self.counting_effort < 0
        ):
            refuse("Pollen counting effort must be a nonnegative integer or null")
        if type(self.all_zero_count) is not bool:
            refuse("Pollen all-zero status must be explicit")
        _taxon_values(cast(tuple[tuple[str, object], ...], self.values))
        for _, observation_value in self.values:
            if observation_value is not None and (
                isinstance(observation_value, bool)
                or not isinstance(observation_value, int)
                or observation_value < 0
            ):
                refuse("Pollen values must be nonnegative integers or null")
        counts = [value for _, value in self.values]
        missing = any(value is None for value in counts)
        known_total = sum(value for value in counts if value is not None)
        if (
            self.all_zero_count is not (not missing and known_total == 0)
            or (
                self.status == "available"
                and (missing or self.counting_effort != known_total)
            )
            or (
                self.status == "missing"
                and (
                    not missing
                    or (
                        self.counting_effort is not None
                        and self.counting_effort < known_total
                    )
                )
            )
            or (
                self.status == "refused"
                and (
                    any(value is not None for value in counts)
                    or self.counting_effort is not None
                )
            )
        ):
            refuse("Pollen values, effort and terminal status differ")


@dataclass(frozen=True, init=False)
class MeasuredVegetationSourceProduct:
    """Authenticated measured source; construction is restricted to its reader."""

    canonical_product_json: str
    product_sha256: str
    units: tuple[MeasuredVegetationUnit, ...]

    def __init__(
        self,
        canonical_product_json: str,
        product_sha256: str,
        units: tuple[MeasuredVegetationUnit, ...],
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _PRODUCT_FACTORY_TOKEN:
            refuse("Measured vegetation products require the governed reader")
        object.__setattr__(self, "canonical_product_json", canonical_product_json)
        object.__setattr__(self, "product_sha256", product_sha256)
        object.__setattr__(self, "units", tuple(units))
        validate_product(
            canonical_product_json,
            product_sha256,
            self.units,
            profile=MEASURED_VEGETATION_SOURCE_PROFILE,
            kind="independent_measured_vegetation",
        )


@dataclass(frozen=True, init=False)
class HeldoutPollenCountSourceProduct:
    """Authenticated count source; construction is restricted to its reader."""

    canonical_product_json: str
    product_sha256: str
    units: tuple[HeldoutPollenCountUnit, ...]

    def __init__(
        self,
        canonical_product_json: str,
        product_sha256: str,
        units: tuple[HeldoutPollenCountUnit, ...],
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _PRODUCT_FACTORY_TOKEN:
            refuse("Held-out pollen products require the governed reader")
        object.__setattr__(self, "canonical_product_json", canonical_product_json)
        object.__setattr__(self, "product_sha256", product_sha256)
        object.__setattr__(self, "units", tuple(units))
        validate_product(
            canonical_product_json,
            product_sha256,
            self.units,
            profile=HELDOUT_POLLEN_SOURCE_PROFILE,
            kind="heldout_pollen_counts",
        )


def _product_payload(
    source: dict[str, object],
    *,
    source_file_sha256: str,
    profile: str,
    units: tuple[MeasuredVegetationUnit, ...] | tuple[HeldoutPollenCountUnit, ...],
    receipt: OutcomeAccessStartReceipt,
    actual_read: dict[str, object],
) -> dict[str, object]:
    counts = {
        status: sum(unit.status == status for unit in units)
        for status in ("available", "missing", "refused")
    }
    metadata = {
        key: value for key, value in source.items() if key not in {"taxa", "units"}
    }
    locator = (
        receipt.plan.sources.vegetation
        if source["source_kind"] == "independent_measured_vegetation"
        else receipt.plan.sources.pollen
    )
    return {
        "schema_version": profile,
        "source_kind": source["source_kind"],
        "source_canonical_json": canonical_json(source),
        "source_file_sha256": digest(source_file_sha256),
        "source_payload_sha256": manifest_sha256(source),
        "reader_profile": source["reader_profile"],
        "reader_code_sha256": source["reader_code_sha256"],
        "source_reference_id": source["source_reference_id"],
        "access_plan_sha256": receipt.plan.plan_sha256,
        "access_start_receipt_sha256": receipt.receipt_sha256,
        "source_locator_sha256": manifest_sha256(locator.as_dict()),
        "actual_reads": [actual_read],
        "metadata": metadata,
        "taxa": source["taxa"],
        "units": [asdict(unit) for unit in units],
        "requested_units": len(units),
        "available_units": counts["available"],
        "missing_units": counts["missing"],
        "refused_units": counts["refused"],
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
    }


def _make_vegetation_product(
    source: dict[str, object],
    source_file_sha256: str,
    units: tuple[MeasuredVegetationUnit, ...],
    receipt: OutcomeAccessStartReceipt,
    actual_read: dict[str, object],
) -> MeasuredVegetationSourceProduct:
    payload = _product_payload(
        source,
        source_file_sha256=source_file_sha256,
        profile=MEASURED_VEGETATION_SOURCE_PROFILE,
        units=units,
        receipt=receipt,
        actual_read=actual_read,
    )
    return MeasuredVegetationSourceProduct(
        canonical_json(payload),
        manifest_sha256(payload),
        units,
        _factory_token=_PRODUCT_FACTORY_TOKEN,
    )


def _make_pollen_product(
    source: dict[str, object],
    source_file_sha256: str,
    units: tuple[HeldoutPollenCountUnit, ...],
    receipt: OutcomeAccessStartReceipt,
    actual_read: dict[str, object],
) -> HeldoutPollenCountSourceProduct:
    payload = _product_payload(
        source,
        source_file_sha256=source_file_sha256,
        profile=HELDOUT_POLLEN_SOURCE_PROFILE,
        units=units,
        receipt=receipt,
        actual_read=actual_read,
    )
    return HeldoutPollenCountSourceProduct(
        canonical_json(payload),
        manifest_sha256(payload),
        units,
        _factory_token=_PRODUCT_FACTORY_TOKEN,
    )
