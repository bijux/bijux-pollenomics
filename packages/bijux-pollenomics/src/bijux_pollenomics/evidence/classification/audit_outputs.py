from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

__all__ = [
    "ClassificationAuditMaterializationResult",
    "ClassificationAuditOutputPaths",
    "ClassificationAuditRefusalError",
    "materialize_classification_audit",
]

_COUNTRY_PARTITION = ("SE", "DK", "NO", "FI", "UNASSIGNED")
_MAPPING_STATUSES = (
    "accepted",
    "accepted_qualified",
    "unmapped",
    "contested",
    "not_applicable",
    "refused",
)
_ACCEPTED_STATUSES = frozenset({"accepted", "accepted_qualified"})
_REVIEW_STATUSES = frozenset({"unmapped", "contested", "refused"})
_ZERO_ACCEPTED_REASON_CODES = (
    "accepted_mapping_not_available",
    "mapping_evidence_not_available",
    "human_review_not_available",
)
_OUTPUT_NAMES = (
    "accepted_mapping_queue.json",
    "concept_denominators.json",
    "country_partitions.json",
    "not_applicable_mapping_queue.json",
    "observation_memberships.json",
    "observation_denominators.json",
    "release_metadata.json",
    "review_queue.json",
    "unmapped_mapping_queue.json",
)
_MANIFEST_NAME = "manifest.json"
_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")


