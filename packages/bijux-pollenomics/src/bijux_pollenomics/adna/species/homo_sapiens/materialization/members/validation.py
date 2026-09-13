"""Independent ownership/reference validation for persisted evidence tables."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import build_aadr_source_file_key
from .contracts import (
    MEMBER_FILES,
    claim_key,
    member_key,
    object_mapping,
    object_rows,
    strings,
    text,
    validate_boundary,
)


def nonnegative_integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("AADR evidence denominator must be a nonnegative integer")
    return value


@dataclass(frozen=True, slots=True)
class _Owner:
    kind: str
    key: str
    rows: tuple[str, ...]
    datasets: tuple[str, ...]
    coordinates: tuple[str, ...]
    chronology: tuple[str, ...]


def validate_member_ownership(
    documents: Iterable[tuple[str, dict[str, object]]],
    *,
    release_manifest_sha256: str,
) -> dict[str, object]:
    """Verify exact row ownership and independent coordinate/chronology partitions."""
    files: dict[str, dict[str, object]] = {}
    rows: dict[str, tuple[str, int]] = {}
    owners: dict[str, _Owner] = {}
    claims: dict[tuple[str, str], tuple[str, str, tuple[str, ...]]] = {}
    source_headers = 0
    for filename, record in documents:
        if filename not in MEMBER_FILES:
            raise ValueError("AADR unexpected member table")
        if filename == "source_files.json":
            source_headers += 1
            for item in object_rows(record.get("source_files")):
                key = text(item["source_file_key"])
                if key in files or key != build_aadr_source_file_key(
                    source_path=text(item["source_path"]),
                    source_release=text(item["source_release"]),
                    dataset_name=text(item["dataset_name"]),
                    source_sha256=text(item["source_sha256"]),
                ):
                    raise ValueError(
                        "AADR duplicate or inconsistent physical source key"
                    )
                nonnegative_integer(item["source_byte_count"])
                nonnegative_integer(item["source_row_count"])
                strings(item["column_names"])
                files[key] = item
        elif filename == "source_rows.ndjson":
            link = object_mapping(record["source_row"])
            key = text(link["key"])
            file_key = text(link["source_file_key"])
            number = nonnegative_integer(link["source_record_number"])
            start = nonnegative_integer(link["source_line_start"])
            end = nonnegative_integer(link["source_line_end"])
            if (
                key in rows
                or file_key not in files
                or number == 0
                or key != f"{file_key}:record:{number}"
                or start < 2
                or end < start
            ):
                raise ValueError("AADR invalid or duplicate physical source row")
            file = files[file_key]
            for name in (
                "source_path",
                "source_release",
                "dataset_name",
                "source_sha256",
            ):
                if link[name] != file[name]:
                    raise ValueError("AADR source row/file identity diverges")
            tokens = strings(record["raw_tokens"])
            if (
                strings(record["unmatched_raw_tokens"])
                != tokens[len(strings(file["column_names"])) :]
            ):
                raise ValueError("AADR unmatched source tokens diverge")
            if record["taxon_scope_status"] != "not_asserted_by_source":
                raise ValueError("AADR source cannot assert taxon scope")
            rows[key] = (file_key, number)
        elif filename in {"members.ndjson", "unkeyed_rows.ndjson"}:
            validate_boundary(record["admission_boundary"])
            keyed = filename == "members.ndjson"
            kind = "member" if keyed else "unkeyed_row"
            key = text(record["member_key" if keyed else "source_row_key"])
            owned_rows = strings(record["source_row_keys"])
            if (
                key in owners
                or not owned_rows
                or len(set(owned_rows)) != len(owned_rows)
            ):
                raise ValueError("AADR duplicate or empty evidence owner")
            if keyed and key != member_key(
                release_manifest_sha256, text(record["genetic_id"])
            ):
                raise ValueError("AADR release/member identity diverges")
            if not keyed and (
                owned_rows != (key,)
                or record["refusal_reason_code"] != "genetic_id_missing"
            ):
                raise ValueError("AADR invalid unkeyed row disposition")
            strings(record["genetic_id_raw_values"])
            owners[key] = _Owner(
                kind,
                key,
                owned_rows,
                strings(record["dataset_names"]),
                strings(record["coordinate_claim_keys"]),
                strings(record["chronology_claim_keys"]),
            )
        else:
            kind = (
                "coordinate" if filename == "coordinate_claims.ndjson" else "chronology"
            )
            key = text(record["claim_key"])
            owner_kind = text(record["owner_kind"])
            owner = text(record["owner_key"])
            evidence = object_mapping(record["evidence"])
            row_keys = strings(evidence["source_row_keys"])
            if (kind, key) in claims or key != claim_key(
                kind, owner_kind, owner, row_keys
            ):
                raise ValueError("AADR invalid or duplicate evidence claim")
            if (
                kind == "chronology"
                and evidence.get("scientifically_admitted") is not False
            ):
                raise ValueError("AADR chronology cannot grant scientific admission")
            claims[(kind, key)] = (owner_kind, owner, row_keys)
    if source_headers != 1:
        raise ValueError("AADR requires exactly one physical-source header")
    per_file: dict[str, list[int]] = {key: [] for key in files}
    for file_key, number in rows.values():
        per_file[file_key].append(number)
    for key, numbers in per_file.items():
        count = nonnegative_integer(files[key]["source_row_count"])
        if len(numbers) != count or sorted(numbers) != list(range(1, count + 1)):
            raise ValueError("AADR physical source-row denominator diverges")
    assigned: Counter[str] = Counter()
    referenced: set[tuple[str, str]] = set()
    for member_owner in owners.values():
        assigned.update(member_owner.rows)
        if any(key not in rows for key in member_owner.rows):
            raise ValueError("AADR owner references an unknown source row")
        datasets = sorted(
            {text(files[rows[key][0]]["dataset_name"]) for key in member_owner.rows}
        )
        if list(member_owner.datasets) != datasets:
            raise ValueError("AADR owner panel membership diverges")
        for kind, keys in (
            ("coordinate", member_owner.coordinates),
            ("chronology", member_owner.chronology),
        ):
            partition: Counter[str] = Counter()
            for key in keys:
                identity = (kind, key)
                if identity in referenced or identity not in claims:
                    raise ValueError("AADR missing or multiply referenced claim")
                claim_owner_kind, claim_owner, claim_rows = claims[identity]
                if (claim_owner_kind, claim_owner) != (
                    member_owner.kind,
                    member_owner.key,
                ):
                    raise ValueError("AADR cross-owner claim reference")
                partition.update(claim_rows)
                referenced.add(identity)
            if partition != Counter(member_owner.rows):
                raise ValueError("AADR claim groups do not partition owner rows")
    if assigned != Counter(dict.fromkeys(rows, 1)) or referenced != set(claims):
        raise ValueError("AADR source ownership or claim closure incomplete")
    unkeyed = sum(owner.kind == "unkeyed_row" for owner in owners.values())
    return {
        "source_file_count": len(files),
        "source_row_count": len(rows),
        "keyed_source_row_count": len(rows) - unkeyed,
        "unkeyed_source_row_count": unkeyed,
        "member_count": len(owners) - unkeyed,
        "coordinate_claim_count": sum(kind == "coordinate" for kind, _ in claims),
        "chronology_claim_count": sum(kind == "chronology" for kind, _ in claims),
    }
