from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import cast

from ...contracts import canonical_json, finite_number, required_identity
from ..contracts import EvaluationSite, Support, digest, refuse
from ..observation_access import (
    HELDOUT_POLLEN_READER_PROFILE,
    MEASURED_VEGETATION_READER_PROFILE,
    OutcomeAccessStartReceipt,
)
from ..release import FinalEvaluationProtocol, ProtocolId
from .contracts import (
    HeldoutPollenCountSourceProduct,
    HeldoutPollenCountUnit,
    MeasuredVegetationSourceProduct,
    MeasuredVegetationUnit,
    UnitStatus,
    _expected_sites,
    _make_pollen_product,
    _make_vegetation_product,
    _unit_provenance,
)

MEASURED_VEGETATION_SOURCE_SCHEMA = "pollenomics-measured-vegetation-source.v1"
HELDOUT_POLLEN_SOURCE_SCHEMA = "pollenomics-heldout-pollen-count-source.v1"
_MAX_SOURCE_BYTES = 64 * 1024 * 1024
_COMMON_KEYS = frozenset(
    {
        "schema_version",
        "source_kind",
        "evidence_role",
        "reader_profile",
        "reader_code_sha256",
        "provider_id",
        "dataset_id",
        "release_id",
        "source_snapshot_sha256",
        "source_member",
        "source_member_sha256",
        "citation",
        "license",
        "rights_status",
        "rights_evidence_sha256",
        "release_disposition",
        "source_reference_id",
        "taxon_mapping_sha256",
        "taxon_mapping_review_id",
        "normalization_profile",
        "normalization_code_sha256",
        "taxa",
        "units",
    }
)
_VEGETATION_KEYS = _COMMON_KEYS | {"field_method"}
_POLLEN_KEYS = _COMMON_KEYS | {"counting_method"}
_UNIT_KEYS = frozenset(
    {
        "observation_id",
        "record_id",
        "site_id",
        "group_id",
        "block_id",
        "bin_id",
        "source_reference_id",
        "source_sample_id",
        "source_row_id",
        "support",
        "status",
        "reason_code",
        "values",
    }
)
_POLLEN_UNIT_KEYS = _UNIT_KEYS | {
    "pollen_channel_input_id",
    "pollen_channel_source_sha256",
    "counting_effort",
    "all_zero_count",
}
_SOURCE_READ_FACTORY_TOKEN = object()


@dataclass(frozen=True, init=False)
class SourceRead:
    source_kind: str
    path: Path
    content: bytes
    source_sha256: str

    def __init__(
        self,
        source_kind: str,
        path: Path,
        content: bytes,
        source_sha256: str,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _SOURCE_READ_FACTORY_TOKEN:
            refuse("Observation source reads require the governed filesystem reader")
        object.__setattr__(self, "source_kind", required_identity(source_kind))
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "source_sha256", digest(source_sha256))

    def receipt(self) -> dict[str, object]:
        return {
            "source_kind": self.source_kind,
            "path": str(self.path),
            "source_sha256": self.source_sha256,
            "bytes": len(self.content),
        }


def governed_reader_code_sha256() -> str:
    try:
        content = Path(__file__).read_bytes()
    except OSError as exc:
        refuse(f"Cannot identify governed observation reader code: {exc}")
    return hashlib.sha256(content).hexdigest()


def _read_source_bytes(path: Path, *, source_kind: str) -> SourceRead:
    if not isinstance(path, Path) or not path.is_absolute():
        refuse("Observation readers require an absolute typed source path")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            details = os.fstat(stream.fileno())
            if not stat.S_ISREG(details.st_mode) or details.st_size > _MAX_SOURCE_BYTES:
                refuse("Observation source must be a bounded regular file")
            content = stream.read(_MAX_SOURCE_BYTES + 1)
            if len(content) > _MAX_SOURCE_BYTES:
                refuse("Observation source exceeds its byte budget")
    except OSError as exc:
        refuse(f"Cannot read planned observation source: {exc}")
    return SourceRead(
        source_kind,
        path,
        content,
        hashlib.sha256(content).hexdigest(),
        _factory_token=_SOURCE_READ_FACTORY_TOKEN,
    )


