"""Structural and denominator validation for compact AADR accountability receipts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from bijux_pollenomics.adna.species.homo_sapiens.materialization.projection import (
    AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
    validate_aadr_accountability_summary,
)

from ..source_rows import validate_aadr_logical_source_path
from .contracts import (
    AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE,
    AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS,
    AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
    AADR_SOURCE_COUNTRY_POLICY_VERSION,
    POLITICAL_ENTITY_DISPOSITIONS,
)
from .political_entities import FOUR_COUNTRY_EXACT_SOURCE_VALUES

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COUNTRY_CODES = ("DK", "FI", "NO", "SE")
_PHYSICAL_ROW_DISPOSITIONS = (*_COUNTRY_CODES, "other", "missing")
_LINKED_ROW_DISPOSITIONS = (*POLITICAL_ENTITY_DISPOSITIONS, "unkeyed")
_POLITICAL_EVIDENCE_STATUSES = {
    "reported",
    "value_missing",
    "token_missing",
    "column_unavailable",
}


def validate_aadr_source_accountability_receipt(
    receipt: Mapping[str, object],
) -> None:
    """Reject receipts that imply admission or lose an accountable population."""
    if receipt.get("schema_version") != AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION:
        raise ValueError("AADR source-accountability schema version is unsupported")
    if receipt.get("record_kind") != "source_accountability_receipt":
        raise ValueError("AADR source-accountability record kind is invalid")
    if receipt.get("source_family") != "AADR":
        raise ValueError("AADR source-accountability source family is invalid")
    source_release = _nonempty_string(receipt.get("source_release"), "source_release")
    _require_false_boundaries(receipt, "receipt")

    release_manifest = _mapping(receipt.get("release_manifest"), "release_manifest")
    validate_aadr_logical_source_path(
        _nonempty_string(release_manifest.get("logical_path"), "manifest logical_path")
    )
    _sha256(release_manifest.get("sha256"), "manifest sha256")
    _nonnegative_integer(release_manifest.get("byte_count"), "manifest byte_count")

    projection = _mapping(
        receipt.get("accountability_projection"), "accountability_projection"
    )
    summary = _mapping(projection.get("summary"), "accountability summary")
    validate_aadr_accountability_summary(summary)
    summary_denominators = _mapping(summary.get("denominators"), "summary denominators")
    source_row_count = _nonnegative_integer(
        summary_denominators.get("source_row_count"), "summary source_row_count"
    )
    genetic_id_count = _nonnegative_integer(
        summary_denominators.get("genetic_id_count"), "summary genetic_id_count"
    )
    unkeyed_source_row_count = _nonnegative_integer(
        summary_denominators.get("unkeyed_source_row_count"),
        "summary unkeyed_source_row_count",
    )
    _validate_source_releases(summary, source_release)
    _validate_input_artifacts(
        receipt.get("input_artifacts"),
        release_manifest=release_manifest,
        source_files=_sequence(summary.get("source_files"), "source_files"),
    )
    _validate_stream(
        _mapping(projection.get("stream"), "accountability stream"),
        expected_line_count=1 + genetic_id_count + unkeyed_source_row_count,
    )

    political = _mapping(
        receipt.get("source_reported_political_entity"),
        "source_reported_political_entity",
    )
    if political.get("policy_version") != AADR_SOURCE_COUNTRY_POLICY_VERSION:
        raise ValueError("AADR Political Entity policy version is unsupported")
    if political.get("matching_rule") != (
        "outer_trimmed_case_sensitive_exact_source_value"
    ):
        raise ValueError("AADR Political Entity matching rule is invalid")
    _validate_exact_source_values(political.get("exact_source_values"))
    denominators = _mapping(political.get("denominators"), "political denominators")
    if (
        _nonnegative_integer(
            denominators.get("source_row_count"), "political source_row_count"
        )
        != source_row_count
    ):
        raise ValueError("AADR Political Entity source-row denominator diverges")
    keyed_source_row_count = _nonnegative_integer(
        denominators.get("keyed_source_row_count"), "political keyed_source_row_count"
    )
    if (
        _nonnegative_integer(
            denominators.get("unkeyed_source_row_count"),
            "political unkeyed_source_row_count",
        )
        != unkeyed_source_row_count
    ):
        raise ValueError("AADR Political Entity unkeyed-row denominator diverges")
    if keyed_source_row_count + unkeyed_source_row_count != source_row_count:
        raise ValueError("AADR Political Entity keyed-row denominator diverges")
    if (
        _nonnegative_integer(
            denominators.get("genetic_id_count"), "political genetic_id_count"
        )
        != genetic_id_count
    ):
        raise ValueError("AADR Political Entity Genetic-ID denominator diverges")

    physical_counts = _exact_count_mapping(
        political.get("physical_source_row_exact_value_counts"),
        "physical source rows",
        _PHYSICAL_ROW_DISPOSITIONS,
    )
    if sum(physical_counts.values()) != source_row_count:
        raise ValueError("AADR physical Political Entity rows diverge")
    linked_counts = _exact_count_mapping(
        political.get("record_linked_source_row_disposition_counts"),
        "record-linked source rows",
        _LINKED_ROW_DISPOSITIONS,
    )
    if sum(linked_counts.values()) != source_row_count:
        raise ValueError("AADR record-linked source rows diverge")
    if linked_counts["unkeyed"] != unkeyed_source_row_count:
        raise ValueError("AADR record-linked unkeyed rows diverge")
    genetic_counts = _exact_count_mapping(
        political.get("genetic_id_disposition_counts"),
        "Genetic-ID dispositions",
        POLITICAL_ENTITY_DISPOSITIONS,
    )
    if sum(genetic_counts.values()) != genetic_id_count:
        raise ValueError("AADR Political Entity Genetic-ID dispositions diverge")
    if (
        sum(
            _count_mapping(
                political.get("reconciliation_status_counts"),
                "Political Entity reconciliation statuses",
            ).values()
        )
        != genetic_id_count
    ):
        raise ValueError("AADR Political Entity reconciliation statuses diverge")
    if (
        sum(
            _count_mapping(
                political.get("evidence_status_counts"),
                "Political Entity evidence statuses",
            ).values()
        )
        != source_row_count
    ):
        raise ValueError("AADR Political Entity evidence statuses diverge")
    _validate_source_value_counts(
        political.get("source_value_counts"), expected=source_row_count
    )
    _validate_partitions(
        political.get("review_partitions"),
        genetic_counts=genetic_counts,
        linked_counts=linked_counts,
    )


def _validate_source_releases(
    summary: Mapping[str, object], expected_release: str
) -> None:
    source_files = _sequence(summary.get("source_files"), "source_files")
    if not source_files:
        raise ValueError("AADR accountability source-file ledger cannot be empty")
    for index, item in enumerate(source_files):
        source_file = _mapping(item, f"source_files[{index}]")
        if source_file.get("source_release") != expected_release:
            raise ValueError("AADR source-file release differs from receipt")
        validate_aadr_logical_source_path(
            _nonempty_string(source_file.get("source_path"), "source path")
        )


def _validate_input_artifacts(
    value: object,
    *,
    release_manifest: Mapping[str, object],
    source_files: Sequence[object],
) -> None:
    expected = [
        {
            "path": _nonempty_string(
                release_manifest.get("logical_path"), "manifest logical_path"
            ),
            "sha256": _sha256(release_manifest.get("sha256"), "manifest sha256"),
            "byte_count": _nonnegative_integer(
                release_manifest.get("byte_count"), "manifest byte_count"
            ),
        }
    ]
    for index, item in enumerate(source_files):
        source_file = _mapping(item, f"source_files[{index}]")
        expected.append(
            {
                "path": _nonempty_string(
                    source_file.get("source_path"), "source path"
                ),
                "sha256": _sha256(
                    source_file.get("source_sha256"), "source sha256"
                ),
                "byte_count": _nonnegative_integer(
                    source_file.get("source_byte_count"), "source byte_count"
                ),
            }
        )
    expected.sort(key=lambda artifact: str(artifact["path"]))
    expected_paths = [str(artifact["path"]) for artifact in expected]
    if len(expected_paths) != len(set(expected_paths)):
        raise ValueError("AADR expected input-artifact paths must be unique")

    artifacts = _sequence(value, "input_artifacts")
    observed: list[dict[str, object]] = []
    for index, item in enumerate(artifacts):
        artifact = _mapping(item, f"input_artifacts[{index}]")
        if set(artifact) != {"path", "sha256", "byte_count"}:
            raise ValueError("AADR input artifact fields are incomplete or unexpected")
        path = validate_aadr_logical_source_path(
            _nonempty_string(artifact.get("path"), "input artifact path")
        )
        observed.append(
            {
                "path": path,
                "sha256": _sha256(
                    artifact.get("sha256"), "input artifact sha256"
                ),
                "byte_count": _nonnegative_integer(
                    artifact.get("byte_count"), "input artifact byte_count"
                ),
            }
        )

    observed_paths = [str(artifact["path"]) for artifact in observed]
    if len(observed_paths) != len(set(observed_paths)):
        raise ValueError("AADR input-artifact paths must be unique")
    if observed_paths != sorted(observed_paths):
        raise ValueError("AADR input artifacts must be deterministically ordered")
    if set(observed_paths) != set(expected_paths):
        raise ValueError(
            "AADR input-artifact paths must exactly match the manifest and source files"
        )
    if observed != expected:
        raise ValueError("AADR input-artifact identity differs from its declared source")


def _validate_stream(stream: Mapping[str, object], *, expected_line_count: int) -> None:
    if stream.get("schema_version") != AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION:
        raise ValueError("AADR accountability stream schema version is unsupported")
    if stream.get("media_type") != AADR_ACCOUNTABILITY_STREAM_MEDIA_TYPE:
        raise ValueError("AADR accountability stream media type is invalid")
    if stream.get("storage_class") != AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS:
        raise ValueError("AADR accountability stream storage class is invalid")
    if stream.get("materialized") is not False or stream.get("tracked") is not False:
        raise ValueError(
            "AADR accountability receipt cannot claim a stored full stream"
        )
    if _nonnegative_integer(stream.get("line_count"), "stream line_count") != (
        expected_line_count
    ):
        raise ValueError("AADR accountability stream line denominator diverges")
    if _nonnegative_integer(stream.get("byte_count"), "stream byte_count") <= 0:
        raise ValueError("AADR accountability stream byte count must be positive")
    _sha256(stream.get("sha256"), "stream sha256")


def _validate_exact_source_values(value: object) -> None:
    rows = _sequence(value, "exact_source_values")
    expected = tuple(
        sorted(
            (
                {"country_code": country_code, "source_value": source_value}
                for source_value, country_code in FOUR_COUNTRY_EXACT_SOURCE_VALUES.items()
            ),
            key=lambda row: row["country_code"],
        )
    )
    observed = tuple(dict(_mapping(row, "exact source value")) for row in rows)
    if observed != expected:
        raise ValueError("AADR exact Political Entity source values diverge")


def _validate_source_value_counts(value: object, *, expected: int) -> None:
    rows = _sequence(value, "source_value_counts")
    observed = 0
    identities: set[tuple[object, object, object]] = set()
    ordered_identities: list[tuple[str, str, str]] = []
    for row in rows:
        item = _mapping(row, "source value count")
        status = _nonempty_string(item.get("status"), "source value status")
        if status not in _POLITICAL_EVIDENCE_STATUSES:
            raise ValueError("AADR source-value evidence status is unsupported")
        raw_value = item.get("raw_value")
        trimmed_value = item.get("trimmed_value")
        if raw_value is not None and not isinstance(raw_value, str):
            raise ValueError("AADR source-value raw token must be text or null")
        if trimmed_value is not None and not isinstance(trimmed_value, str):
            raise ValueError("AADR source-value trimmed token must be text or null")
        if status == "reported" and (
            not isinstance(raw_value, str)
            or not isinstance(trimmed_value, str)
            or not trimmed_value
            or raw_value.strip() != trimmed_value
        ):
            raise ValueError("AADR reported source-value token is inconsistent")
        if status == "value_missing" and (
            not isinstance(raw_value, str)
            or raw_value.strip()
            or trimmed_value is not None
        ):
            raise ValueError("AADR missing source-value token is inconsistent")
        if status in {"token_missing", "column_unavailable"} and (
            raw_value is not None or trimmed_value is not None
        ):
            raise ValueError("AADR unavailable source-value token is inconsistent")
        identity = (status, raw_value, trimmed_value)
        if identity in identities:
            raise ValueError("AADR source-value count identities must be unique")
        identities.add(identity)
        ordered_identities.append((status, trimmed_value or "", raw_value or ""))
        observed += _nonnegative_integer(
            item.get("source_row_count"), "source value row count"
        )
    if ordered_identities != sorted(ordered_identities):
        raise ValueError("AADR source-value counts must be deterministically ordered")
    if observed != expected:
        raise ValueError("AADR source-value row denominator diverges")


def _validate_partitions(
    value: object,
    *,
    genetic_counts: Mapping[str, int],
    linked_counts: Mapping[str, int],
) -> None:
    partitions = _sequence(value, "review_partitions")
    observed_dispositions: list[str] = []
    for partition_value in partitions:
        partition = _mapping(partition_value, "review partition")
        disposition = _nonempty_string(
            partition.get("disposition"), "partition disposition"
        )
        observed_dispositions.append(disposition)
        genetic_id_count = _nonnegative_integer(
            partition.get("genetic_id_count"), "partition genetic_id_count"
        )
        linked_source_row_count = _nonnegative_integer(
            partition.get("linked_source_row_count"),
            "partition linked_source_row_count",
        )
        if genetic_counts.get(disposition) != genetic_id_count:
            raise ValueError("AADR partition Genetic-ID denominator diverges")
        if linked_counts.get(disposition) != linked_source_row_count:
            raise ValueError("AADR partition linked-row denominator diverges")
        expected_country_code: str | None = (
            disposition if disposition in _COUNTRY_CODES else None
        )
        if partition.get("country_code") != expected_country_code:
            raise ValueError("AADR partition country code diverges")
        expected_source_value = next(
            (
                source_value
                for source_value, country_code in FOUR_COUNTRY_EXACT_SOURCE_VALUES.items()
                if country_code == disposition
            ),
            None,
        )
        if partition.get("exact_source_value") != expected_source_value:
            raise ValueError("AADR partition source value diverges")
        _require_false_boundaries(partition, f"partition {disposition}")
        _validate_coordinate_review(
            _mapping(partition.get("coordinate_review"), "coordinate_review"),
            genetic_id_count=genetic_id_count,
        )
        _validate_chronology_review(
            _mapping(partition.get("chronology_review"), "chronology_review"),
            genetic_id_count=genetic_id_count,
        )
    if tuple(observed_dispositions) != POLITICAL_ENTITY_DISPOSITIONS:
        raise ValueError("AADR review partitions are incomplete or unordered")


def _validate_coordinate_review(
    review: Mapping[str, object], *, genetic_id_count: int
) -> None:
    if review.get("country_assignment_admitted") is not False:
        raise ValueError("AADR coordinate review cannot admit country assignment")
    if review.get("map_admitted") is not False:
        raise ValueError("AADR coordinate review cannot admit map records")
    evidence_group_count = _nonnegative_integer(
        review.get("evidence_group_count"), "coordinate evidence_group_count"
    )
    if (
        sum(
            _count_mapping(
                review.get("source_parse_status_counts"), "coordinate parse statuses"
            ).values()
        )
        != evidence_group_count
    ):
        raise ValueError("AADR coordinate evidence-group denominator diverges")
    for field in (
        "genetic_id_availability_counts",
        "reconciliation_status_counts",
    ):
        if sum(_count_mapping(review.get(field), field).values()) != genetic_id_count:
            raise ValueError(f"AADR coordinate {field} denominator diverges")


def _validate_chronology_review(
    review: Mapping[str, object], *, genetic_id_count: int
) -> None:
    if review.get("scientifically_admitted") is not False:
        raise ValueError("AADR chronology review cannot admit scientific chronology")
    if review.get("scientifically_admitted_count") != 0:
        raise ValueError("AADR chronology scientific admission count must be zero")
    evidence_group_count = _nonnegative_integer(
        review.get("evidence_group_count"), "chronology evidence_group_count"
    )
    for field in (
        "evaluation_status_counts",
        "refusal_reason_counts",
        "date_method_family_counts",
        "date_mean_status_counts",
        "date_mean_sign_counts",
        "date_stddev_status_counts",
        "date_stddev_sign_counts",
        "full_date_status_counts",
    ):
        if (
            sum(_count_mapping(review.get(field), field).values())
            != evidence_group_count
        ):
            raise ValueError(f"AADR chronology {field} denominator diverges")
    if (
        sum(
            _count_mapping(
                review.get("reconciliation_status_counts"),
                "chronology reconciliation statuses",
            ).values()
        )
        != genetic_id_count
    ):
        raise ValueError("AADR chronology reconciliation denominator diverges")


def _require_false_boundaries(value: Mapping[str, object], label: str) -> None:
    expected = {
        "taxon_scope_status": "not_asserted_by_source",
        "scientifically_admitted": False,
        "country_assignment_admitted": False,
        "map_admitted": False,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ValueError(f"AADR {label} {key} boundary diverges")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"AADR {label} must be a string-keyed object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"AADR {label} must be a sequence")
    return value


def _count_mapping(value: object, label: str) -> dict[str, int]:
    mapping = _mapping(value, label)
    return {
        key: _nonnegative_integer(item, f"{label}.{key}")
        for key, item in mapping.items()
    }


def _exact_count_mapping(
    value: object,
    label: str,
    expected_keys: tuple[str, ...],
) -> dict[str, int]:
    counts = _count_mapping(value, label)
    if set(counts) != set(expected_keys):
        raise ValueError(f"AADR {label} keys are incomplete")
    return counts


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"AADR {label} must be a nonnegative integer")
    return value


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"AADR {label} must be non-empty text")
    return value


def _sha256(value: object, label: str) -> str:
    digest = _nonempty_string(value, label)
    if not _SHA256_RE.fullmatch(digest):
        raise ValueError(f"AADR {label} must be lowercase SHA-256")
    return digest


__all__ = ["validate_aadr_source_accountability_receipt"]
