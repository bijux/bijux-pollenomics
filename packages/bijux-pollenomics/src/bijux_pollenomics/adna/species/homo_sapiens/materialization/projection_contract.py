"""Schema identity and denominator checks for AADR accountability summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .models import build_aadr_source_file_key

AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION = "aadr-panel-accountability-review.v1"

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def validate_aadr_accountability_summary(summary: Mapping[str, object]) -> None:
    """Reject a projected summary whose identities or denominators diverge."""
    if summary.get("schema_version") != AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION:
        raise ValueError("AADR accountability summary schema version is unsupported")
    denominators = _mapping(summary.get("denominators"), "denominators")
    source_file_count = _nonnegative_integer(
        denominators.get("source_file_count"), "source_file_count"
    )
    source_row_count = _nonnegative_integer(
        denominators.get("source_row_count"), "source_row_count"
    )
    keyed_source_row_count = _nonnegative_integer(
        denominators.get("keyed_source_row_count"), "keyed_source_row_count"
    )
    unkeyed_source_row_count = _nonnegative_integer(
        denominators.get("unkeyed_source_row_count"), "unkeyed_source_row_count"
    )
    genetic_id_count = _nonnegative_integer(
        denominators.get("genetic_id_count"), "genetic_id_count"
    )
    coordinate_group_count = _nonnegative_integer(
        denominators.get("coordinate_evidence_group_count"),
        "coordinate_evidence_group_count",
    )
    chronology_group_count = _nonnegative_integer(
        denominators.get("chronology_evidence_group_count"),
        "chronology_evidence_group_count",
    )
    if keyed_source_row_count + unkeyed_source_row_count != source_row_count:
        raise ValueError("AADR keyed and unkeyed source-row denominators diverge")

    dataset_names = _string_sequence(summary.get("dataset_names"), "dataset_names")
    if dataset_names != tuple(sorted(set(dataset_names))):
        raise ValueError("AADR accountability datasets must be unique and sorted")
    source_file_counts = _validate_source_files(
        summary.get("source_files"), dataset_names
    )
    source_files = summary.get("source_files")
    if not isinstance(source_files, Sequence) or len(source_files) != source_file_count:
        raise ValueError("AADR source-file count denominator diverges")
    if sum(source_file_counts.values()) != source_row_count:
        raise ValueError("AADR source-file ledger denominator diverges")

    dataset_counts = _mapping(summary.get("dataset_counts"), "dataset_counts")
    source_dataset_counts = _count_mapping(
        dataset_counts.get("source_rows"), "dataset source rows"
    )
    if source_dataset_counts != {
        dataset_name: source_file_counts.get(dataset_name, 0)
        for dataset_name in dataset_names
    }:
        raise ValueError("AADR source-file and dataset row counts diverge")
    membership_counts = _count_mapping(
        dataset_counts.get("genetic_id_memberships"), "genetic ID memberships"
    )
    if set(membership_counts) != set(dataset_names):
        raise ValueError("AADR Genetic-ID membership datasets diverge")

    statuses = _mapping(summary.get("status_counts"), "status_counts")
    for name in (
        "panel",
        "coordinate",
        "chronology",
        "reconciliation",
        "taxon_scope_genetic_ids",
    ):
        _require_count_sum(statuses, name, genetic_id_count)
    _require_count_sum(statuses, "coordinate_evidence", coordinate_group_count)
    _require_count_sum(statuses, "chronology_evaluation", chronology_group_count)
    _require_count_sum(statuses, "chronology_refusal_reason", chronology_group_count)
    _require_count_sum(statuses, "taxon_scope_unkeyed_rows", unkeyed_source_row_count)
    _require_count_sum(statuses, "unkeyed_refusal_reason", unkeyed_source_row_count)
    if summary.get("scientifically_admitted") is not False:
        raise ValueError("AADR accountability summary cannot admit scientific claims")
    if summary.get("scientifically_admitted_chronology_group_count") != 0:
        raise ValueError("AADR accountability chronology admission count must be zero")
    if summary.get("taxon_scope_status") != "not_asserted_by_source":
        raise ValueError("AADR accountability summary must not assert a taxon")


def _validate_source_files(
    value: object, dataset_names: tuple[str, ...]
) -> dict[str, int]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("AADR source_files must be a sequence")
    observed_keys: list[str] = []
    dataset_counts = dict.fromkeys(dataset_names, 0)
    for index, item in enumerate(value):
        source_file = _mapping(item, f"source_files[{index}]")
        key = _nonempty_string(source_file.get("source_file_key"), "source_file_key")
        if key in observed_keys:
            raise ValueError("AADR source-file ledger keys must be unique")
        observed_keys.append(key)
        dataset_name = _nonempty_string(
            source_file.get("dataset_name"), "source-file dataset_name"
        )
        if dataset_name not in dataset_counts:
            raise ValueError("AADR source-file ledger names an unknown dataset")
        source_path = _nonempty_string(source_file.get("source_path"), "source_path")
        source_release = _nonempty_string(
            source_file.get("source_release"), "source_release"
        )
        digest = _nonempty_string(source_file.get("source_sha256"), "source_sha256")
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError("AADR source-file ledger digest must be lowercase SHA-256")
        _nonnegative_integer(source_file.get("source_byte_count"), "source_byte_count")
        row_count = _nonnegative_integer(
            source_file.get("source_row_count"), "source_row_count"
        )
        _string_sequence(source_file.get("column_names"), "column_names")
        if key != build_aadr_source_file_key(
            source_path=source_path,
            source_release=source_release,
            dataset_name=dataset_name,
            source_sha256=digest,
        ):
            raise ValueError("AADR source-file ledger identity key diverges")
        dataset_counts[dataset_name] += row_count
    if observed_keys != sorted(observed_keys):
        raise ValueError("AADR source-file ledger must be deterministically ordered")
    return dataset_counts


def _require_count_sum(
    statuses: Mapping[str, object], name: str, expected: int
) -> None:
    counts = _count_mapping(statuses.get(name), name)
    if sum(counts.values()) != expected:
        raise ValueError(f"AADR {name} status denominator diverges")


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"AADR {name} must be a string-keyed object")
    return value


def _count_mapping(value: object, name: str) -> dict[str, int]:
    mapping = _mapping(value, name)
    return {
        key: _nonnegative_integer(item, f"{name}.{key}")
        for key, item in mapping.items()
    }


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"AADR {name} must be a nonnegative integer")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"AADR {name} must be a non-empty string")
    return value


def _string_sequence(value: object, name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"AADR {name} must be a string sequence")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"AADR {name} must contain only strings")
    return tuple(value)


__all__ = [
    "AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION",
    "build_aadr_source_file_key",
    "validate_aadr_accountability_summary",
]