def _payload(read: SourceRead, expected_sha256: str) -> dict[str, object]:
    if read.source_sha256 != digest(expected_sha256):
        refuse("Observation source bytes differ from their access-plan pin")
    try:
        text = read.content.decode("utf-8")
    except UnicodeDecodeError as exc:
        refuse(f"Observation source must be UTF-8: {exc}")
    if not text.endswith("\n") or text.count("\n") != 1:
        refuse("Observation source must contain one canonical JSON line")
    canonical = text[:-1]
    try:
        value = json.loads(canonical)
    except json.JSONDecodeError as exc:
        refuse(f"Malformed observation source JSON: {exc}")
    if not isinstance(value, dict) or canonical_json(value) != canonical:
        refuse("Observation source JSON is not canonical")
    return cast(dict[str, object], value)


def _source_header(
    value: dict[str, object],
    *,
    keys: frozenset[str],
    schema: str,
    kind: str,
    profile: str,
    reference: str,
    reader_code_sha256: str,
) -> tuple[str, ...]:
    if frozenset(value) != keys:
        refuse("Observation source fields differ from the exact schema")
    identities = (
        "provider_id",
        "dataset_id",
        "release_id",
        "source_member",
        "citation",
        "license",
        "taxon_mapping_review_id",
        "normalization_profile",
    )
    for field in identities:
        required_identity(cast(str, value.get(field)))
    for field in (
        "source_snapshot_sha256",
        "source_member_sha256",
        "taxon_mapping_sha256",
        "normalization_code_sha256",
        "reader_code_sha256",
    ):
        digest(cast(str, value.get(field)))
    if (
        value.get("schema_version") != schema
        or value.get("source_kind") != kind
        or value.get("evidence_role") != kind
        or value.get("reader_profile") != profile
        or value.get("reader_code_sha256") != reader_code_sha256
        or value.get("source_reference_id") != reference
        or value.get("rights_status") != "admitted"
        or value.get("release_disposition") != "admitted_for_final_evaluation"
    ):
        refuse("Observation source authority, role, reader or rights differ")
    taxa = value.get("taxa")
    if (
        not isinstance(taxa, list)
        or any(not isinstance(taxon, str) for taxon in taxa)
        or taxa != sorted(set(taxa))
    ):
        refuse("Observation source taxa must be sorted and unique")
    return tuple(cast(list[str], taxa))


def _support(value: object) -> Support:
    if not isinstance(value, dict):
        refuse("Observation source support must be an object")
    try:
        return Support(**value)
    except (TypeError, ValueError) as exc:
        refuse(f"Malformed observation support: {exc}")


def _unit_identity(
    row: dict[str, object], site: EvaluationSite, reference: str
) -> tuple[Support, UnitStatus, str | None, str]:
    for field in (
        "observation_id",
        "record_id",
        "site_id",
        "group_id",
        "block_id",
        "bin_id",
        "source_reference_id",
        "source_sample_id",
        "source_row_id",
    ):
        required_identity(cast(str, row.get(field)))
    expected = {
        "record_id": site.record_id,
        "site_id": site.site_id,
        "group_id": site.group_id,
        "block_id": site.block_id,
        "bin_id": site.bin_id,
        "source_reference_id": reference,
    }
    if any(row.get(field) != value for field, value in expected.items()):
        refuse("Observation source ownership or reference differs from scope")
    support = _support(row.get("support"))
    if site.support is None or support != site.support:
        refuse("Observation source support differs from the exact frozen scope")
    status, reason = row.get("status"), row.get("reason_code")
    if status not in {"available", "missing", "refused"} or (status == "available") != (
        reason is None
    ):
        refuse("Observation source terminal status or reason differs")
    if reason is not None:
        required_identity(cast(str, reason))
    return (
        support,
        cast(UnitStatus, status),
        cast(str | None, reason),
        cast(str, row["source_sample_id"]),
    )