class ClassificationAuditRefusalError(ValueError):
    """Refuse an unsafe or scientifically inconsistent audit publication."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class ClassificationAuditOutputPaths:
    """Every governed output path required for one atomic audit bundle."""

    output_root: Path
    accepted_mapping_queue: Path
    concept_denominators: Path
    country_partitions: Path
    not_applicable_mapping_queue: Path
    observation_memberships: Path
    observation_denominators: Path
    release_metadata: Path
    review_queue: Path
    unmapped_mapping_queue: Path
    manifest: Path

    @classmethod
    def under(cls, output_root: Path) -> ClassificationAuditOutputPaths:
        """Declare the complete fixed path set below one output root."""
        output_root = Path(output_root)
        return cls(
            output_root=output_root,
            accepted_mapping_queue=output_root / "accepted_mapping_queue.json",
            concept_denominators=output_root / "concept_denominators.json",
            country_partitions=output_root / "country_partitions.json",
            not_applicable_mapping_queue=(
                output_root / "not_applicable_mapping_queue.json"
            ),
            observation_memberships=output_root / "observation_memberships.json",
            observation_denominators=output_root / "observation_denominators.json",
            release_metadata=output_root / "release_metadata.json",
            review_queue=output_root / "review_queue.json",
            unmapped_mapping_queue=output_root / "unmapped_mapping_queue.json",
            manifest=output_root / _MANIFEST_NAME,
        )

    def payload_paths(self) -> tuple[Path, ...]:
        return (
            self.accepted_mapping_queue,
            self.concept_denominators,
            self.country_partitions,
            self.not_applicable_mapping_queue,
            self.observation_memberships,
            self.observation_denominators,
            self.release_metadata,
            self.review_queue,
            self.unmapped_mapping_queue,
        )


@dataclass(frozen=True)
class ClassificationAuditMaterializationResult:
    """Observable disposition and identity for one audit materialization."""

    output_root: Path
    disposition: str
    manifest_sha256: str
    file_count: int
    concept_count: int
    observation_count: int
    accepted_mapping_count: int
    release_status: str


def materialize_classification_audit(
    accounting: Mapping[str, object],
    *,
    paths: ClassificationAuditOutputPaths,
    allowed_output_parent: Path,
    classification_contract_version: str,
    classification_contract_digest: str,
) -> ClassificationAuditMaterializationResult:
    """Reconcile and atomically publish a deterministic classification audit."""
    _validate_output_paths(paths, Path(allowed_output_parent))
    classification_contract_version = _required_text(
        classification_contract_version,
        field_name="classification_contract_version",
    )
    classification_contract_digest = _required_digest(
        classification_contract_digest,
        field_name="classification_contract_digest",
    )
    concepts, memberships = _validated_accounting_rows(accounting)
    _validate_accounting_reconciliation(accounting, concepts, memberships)
    payloads, release_status = _build_payloads(
        accounting=accounting,
        concepts=concepts,
        memberships=memberships,
        classification_contract_version=classification_contract_version,
        classification_contract_digest=classification_contract_digest,
    )
    serialized_payloads = {
        name: _canonical_json_bytes(payload) for name, payload in payloads.items()
    }
    manifest = _build_manifest(
        accounting=accounting,
        serialized_payloads=serialized_payloads,
        classification_contract_version=classification_contract_version,
        classification_contract_digest=classification_contract_digest,
    )
    manifest_bytes = _canonical_json_bytes(manifest)
    expected_files = {**serialized_payloads, _MANIFEST_NAME: manifest_bytes}
    disposition = _publish_atomically(
        output_root=paths.output_root,
        allowed_output_parent=Path(allowed_output_parent),
        expected_files=expected_files,
    )
    accepted_count = sum(
        str(row["mapping_status"]) in _ACCEPTED_STATUSES for row in concepts
    )
    return ClassificationAuditMaterializationResult(
        output_root=paths.output_root,
        disposition=disposition,
        manifest_sha256=_sha256(manifest_bytes),
        file_count=len(expected_files),
        concept_count=len(concepts),
        observation_count=len(memberships),
        accepted_mapping_count=accepted_count,
        release_status=release_status,
    )


def _validated_accounting_rows(
    accounting: Mapping[str, object],
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    if accounting.get("schema_version") != "neotoma-classification-accounting.v1":
        _refuse(
            "unsupported_accounting_schema",
            "classification audit requires neotoma-classification-accounting.v1",
        )
    if accounting.get("source_family") != "neotoma":
        _refuse(
            "unsupported_source_family",
            "classification audit requires source-native Neotoma accounting",
        )
    _required_text(
        accounting.get("source_snapshot_id"), field_name="source_snapshot_id"
    )
    _required_text(accounting.get("build_id"), field_name="build_id")
    concepts = _mapping_sequence(accounting.get("concepts"), field_name="concepts")
    memberships = _mapping_sequence(
        accounting.get("observation_memberships"),
        field_name="observation_memberships",
    )
    concept_ids: set[str] = set()
    concept_statuses: dict[str, str] = {}
    for concept in concepts:
        concept_id = _required_text(
            concept.get("classification_concept_id"),
            field_name="classification_concept_id",
        )
        if concept_id in concept_ids:
            _refuse("duplicate_concept_id", f"duplicate concept: {concept_id}")
        concept_ids.add(concept_id)
        status = str(concept.get("mapping_status", ""))
        if status not in _MAPPING_STATUSES:
            _refuse("invalid_mapping_status", f"unsupported status: {status}")
        concept_statuses[concept_id] = status
        observation_count = concept.get("observation_count")
        if (
            isinstance(observation_count, bool)
            or not isinstance(observation_count, int)
            or observation_count < 0
        ):
            _refuse(
                "invalid_accounting_reconciliation",
                f"concept {concept_id} has invalid observation_count",
            )
    observation_ids: set[str] = set()
    for membership in memberships:
        observation_id = _required_text(
            membership.get("observation_id"), field_name="observation_id"
        )
        concept_id = _required_text(
            membership.get("classification_concept_id"),
            field_name="classification_concept_id",
        )
        if observation_id in observation_ids:
            _refuse(
                "duplicate_observation_membership",
                f"duplicate observation membership: {observation_id}",
            )
        observation_ids.add(observation_id)
        if concept_id not in concept_ids:
            _refuse(
                "orphan_concept_membership",
                f"observation references unknown concept: {concept_id}",
            )
        status = str(membership.get("mapping_status", ""))
        if status not in _MAPPING_STATUSES:
            _refuse("invalid_mapping_status", f"unsupported status: {status}")
        if status != concept_statuses[concept_id]:
            _refuse(
                "invalid_accounting_reconciliation",
                f"membership status conflicts with concept: {observation_id}",
            )
        for field_name in ("source_country_code", "governed_country_code"):
            country_code = str(membership.get(field_name, ""))
            if country_code not in _COUNTRY_PARTITION:
                _refuse(
                    "invalid_country_partition",
                    f"{field_name} is outside the governed partition: {country_code}",
                )
    return (
        tuple(sorted(concepts, key=lambda row: str(row["classification_concept_id"]))),
        tuple(sorted(memberships, key=lambda row: str(row["observation_id"]))),
    )


def _validate_accounting_reconciliation(
    accounting: Mapping[str, object],
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> None:
    reconciliation = accounting.get("reconciliation")
    if not isinstance(reconciliation, Mapping):
        _refuse(
            "invalid_accounting_reconciliation",
            "accounting requires a reconciliation object",
        )
    assert isinstance(reconciliation, Mapping)
    expected_counts = {
        "unique_observation_count": len(memberships),
        "observation_membership_count": len(memberships),
        "concept_count": len(concepts),
        "concept_observation_count_sum": len(memberships),
        "mapping_status_concept_count_sum": len(concepts),
        "mapping_status_observation_count_sum": len(memberships),
        "accepted_concept_count": sum(
            str(row["mapping_status"]) in _ACCEPTED_STATUSES for row in concepts
        ),
        "release_eligible_concept_count": sum(
            bool(row.get("release_eligible", False)) for row in concepts
        ),
    }
    for field_name, expected_count in expected_counts.items():
        if reconciliation.get(field_name) != expected_count:
            _refuse(
                "invalid_accounting_reconciliation",
                f"{field_name} does not reconcile to {expected_count}",
            )
    membership_counts = Counter(
        str(row["classification_concept_id"]) for row in memberships
    )
    for concept in concepts:
        concept_id = str(concept["classification_concept_id"])
        if concept.get("observation_count") != membership_counts[concept_id]:
            _refuse(
                "invalid_accounting_reconciliation",
                f"concept observation count does not reconcile: {concept_id}",
            )
    expected_country_partitions = _country_partitions(memberships)
    partitions = accounting.get("partitions")
    if not isinstance(partitions, Mapping):
        _refuse(
            "invalid_accounting_reconciliation",
            "accounting requires partition tables",
        )
    assert isinstance(partitions, Mapping)
    concept_status_counts = Counter(str(row["mapping_status"]) for row in concepts)
    observation_status_counts = Counter(
        str(row["mapping_status"]) for row in memberships
    )
    expected_status_partition = tuple(
        {
            "value": status,
            "concept_count": concept_status_counts[status],
            "observation_count": observation_status_counts[status],
        }
        for status in _MAPPING_STATUSES
    )
    if _canonical_json_bytes(partitions.get("mapping_status")) != _canonical_json_bytes(
        expected_status_partition
    ):
        _refuse(
            "invalid_accounting_reconciliation",
            "source accounting mapping-status partition does not reconcile",
        )
    for key, expected_partition in expected_country_partitions.items():
        if _canonical_json_bytes(partitions.get(key)) != _canonical_json_bytes(
            expected_partition
        ):
            _refuse(
                "invalid_accounting_reconciliation",
                f"source accounting partition does not reconcile: {key}",
            )


def _build_payloads(
    *,
    accounting: Mapping[str, object],
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    classification_contract_version: str,
    classification_contract_digest: str,
) -> tuple[dict[str, dict[str, object]], str]:
    status_concepts = Counter(str(row["mapping_status"]) for row in concepts)
    status_observations = Counter(str(row["mapping_status"]) for row in memberships)
    queue_rows = tuple(_queue_row(row) for row in concepts)
    accepted_rows = tuple(
        row for row in queue_rows if row["mapping_status"] in _ACCEPTED_STATUSES
    )
    unmapped_rows = tuple(
        row for row in queue_rows if row["mapping_status"] == "unmapped"
    )
    not_applicable_rows = tuple(
        row for row in queue_rows if row["mapping_status"] == "not_applicable"
    )
    review_rows = tuple(
        row
        for row in queue_rows
        if row["mapping_status"] in _REVIEW_STATUSES
        or (row["mapping_status"] in _ACCEPTED_STATUSES and not row["review_complete"])
    )
    reviewed_accepted_count = sum(bool(row["review_complete"]) for row in accepted_rows)
    release_eligible_count = sum(bool(row["release_eligible"]) for row in accepted_rows)
    source_review = accounting.get("review")
    if not isinstance(source_review, Mapping):
        _refuse(
            "invalid_accounting_schema",
            "classification accounting requires review metadata",
        )
    assert isinstance(source_review, Mapping)
    release_reason_codes: tuple[str, ...]
    if not accepted_rows:
        release_status = "refused"
        release_reason_codes = _ZERO_ACCEPTED_REASON_CODES
    elif reviewed_accepted_count != len(accepted_rows):
        release_status = "refused"
        release_reason_codes = ("accepted_mapping_review_incomplete",)
    else:
        release_status = "review_required"
        release_reason_codes = ("independent_scientific_review_required",)
    common = {
        "source_family": accounting["source_family"],
        "source_snapshot_id": accounting["source_snapshot_id"],
        "build_id": accounting["build_id"],
        "classification_contract_version": classification_contract_version,
        "classification_contract_digest": classification_contract_digest,
    }
    country_partitions = _country_partitions(memberships)
    return (
        {
            "concept_denominators.json": {
                "schema_version": "classification-concept-denominators.v1",
                **common,
                "record_count": len(concepts),
                "total_concept_count": len(concepts),
                "mapping_status_counts": {
                    status: status_concepts[status] for status in _MAPPING_STATUSES
                },
                "accepted_queue_count": len(accepted_rows),
                "unmapped_queue_count": len(unmapped_rows),
                "not_applicable_queue_count": len(not_applicable_rows),
                "review_queue_count": len(review_rows),
            },
            "observation_denominators.json": {
                "schema_version": "classification-observation-denominators.v1",
                **common,
                "record_count": len(memberships),
                "total_observation_count": len(memberships),
                "mapping_status_counts": {
                    status: status_observations[status] for status in _MAPPING_STATUSES
                },
                "source_country_counts": _observation_country_counts(
                    memberships, "source_country_code"
                ),
                "governed_country_counts": _observation_country_counts(
                    memberships, "governed_country_code"
                ),
            },
            "observation_memberships.json": {
                "schema_version": "classification-observation-memberships.v1",
                **common,
                "record_count": len(memberships),
                "records": tuple(dict(row) for row in memberships),
            },
            "country_partitions.json": {
                "schema_version": "classification-country-partitions.v1",
                **common,
                "record_count": len(_COUNTRY_PARTITION) * 2
                + len(_COUNTRY_PARTITION) ** 2,
                **country_partitions,
            },
            "accepted_mapping_queue.json": _queue_payload(
                "classification-accepted-mapping-queue.v1",
                common,
                accepted_rows,
                queue_semantics="accepted and accepted-qualified source concepts",
            ),
            "unmapped_mapping_queue.json": _queue_payload(
                "classification-unmapped-mapping-queue.v1",
                common,
                unmapped_rows,
                queue_semantics="source concepts without an accepted mapping",
            ),
            "not_applicable_mapping_queue.json": _queue_payload(
                "classification-not-applicable-mapping-queue.v1",
                common,
                not_applicable_rows,
                queue_semantics="explicit non-biological source concepts",
            ),
            "review_queue.json": {
                **_queue_payload(
                    "classification-review-queue.v1",
                    common,
                    review_rows,
                    queue_semantics=(
                        "unmapped, contested, refused, or incompletely reviewed "
                        "accepted source concepts"
                    ),
                ),
                "unresolved_concept_ids": source_review.get(
                    "unresolved_concept_ids", ()
                ),
                "country_release_blockers": source_review.get(
                    "country_release_blockers", ()
                ),
                "integrity_blockers": source_review.get("integrity_blockers", ()),
            },
            "release_metadata.json": {
                "schema_version": "classification-release-metadata.v1",
                **common,
                "status_namespace": "classification_release",
                "release_status": release_status,
                "public_release_allowed": False,
                "release_reason_codes": release_reason_codes,
                "accepted_mapping_count": len(accepted_rows),
                "reviewed_accepted_mapping_count": reviewed_accepted_count,
                "release_eligible_mapping_count": release_eligible_count,
                "unmapped_mapping_count": len(unmapped_rows),
                "not_applicable_mapping_count": len(not_applicable_rows),
                "human_approval_synthesized": False,
                "record_count": 1,
            },
        },
        release_status,
    )


def _queue_row(concept: Mapping[str, object]) -> dict[str, object]:
    citations = tuple(
        sorted(
            str(value)
            for value in _sequence_values(
                concept.get("evidence_reference_ids"),
                field_name="evidence_reference_ids",
            )
        )
    )
    roles = tuple(
        sorted(
            str(value)
            for value in _sequence_values(
                concept.get("role_ids"), field_name="role_ids"
            )
        )
    )
    mapping_version = concept.get("crosswalk_version")
    reviewer_id = concept.get("reviewer_id")
    decision_date = concept.get("decision_date")
    accepted_taxon_concept_id = concept.get("accepted_taxon_concept_id")
    status = str(concept["mapping_status"])
    review_complete = (
        status in _ACCEPTED_STATUSES
        and all(
            _nonempty(value)
            for value in (
                mapping_version,
                reviewer_id,
                decision_date,
                accepted_taxon_concept_id,
            )
        )
        and bool(citations)
    )
    return {
        "classification_concept_id": concept["classification_concept_id"],
        "source_family": concept.get("source_family"),
        "source_variable_id": concept.get("source_variable_id"),
        "source_taxon_id": concept.get("source_taxon_id"),
        "source_reported_name": concept.get("source_reported_name"),
        "source_element_type": concept.get("source_element_type"),
        "source_unit": concept.get("source_unit"),
        "mapping_status": status,
        "mapping_reason_code": concept.get("mapping_reason_code"),
        "accepted_taxon_concept_id": accepted_taxon_concept_id,
        "accepted_taxon_name": concept.get("accepted_taxon_name"),
        "primary_group_id": concept.get("primary_group_id"),
        "primary_subgroup_id": concept.get("primary_subgroup_id"),
        "role_ids": roles,
        "mapping_version": mapping_version,
        "reviewer_id": reviewer_id,
        "decision_date": decision_date,
        "citation_reference_ids": citations,
        "review_complete": review_complete,
        "release_eligible": bool(concept.get("release_eligible", False))
        and review_complete,
        "release_blocker_reason_codes": tuple(
            sorted(
                str(value)
                for value in _sequence_values(
                    concept.get("release_blocker_reason_codes", ()),
                    field_name="release_blocker_reason_codes",
                )
            )
        ),
        "source_country_codes": tuple(
            _sequence_values(
                concept.get("source_country_codes", ()),
                field_name="source_country_codes",
            )
        ),
        "governed_country_codes": tuple(
            _sequence_values(
                concept.get("governed_country_codes", ()),
                field_name="governed_country_codes",
            )
        ),
        "observation_count": concept["observation_count"],
    }


def _queue_payload(
    schema_version: str,
    common: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    *,
    queue_semantics: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        **common,
        "queue_semantics": queue_semantics,
        "record_count": len(rows),
        "records": tuple(rows),
    }


def _country_partitions(
    memberships: Sequence[Mapping[str, object]],
) -> dict[str, tuple[dict[str, object], ...]]:
    concept_memberships: dict[tuple[str, str], set[str]] = defaultdict(set)
    observation_counts: Counter[tuple[str, str]] = Counter()
    for row in memberships:
        concept_id = str(row["classification_concept_id"])
        for dimension in ("source_country", "governed_country"):
            code = str(row[f"{dimension}_code"])
            concept_memberships[(dimension, code)].add(concept_id)
            observation_counts[(dimension, code)] += 1
    source_rows = tuple(
        {
            "country_code": code,
            "concept_membership_count": len(
                concept_memberships[("source_country", code)]
            ),
            "observation_count": observation_counts[("source_country", code)],
        }
        for code in _COUNTRY_PARTITION
    )
    governed_rows = tuple(
        {
            "country_code": code,
            "concept_membership_count": len(
                concept_memberships[("governed_country", code)]
            ),
            "observation_count": observation_counts[("governed_country", code)],
        }
        for code in _COUNTRY_PARTITION
    )
    relation_observations = Counter(
        (
            str(row["source_country_code"]),
            str(row["governed_country_code"]),
        )
        for row in memberships
    )
    relation_concepts: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in memberships:
        pair = (
            str(row["source_country_code"]),
            str(row["governed_country_code"]),
        )
        relation_concepts[pair].add(str(row["classification_concept_id"]))
    relation_rows = tuple(
        {
            "source_country_code": source,
            "governed_country_code": governed,
            "concept_membership_count": len(relation_concepts[(source, governed)]),
            "observation_count": relation_observations[(source, governed)],
        }
        for source in _COUNTRY_PARTITION
        for governed in _COUNTRY_PARTITION
    )
    return {
        "source_country": source_rows,
        "governed_country": governed_rows,
        "country_relation": relation_rows,
    }


def _observation_country_counts(
    memberships: Sequence[Mapping[str, object]], field_name: str
) -> dict[str, int]:
    counts = Counter(str(row[field_name]) for row in memberships)
    return {code: counts[code] for code in _COUNTRY_PARTITION}


def _build_manifest(
    *,
    accounting: Mapping[str, object],
    serialized_payloads: Mapping[str, bytes],
    classification_contract_version: str,
    classification_contract_digest: str,
) -> dict[str, object]:
    entries = tuple(
        {
            "path": name,
            "sha256": _sha256(serialized_payloads[name]),
            "record_count": _payload_record_count(serialized_payloads[name]),
        }
        for name in sorted(serialized_payloads)
    )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    return {
        "schema_version": "classification-audit-manifest.v1",
        "source_family": accounting["source_family"],
        "source_snapshot_id": accounting["source_snapshot_id"],
        "build_id": accounting["build_id"],
        "classification_contract_version": classification_contract_version,
        "classification_contract_digest": classification_contract_digest,
        "input_accounting_sha256": _sha256(_canonical_json_bytes(accounting)),
        "bundle_digest": _sha256(digest_input),
        "payload_file_count": len(entries),
        "files": entries,
    }


def _payload_record_count(payload_bytes: bytes) -> int:
    payload: object = json.loads(payload_bytes)
    if not isinstance(payload, dict):
        _refuse("invalid_output_reconciliation", "audit payload must be an object")
    assert isinstance(payload, dict)
    count = payload.get("record_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        _refuse(
            "invalid_output_reconciliation",
            "audit payload requires a non-negative record_count",
        )
    assert isinstance(count, int)
    return count


def _publish_atomically(
    *,
    output_root: Path,
    allowed_output_parent: Path,
    expected_files: Mapping[str, bytes],
) -> str:
    lock_path = allowed_output_parent / f".{output_root.name}.materialization.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ClassificationAuditRefusalError(
            "materialization_lock_exists",
            f"another materialization owns {lock_path.name}",
        ) from error
    try:
        os.close(descriptor)
        if output_root.exists() or output_root.is_symlink():
            if _existing_bundle_is_identical(output_root, expected_files):
                return "unchanged"
            _refuse(
                "non_identical_overwrite_refused",
                "existing audit output is not byte-identical",
            )
        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f".{output_root.name}.staging-",
                dir=allowed_output_parent,
            )
        )
        try:
            for name in sorted(expected_files):
                with (staging_root / name).open("xb") as stream:
                    stream.write(expected_files[name])
                    stream.flush()
                    os.fsync(stream.fileno())
            if output_root.exists() or output_root.is_symlink():
                _refuse(
                    "non_identical_overwrite_refused",
                    "audit output appeared while staging",
                )
            staging_root.rename(output_root)
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root)
            raise
        return "created"
    finally:
        lock_path.unlink(missing_ok=True)


def _existing_bundle_is_identical(
    output_root: Path, expected_files: Mapping[str, bytes]
) -> bool:
    if output_root.is_symlink() or not output_root.is_dir():
        return False
    actual_entries = tuple(sorted(path.name for path in output_root.iterdir()))
    if actual_entries != tuple(sorted(expected_files)):
        return False
    return all(
        not (output_root / name).is_symlink()
        and (output_root / name).is_file()
        and (output_root / name).read_bytes() == expected
        for name, expected in expected_files.items()
    )


def _validate_output_paths(
    paths: ClassificationAuditOutputPaths, allowed_output_parent: Path
) -> None:
    output_root = paths.output_root
    if not output_root.is_absolute() or not allowed_output_parent.is_absolute():
        _refuse("unsafe_output_path", "audit output paths must be absolute")
    if ".." in output_root.parts or ".." in allowed_output_parent.parts:
        _refuse("unsafe_output_path", "parent traversal is not allowed")
    if allowed_output_parent.is_symlink() or not allowed_output_parent.is_dir():
        _refuse(
            "unsafe_output_path",
            "allowed output parent must be an existing non-symlink directory",
        )
    resolved_parent = allowed_output_parent.resolve(strict=True)
    if resolved_parent == Path(resolved_parent.anchor):
        _refuse("unsafe_output_path", "filesystem root cannot own audit output")
    if output_root.parent != allowed_output_parent or output_root.is_symlink():
        _refuse(
            "unsafe_output_path",
            "audit output root must be one direct non-symlink child",
        )
    declared_paths = (*paths.payload_paths(), paths.manifest)
    expected_names = (*_OUTPUT_NAMES, _MANIFEST_NAME)
    if (
        any(path.parent != output_root for path in declared_paths)
        or tuple(sorted(path.name for path in declared_paths))
        != tuple(sorted(expected_names))
        or len(set(declared_paths)) != len(declared_paths)
    ):
        _refuse(
            "unsafe_output_path",
            "explicit audit paths must match the governed output set",
        )
    if output_root.parent.resolve(strict=True) != resolved_parent:
        _refuse("unsafe_output_path", "audit output escapes its allowed parent")


def _mapping_sequence(
    value: object, *, field_name: str
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _refuse("invalid_accounting_schema", f"{field_name} must be an array")
    assert isinstance(value, Sequence)
    if not all(isinstance(row, Mapping) for row in value):
        _refuse("invalid_accounting_schema", f"{field_name} rows must be objects")
    return tuple(row for row in value if isinstance(row, Mapping))


def _sequence_values(value: object, *, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _refuse("invalid_classification_record", f"{field_name} must be an array")
    assert isinstance(value, Sequence)
    return tuple(value)


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ClassificationAuditRefusalError(
            "invalid_output_serialization",
            "classification audit must be finite canonical JSON",
        ) from error
    return f"{rendered}\n".encode("utf-8")


def _required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _refuse("invalid_accounting_schema", f"{field_name} must be non-empty")
    assert isinstance(value, str)
    return value.strip()


def _required_digest(value: object, *, field_name: str) -> str:
    text = _required_text(value, field_name=field_name)
    if _SHA256_PATTERN.fullmatch(text) is None:
        _refuse(
            "invalid_contract_digest",
            f"{field_name} must be a prefixed SHA-256 digest",
        )
    return text


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _refuse(reason_code: str, detail: str) -> None:
    raise ClassificationAuditRefusalError(reason_code, detail)
