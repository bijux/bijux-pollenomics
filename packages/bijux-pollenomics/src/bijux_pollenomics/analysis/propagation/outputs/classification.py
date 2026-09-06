"""Classification authority identity and queue validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from .codec import _refuse, _sha256
from .inputs import _json_object, _path_has_symlink_component, _read_identity_file
from .models import (
    _ACCEPTED_CLASSIFICATION_STATUSES,
    _CLASSIFICATION_ACCEPTED_QUEUE_NAME,
    _CLASSIFICATION_AUTHORITY,
    _CLASSIFICATION_MANIFEST_NAME,
    _CLASSIFICATION_MAPPING_STATUSES,
    _CLASSIFICATION_PAYLOAD_NAMES,
    _CLASSIFICATION_QUEUE_NAMES,
    _CLASSIFICATION_RELEASE_NAME,
    _CLASSIFICATION_SCHEMA_VERSIONS,
)
from .producer import _identity_manifest_entries


def _validate_classification_bundle_identity(
    bundle_root: Path,
    *,
    build_id: str,
    classification_contract_version: str,
    classification_review_digest: str,
    accepted_classification_mapping_count: int,
) -> None:
    # The product-owned authority is the trust anchor.  Caller pins remain
    # useful replay guards, but cannot authorize a coherently rehashed bundle.
    if (
        not bundle_root.is_absolute()
        or _path_has_symlink_component(bundle_root)
        or not bundle_root.is_dir()
    ):
        _refuse(
            "invalid_classification_identity",
            "classification_bundle_root must be an absolute non-symlink directory",
        )
    manifest_bytes = _read_identity_file(
        bundle_root / _CLASSIFICATION_MANIFEST_NAME,
        parent=bundle_root,
        reason_code="invalid_classification_identity",
    )
    observed_manifest_sha256 = _sha256(manifest_bytes)
    if observed_manifest_sha256 != _CLASSIFICATION_AUTHORITY.manifest_sha256:
        _refuse(
            "invalid_classification_authority",
            "classification manifest is not authorized by the propagation producer",
        )
    if observed_manifest_sha256 != classification_review_digest:
        _refuse(
            "invalid_classification_identity",
            "classification_review_digest does not match classification manifest bytes",
        )
    manifest = _json_object(
        manifest_bytes,
        reason_code="invalid_classification_identity",
        label="classification manifest",
    )
    if manifest.get("schema_version") != "classification-audit-manifest.v1":
        _refuse(
            "invalid_classification_identity",
            "classification manifest schema_version is not governed",
        )
    entries = _identity_manifest_entries(
        manifest,
        reason_code="invalid_classification_identity",
    )
    entry_names = {entry[0] for entry in entries}
    if len(entry_names) != len(_CLASSIFICATION_PAYLOAD_NAMES) or any(
        name not in _CLASSIFICATION_PAYLOAD_NAMES for name in entry_names
    ):
        _refuse(
            "invalid_classification_identity",
            "classification manifest does not contain the governed payload set",
        )
    expected_names = {_CLASSIFICATION_MANIFEST_NAME, *(entry[0] for entry in entries)}
    actual_names = {path.name for path in bundle_root.iterdir()}
    if actual_names != expected_names:
        _refuse(
            "invalid_classification_identity",
            "classification bundle inventory does not match its manifest",
        )
    payloads: dict[str, dict[str, Any]] = {}
    for name, expected_digest, expected_count in entries:
        payload_bytes = _read_identity_file(
            bundle_root / name,
            parent=bundle_root,
            reason_code="invalid_classification_identity",
        )
        if _sha256(payload_bytes) != expected_digest:
            _refuse(
                "invalid_classification_identity",
                f"classification payload digest changed: {name}",
            )
        payload = _json_object(
            payload_bytes,
            reason_code="invalid_classification_identity",
            label=f"classification payload {name}",
        )
        if payload.get("schema_version") != _CLASSIFICATION_SCHEMA_VERSIONS[name]:
            _refuse(
                "invalid_classification_identity",
                f"classification payload schema is not governed: {name}",
            )
        if payload.get("record_count") != expected_count:
            _refuse(
                "invalid_classification_identity",
                f"classification payload count changed: {name}",
            )
        if name in _CLASSIFICATION_QUEUE_NAMES:
            records = payload.get("records")
            if not isinstance(records, list) or len(records) != expected_count:
                _refuse(
                    "invalid_classification_reconciliation",
                    f"classification records do not match record_count: {name}",
                )
        if (
            payload.get("source_family") != manifest.get("source_family")
            or payload.get("source_snapshot_id") != manifest.get("source_snapshot_id")
            or payload.get("build_id") != manifest.get("build_id")
            or payload.get("classification_contract_version")
            != manifest.get("classification_contract_version")
            or payload.get("classification_contract_digest")
            != manifest.get("classification_contract_digest")
            or payload.get("classification_producer_id")
            != manifest.get("classification_producer_id")
            or payload.get("classification_producer_version")
            != manifest.get("classification_producer_version")
            or payload.get("classification_producer_digest")
            != manifest.get("classification_producer_digest")
        ):
            _refuse(
                "invalid_classification_identity",
                f"classification payload identity changed: {name}",
            )
        payloads[name] = payload
    digest_input = "".join(
        f"{name}\0{digest}\0{count}\n" for name, digest, count in entries
    ).encode("utf-8")
    if manifest.get("bundle_digest") != _sha256(digest_input):
        _refuse(
            "invalid_classification_identity",
            "classification bundle digest does not reconcile",
        )
    if (
        manifest.get("build_id") != build_id
        or manifest.get("classification_contract_version")
        != classification_contract_version
        or manifest.get("source_family") != _CLASSIFICATION_AUTHORITY.source_family
        or manifest.get("source_snapshot_id")
        != _CLASSIFICATION_AUTHORITY.source_snapshot_id
        or manifest.get("build_id") != _CLASSIFICATION_AUTHORITY.build_id
        or manifest.get("classification_contract_version")
        != _CLASSIFICATION_AUTHORITY.contract_version
        or manifest.get("classification_contract_digest")
        != _CLASSIFICATION_AUTHORITY.contract_digest
        or manifest.get("classification_producer_id")
        != _CLASSIFICATION_AUTHORITY.producer_id
        or manifest.get("classification_producer_version")
        != _CLASSIFICATION_AUTHORITY.producer_version
        or manifest.get("classification_producer_digest")
        != _CLASSIFICATION_AUTHORITY.producer_digest
    ):
        _refuse(
            "invalid_classification_identity",
            "classification manifest does not match caller and product authority pins",
        )
    release = payloads.get(_CLASSIFICATION_RELEASE_NAME)
    accepted_queue = payloads.get(_CLASSIFICATION_ACCEPTED_QUEUE_NAME)
    if release is None or accepted_queue is None:
        _refuse(
            "invalid_classification_identity",
            "classification release metadata and accepted queue must be manifested",
        )
    if (
        release.get("schema_version") != "classification-release-metadata.v1"
        or release.get("build_id") != build_id
        or release.get("classification_contract_version")
        != classification_contract_version
        or accepted_queue.get("build_id") != build_id
        or accepted_queue.get("classification_contract_version")
        != classification_contract_version
    ):
        _refuse(
            "invalid_classification_identity",
            "classification release and accepted queue do not match pinned identities",
        )
    accepted_records = accepted_queue.get("records")
    if not isinstance(accepted_records, list):
        _refuse(
            "invalid_classification_identity",
            "classification accepted queue records must be an array",
        )
    concept_denominators = payloads["concept_denominators.json"]
    observation_denominators = payloads["observation_denominators.json"]
    observation_memberships = payloads["observation_memberships.json"]
    not_applicable_queue = payloads["not_applicable_mapping_queue.json"]
    review_queue = payloads["review_queue.json"]
    unmapped_queue = payloads["unmapped_mapping_queue.json"]
    country_partitions = payloads["country_partitions.json"]
    country_partition_count = 0
    for field in ("source_country", "governed_country", "country_relation"):
        country_partition_records = country_partitions.get(field)
        if not isinstance(country_partition_records, list) or any(
            not isinstance(record, Mapping) for record in country_partition_records
        ):
            _refuse(
                "invalid_classification_reconciliation",
                f"classification country partition is invalid: {field}",
            )
        country_partition_count += len(country_partition_records)
    concept_status_counts = _classification_status_counts(
        concept_denominators.get("mapping_status_counts"),
        label="concept mapping_status_counts",
    )
    observation_status_counts = _classification_status_counts(
        observation_denominators.get("mapping_status_counts"),
        label="observation mapping_status_counts",
    )
    concept_count = _classification_count(
        concept_denominators.get("record_count"), label="concept record_count"
    )
    observation_count = _classification_count(
        observation_denominators.get("record_count"),
        label="observation record_count",
    )
    accepted_count = len(accepted_records)
    unmapped_count = _classification_count(
        unmapped_queue.get("record_count"), label="unmapped queue record_count"
    )
    not_applicable_count = _classification_count(
        not_applicable_queue.get("record_count"),
        label="not-applicable queue record_count",
    )
    review_count = _classification_count(
        review_queue.get("record_count"), label="review queue record_count"
    )
    observation_records = cast(list[object], observation_memberships["records"])
    observed_observation_statuses: Counter[str] = Counter()
    for record in observation_records:
        if not isinstance(record, Mapping):
            _refuse(
                "invalid_classification_reconciliation",
                "classification observation membership must be an object",
            )
        status = record.get("mapping_status")
        if status not in _CLASSIFICATION_MAPPING_STATUSES:
            _refuse(
                "invalid_classification_reconciliation",
                "classification observation membership status is not governed",
            )
        observed_observation_statuses[str(status)] += 1
    if (
        concept_denominators.get("total_concept_count") != concept_count
        or sum(concept_status_counts.values()) != concept_count
        or concept_denominators.get("accepted_queue_count") != accepted_count
        or accepted_count
        != concept_status_counts["accepted"]
        + concept_status_counts["accepted_qualified"]
        or concept_denominators.get("unmapped_queue_count") != unmapped_count
        or unmapped_count != concept_status_counts["unmapped"]
        or concept_denominators.get("not_applicable_queue_count")
        != not_applicable_count
        or not_applicable_count != concept_status_counts["not_applicable"]
        or concept_denominators.get("review_queue_count") != review_count
        or review_count
        != concept_status_counts["unmapped"]
        + concept_status_counts["contested"]
        + concept_status_counts["refused"]
        or observation_denominators.get("total_observation_count") != observation_count
        or sum(observation_status_counts.values()) != observation_count
        or observation_memberships.get("record_count") != observation_count
        or dict(observed_observation_statuses)
        != {
            status: count
            for status, count in observation_status_counts.items()
            if count
        }
        or country_partitions.get("record_count") != country_partition_count
    ):
        _refuse(
            "invalid_classification_reconciliation",
            "classification queue and denominator counts do not reconcile",
        )
    for records, allowed_statuses, label in (
        (accepted_records, _ACCEPTED_CLASSIFICATION_STATUSES, "accepted"),
        (cast(list[object], unmapped_queue["records"]), {"unmapped"}, "unmapped"),
        (
            cast(list[object], not_applicable_queue["records"]),
            {"not_applicable"},
            "not-applicable",
        ),
        (
            cast(list[object], review_queue["records"]),
            {"unmapped", "contested", "refused"},
            "review",
        ),
    ):
        _validate_classification_queue_statuses(
            records, allowed_statuses=allowed_statuses, label=label
        )
    review_records = cast(list[object], review_queue["records"])
    not_applicable_records = cast(list[object], not_applicable_queue["records"])
    unmapped_records = cast(list[object], unmapped_queue["records"])
    partition_records = [*accepted_records, *not_applicable_records, *review_records]
    partition_statuses = Counter(
        str(cast(Mapping[str, object], record)["mapping_status"])
        for record in partition_records
    )
    partition_ids = [
        cast(Mapping[str, object], record).get("classification_concept_id")
        for record in partition_records
    ]
    unmapped_ids = {
        cast(Mapping[str, object], record).get("classification_concept_id")
        for record in unmapped_records
    }
    review_unmapped_ids = {
        cast(Mapping[str, object], record).get("classification_concept_id")
        for record in review_records
        if cast(Mapping[str, object], record).get("mapping_status") == "unmapped"
    }
    if (
        dict(partition_statuses)
        != {status: count for status, count in concept_status_counts.items() if count}
        or any(
            not isinstance(identifier, str) or not identifier
            for identifier in partition_ids
        )
        or len(partition_ids) != len(set(partition_ids))
        or unmapped_ids != review_unmapped_ids
    ):
        _refuse(
            "invalid_classification_reconciliation",
            "classification concept queues do not form the declared partition",
        )
    embedded_count = release.get("accepted_mapping_count")
    if (
        isinstance(embedded_count, bool)
        or not isinstance(embedded_count, int)
        or embedded_count != accepted_classification_mapping_count
        or embedded_count != _CLASSIFICATION_AUTHORITY.accepted_mapping_count
        or accepted_queue.get("record_count") != embedded_count
        or len(accepted_records) != embedded_count
        or release.get("reviewed_accepted_mapping_count") != embedded_count
        or release.get("human_approval_synthesized") is not False
        or release.get("release_eligible_mapping_count")
        != sum(
            cast(Mapping[str, object], record).get("release_eligible") is True
            for record in accepted_records
        )
        or release.get("unmapped_mapping_count") != unmapped_count
        or release.get("not_applicable_mapping_count") != not_applicable_count
    ):
        _refuse(
            "invalid_classification_reconciliation",
            "accepted classification count does not match the verified bundle",
        )
    for record in accepted_records:
        if not isinstance(record, Mapping):
            _refuse(
                "invalid_classification_reconciliation",
                "accepted classification record must be an object",
            )
        citations = record.get("citation_reference_ids")
        if (
            record.get("review_complete") is not True
            or not all(
                isinstance(record.get(field), str) and bool(record.get(field))
                for field in (
                    "mapping_version",
                    "reviewer_id",
                    "decision_date",
                    "accepted_taxon_concept_id",
                )
            )
            or not isinstance(citations, list)
            or not citations
            or any(
                not isinstance(citation, str) or not citation for citation in citations
            )
        ):
            _refuse(
                "invalid_classification_reconciliation",
                "accepted classification record lacks complete governed review evidence",
            )


def _classification_count(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _refuse("invalid_classification_reconciliation", f"{label} is invalid")
    return value


def _classification_status_counts(value: object, *, label: str) -> dict[str, int]:
    if not isinstance(value, Mapping):
        _refuse(
            "invalid_classification_reconciliation",
            f"{label} does not contain the governed status partition",
        )
    status_counts = cast(Mapping[str, object], value)
    status_names = set(status_counts)
    if len(status_names) != len(_CLASSIFICATION_MAPPING_STATUSES) or any(
        status not in _CLASSIFICATION_MAPPING_STATUSES for status in status_names
    ):
        _refuse(
            "invalid_classification_reconciliation",
            f"{label} does not contain the governed status partition",
        )
    return {
        status: _classification_count(status_counts[status], label=f"{label}.{status}")
        for status in sorted(_CLASSIFICATION_MAPPING_STATUSES)
    }


def _validate_classification_queue_statuses(
    records: Sequence[object],
    *,
    allowed_statuses: set[str] | frozenset[str],
    label: str,
) -> None:
    for record in records:
        if not isinstance(record, Mapping) or record.get("mapping_status") not in (
            allowed_statuses
        ):
            _refuse(
                "invalid_classification_reconciliation",
                f"classification {label} queue contains an invalid status",
            )