def _values(value: object, taxa: tuple[str, ...]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != set(taxa):
        refuse("Observation values differ from the frozen taxon denominator")
    return cast(dict[str, object], value)


def _validate_withheld_assignments(receipt: OutcomeAccessStartReceipt) -> None:
    protocols: dict[str, FinalEvaluationProtocol] = {
        protocol.protocol_id: protocol
        for protocol in receipt.plan.prediction_product.protocols
    }
    for assignment in receipt.plan.assignments:
        if assignment.observation_kind != "heldout_pollen_counts":
            continue
        protocol = protocols[assignment.protocol_id]
        if not any(
            fold.fold_id == assignment.fold_id
            and assignment.record_id in fold.test_record_ids
            for fold in protocol.scope.folds
        ):
            refuse("Held-out pollen assignment is not an outer test target")
        selected = [
            row
            for row in receipt.plan.prediction_product.rows_for(
                cast(ProtocolId, assignment.protocol_id)
            )
            if row.fold_id == assignment.fold_id
            and row.record_id == assignment.record_id
            and row.target == "pollen_composition"
        ]
        if not selected or any(
            row.experiment != "all_target_pollen_withheld"
            or row.observed_pollen is not None
            for row in selected
        ):
            refuse("Locally assimilated pollen cannot be a withheld outcome")


def _read_measured_vegetation_source(
    read: SourceRead, receipt: OutcomeAccessStartReceipt
) -> MeasuredVegetationSourceProduct:
    locator = receipt.plan.sources.vegetation
    value = _payload(read, locator.expected_source_sha256)
    code = governed_reader_code_sha256()
    taxa = _source_header(
        value,
        keys=_VEGETATION_KEYS,
        schema=MEASURED_VEGETATION_SOURCE_SCHEMA,
        kind="independent_measured_vegetation",
        profile=MEASURED_VEGETATION_READER_PROFILE,
        reference=locator.source_reference_id,
        reader_code_sha256=code,
    )
    required_identity(cast(str, value["field_method"]))
    expected = _expected_sites(receipt, "independent_measured_vegetation")
    if taxa != receipt.plan.prediction_product.protocols[0].scope.taxa:
        refuse("Measured vegetation taxa differ from the evaluation scope")
    raw_units = value.get("units")
    if not isinstance(raw_units, list):
        refuse("Measured vegetation units must be an array")
    units: list[MeasuredVegetationUnit] = []
    for item in raw_units:
        if not isinstance(item, dict) or frozenset(item) != _UNIT_KEYS:
            refuse("Measured vegetation unit fields differ")
        row = cast(dict[str, object], item)
        observation_id = cast(str, row["observation_id"])
        site = expected.get(observation_id)
        if site is None:
            refuse("Measured vegetation names an unexpected observation")
        support, status, reason, sample = _unit_identity(
            row, site, locator.source_reference_id
        )
        values = _values(row["values"], taxa)
        parsed = {
            taxon: None if raw is None else finite_number(raw)
            for taxon, raw in values.items()
        }
        if any(
            number is not None and not 0 <= number <= 1 for number in parsed.values()
        ):
            refuse("Measured vegetation fractions must lie in [0,1] or be null")
        missing = any(number is None for number in parsed.values())
        present_total = sum(number for number in parsed.values() if number is not None)
        if (
            (status == "available" and (missing or abs(present_total - 1) > 1e-9))
            or (status == "missing" and not missing)
            or (
                status == "refused"
                and any(number is not None for number in parsed.values())
            )
            or present_total > 1 + 1e-9
        ):
            refuse("Measured vegetation status, missingness or closure differs")
        units.append(
            MeasuredVegetationUnit(
                observation_id,
                site.record_id,
                site.site_id,
                site.group_id,
                site.block_id,
                site.bin_id,
                locator.source_reference_id,
                sample,
                cast(str, row["source_row_id"]),
                *_unit_provenance(value, row),
                support,
                status,
                reason,
                tuple((taxon, parsed[taxon]) for taxon in taxa),
            )
        )
    if {unit.observation_id for unit in units} != set(expected) or len(units) != len(
        expected
    ):
        refuse("Measured vegetation omitted, duplicated or added source units")
    ordered = tuple(sorted(units, key=lambda unit: unit.observation_id))
    return _make_vegetation_product(
        value, read.source_sha256, ordered, receipt, read.receipt()
    )


def _pollen_channel(
    receipt: OutcomeAccessStartReceipt,
    observation_id: str,
    input_id: object,
    source_sha256: object,
) -> None:
    digest(cast(str, source_sha256))
    matched = False
    for protocol in receipt.plan.prediction_product.protocols:
        site = next(
            (
                item
                for item in protocol.scope.sites
                if item.pollen_observation_id == observation_id
            ),
            None,
        )
        if site is None:
            continue
        owner = next(
            (
                item
                for item in protocol.scope.observation_channels
                if item.record_id == site.record_id
            ),
            None,
        )
        if owner is None or not any(
            channel.input_id == input_id and channel.source_sha256 == source_sha256
            for channel in owner.pollen_channels
        ):
            refuse("Held-out pollen channel digest or ownership differs from scope")
        matched = True
    if not matched:
        refuse("Held-out pollen has no frozen observation-channel owner")


def _read_heldout_pollen_source(
    read: SourceRead, receipt: OutcomeAccessStartReceipt
) -> HeldoutPollenCountSourceProduct:
    locator = receipt.plan.sources.pollen
    value = _payload(read, locator.expected_source_sha256)
    code = governed_reader_code_sha256()
    taxa = _source_header(
        value,
        keys=_POLLEN_KEYS,
        schema=HELDOUT_POLLEN_SOURCE_SCHEMA,
        kind="heldout_pollen_counts",
        profile=HELDOUT_POLLEN_READER_PROFILE,
        reference=locator.source_reference_id,
        reader_code_sha256=code,
    )
    required_identity(cast(str, value["counting_method"]))
    _validate_withheld_assignments(receipt)
    expected = _expected_sites(receipt, "heldout_pollen_counts")
    if taxa != receipt.plan.prediction_product.protocols[0].scope.taxa:
        refuse("Held-out pollen taxa differ from the evaluation scope")
    raw_units = value.get("units")
    if not isinstance(raw_units, list):
        refuse("Held-out pollen units must be an array")
    units: list[HeldoutPollenCountUnit] = []
    for item in raw_units:
        if not isinstance(item, dict) or frozenset(item) != _POLLEN_UNIT_KEYS:
            refuse("Held-out pollen unit fields differ")
        row = cast(dict[str, object], item)
        observation_id = cast(str, row["observation_id"])
        site = expected.get(observation_id)
        if site is None:
            refuse("Held-out pollen names an unexpected observation")
        support, status, reason, sample = _unit_identity(
            row, site, locator.source_reference_id
        )
        _pollen_channel(
            receipt,
            observation_id,
            row["pollen_channel_input_id"],
            row["pollen_channel_source_sha256"],
        )
        raw_values = _values(row["values"], taxa)
        if any(
            raw is not None
            and (isinstance(raw, bool) or not isinstance(raw, int) or raw < 0)
            for raw in raw_values.values()
        ):
            refuse("Held-out pollen values must be nonnegative integer counts or null")
        parsed = {taxon: cast(int | None, raw_values[taxon]) for taxon in taxa}
        effort = row["counting_effort"]
        if effort is not None and (
            isinstance(effort, bool) or not isinstance(effort, int) or effort < 0
        ):
            refuse("Held-out pollen counting effort is invalid")
        missing = any(count is None for count in parsed.values())
        known_total = sum(count for count in parsed.values() if count is not None)
        all_zero = not missing and known_total == 0
        if (
            type(row["all_zero_count"]) is not bool
            or row["all_zero_count"] is not all_zero
            or (status == "available" and (missing or effort != known_total))
            or (
                status == "missing"
                and (not missing or (effort is not None and effort < known_total))
            )
            or (
                status == "refused"
                and (
                    any(count is not None for count in parsed.values())
                    or effort is not None
                )
            )
        ):
            refuse(
                "Held-out pollen status, effort, missingness or all-zero flag differs"
            )
        units.append(
            HeldoutPollenCountUnit(
                observation_id,
                site.record_id,
                site.site_id,
                site.group_id,
                site.block_id,
                site.bin_id,
                locator.source_reference_id,
                sample,
                cast(str, row["source_row_id"]),
                *_unit_provenance(value, row),
                cast(str, row["pollen_channel_input_id"]),
                cast(str, row["pollen_channel_source_sha256"]),
                support,
                status,
                reason,
                cast(int | None, effort),
                cast(bool, row["all_zero_count"]),
                tuple((taxon, parsed[taxon]) for taxon in taxa),
            )
        )
    if {unit.observation_id for unit in units} != set(expected) or len(units) != len(
        expected
    ):
        refuse("Held-out pollen omitted, duplicated or added source units")
    ordered = tuple(sorted(units, key=lambda unit: unit.observation_id))
    return _make_pollen_product(
        value, read.source_sha256, ordered, receipt, read.receipt()
    )
