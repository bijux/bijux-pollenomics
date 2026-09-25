"""Replay retained Rootsi workbooks into refusal-bounded structural candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterator, Sequence
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import NoReturn, cast

from bijux_pollenomics.collection.sources.rootsi import (
    RootsiSiteMetadataClaim,
    normalize_rootsi_site_metadata,
)
from bijux_pollenomics.collection.sources.rootsi.authority import (
    ARCHIVE_SHA256,
    METADATA_MEMBER,
    METADATA_SHA256,
)
from bijux_pollenomics.collection.sources.rootsi.cells import (
    replay_rootsi_cell_review,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

JsonObject = dict[str, object]

SCHEMA_VERSION = "essd-rootsi-retained-workbook-replay.v1"
PROFILE = "rootsi-retained-workbook-structural-replay-v1"
STATUS = "private_structural_candidates_only"

TYPED_CELL_REVIEW_MANIFEST_SHA256 = (
    "2e5b5a3a10cec59fc8086c0c99db56bb394e9d1f180bbd5571c1098c262c9179"
)
NATIVE_INVENTORY_SHA256 = (
    "3353156471c2d04f2dce4138d29ad1a4891896d223c2c37dd5c531ba51c17b5a"
)
CANDIDATE_CLOSURE_MANIFEST_SHA256 = (
    "714f60289143e38f38a9e6acb75d4a150be79ba6637f6c222d89998c291b5ffe"
)
CANDIDATE_PAIR_IDENTITY_SHA256 = (
    "ca94f04342f5c54212dc3ef9acfa0cbeea6e92419878f951ec23b2a0acf5cfd6"
)
WORKBOOK_ROSTER_SHA256 = (
    "1e927af9c373c8cf9da3ae8c412c166e121cf2bc6e7c8bb50eb399652161abfb"
)
TYPED_CELL_REVIEW_FILES_SHA256 = (
    "ceb7703bf17ebbeb85c279b74f2ced0da545bc228c365a01b45644655ac61289"
)
CANDIDATE_CLOSURE_FILES_SHA256 = (
    "d701ea0054ec6fb2566dd9c452d768b416dc5d7db838c8d8e501eceecaccb9e7"
)
METADATA_WORKBOOK_BINDINGS_SHA256 = (
    "c75b3108e0f9569088d1cb9483cf6e39b2696354de6180b075588e72a0f1f965"
)

WORKBOOKS = 79
SHEETS = 107
RECTANGLE_POSITIONS = 547_330
HEADER_FIELDS = 7_459
DATA_ROW_CANDIDATES = 5_170
DATA_ROW_POSITIONS = 527_205
DATA_ROW_NUMERIC_POSITIONS = 527_072
DATA_ROW_EMPTY_POSITIONS = 132
DATA_ROW_TEXT_POSITIONS = 1
SAMPLE_DENOMINATOR_RECORDS = 79
SAMPLE_DENOMINATOR_AGREEMENTS = 78
HEADER_TEXT_POSITIONS = 7_458
HEADER_EMPTY_POSITIONS = 1
HEADER_NONEMPTY_TEXT_POSITIONS = 7_434

_MANIFEST = "manifest.json"
_WORKBOOK_PROFILES = "workbook-profiles.jsonl"
_HEADER_FIELDS = "header-fields.jsonl"
_DATA_ROWS = "data-row-candidates.jsonl"
_SAMPLE_REVIEW = "sample-denominator-review.csv"
_REPORT = "report.json"
_OUTPUT_NAMES = (
    _MANIFEST,
    _WORKBOOK_PROFILES,
    _HEADER_FIELDS,
    _DATA_ROWS,
    _SAMPLE_REVIEW,
    _REPORT,
)
_REVIEW_NAMES = {
    "manifest.json",
    "workbooks.json",
    "sheets.jsonl",
    "cells.jsonl",
    "accounting.json",
    "capture-inventory.json",
}
_CLOSURE_NAMES = {
    "manifest.json",
    "publication-candidates.jsonl",
    "rootsi-crosswalk.csv",
    "requirement-status.csv",
    "report.json",
}
_DIGEST = re.compile(r"[a-f0-9]{64}")
_CELL_FIELDS = {
    "cell_id",
    "workbook_id",
    "sheet_ordinal",
    "row",
    "column",
    "cell_type",
    "decoded_value",
    "binary64_hex",
    "xf_index",
    "refusal_reason",
}
_STRUCTURAL_COUNT_NAMES = (
    "empty",
    "text",
    "number",
    "date",
    "boolean",
    "error",
    "blank",
    "unsupported",
)
_SAMPLE_COLUMNS = (
    "namespace",
    "archive_member",
    "workbook_sha256",
    "rootsi_source_row",
    "rootsi_source_locator",
    "rootsi_site_name_raw",
    "rootsi_sequence_label_raw",
    "rootsi_observation_workbook_claim_raw",
    "rootsi_sample_count_raw",
    "rootsi_sample_count_claim",
    "mechanical_data_row_candidates",
    "sample_denominator_agrees",
    "sample_denominator_status",
    "historical_primary_input_identity_status",
)


class RootsiWorkbookReplayError(ValueError):
    """Raised when retained workbook evidence cannot be replayed exactly."""


def _refuse(reason: str, detail: object) -> NoReturn:
    raise RootsiWorkbookReplayError(f"rootsi_workbook_replay_{reason}: {detail}")


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        _refuse("invalid_digest", field)
    return value


def _integer(value: object, field: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _refuse("invalid_integer", field)
    return value


def _text(value: object, field: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value):
        _refuse("invalid_text", field)
    return value


def _pairs(rows: list[tuple[str, object]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in rows:
        if key in result:
            _refuse("duplicate_json_key", key)
        result[key] = value
    return result


def _nonfinite(value: str) -> NoReturn:
    _refuse("nonfinite_json", value)


def _decode(content: bytes, field: str) -> object:
    try:
        return json.loads(
            content,
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
        )
    except (UnicodeError, ValueError) as exc:
        _refuse("invalid_json", f"{field}: {exc}")


def _object(content: bytes, field: str) -> JsonObject:
    value = _decode(content, field)
    if not isinstance(value, dict):
        _refuse("invalid_json_object", field)
    return cast(JsonObject, value)


def _array(content: bytes, field: str) -> list[object]:
    value = _decode(content, field)
    if not isinstance(value, list):
        _refuse("invalid_json_array", field)
    return cast(list[object], value)


def _encode(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _refuse("unencodable_json", str(exc))


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_id(*parts: object) -> str:
    return _sha256(_encode(parts))


def _checked_path(path: Path) -> Path:
    result = Path(os.path.abspath(Path(path)))
    if any(item.is_symlink() for item in (result, *result.parents)):
        _refuse("symlink_path", result)
    return result


def _file_identity(path: Path) -> JsonObject:
    path = _checked_path(path)
    if not path.is_file():
        _refuse("missing_file", path)
    with path.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        byte_count = os.fstat(stream.fileno()).st_size
    return {"sha256": sha256, "bytes": byte_count}


def _read_pinned(path: Path, expected_sha256: str) -> bytes:
    path = _checked_path(path)
    content = path.read_bytes()
    if _sha256(content) != _digest(expected_sha256, str(path)):
        _refuse("input_digest_mismatch", path)
    return content


class _StreamIdentity:
    __slots__ = ("_bytes", "_hasher")

    def __init__(self) -> None:
        self._hasher = hashlib.sha256()
        self._bytes = 0

    def add(self, content: bytes) -> None:
        self._hasher.update(content)
        self._bytes += len(content)

    def as_dict(self) -> JsonObject:
        return {"sha256": self._hasher.hexdigest(), "bytes": self._bytes}


def _json_lines(
    path: Path, identity: _StreamIdentity | None = None
) -> Iterator[JsonObject]:
    path = _checked_path(path)
    with path.open("rb") as stream:
        for number, line in enumerate(stream, start=1):
            if identity is not None:
                identity.add(line)
            if not line.endswith(b"\n") or not line.strip():
                _refuse("invalid_json_line", f"{path.name}:{number}")
            value = _decode(line, f"{path.name}:{number}")
            if not isinstance(value, dict):
                _refuse("invalid_json_line", f"{path.name}:{number}")
            yield cast(JsonObject, value)


def _directory_files(directory: Path, expected: set[str], label: str) -> Path:
    directory = _checked_path(directory)
    if not directory.is_dir():
        _refuse("missing_directory", label)
    children = tuple(directory.iterdir())
    if {item.name for item in children} != expected:
        _refuse("unexpected_inventory", label)
    if any(item.is_symlink() or not item.is_file() for item in children):
        _refuse("unsafe_inventory", label)
    return directory


@dataclass(frozen=True)
class RootsiWorkbookReplayInput:
    """Exact retained parents required for one workbook-byte replay."""

    typed_cell_review_dir: Path
    expected_cell_review_manifest_sha256: str
    native_inventory_path: Path
    expected_native_inventory_sha256: str
    workbook_directory: Path
    rootsi_metadata_path: Path
    expected_rootsi_metadata_sha256: str
    candidate_closure_dir: Path
    expected_candidate_closure_manifest_sha256: str

    def __post_init__(self) -> None:
        for field, value in (
            ("cell review manifest", self.expected_cell_review_manifest_sha256),
            ("native inventory", self.expected_native_inventory_sha256),
            ("Rootsi metadata", self.expected_rootsi_metadata_sha256),
            ("candidate closure", self.expected_candidate_closure_manifest_sha256),
        ):
            _digest(value, field)


@dataclass(frozen=True)
class RootsiWorkbookReplayBundle:
    """Durable private structural replay identity with no scientific admission."""

    directory: Path
    manifest_sha256: str
    workbook_profiles: int
    header_fields: int
    data_row_candidates: int
    sample_denominator_records: int
    candidate_pair_identity_sha256: str


@dataclass(frozen=True)
class _Snapshot:
    label: str
    path: Path
    sha256: str
    byte_count: int

    def as_dict(self) -> JsonObject:
        return {"sha256": self.sha256, "bytes": self.byte_count}


@dataclass(frozen=True)
class _Workbook:
    archive_member: str
    path: Path
    sha256: str
    byte_count: int
    workbook_id: str
    excel_date_mode: int
    sheet_count: int

    def source_dict(self) -> JsonObject:
        return {
            "archive_member": self.archive_member,
            "sha256": self.sha256,
            "bytes": self.byte_count,
        }


@dataclass(frozen=True)
class _Sheet:
    workbook_id: str
    ordinal: int
    name: str
    rows: int
    columns: int
    rectangle_positions: int
    merged_ranges: tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class _Inputs:
    source: RootsiWorkbookReplayInput
    snapshots: tuple[_Snapshot, ...]
    review_manifest: JsonObject
    review_accounting: JsonObject
    workbooks: tuple[_Workbook, ...]
    sheets: tuple[_Sheet, ...]
    metadata: tuple[RootsiSiteMetadataClaim, ...]
    candidate_manifest: JsonObject
    candidate_report: JsonObject


@dataclass(frozen=True)
class _Row:
    index: int
    decoded_cells_sha256: str
    nonempty_cells: int
    nonempty_text_cells: int
    structural_counts: tuple[tuple[str, int], ...]
    cells: tuple[JsonObject, ...]


@dataclass(frozen=True)
class _SheetAnalysis:
    sheet: _Sheet
    nonempty_cells: int
    nonempty_rows: int
    rows: tuple[_Row, ...]
    header_row: int | None
    header_cells: tuple[JsonObject, ...]


_replay_cell_review = replay_rootsi_cell_review
_publish_new_output_tree = publish_new_output_tree


def _producer_identity() -> JsonObject:
    path = Path(__file__).resolve()
    identity = _file_identity(path)
    return {"essd_reproduction/rootsi_workbook_replay.py": identity}


def _snapshot(label: str, path: Path) -> _Snapshot:
    checked = _checked_path(path)
    identity = _file_identity(checked)
    return _Snapshot(
        label,
        checked,
        cast(str, identity["sha256"]),
        cast(int, identity["bytes"]),
    )


def _member_name(value: object) -> str:
    name = _text(value, "archive_member")
    parts = name.split("/")
    if (
        "\x00" in name
        or "\\" in name
        or PurePosixPath(name).is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
        or len(parts) != 2
        or parts[0] != "rootsi"
        or not name.endswith(".xls")
    ):
        _refuse("invalid_archive_member", name)
    return name


def _native_inventory(content: bytes) -> tuple[JsonObject, ...]:
    inventory = _object(content, "native inventory")
    required = {
        "archive_sha256",
        "workbook_count",
        "tool_version",
        "source_unchanged",
        "supplied_code_executed",
        "scope",
        "cell_type_contract",
        "workbooks",
        "completed_at",
        "elapsed_seconds",
    }
    if set(inventory) != required:
        _refuse("native_inventory_fields", sorted(inventory))
    rows = inventory["workbooks"]
    if (
        inventory["archive_sha256"] != ARCHIVE_SHA256
        or inventory["source_unchanged"] is not True
        or inventory["supplied_code_executed"] is not False
        or _integer(inventory["workbook_count"], "workbook_count") != WORKBOOKS
        or not isinstance(rows, list)
        or len(rows) != WORKBOOKS
    ):
        _refuse("native_inventory_posture", "governed retained inventory required")
    result: list[JsonObject] = []
    names: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            _refuse("native_workbook_record", "object required")
        row = cast(JsonObject, raw)
        name = _member_name(row.get("archive_member"))
        if name in names:
            _refuse("duplicate_workbook", name)
        names.add(name)
        result.append(
            {
                "archive_member": name,
                "sha256": _digest(row.get("sha256"), name),
                "bytes": _integer(row.get("byte_count"), name, minimum=1),
            }
        )
    result.sort(key=lambda item: cast(str, item["archive_member"]))
    if _sha256(_encode(result)) != WORKBOOK_ROSTER_SHA256:
        _refuse("workbook_roster_changed", "native inventory")
    return tuple(result)


def _workbook_files(
    directory: Path, roster: tuple[JsonObject, ...]
) -> tuple[dict[str, Path], tuple[_Snapshot, ...]]:
    directory = _checked_path(directory)
    if not directory.is_dir():
        _refuse("missing_workbook_directory", directory)
    by_basename = {
        PurePosixPath(cast(str, row["archive_member"])).name: row for row in roster
    }
    if len(by_basename) != WORKBOOKS:
        _refuse("workbook_basename_collision", directory)
    children = tuple(directory.iterdir())
    if {item.name for item in children} != set(by_basename):
        _refuse("workbook_directory_inventory", directory)
    if any(item.is_symlink() or not item.is_file() for item in children):
        _refuse("unsafe_workbook_file", directory)
    files: dict[str, Path] = {}
    snapshots: list[_Snapshot] = []
    for basename, row in sorted(by_basename.items()):
        path = _checked_path(directory / basename)
        identity = _file_identity(path)
        expected = {"sha256": row["sha256"], "bytes": row["bytes"]}
        if identity != expected:
            _refuse("workbook_identity_mismatch", basename)
        member = cast(str, row["archive_member"])
        files[member] = path
        snapshots.append(
            _Snapshot(
                f"workbook:{member}",
                path,
                cast(str, identity["sha256"]),
                cast(int, identity["bytes"]),
            )
        )
    return files, tuple(snapshots)


def _review_manifest(
    directory: Path, expected_sha256: str, roster: tuple[JsonObject, ...]
) -> tuple[JsonObject, JsonObject, tuple[_Snapshot, ...]]:
    directory = _directory_files(directory, _REVIEW_NAMES, "typed cell review")
    snapshots = tuple(
        _snapshot(f"typed_cell_review:{name}", directory / name)
        for name in sorted(_REVIEW_NAMES)
    )
    manifest_bytes = _read_pinned(directory / _MANIFEST, expected_sha256)
    manifest = _object(manifest_bytes, "typed cell review manifest")
    capture = manifest.get("capture")
    if (
        manifest.get("schema") != "quarantined-rootsi-cell-review.v1"
        or manifest.get("scientific_admission") != "refused"
        or not isinstance(capture, dict)
    ):
        _refuse("typed_review_posture", directory)
    capture = cast(JsonObject, capture)
    selected = capture.get("selected_workbooks")
    if (
        capture.get("inventory_sha256") != NATIVE_INVENTORY_SHA256
        or capture.get("archive_sha256") != ARCHIVE_SHA256
        or capture.get("available_workbooks") != WORKBOOKS
        or capture.get("scope") != "complete_retained_capture"
        or capture.get("archive_membership_verification")
        != "retained_receipt_bound_not_replayed"
        or selected != list(roster)
    ):
        _refuse("typed_review_capture", directory)
    members = manifest.get("members")
    if not isinstance(members, dict) or set(members) != _REVIEW_NAMES - {_MANIFEST}:
        _refuse("typed_review_member_inventory", directory)
    for name in sorted(_REVIEW_NAMES - {_MANIFEST}):
        if members.get(name) != _file_identity(directory / name):
            _refuse("typed_review_member_identity", name)
    accounting = _object(
        (directory / "accounting.json").read_bytes(), "typed review accounting"
    )
    if (
        accounting.get("workbooks") != WORKBOOKS
        or accounting.get("sheets") != SHEETS
        or accounting.get("rectangle_positions") != RECTANGLE_POSITIONS
        or accounting.get("scientifically_admitted_observations") != 0
    ):
        _refuse("typed_review_denominators", accounting)
    return manifest, accounting, snapshots


def _candidate_closure(
    directory: Path, expected_sha256: str
) -> tuple[JsonObject, JsonObject, tuple[_Snapshot, ...]]:
    directory = _directory_files(directory, _CLOSURE_NAMES, "candidate closure")
    snapshots = tuple(
        _snapshot(f"candidate_closure:{name}", directory / name)
        for name in sorted(_CLOSURE_NAMES)
    )
    manifest = _object(
        _read_pinned(directory / _MANIFEST, expected_sha256),
        "candidate closure manifest",
    )
    if (
        manifest.get("schema_version") != "essd-rootsi-input-closure-manifest.v1"
        or manifest.get("profile") != "landclim-ii-rootsi-metadata-candidate-closure-v1"
    ):
        _refuse("candidate_closure_profile", directory)
    contract = manifest.get("output_contract")
    if (
        not isinstance(contract, dict)
        or contract.get("candidate_pair_identity_sha256")
        != CANDIDATE_PAIR_IDENTITY_SHA256
    ):
        _refuse("candidate_pair_identity", directory)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 4:
        _refuse("candidate_artifact_inventory", directory)
    expected_artifacts = _CLOSURE_NAMES - {_MANIFEST}
    seen: set[str] = set()
    ordered_names: list[str] = []
    for raw in artifacts:
        if not isinstance(raw, dict):
            _refuse("candidate_artifact_record", directory)
        row = cast(JsonObject, raw)
        name = _text(row.get("path"), "candidate artifact")
        if name not in expected_artifacts or name in seen:
            _refuse("candidate_artifact_inventory", name)
        seen.add(name)
        ordered_names.append(name)
        identity = _file_identity(directory / name)
        if (
            row.get("sha256") != identity["sha256"]
            or row.get("byte_count") != identity["bytes"]
        ):
            _refuse("candidate_artifact_identity", name)
    if seen != expected_artifacts:
        _refuse("candidate_artifact_inventory", directory)
    report = _object((directory / _REPORT).read_bytes(), "candidate closure report")
    pair = report.get("pair_identity")
    claims = report.get("claims")
    if (
        not isinstance(pair, dict)
        or pair.get("sha256") != CANDIDATE_PAIR_IDENTITY_SHA256
        or pair.get("accepted_pairs") != WORKBOOKS
        or not isinstance(claims, dict)
        or claims.get("rootsi_is_authenticated_historical_input") is not False
        or claims.get("whole_paper_reproduction_certified") is not False
        or claims.get("publication_allowed") is not False
    ):
        _refuse("candidate_closure_claims", directory)
    try:
        crosswalk_text = (directory / "rootsi-crosswalk.csv").read_text(
            encoding="utf-8"
        )
    except UnicodeError as exc:
        _refuse("candidate_crosswalk_encoding", exc)
    reader = csv.DictReader(io.StringIO(crosswalk_text, newline=""))
    crosswalk = list(reader)
    if (
        reader.fieldnames is None
        or len(set(reader.fieldnames)) != len(reader.fieldnames)
        or len(crosswalk) != 81
    ):
        _refuse("candidate_crosswalk_contract", directory)
    eke = [row for row in crosswalk if row.get("rootsi_sequence_label_raw") == "EKE"]
    if len(eke) != 1 or {
        "rootsi_source_row": eke[0].get("rootsi_source_row"),
        "rootsi_sample_count_raw": eke[0].get("rootsi_sample_count_raw"),
        "rootsi_sample_count_claim": eke[0].get("rootsi_sample_count_claim"),
        "publication_candidate_rows_json": eke[0].get(
            "publication_candidate_rows_json"
        ),
        "sample_count_agrees_json": eke[0].get("sample_count_agrees_json"),
        "historical_primary_input_identity_status": eke[0].get(
            "historical_primary_input_identity_status"
        ),
    } != {
        "rootsi_source_row": "14",
        "rootsi_sample_count_raw": "25",
        "rootsi_sample_count_claim": "25",
        "publication_candidate_rows_json": "[981]",
        "sample_count_agrees_json": "[false]",
        "historical_primary_input_identity_status": "not_authenticated",
    }:
        _refuse("eke_candidate_context", eke)
    return manifest, report, snapshots


def _review_structure(
    directory: Path, roster: tuple[JsonObject, ...], workbook_files: dict[str, Path]
) -> tuple[tuple[_Workbook, ...], tuple[_Sheet, ...]]:
    raw_workbooks = _array(
        (directory / "workbooks.json").read_bytes(), "typed workbooks"
    )
    if len(raw_workbooks) != WORKBOOKS:
        _refuse("workbook_count", len(raw_workbooks))
    workbooks: list[_Workbook] = []
    for raw, source in zip(raw_workbooks, roster, strict=True):
        if not isinstance(raw, dict):
            _refuse("workbook_record", "object required")
        row = cast(JsonObject, raw)
        member = cast(str, source["archive_member"])
        mode = _integer(row.get("excel_date_mode"), "excel_date_mode")
        if mode not in (0, 1):
            _refuse("excel_date_mode", member)
        workbook = _Workbook(
            archive_member=member,
            path=workbook_files[member],
            sha256=cast(str, source["sha256"]),
            byte_count=cast(int, source["bytes"]),
            workbook_id=_digest(row.get("workbook_id"), "workbook_id"),
            excel_date_mode=mode,
            sheet_count=_integer(row.get("sheet_count"), "sheet_count", minimum=1),
        )
        if (
            set(row)
            != {
                "archive_member",
                "bytes",
                "excel_date_mode",
                "sha256",
                "sheet_count",
                "workbook_id",
            }
            or row.get("archive_member") != member
            or row.get("sha256") != workbook.sha256
            or row.get("bytes") != workbook.byte_count
            or row.get("workbook_id")
            != _source_id(ARCHIVE_SHA256, member, workbook.sha256)
        ):
            _refuse("workbook_record_identity", member)
        workbooks.append(workbook)
    sheet_rows = tuple(_json_lines(directory / "sheets.jsonl"))
    if len(sheet_rows) != SHEETS:
        _refuse("sheet_count", len(sheet_rows))
    sheets: list[_Sheet] = []
    position = 0
    rectangle_positions = 0
    for workbook in workbooks:
        for ordinal in range(workbook.sheet_count):
            row = sheet_rows[position]
            position += 1
            if set(row) != {
                "workbook_id",
                "sheet_ordinal",
                "name",
                "nrows",
                "ncols",
                "rectangle_positions",
                "merged_ranges",
            }:
                _refuse("sheet_fields", workbook.archive_member)
            rows = _integer(row.get("nrows"), "nrows")
            columns = _integer(row.get("ncols"), "ncols")
            rectangle = _integer(row.get("rectangle_positions"), "positions")
            if (
                row.get("workbook_id") != workbook.workbook_id
                or row.get("sheet_ordinal") != ordinal
                or rectangle != rows * columns
            ):
                _refuse("sheet_identity", workbook.archive_member)
            raw_ranges = row.get("merged_ranges")
            if not isinstance(raw_ranges, list):
                _refuse("merged_ranges", workbook.archive_member)
            ranges: list[tuple[int, int, int, int]] = []
            for raw_range in raw_ranges:
                if not isinstance(raw_range, list) or len(raw_range) != 4:
                    _refuse("merged_range", workbook.archive_member)
                values = tuple(_integer(value, "merged range") for value in raw_range)
                ranges.append(cast(tuple[int, int, int, int], values))
            sheets.append(
                _Sheet(
                    workbook.workbook_id,
                    ordinal,
                    _text(row.get("name"), "sheet name"),
                    rows,
                    columns,
                    rectangle,
                    tuple(ranges),
                )
            )
            rectangle_positions += rectangle
    if position != len(sheet_rows) or rectangle_positions != RECTANGLE_POSITIONS:
        _refuse("sheet_partition", rectangle_positions)
    return tuple(workbooks), tuple(sheets)


def _validate_governed_pins(source: RootsiWorkbookReplayInput) -> None:
    pins = {
        "cell review": (
            source.expected_cell_review_manifest_sha256,
            TYPED_CELL_REVIEW_MANIFEST_SHA256,
        ),
        "native inventory": (
            source.expected_native_inventory_sha256,
            NATIVE_INVENTORY_SHA256,
        ),
        "metadata": (source.expected_rootsi_metadata_sha256, METADATA_SHA256),
        "candidate closure": (
            source.expected_candidate_closure_manifest_sha256,
            CANDIDATE_CLOSURE_MANIFEST_SHA256,
        ),
    }
    for label, (actual, expected) in pins.items():
        if actual != expected:
            _refuse("ungoverned_parent", label)


def _load_inputs(source: RootsiWorkbookReplayInput) -> _Inputs:
    """Replay exact workbook bytes, then load structural review rows."""
    if not isinstance(source, RootsiWorkbookReplayInput):
        _refuse("untyped_input", type(source).__name__)
    _validate_governed_pins(source)
    inventory_path = _checked_path(source.native_inventory_path)
    inventory_bytes = _read_pinned(
        inventory_path, source.expected_native_inventory_sha256
    )
    roster = _native_inventory(inventory_bytes)
    workbook_files, workbook_snapshots = _workbook_files(
        source.workbook_directory, roster
    )
    review_dir = _directory_files(
        source.typed_cell_review_dir, _REVIEW_NAMES, "typed cell review"
    )
    before = (
        _snapshot("native_inventory", inventory_path),
        *workbook_snapshots,
        _snapshot("rootsi_metadata", source.rootsi_metadata_path),
    )
    _replay_cell_review(
        review_dir,
        expected_manifest_sha256=source.expected_cell_review_manifest_sha256,
        inventory_path=inventory_path,
        expected_inventory_sha256=source.expected_native_inventory_sha256,
        workbook_files=workbook_files,
        scope="complete_retained_capture",
    )
    _require_unchanged(before)
    review_manifest, review_accounting, review_snapshots = _review_manifest(
        review_dir, source.expected_cell_review_manifest_sha256, roster
    )
    if (
        _file_identity(inventory_path)
        != _file_identity(review_dir / "capture-inventory.json")
        or inventory_bytes != (review_dir / "capture-inventory.json").read_bytes()
    ):
        _refuse("inventory_copy_mismatch", review_dir)
    metadata_path = _checked_path(source.rootsi_metadata_path)
    if (
        _file_identity(metadata_path)["sha256"]
        != source.expected_rootsi_metadata_sha256
    ):
        _refuse("metadata_digest_mismatch", metadata_path)
    metadata = normalize_rootsi_site_metadata(metadata_path)
    if len(metadata) != 81:
        _refuse("metadata_denominator", len(metadata))
    candidate_manifest, candidate_report, candidate_snapshots = _candidate_closure(
        source.candidate_closure_dir,
        source.expected_candidate_closure_manifest_sha256,
    )
    workbooks, sheets = _review_structure(review_dir, roster, workbook_files)
    snapshots = tuple(
        sorted(
            (*before, *review_snapshots, *candidate_snapshots),
            key=lambda item: item.label,
        )
    )
    _require_unchanged(snapshots)
    return _Inputs(
        source,
        snapshots,
        review_manifest,
        review_accounting,
        workbooks,
        sheets,
        metadata,
        candidate_manifest,
        candidate_report,
    )


def _require_unchanged(snapshots: Sequence[_Snapshot]) -> None:
    for snapshot in snapshots:
        if _file_identity(snapshot.path) != snapshot.as_dict():
            _refuse("input_changed", snapshot.label)


def _cell_nonempty(cell: JsonObject) -> bool:
    cell_type = cast(int, cell["cell_type"])
    if cell_type in (0, 6):
        return False
    if cell_type == 1:
        return cell["decoded_value"] != ""
    return True


def _cell_kind(cell_type: int) -> str:
    return {
        0: "empty",
        1: "text",
        2: "number",
        3: "date",
        4: "boolean",
        5: "error",
        6: "blank",
    }.get(cell_type, "unsupported")


def _validate_cell(
    cell: JsonObject, workbook: _Workbook, sheet: _Sheet, row: int, column: int
) -> None:
    if set(cell) != _CELL_FIELDS:
        _refuse("cell_fields", cell.get("cell_id"))
    cell_type = _integer(cell.get("cell_type"), "cell_type")
    if (
        cell.get("workbook_id") != workbook.workbook_id
        or cell.get("sheet_ordinal") != sheet.ordinal
        or cell.get("row") != row
        or cell.get("column") != column
        or cell.get("cell_id")
        != _source_id(workbook.workbook_id, sheet.ordinal, row, column)
    ):
        _refuse("cell_position", f"{workbook.archive_member}:{row}:{column}")
    decoded = cell.get("decoded_value")
    binary64 = cell.get("binary64_hex")
    if cell_type in (0, 1, 6):
        if not isinstance(decoded, str) or (cell_type in (0, 6) and decoded != ""):
            _refuse("cell_text_contract", cell.get("cell_id"))
        if binary64 is not None:
            _refuse("cell_binary64_contract", cell.get("cell_id"))
    elif cell_type in (2, 3):
        binary = _text(binary64, "binary64_hex")
        try:
            value = float.fromhex(binary)
        except ValueError as exc:
            _refuse("invalid_binary64", exc)
        if value.hex() != binary:
            _refuse("noncanonical_binary64", binary)
        if math.isfinite(value):
            if type(decoded) not in (int, float) or decoded != value:
                _refuse("decoded_number_mismatch", cell.get("cell_id"))
        elif decoded is not None:
            _refuse("decoded_number_mismatch", cell.get("cell_id"))
    elif cell_type in (4, 5):
        _integer(decoded, "boolean or error")
    refusal_reason = cell.get("refusal_reason")
    if refusal_reason is not None and not isinstance(refusal_reason, str):
        _refuse("cell_refusal_reason", cell.get("cell_id"))
    xf_index = cell.get("xf_index")
    if xf_index is not None and type(xf_index) is not int:
        _refuse("cell_xf_index", cell.get("cell_id"))


def _analyze_sheet(
    cells: Iterator[JsonObject], workbook: _Workbook, sheet: _Sheet
) -> _SheetAnalysis:
    rows: list[_Row] = []
    nonempty_cells = 0
    nonempty_rows = 0
    maximum_text = -1
    header_rows: list[int] = []
    header_cells: tuple[JsonObject, ...] = ()
    for row_index in range(sheet.rows):
        row_cells: list[JsonObject] = []
        counts: Counter[str] = Counter()
        row_nonempty = 0
        nonempty_text = 0
        digest = hashlib.sha256()
        for column in range(sheet.columns):
            cell = next(cells, None)
            if cell is None:
                _refuse(
                    "missing_cell", f"{workbook.archive_member}:{row_index}:{column}"
                )
            _validate_cell(cell, workbook, sheet, row_index, column)
            row_cells.append(cell)
            digest.update(_encode(cell))
            cell_type = cast(int, cell["cell_type"])
            counts[_cell_kind(cell_type)] += 1
            if _cell_nonempty(cell):
                row_nonempty += 1
            if cell_type == 1 and cell["decoded_value"] != "":
                nonempty_text += 1
        if row_nonempty:
            nonempty_rows += 1
            nonempty_cells += row_nonempty
        rows.append(
            _Row(
                row_index,
                digest.hexdigest(),
                row_nonempty,
                nonempty_text,
                tuple((name, counts[name]) for name in _STRUCTURAL_COUNT_NAMES),
                tuple(row_cells),
            )
        )
        if nonempty_text > maximum_text:
            maximum_text = nonempty_text
            header_rows = [row_index]
            header_cells = tuple(row_cells)
        elif nonempty_text == maximum_text:
            header_rows.append(row_index)
    header_row: int | None = None
    if nonempty_cells:
        if maximum_text <= 0 or len(header_rows) != 1:
            _refuse("ambiguous_header", workbook.archive_member)
        header_row = header_rows[0]
    return _SheetAnalysis(
        sheet,
        nonempty_cells,
        nonempty_rows,
        tuple(rows),
        header_row,
        header_cells,
    )


def _profile(
    workbook: _Workbook,
    analyses: tuple[_SheetAnalysis, ...],
) -> tuple[JsonObject, tuple[JsonObject, ...], tuple[JsonObject, ...]]:
    active = tuple(item for item in analyses if item.nonempty_cells)
    if len(active) != 1:
        _refuse("nonempty_sheet_count", workbook.archive_member)
    sheet = active[0]
    if sheet.header_row is None:
        _refuse("missing_header", workbook.archive_member)
    header_row = sheet.rows[sheet.header_row]
    candidates = tuple(
        row
        for row in sheet.rows
        if row.index > sheet.header_row and row.nonempty_cells > 0
    )
    if not candidates or tuple(row.index for row in candidates) != tuple(
        range(candidates[0].index, candidates[-1].index + 1)
    ):
        _refuse("noncontiguous_data_rows", workbook.archive_member)
    header_records = tuple(
        {
            "schema_version": "essd-rootsi-header-field.v1",
            "archive_member": workbook.archive_member,
            "workbook_id": workbook.workbook_id,
            "workbook_sha256": workbook.sha256,
            "sheet_ordinal": sheet.sheet.ordinal,
            "sheet_name": sheet.sheet.name,
            "header_row_index": sheet.header_row,
            "header_row_number": sheet.header_row + 1,
            "column_index": column,
            "column_number": column + 1,
            "cell_id": cell["cell_id"],
            "cell_type": cell["cell_type"],
            "decoded_value": cell["decoded_value"],
            "binary64_hex": cell["binary64_hex"],
            "xf_index": cell["xf_index"],
            "refusal_reason": cell["refusal_reason"],
            "nonempty_text_candidate": (
                cell["cell_type"] == 1 and cell["decoded_value"] != ""
            ),
            "scientific_classification": "unreviewed",
        }
        for column, cell in enumerate(sheet.header_cells)
    )
    row_records = tuple(
        {
            "schema_version": "essd-rootsi-data-row-candidate.v1",
            "archive_member": workbook.archive_member,
            "workbook_id": workbook.workbook_id,
            "workbook_sha256": workbook.sha256,
            "sheet_ordinal": sheet.sheet.ordinal,
            "sheet_name": sheet.sheet.name,
            "row_index": row.index,
            "row_number": row.index + 1,
            "decoded_cells_sha256": row.decoded_cells_sha256,
            "decoded_digest_contract": "canonical_cell_json_lines_sha256",
            "column_positions": sheet.sheet.columns,
            "nonempty_cells": row.nonempty_cells,
            "nonempty_text_cells": row.nonempty_text_cells,
            "structural_cell_type_counts": dict(row.structural_counts),
            "cells": list(row.cells),
            "taxonomy_status": "unreviewed",
            "chronology_status": "unreviewed",
            "unit_status": "unreviewed",
            "historical_primary_input_identity": "not_authenticated",
        }
        for row in candidates
    )
    first = sheet.header_cells[0]
    profile: JsonObject = {
        "schema_version": "essd-rootsi-workbook-profile.v1",
        "archive_member": workbook.archive_member,
        "workbook_id": workbook.workbook_id,
        "workbook_sha256": workbook.sha256,
        "workbook_bytes": workbook.byte_count,
        "excel_date_mode_raw": workbook.excel_date_mode,
        "sheet_count": workbook.sheet_count,
        "empty_auxiliary_sheets": len(analyses) - 1,
        "nonempty_sheet_ordinal": sheet.sheet.ordinal,
        "nonempty_sheet_name": sheet.sheet.name,
        "source_rows": sheet.sheet.rows,
        "source_columns": sheet.sheet.columns,
        "source_rectangle_positions": sheet.sheet.rectangle_positions,
        "header_rule": "unique_global_maximum_nonempty_text_cells",
        "header_row_index": sheet.header_row,
        "header_row_number": sheet.header_row + 1,
        "header_nonempty_text_cells": header_row.nonempty_text_cells,
        "header_decoded_cells_sha256": header_row.decoded_cells_sha256,
        "header_field_positions": len(header_records),
        "header_first_field_empty": not _cell_nonempty(first),
        "pre_header_nonempty_rows": sum(
            row.nonempty_cells > 0 for row in sheet.rows if row.index < sheet.header_row
        ),
        "data_row_rule": "every_later_nonempty_row",
        "data_row_first_index": candidates[0].index,
        "data_row_first_number": candidates[0].index + 1,
        "data_row_last_index": candidates[-1].index,
        "data_row_last_number": candidates[-1].index + 1,
        "data_row_positions": sum(sheet.sheet.columns for _ in candidates),
        "data_row_candidates": len(row_records),
        "taxonomy_status": "unreviewed",
        "chronology_status": "unreviewed",
        "axis_status": "unreviewed",
        "units_status": "unreviewed",
        "formula_origin": "unavailable",
        "numeric_decimal_lexeme": "unavailable",
        "historical_primary_input_identity": "not_authenticated",
        "scientific_admission": "refused",
    }
    return profile, header_records, row_records


def _write_json_line(stream: io.BufferedWriter, value: object) -> None:
    stream.write(_encode(value))


def _analyze_cells(
    inputs: _Inputs, stage: Path
) -> tuple[tuple[JsonObject, ...], int, int, int]:
    sheets_by_workbook: dict[str, list[_Sheet]] = {
        workbook.workbook_id: [] for workbook in inputs.workbooks
    }
    for sheet in inputs.sheets:
        sheets_by_workbook[sheet.workbook_id].append(sheet)
    profiles: list[JsonObject] = []
    header_count = 0
    row_count = 0
    cell_count = 0
    header_types: Counter[str] = Counter()
    header_nonempty_text = 0
    data_types: Counter[str] = Counter()
    data_positions = 0
    data_text_cells: list[tuple[str, JsonObject]] = []
    with (
        (stage / _WORKBOOK_PROFILES).open("xb") as profile_stream,
        (stage / _HEADER_FIELDS).open("xb") as header_stream,
        (stage / _DATA_ROWS).open("xb") as row_stream,
    ):
        cells = iter(_json_lines(inputs.source.typed_cell_review_dir / "cells.jsonl"))
        for workbook in inputs.workbooks:
            analyses = tuple(
                _analyze_sheet(cells, workbook, sheet)
                for sheet in sheets_by_workbook[workbook.workbook_id]
            )
            cell_count += sum(item.sheet.rectangle_positions for item in analyses)
            profile, headers, rows = _profile(workbook, analyses)
            profiles.append(profile)
            _write_json_line(profile_stream, profile)
            for record in headers:
                _write_json_line(header_stream, record)
                kind = _cell_kind(cast(int, record["cell_type"]))
                header_types[kind] += 1
                header_nonempty_text += int(record["nonempty_text_candidate"] is True)
            for record in rows:
                _write_json_line(row_stream, record)
                cells_value = record["cells"]
                if not isinstance(cells_value, list):
                    _refuse("data_row_cells", workbook.archive_member)
                data_positions += len(cells_value)
                for cell in cells_value:
                    if not isinstance(cell, dict):
                        _refuse("data_row_cell", workbook.archive_member)
                    cell = cast(JsonObject, cell)
                    kind = _cell_kind(cast(int, cell["cell_type"]))
                    data_types[kind] += 1
                    if kind == "text":
                        data_text_cells.append((workbook.archive_member, cell))
            header_count += len(headers)
            row_count += len(rows)
        if next(cells, None) is not None:
            _refuse("extra_cells", inputs.source.typed_cell_review_dir)
        for stream in (profile_stream, header_stream, row_stream):
            stream.flush()
            os.fsync(stream.fileno())
    if (
        len(profiles) != WORKBOOKS
        or header_count != HEADER_FIELDS
        or row_count != DATA_ROW_CANDIDATES
        or cell_count != RECTANGLE_POSITIONS
        or data_positions != DATA_ROW_POSITIONS
    ):
        _refuse(
            "mechanical_denominators",
            (len(profiles), header_count, row_count, cell_count, data_positions),
        )
    if (
        header_types
        != Counter({"text": HEADER_TEXT_POSITIONS, "empty": HEADER_EMPTY_POSITIONS})
        or header_nonempty_text != HEADER_NONEMPTY_TEXT_POSITIONS
    ):
        _refuse("header_position_partition", dict(header_types))
    if data_types != Counter(
        {
            "number": DATA_ROW_NUMERIC_POSITIONS,
            "empty": DATA_ROW_EMPTY_POSITIONS,
            "text": DATA_ROW_TEXT_POSITIONS,
        }
    ):
        _refuse("data_position_partition", dict(data_types))
    if len(data_text_cells) != 1:
        _refuse("data_text_variant", data_text_cells)
    text_member, text_cell = data_text_cells[0]
    if (
        text_member != "rootsi/RASH.xls"
        or text_cell.get("row") != 11
        or text_cell.get("column") != 53
        or text_cell.get("decoded_value") != "  "
        or text_cell.get("binary64_hex") is not None
        or text_cell.get("cell_type") != 1
    ):
        _refuse("data_text_variant", data_text_cells)
    blank_first = [
        profile["archive_member"]
        for profile in profiles
        if profile["header_first_field_empty"] is True
    ]
    if blank_first != ["rootsi/GIL.xls"]:
        _refuse("blank_first_header_variant", blank_first)
    sheet_counts = Counter(cast(int, profile["sheet_count"]) for profile in profiles)
    header_rows = Counter(
        cast(int, profile["header_row_index"]) for profile in profiles
    )
    first_rows = Counter(
        cast(int, profile["data_row_first_index"]) for profile in profiles
    )
    nonstandard_sheets = [
        profile["archive_member"]
        for profile in profiles
        if profile["nonempty_sheet_name"] != "Sheet1"
    ]
    if (
        sheet_counts != Counter({1: 65, 3: 14})
        or header_rows != Counter({0: 41, 2: 38})
        or first_rows != Counter({1: 41, 4: 38})
        or nonstandard_sheets != ["rootsi/GIL.xls"]
        or next(
            profile
            for profile in profiles
            if profile["archive_member"] == "rootsi/GIL.xls"
        )["nonempty_sheet_name"]
        != "LC_GILLT"
    ):
        _refuse(
            "workbook_structure_partition",
            (
                dict(sheet_counts),
                dict(header_rows),
                dict(first_rows),
                nonstandard_sheets,
            ),
        )
    return tuple(profiles), header_count, row_count, cell_count


def _sample_review(
    inputs: _Inputs, profiles: tuple[JsonObject, ...], stage: Path
) -> tuple[int, int, JsonObject]:
    by_member = {cast(str, profile["archive_member"]): profile for profile in profiles}
    crosswalk_path = inputs.source.candidate_closure_dir / "rootsi-crosswalk.csv"
    with crosswalk_path.open(newline="", encoding="utf-8") as crosswalk_stream:
        reader = csv.DictReader(crosswalk_stream)
        required_fields = {
            "rootsi_source_row",
            "rootsi_observation_workbook_claim",
            "typed_workbook_member",
            "publication_candidate_status",
        }
        if reader.fieldnames is None or not required_fields.issubset(reader.fieldnames):
            _refuse("candidate_workbook_binding_fields", reader.fieldnames)
        candidate_by_source_row: dict[int, dict[str, str]] = {}
        for row in reader:
            try:
                source_row = int(row["rootsi_source_row"])
            except (KeyError, ValueError) as exc:
                _refuse("candidate_workbook_binding_row", exc)
            if source_row in candidate_by_source_row:
                _refuse("duplicate_candidate_workbook_binding", source_row)
            candidate_by_source_row[source_row] = row
    if set(candidate_by_source_row) != {
        claim.source_row_number for claim in inputs.metadata
    }:
        _refuse("candidate_workbook_binding_partition", len(candidate_by_source_row))

    metadata_by_member: dict[str, RootsiSiteMetadataClaim] = {}
    for claim in inputs.metadata:
        candidate = candidate_by_source_row[claim.source_row_number]
        raw_claim = candidate["rootsi_observation_workbook_claim"]
        if raw_claim != (claim.observation_workbook_claim or ""):
            _refuse("candidate_metadata_claim_mismatch", claim.source_row_number)
        member_raw = candidate["typed_workbook_member"]
        if claim.observation_workbook_claim is None:
            if (
                member_raw
                or candidate["publication_candidate_status"]
                != "no_rootsi_metadata_candidate"
            ):
                _refuse(
                    "unexpected_candidate_workbook_binding", claim.source_row_number
                )
            continue
        if (
            candidate["publication_candidate_status"]
            != "unique_rootsi_metadata_candidate"
        ):
            _refuse("unqualified_candidate_workbook_binding", claim.source_row_number)
        # Use the exact candidate-closure member while retaining the metadata's
        # native workbook claim below; case spelling is not historical identity.
        member = _member_name(member_raw)
        if member not in by_member:
            _refuse("candidate_workbook_not_replayed", member)
        if member in metadata_by_member:
            _refuse("duplicate_metadata_workbook_claim", member)
        metadata_by_member[member] = claim
    if set(metadata_by_member) != set(by_member):
        _refuse("metadata_workbook_partition", "79 exact claims required")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(_SAMPLE_COLUMNS)
    agreements = 0
    mismatch: JsonObject | None = None
    for member in sorted(by_member):
        profile = by_member[member]
        claim = metadata_by_member[member]
        source_values = dict(claim.source_values)
        rows = cast(int, profile["data_row_candidates"])
        agrees = claim.sample_count_claim == rows
        agreements += int(agrees)
        status = "agrees" if agrees else "mismatch_preserved"
        writer.writerow(
            (
                "essd-rootsi-sample-denominator-review.v1",
                member,
                profile["workbook_sha256"],
                claim.source_row_number,
                f"{METADATA_MEMBER}!{claim.source_row_number}",
                claim.site_name,
                claim.site_label,
                claim.observation_workbook_claim,
                source_values["nr_samples"],
                "" if claim.sample_count_claim is None else claim.sample_count_claim,
                rows,
                str(agrees).lower(),
                status,
                "not_authenticated",
            )
        )
        if not agrees:
            mismatch = {
                "archive_member": member,
                "metadata_sample_count_raw": source_values["nr_samples"],
                "metadata_sample_count_claim": claim.sample_count_claim,
                "mechanical_data_row_candidates": rows,
                "status": status,
            }
    content = stream.getvalue().encode("utf-8")
    with (stage / _SAMPLE_REVIEW).open("xb") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    expected_mismatch = {
        "archive_member": "rootsi/EKE.xls",
        "metadata_sample_count_raw": "25",
        "metadata_sample_count_claim": 25,
        "mechanical_data_row_candidates": 42,
        "status": "mismatch_preserved",
    }
    if agreements != SAMPLE_DENOMINATOR_AGREEMENTS or mismatch != expected_mismatch:
        _refuse("sample_denominator_partition", mismatch)
    return len(by_member), agreements, expected_mismatch


def _claims() -> JsonObject:
    return {
        "workbook_bytes_replayed_against_typed_cells": True,
        "archive_membership_replayed": False,
        "archive_membership_verification": "retained_receipt_bound_not_replayed",
        "candidate_pair_promoted_to_historical_identity": False,
        "historical_primary_input_identity_verified": False,
        "chronology_interpreted": False,
        "taxonomy_interpreted": False,
        "axes_interpreted": False,
        "zeros_interpreted": False,
        "negatives_interpreted": False,
        "formulas_recovered": False,
        "units_interpreted": False,
        "basin_and_profile_semantics_reviewed": False,
        "rights_cleared": False,
        "reproduction_ready": False,
        "whole_paper_reproduction_certified": False,
        "scientifically_accepted": False,
        "scientific_acceptance": "not_evaluated",
        "public_release_allowed": False,
    }


def _source_manifest(inputs: _Inputs) -> JsonObject:
    roster = [workbook.source_dict() for workbook in inputs.workbooks]
    review_files = {
        snapshot.path.name: snapshot.as_dict()
        for snapshot in inputs.snapshots
        if snapshot.label.startswith("typed_cell_review:")
    }
    closure_files = {
        snapshot.path.name: snapshot.as_dict()
        for snapshot in inputs.snapshots
        if snapshot.label.startswith("candidate_closure:")
    }
    metadata = next(
        snapshot for snapshot in inputs.snapshots if snapshot.label == "rootsi_metadata"
    )
    inventory = next(
        snapshot
        for snapshot in inputs.snapshots
        if snapshot.label == "native_inventory"
    )
    return {
        "typed_cell_review": {
            "manifest_sha256": inputs.source.expected_cell_review_manifest_sha256,
            "schema": inputs.review_manifest["schema"],
            "files": review_files,
            "files_sha256": _sha256(_encode(review_files)),
            "workbooks": WORKBOOKS,
            "sheets": SHEETS,
            "rectangle_positions": RECTANGLE_POSITIONS,
            "scientific_admission": "refused",
        },
        "native_inventory": {
            **inventory.as_dict(),
            "archive_sha256": ARCHIVE_SHA256,
            "workbook_roster_sha256": WORKBOOK_ROSTER_SHA256,
            "workbooks": WORKBOOKS,
            "archive_membership_verification": ("retained_receipt_bound_not_replayed"),
        },
        "retained_workbooks": {
            "count": WORKBOOKS,
            "roster_sha256": WORKBOOK_ROSTER_SHA256,
            "members": roster,
        },
        "rootsi_metadata": {
            **metadata.as_dict(),
            "archive_sha256": ARCHIVE_SHA256,
            "member": METADATA_MEMBER,
            "records": 81,
        },
        "candidate_closure": {
            "manifest_sha256": (
                inputs.source.expected_candidate_closure_manifest_sha256
            ),
            "schema_version": inputs.candidate_manifest["schema_version"],
            "files": closure_files,
            "files_sha256": _sha256(_encode(closure_files)),
            "candidate_pair_identity_sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
            "accepted_pairs": WORKBOOKS,
            "candidate_pair_promoted": False,
        },
    }


def _report(
    inputs: _Inputs,
    *,
    mismatch: JsonObject,
) -> JsonObject:
    without_workbook = [
        {
            "rootsi_source_row": claim.source_row_number,
            "rootsi_site_name_raw": claim.site_name,
            "rootsi_sequence_label_raw": claim.site_label,
            "observation_workbook_claim": None,
            "status": "source_metadata_no_workbook_claim",
        }
        for claim in inputs.metadata
        if claim.observation_workbook_claim is None
    ]
    if without_workbook != [
        {
            "rootsi_source_row": 3,
            "rootsi_site_name_raw": "Åbodasjön",
            "rootsi_sequence_label_raw": "ABO",
            "observation_workbook_claim": None,
            "status": "source_metadata_no_workbook_claim",
        },
        {
            "rootsi_source_row": 46,
            "rootsi_site_name_raw": "Lindhultsgöl",
            "rootsi_sequence_label_raw": "LIND",
            "observation_workbook_claim": None,
            "status": "source_metadata_no_workbook_claim",
        },
    ]:
        _refuse("metadata_without_workbook_claim", without_workbook)
    mismatch = {
        **mismatch,
        "landclim_candidate_publication_rows": [981],
        "landclim_candidate_reported_sample_count": 42,
        "candidate_count_coincidence_resolves_revision_identity": False,
    }
    return {
        "schema_version": "essd-rootsi-retained-workbook-replay-report.v1",
        "profile": PROFILE,
        "status": STATUS,
        "source_hashes": {
            "typed_cell_review_manifest_sha256": (
                inputs.source.expected_cell_review_manifest_sha256
            ),
            "native_inventory_sha256": inputs.source.expected_native_inventory_sha256,
            "workbook_roster_sha256": WORKBOOK_ROSTER_SHA256,
            "rootsi_metadata_sha256": inputs.source.expected_rootsi_metadata_sha256,
            "candidate_closure_manifest_sha256": (
                inputs.source.expected_candidate_closure_manifest_sha256
            ),
            "candidate_pair_identity_sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
        },
        "observed_denominators": {
            "workbooks": WORKBOOKS,
            "sheets": SHEETS,
            "rectangle_positions_streamed": RECTANGLE_POSITIONS,
            "workbook_profiles": WORKBOOKS,
            "header_field_positions": HEADER_FIELDS,
            "data_row_candidates": DATA_ROW_CANDIDATES,
            "sample_denominator_records": SAMPLE_DENOMINATOR_RECORDS,
            "sample_denominator_agreements": SAMPLE_DENOMINATOR_AGREEMENTS,
            "sample_denominator_mismatches": 1,
            "blank_first_header_variants": 1,
            "metadata_rows_without_workbook_claim": 2,
            "data_row_candidate_positions": DATA_ROW_POSITIONS,
            "data_row_numeric_positions": DATA_ROW_NUMERIC_POSITIONS,
            "data_row_empty_positions": DATA_ROW_EMPTY_POSITIONS,
            "data_row_text_positions": DATA_ROW_TEXT_POSITIONS,
        },
        "mechanical_rules": {
            "nonempty_sheet": "contains_at_least_one_nonempty_decoded_cell",
            "sheet_selection": "exactly_one_nonempty_sheet_per_workbook",
            "header": "unique_row_with_global_maximum_nonempty_text_cells",
            "header_fields": "every_source_column_position_on_selected_header_row",
            "data_rows": "every_later_nonempty_row",
            "empty_auxiliary_sheets": "allowed",
            "header_ties": "refused",
            "multiple_nonempty_sheets": "refused",
        },
        "preserved_variants": {
            "sample_denominator_mismatch": mismatch,
            "blank_first_header_field": {
                "archive_member": "rootsi/GIL.xls",
                "preserved": True,
                "interpretation": "structural_variant_only",
            },
            "metadata_without_workbook_claim": without_workbook,
            "whitespace_data_cell": {
                "archive_member": "rootsi/RASH.xls",
                "row_index": 11,
                "column_index": 53,
                "decoded_value": "  ",
                "interpretation": "preserved_source_text_not_missingness_decision",
            },
        },
        "candidate_pair": {
            "sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
            "accepted_pairs": WORKBOOKS,
            "interpretation": "metadata_candidate_not_historical_input_identity",
        },
        "claims": _claims(),
        "blocking_dependencies": [
            "historical workbook revision identity",
            "selected chronology and sample identity",
            "taxon and count-denominator review",
            "axis and unit review",
            "formula provenance",
            "per-sequence rights",
            "basin and publication-profile semantics",
            "qualified scientific review",
        ],
    }


def _artifact(name: str, path: Path, logical_rows: int) -> JsonObject:
    identity = _file_identity(path)
    return {
        "path": name,
        "sha256": identity["sha256"],
        "byte_count": identity["bytes"],
        "logical_rows": logical_rows,
    }


def _write_stage(inputs: _Inputs, stage: Path, producer: JsonObject) -> str:
    profiles, header_count, row_count, cell_count = _analyze_cells(inputs, stage)
    sample_count, agreements, mismatch = _sample_review(inputs, profiles, stage)
    if (
        header_count != HEADER_FIELDS
        or row_count != DATA_ROW_CANDIDATES
        or cell_count != RECTANGLE_POSITIONS
        or sample_count != SAMPLE_DENOMINATOR_RECORDS
        or agreements != SAMPLE_DENOMINATOR_AGREEMENTS
    ):
        _refuse("stage_denominators", stage)
    report = _report(inputs, mismatch=mismatch)
    with (stage / _REPORT).open("xb") as stream:
        stream.write(_encode(report))
        stream.flush()
        os.fsync(stream.fileno())
    artifacts = [
        _artifact(_WORKBOOK_PROFILES, stage / _WORKBOOK_PROFILES, WORKBOOKS),
        _artifact(_HEADER_FIELDS, stage / _HEADER_FIELDS, HEADER_FIELDS),
        _artifact(_DATA_ROWS, stage / _DATA_ROWS, DATA_ROW_CANDIDATES),
        _artifact(_SAMPLE_REVIEW, stage / _SAMPLE_REVIEW, SAMPLE_DENOMINATOR_RECORDS),
        _artifact(_REPORT, stage / _REPORT, 1),
    ]
    manifest: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "profile": PROFILE,
        "status": STATUS,
        "producer": {
            "files": producer,
            "files_sha256": _sha256(_encode(producer)),
        },
        "sources": _source_manifest(inputs),
        "output_contract": {
            "output_file_count": len(_OUTPUT_NAMES),
            "workbook_profiles": WORKBOOKS,
            "header_field_positions": HEADER_FIELDS,
            "data_row_candidates": DATA_ROW_CANDIDATES,
            "sample_denominator_records": SAMPLE_DENOMINATOR_RECORDS,
            "sample_denominator_agreements": SAMPLE_DENOMINATOR_AGREEMENTS,
            "candidate_pair_identity_sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
            "csv_null_encoding": "empty_field_with_explicit_status_columns",
        },
        "artifacts": artifacts,
        "claims": _claims(),
    }
    manifest_bytes = _encode(manifest)
    with (stage / _MANIFEST).open("xb") as stream:
        stream.write(manifest_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    _fsync_directory(stage)
    return _sha256(manifest_bytes)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _destination(source: RootsiWorkbookReplayInput, destination: Path) -> Path:
    target = _checked_path(destination)
    if target.exists() or target.is_symlink():
        _refuse("destination_exists", target)
    inputs = (
        _checked_path(source.typed_cell_review_dir),
        _checked_path(source.native_inventory_path),
        _checked_path(source.workbook_directory),
        _checked_path(source.rootsi_metadata_path),
        _checked_path(source.candidate_closure_dir),
    )
    if any(
        target == item or target.is_relative_to(item) or item.is_relative_to(target)
        for item in inputs
    ):
        _refuse("output_overlaps_input", target)
    return target


def _output_identity_map(directory: Path) -> dict[str, JsonObject]:
    return {name: _file_identity(directory / name) for name in _OUTPUT_NAMES}


def _read_output_manifest(
    directory: Path, expected_manifest_sha256: str
) -> tuple[JsonObject, dict[str, JsonObject]]:
    directory = _directory_files(directory, set(_OUTPUT_NAMES), "replay bundle")
    manifest_bytes = (directory / _MANIFEST).read_bytes()
    manifest_identity = {
        "sha256": _sha256(manifest_bytes),
        "bytes": len(manifest_bytes),
    }
    if manifest_identity["sha256"] != _digest(
        expected_manifest_sha256, "manifest_sha256"
    ):
        _refuse("manifest_digest_mismatch", directory)
    return _object(manifest_bytes, _MANIFEST), {_MANIFEST: manifest_identity}


def _manifest_contract(manifest: JsonObject) -> None:
    if set(manifest) != {
        "schema_version",
        "profile",
        "status",
        "producer",
        "sources",
        "output_contract",
        "artifacts",
        "claims",
    }:
        _refuse("manifest_fields", sorted(manifest))
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["profile"] != PROFILE
        or manifest["status"] != STATUS
        or manifest["claims"] != _claims()
    ):
        _refuse("manifest_posture", "claims or profile changed")
    producer = manifest["producer"]
    if not isinstance(producer, dict) or set(producer) != {"files", "files_sha256"}:
        _refuse("producer_contract", producer)
    files = producer["files"]
    if (
        not isinstance(files, dict)
        or set(files) != {"essd_reproduction/rootsi_workbook_replay.py"}
        or producer["files_sha256"] != _sha256(_encode(files))
    ):
        _refuse("producer_contract", producer)
    for identity in files.values():
        if (
            not isinstance(identity, dict)
            or set(identity) != {"sha256", "bytes"}
            or _digest(identity.get("sha256"), "producer sha256")
            != identity.get("sha256")
            or _integer(identity.get("bytes"), "producer bytes", minimum=1)
            != identity.get("bytes")
        ):
            _refuse("producer_contract", identity)
    contract = manifest["output_contract"]
    expected_contract = {
        "output_file_count": len(_OUTPUT_NAMES),
        "workbook_profiles": WORKBOOKS,
        "header_field_positions": HEADER_FIELDS,
        "data_row_candidates": DATA_ROW_CANDIDATES,
        "sample_denominator_records": SAMPLE_DENOMINATOR_RECORDS,
        "sample_denominator_agreements": SAMPLE_DENOMINATOR_AGREEMENTS,
        "candidate_pair_identity_sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
        "csv_null_encoding": "empty_field_with_explicit_status_columns",
    }
    if contract != expected_contract:
        _refuse("output_contract", contract)
    sources = manifest["sources"]
    if not isinstance(sources, dict) or set(sources) != {
        "typed_cell_review",
        "native_inventory",
        "retained_workbooks",
        "rootsi_metadata",
        "candidate_closure",
    }:
        _refuse("source_manifest", "object required")
    review = sources.get("typed_cell_review")
    native = sources.get("native_inventory")
    retained = sources.get("retained_workbooks")
    metadata = sources.get("rootsi_metadata")
    closure = sources.get("candidate_closure")
    if not all(
        isinstance(value, dict)
        for value in (review, native, retained, metadata, closure)
    ):
        _refuse("source_manifest", "five parents required")
    review = cast(JsonObject, review)
    native = cast(JsonObject, native)
    retained = cast(JsonObject, retained)
    metadata = cast(JsonObject, metadata)
    closure = cast(JsonObject, closure)
    if (
        set(review)
        != {
            "manifest_sha256",
            "schema",
            "files",
            "files_sha256",
            "workbooks",
            "sheets",
            "rectangle_positions",
            "scientific_admission",
        }
        or set(native)
        != {
            "sha256",
            "bytes",
            "archive_sha256",
            "workbook_roster_sha256",
            "workbooks",
            "archive_membership_verification",
        }
        or set(retained) != {"count", "roster_sha256", "members"}
        or set(metadata) != {"sha256", "bytes", "archive_sha256", "member", "records"}
        or set(closure)
        != {
            "manifest_sha256",
            "schema_version",
            "files",
            "files_sha256",
            "candidate_pair_identity_sha256",
            "accepted_pairs",
            "candidate_pair_promoted",
        }
    ):
        _refuse("source_manifest_fields", "exact source contracts required")
    review_files = review.get("files")
    closure_files = closure.get("files")
    if (
        not isinstance(review_files, dict)
        or set(review_files) != _REVIEW_NAMES
        or not isinstance(closure_files, dict)
        or set(closure_files) != _CLOSURE_NAMES
    ):
        _refuse("source_file_maps", "exact parent inventories required")
    for label, files_map in (
        ("typed cell review", review_files),
        ("candidate closure", closure_files),
    ):
        for name, identity in files_map.items():
            if (
                not isinstance(name, str)
                or not isinstance(identity, dict)
                or set(identity) != {"sha256", "bytes"}
                or _digest(identity.get("sha256"), f"{label}:{name}")
                != identity.get("sha256")
                or _integer(identity.get("bytes"), f"{label}:{name}", minimum=1)
                != identity.get("bytes")
            ):
                _refuse("source_file_map_identity", f"{label}:{name}")
    if (
        review.get("manifest_sha256") != TYPED_CELL_REVIEW_MANIFEST_SHA256
        or review.get("files_sha256") != TYPED_CELL_REVIEW_FILES_SHA256
        or review.get("files_sha256") != _sha256(_encode(review_files))
        or review.get("workbooks") != WORKBOOKS
        or review.get("schema") != "quarantined-rootsi-cell-review.v1"
        or review.get("sheets") != SHEETS
        or review.get("rectangle_positions") != RECTANGLE_POSITIONS
        or review.get("scientific_admission") != "refused"
        or native.get("sha256") != NATIVE_INVENTORY_SHA256
        or native.get("archive_sha256") != ARCHIVE_SHA256
        or native.get("workbook_roster_sha256") != WORKBOOK_ROSTER_SHA256
        or native.get("workbooks") != WORKBOOKS
        or native.get("archive_membership_verification")
        != "retained_receipt_bound_not_replayed"
        or retained.get("count") != WORKBOOKS
        or retained.get("roster_sha256") != WORKBOOK_ROSTER_SHA256
        or metadata.get("sha256") != METADATA_SHA256
        or metadata.get("bytes") != 54_688
        or metadata.get("archive_sha256") != ARCHIVE_SHA256
        or metadata.get("member") != METADATA_MEMBER
        or metadata.get("records") != 81
        or closure.get("manifest_sha256") != CANDIDATE_CLOSURE_MANIFEST_SHA256
        or closure.get("schema_version") != "essd-rootsi-input-closure-manifest.v1"
        or closure.get("files_sha256") != CANDIDATE_CLOSURE_FILES_SHA256
        or closure.get("files_sha256") != _sha256(_encode(closure_files))
        or closure.get("candidate_pair_identity_sha256")
        != CANDIDATE_PAIR_IDENTITY_SHA256
        or closure.get("accepted_pairs") != WORKBOOKS
        or closure.get("candidate_pair_promoted") is not False
    ):
        _refuse("source_manifest", "governed identities changed")
    if (
        cast(JsonObject, review_files["manifest.json"])["sha256"]
        != TYPED_CELL_REVIEW_MANIFEST_SHA256
        or cast(JsonObject, review_files["capture-inventory.json"])["sha256"]
        != NATIVE_INVENTORY_SHA256
        or cast(JsonObject, closure_files["manifest.json"])["sha256"]
        != CANDIDATE_CLOSURE_MANIFEST_SHA256
        or native.get("sha256")
        != cast(JsonObject, review_files["capture-inventory.json"])["sha256"]
        or native.get("bytes")
        != cast(JsonObject, review_files["capture-inventory.json"])["bytes"]
    ):
        _refuse("direct_parent_digest_agreement", "manifest or inventory")
    members = retained.get("members")
    if (
        not isinstance(members, list)
        or _sha256(_encode(members)) != WORKBOOK_ROSTER_SHA256
    ):
        _refuse("source_workbook_roster", "roster changed")
    roster_names: list[str] = []
    for value in members:
        if not isinstance(value, dict) or set(value) != {
            "archive_member",
            "sha256",
            "bytes",
        }:
            _refuse("source_workbook_record", value)
        row = cast(JsonObject, value)
        roster_names.append(_member_name(row.get("archive_member")))
        _digest(row.get("sha256"), "workbook sha256")
        _integer(row.get("bytes"), "workbook bytes", minimum=1)
    if len(roster_names) != WORKBOOKS or roster_names != sorted(set(roster_names)):
        _refuse("source_workbook_order", roster_names)


def _validate_artifacts(
    manifest: JsonObject, identities: dict[str, JsonObject]
) -> None:
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != len(_OUTPUT_NAMES) - 1:
        _refuse("artifact_inventory", "five peer files required")
    expected_rows = {
        _WORKBOOK_PROFILES: WORKBOOKS,
        _HEADER_FIELDS: HEADER_FIELDS,
        _DATA_ROWS: DATA_ROW_CANDIDATES,
        _SAMPLE_REVIEW: SAMPLE_DENOMINATOR_RECORDS,
        _REPORT: 1,
    }
    seen: set[str] = set()
    ordered_names: list[str] = []
    for value in artifacts:
        if not isinstance(value, dict):
            _refuse("artifact_record", value)
        row = cast(JsonObject, value)
        name = _text(row.get("path"), "artifact path")
        if name not in expected_rows or name in seen:
            _refuse("artifact_inventory", name)
        seen.add(name)
        ordered_names.append(name)
        if row != {
            "path": name,
            "sha256": identities[name]["sha256"],
            "byte_count": identities[name]["bytes"],
            "logical_rows": expected_rows[name],
        }:
            _refuse("artifact_identity", name)
    if seen != set(expected_rows):
        _refuse("artifact_inventory", sorted(seen))
    if ordered_names != list(expected_rows):
        _refuse("artifact_order", ordered_names)


def _emitted_cell(
    cell: JsonObject,
    *,
    workbook_id: str,
    sheet_ordinal: int,
    row: int,
    column: int,
) -> tuple[int, bool]:
    if set(cell) != _CELL_FIELDS:
        _refuse("emitted_cell_fields", cell.get("cell_id"))
    cell_type = _integer(cell.get("cell_type"), "cell_type")
    if (
        cell.get("workbook_id") != workbook_id
        or cell.get("sheet_ordinal") != sheet_ordinal
        or cell.get("row") != row
        or cell.get("column") != column
        or cell.get("cell_id") != _source_id(workbook_id, sheet_ordinal, row, column)
    ):
        _refuse("emitted_cell_identity", f"{row}:{column}")
    decoded = cell.get("decoded_value")
    binary64 = cell.get("binary64_hex")
    if cell_type in (0, 1, 6):
        if not isinstance(decoded, str) or (cell_type in (0, 6) and decoded != ""):
            _refuse("emitted_cell_text", cell.get("cell_id"))
        if binary64 is not None:
            _refuse("emitted_cell_binary64", cell.get("cell_id"))
    elif cell_type in (2, 3):
        binary = _text(binary64, "binary64_hex")
        try:
            number = float.fromhex(binary)
        except ValueError as exc:
            _refuse("emitted_cell_binary64", exc)
        if number.hex() != binary or not math.isfinite(number):
            _refuse("emitted_cell_binary64", binary)
        if type(decoded) not in (int, float) or decoded != number:
            _refuse("emitted_cell_number", cell.get("cell_id"))
    elif cell_type in (4, 5):
        _integer(decoded, "boolean or error")
    else:
        _refuse("emitted_cell_type", cell_type)
    xf_index = cell.get("xf_index")
    if xf_index is not None and (type(xf_index) is not int or xf_index < -1):
        _refuse("emitted_cell_xf", cell.get("cell_id"))
    reason = cell.get("refusal_reason")
    if reason is not None and not isinstance(reason, str):
        _refuse("emitted_cell_refusal", cell.get("cell_id"))
    return cell_type, _cell_nonempty(cell)


def _read_profiles(
    directory: Path, manifest: JsonObject
) -> tuple[tuple[JsonObject, ...], JsonObject]:
    identity = _StreamIdentity()
    profiles = tuple(_json_lines(directory / _WORKBOOK_PROFILES, identity))
    if len(profiles) != WORKBOOKS:
        _refuse("profile_denominator", len(profiles))
    retained = cast(
        JsonObject,
        cast(JsonObject, manifest["sources"])["retained_workbooks"],
    )
    roster_values = retained["members"]
    if not isinstance(roster_values, list):
        _refuse("profile_roster", "array required")
    roster = tuple(cast(JsonObject, value) for value in roster_values)
    names = [cast(str, row.get("archive_member")) for row in roster]
    if names != sorted(set(names)):
        _refuse("source_roster_order", names)
    profile_fields = {
        "schema_version",
        "archive_member",
        "workbook_id",
        "workbook_sha256",
        "workbook_bytes",
        "excel_date_mode_raw",
        "sheet_count",
        "empty_auxiliary_sheets",
        "nonempty_sheet_ordinal",
        "nonempty_sheet_name",
        "source_rows",
        "source_columns",
        "source_rectangle_positions",
        "header_rule",
        "header_row_index",
        "header_row_number",
        "header_nonempty_text_cells",
        "header_decoded_cells_sha256",
        "header_field_positions",
        "header_first_field_empty",
        "pre_header_nonempty_rows",
        "data_row_rule",
        "data_row_first_index",
        "data_row_first_number",
        "data_row_last_index",
        "data_row_last_number",
        "data_row_positions",
        "data_row_candidates",
        "taxonomy_status",
        "chronology_status",
        "axis_status",
        "units_status",
        "formula_origin",
        "numeric_decimal_lexeme",
        "historical_primary_input_identity",
        "scientific_admission",
    }
    for profile, source in zip(profiles, roster, strict=True):
        member = source.get("archive_member")
        expected_sheet_name = "LC_GILLT" if member == "rootsi/GIL.xls" else "Sheet1"
        excel_date_mode = _integer(
            profile.get("excel_date_mode_raw"), "excel_date_mode_raw"
        )
        sheet_count = _integer(profile.get("sheet_count"), "sheet_count", minimum=1)
        header_row = _integer(profile.get("header_row_index"), "header_row")
        first_row = _integer(profile.get("data_row_first_index"), "first_data_row")
        last_row = _integer(profile.get("data_row_last_index"), "last_data_row")
        columns = _integer(profile.get("source_columns"), "source_columns", minimum=1)
        source_rows = _integer(profile.get("source_rows"), "source_rows", minimum=1)
        candidates = _integer(
            profile.get("data_row_candidates"), "data_row_candidates", minimum=1
        )
        if (
            set(profile) != profile_fields
            or profile.get("schema_version") != "essd-rootsi-workbook-profile.v1"
            or profile.get("archive_member") != member
            or profile.get("workbook_sha256") != source.get("sha256")
            or profile.get("workbook_bytes") != source.get("bytes")
            or profile.get("workbook_id")
            != _source_id(ARCHIVE_SHA256, member, source.get("sha256"))
            or sheet_count not in (1, 3)
            or excel_date_mode not in (0, 1)
            or profile.get("empty_auxiliary_sheets") != sheet_count - 1
            or profile.get("nonempty_sheet_ordinal") != 0
            or profile.get("nonempty_sheet_name") != expected_sheet_name
            or profile.get("source_rectangle_positions") != source_rows * columns
            or profile.get("header_rule") != "unique_global_maximum_nonempty_text_cells"
            or profile.get("header_row_number") != header_row + 1
            or header_row not in (0, 2)
            or profile.get("pre_header_nonempty_rows") != (0 if header_row == 0 else 1)
            or profile.get("header_field_positions") != columns
            or profile.get("header_first_field_empty")
            is not (member == "rootsi/GIL.xls")
            or _digest(profile.get("header_decoded_cells_sha256"), "header row digest")
            != profile.get("header_decoded_cells_sha256")
            or profile.get("data_row_rule") != "every_later_nonempty_row"
            or profile.get("data_row_first_number") != first_row + 1
            or first_row != (1 if header_row == 0 else 4)
            or profile.get("data_row_last_number") != last_row + 1
            or last_row >= source_rows
            or last_row - first_row + 1 != candidates
            or profile.get("data_row_positions") != candidates * columns
            or profile.get("taxonomy_status") != "unreviewed"
            or profile.get("chronology_status") != "unreviewed"
            or profile.get("axis_status") != "unreviewed"
            or profile.get("units_status") != "unreviewed"
            or profile.get("formula_origin") != "unavailable"
            or profile.get("numeric_decimal_lexeme") != "unavailable"
            or profile.get("historical_primary_input_identity") != "not_authenticated"
            or profile.get("scientific_admission") != "refused"
        ):
            _refuse("profile_contract", member)
    if (
        Counter(profile["sheet_count"] for profile in profiles)
        != Counter({1: 65, 3: 14})
        or Counter(profile["header_row_index"] for profile in profiles)
        != Counter({0: 41, 2: 38})
        or Counter(profile["data_row_first_index"] for profile in profiles)
        != Counter({1: 41, 4: 38})
        or [
            profile["archive_member"]
            for profile in profiles
            if profile["header_first_field_empty"] is True
        ]
        != ["rootsi/GIL.xls"]
        or [
            profile["archive_member"]
            for profile in profiles
            if profile["nonempty_sheet_name"] != "Sheet1"
        ]
        != ["rootsi/GIL.xls"]
    ):
        _refuse("profile_partition", "sheet/header/data variants")
    return profiles, identity.as_dict()


def _validate_headers(directory: Path, profiles: tuple[JsonObject, ...]) -> JsonObject:
    identity = _StreamIdentity()
    records = iter(_json_lines(directory / _HEADER_FIELDS, identity))
    types: Counter[int] = Counter()
    nonempty_text = 0
    positions = 0
    fields = {
        "schema_version",
        "archive_member",
        "workbook_id",
        "workbook_sha256",
        "sheet_ordinal",
        "sheet_name",
        "header_row_index",
        "header_row_number",
        "column_index",
        "column_number",
        "cell_id",
        "cell_type",
        "decoded_value",
        "binary64_hex",
        "xf_index",
        "refusal_reason",
        "nonempty_text_candidate",
        "scientific_classification",
    }
    for profile in profiles:
        digest = hashlib.sha256()
        profile_nonempty_text = 0
        columns = cast(int, profile["source_columns"])
        for column in range(columns):
            record = next(records, None)
            if record is None:
                _refuse("missing_header_position", profile["archive_member"])
            if (
                set(record) != fields
                or record.get("schema_version") != "essd-rootsi-header-field.v1"
                or record.get("archive_member") != profile["archive_member"]
                or record.get("workbook_id") != profile["workbook_id"]
                or record.get("workbook_sha256") != profile["workbook_sha256"]
                or record.get("sheet_ordinal") != profile["nonempty_sheet_ordinal"]
                or record.get("sheet_name") != profile["nonempty_sheet_name"]
                or record.get("header_row_index") != profile["header_row_index"]
                or record.get("header_row_number") != profile["header_row_number"]
                or record.get("column_index") != column
                or record.get("column_number") != column + 1
                or record.get("scientific_classification") != "unreviewed"
            ):
                _refuse("header_position", f"{profile['archive_member']}:{column}")
            cell = {
                "cell_id": record["cell_id"],
                "workbook_id": record["workbook_id"],
                "sheet_ordinal": record["sheet_ordinal"],
                "row": record["header_row_index"],
                "column": record["column_index"],
                "cell_type": record["cell_type"],
                "decoded_value": record["decoded_value"],
                "binary64_hex": record["binary64_hex"],
                "xf_index": record["xf_index"],
                "refusal_reason": record["refusal_reason"],
            }
            cell_type, nonempty = _emitted_cell(
                cell,
                workbook_id=cast(str, profile["workbook_id"]),
                sheet_ordinal=cast(int, profile["nonempty_sheet_ordinal"]),
                row=cast(int, profile["header_row_index"]),
                column=column,
            )
            if record["nonempty_text_candidate"] is not (cell_type == 1 and nonempty):
                _refuse("header_text_flag", record["cell_id"])
            if column == 0 and profile["header_first_field_empty"] is not (
                not nonempty
            ):
                _refuse("header_first_field_flag", profile["archive_member"])
            digest.update(_encode(cell))
            types[cell_type] += 1
            nonempty_text += int(cell_type == 1 and nonempty)
            profile_nonempty_text += int(cell_type == 1 and nonempty)
            positions += 1
        if (
            digest.hexdigest() != profile["header_decoded_cells_sha256"]
            or profile_nonempty_text != profile["header_nonempty_text_cells"]
        ):
            _refuse("header_digest", profile["archive_member"])
    if next(records, None) is not None:
        _refuse("extra_header_position", _HEADER_FIELDS)
    if (
        positions != HEADER_FIELDS
        or types != Counter({1: HEADER_TEXT_POSITIONS, 0: HEADER_EMPTY_POSITIONS})
        or nonempty_text != HEADER_NONEMPTY_TEXT_POSITIONS
    ):
        _refuse("header_partition", (positions, dict(types), nonempty_text))
    return identity.as_dict()


def _validate_data_rows(
    directory: Path, profiles: tuple[JsonObject, ...]
) -> JsonObject:
    identity = _StreamIdentity()
    records = iter(_json_lines(directory / _DATA_ROWS, identity))
    row_fields = {
        "schema_version",
        "archive_member",
        "workbook_id",
        "workbook_sha256",
        "sheet_ordinal",
        "sheet_name",
        "row_index",
        "row_number",
        "decoded_cells_sha256",
        "decoded_digest_contract",
        "column_positions",
        "nonempty_cells",
        "nonempty_text_cells",
        "structural_cell_type_counts",
        "cells",
        "taxonomy_status",
        "chronology_status",
        "unit_status",
        "historical_primary_input_identity",
    }
    positions = 0
    row_count = 0
    types: Counter[int] = Counter()
    text_cells: list[tuple[str, JsonObject]] = []
    for profile in profiles:
        first = cast(int, profile["data_row_first_index"])
        last = cast(int, profile["data_row_last_index"])
        columns = cast(int, profile["source_columns"])
        for row_index in range(first, last + 1):
            record = next(records, None)
            if record is None:
                _refuse("missing_data_row", profile["archive_member"])
            cells = record.get("cells")
            if (
                set(record) != row_fields
                or record.get("schema_version") != "essd-rootsi-data-row-candidate.v1"
                or record.get("archive_member") != profile["archive_member"]
                or record.get("workbook_id") != profile["workbook_id"]
                or record.get("workbook_sha256") != profile["workbook_sha256"]
                or record.get("sheet_ordinal") != profile["nonempty_sheet_ordinal"]
                or record.get("sheet_name") != profile["nonempty_sheet_name"]
                or record.get("row_index") != row_index
                or record.get("row_number") != row_index + 1
                or record.get("decoded_digest_contract")
                != "canonical_cell_json_lines_sha256"
                or record.get("column_positions") != columns
                or not isinstance(cells, list)
                or len(cells) != columns
                or record.get("taxonomy_status") != "unreviewed"
                or record.get("chronology_status") != "unreviewed"
                or record.get("unit_status") != "unreviewed"
                or record.get("historical_primary_input_identity")
                != "not_authenticated"
            ):
                _refuse("data_row_contract", f"{profile['archive_member']}:{row_index}")
            digest = hashlib.sha256()
            row_types: Counter[str] = Counter()
            row_nonempty = 0
            row_nonempty_text = 0
            for column, cell_value in enumerate(cells):
                if not isinstance(cell_value, dict):
                    _refuse("data_cell_object", f"{row_index}:{column}")
                cell = cast(JsonObject, cell_value)
                cell_type, nonempty = _emitted_cell(
                    cell,
                    workbook_id=cast(str, profile["workbook_id"]),
                    sheet_ordinal=cast(int, profile["nonempty_sheet_ordinal"]),
                    row=row_index,
                    column=column,
                )
                digest.update(_encode(cell))
                row_types[_cell_kind(cell_type)] += 1
                row_nonempty += int(nonempty)
                row_nonempty_text += int(cell_type == 1 and nonempty)
                types[cell_type] += 1
                positions += 1
                if cell_type == 1:
                    text_cells.append((cast(str, profile["archive_member"]), cell))
            if (
                digest.hexdigest() != record.get("decoded_cells_sha256")
                or {name: row_types[name] for name in _STRUCTURAL_COUNT_NAMES}
                != record.get("structural_cell_type_counts")
                or record.get("nonempty_cells") != row_nonempty
                or record.get("nonempty_text_cells") != row_nonempty_text
                or row_nonempty == 0
            ):
                _refuse(
                    "data_row_projection", f"{profile['archive_member']}:{row_index}"
                )
            row_count += 1
    if next(records, None) is not None:
        _refuse("extra_data_row", _DATA_ROWS)
    if (
        row_count != DATA_ROW_CANDIDATES
        or positions != DATA_ROW_POSITIONS
        or types
        != Counter(
            {
                2: DATA_ROW_NUMERIC_POSITIONS,
                0: DATA_ROW_EMPTY_POSITIONS,
                1: DATA_ROW_TEXT_POSITIONS,
            }
        )
    ):
        _refuse("data_partition", (row_count, positions, dict(types)))
    if len(text_cells) != 1 or text_cells[0][0] != "rootsi/RASH.xls":
        _refuse("data_text_variant", text_cells)
    text_cell = text_cells[0][1]
    if (
        text_cell["row"] != 11
        or text_cell["column"] != 53
        or text_cell["decoded_value"] != "  "
    ):
        _refuse("data_text_variant", text_cell)
    return identity.as_dict()


def _validate_sample_review(
    directory: Path, profiles: tuple[JsonObject, ...]
) -> JsonObject:
    casefold_members = {
        PurePosixPath(cast(str, profile["archive_member"])).name.casefold(): cast(
            str, profile["archive_member"]
        )
        for profile in profiles
    }
    if len(casefold_members) != len(profiles):
        _refuse("ambiguous_casefold_workbook_members", len(profiles))
    bindings: list[JsonObject] = []
    agreements = 0
    mismatches: list[dict[str, str]] = []
    content = (directory / _SAMPLE_REVIEW).read_bytes()
    identity = {"sha256": _sha256(content), "bytes": len(content)}
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        _refuse("sample_review_encoding", exc)
    with io.StringIO(text, newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(_SAMPLE_COLUMNS):
            _refuse("sample_review_header", reader.fieldnames)
        for profile in profiles:
            row = next(reader, None)
            if row is None or None in row or set(row) != set(_SAMPLE_COLUMNS):
                _refuse("sample_review_row", profile["archive_member"])
            member = cast(str, profile["archive_member"])
            source_row_text = row["rootsi_source_row"]
            claim_text = row["rootsi_sample_count_claim"]
            mechanical_text = row["mechanical_data_row_candidates"]
            if not all(
                value.isdigit()
                for value in (source_row_text, claim_text, mechanical_text)
            ):
                _refuse("sample_review_integer", member)
            source_row = int(source_row_text)
            claim = int(claim_text)
            mechanical = int(mechanical_text)
            raw_workbook_claim = row["rootsi_observation_workbook_claim_raw"]
            claim_member = (
                casefold_members.get(raw_workbook_claim.casefold())
                if raw_workbook_claim
                else None
            )
            agrees = claim == mechanical
            if (
                row["namespace"] != "essd-rootsi-sample-denominator-review.v1"
                or row["archive_member"] != member
                or row["workbook_sha256"] != profile["workbook_sha256"]
                or row["rootsi_source_locator"] != f"{METADATA_MEMBER}!{source_row}"
                or claim_member != member
                or row["rootsi_sample_count_raw"] != claim_text
                or mechanical != profile["data_row_candidates"]
                or row["sample_denominator_agrees"] != str(agrees).lower()
                or row["sample_denominator_status"]
                != ("agrees" if agrees else "mismatch_preserved")
                or row["historical_primary_input_identity_status"]
                != "not_authenticated"
            ):
                _refuse("sample_review_binding", member)
            bindings.append(
                {
                    "archive_member": member,
                    "workbook_sha256": row["workbook_sha256"],
                    "rootsi_source_row": source_row,
                    "rootsi_source_locator": row["rootsi_source_locator"],
                    "rootsi_site_name_raw": row["rootsi_site_name_raw"],
                    "rootsi_sequence_label_raw": row["rootsi_sequence_label_raw"],
                    "rootsi_observation_workbook_claim_raw": row[
                        "rootsi_observation_workbook_claim_raw"
                    ],
                    "rootsi_sample_count_raw": row["rootsi_sample_count_raw"],
                    "rootsi_sample_count_claim": claim,
                }
            )
            agreements += int(agrees)
            if not agrees:
                mismatches.append(row)
        if next(reader, None) is not None:
            _refuse("extra_sample_review_row", _SAMPLE_REVIEW)
    if (
        _sha256(_encode(bindings)) != METADATA_WORKBOOK_BINDINGS_SHA256
        or agreements != SAMPLE_DENOMINATOR_AGREEMENTS
        or len(mismatches) != 1
        or mismatches[0]["archive_member"] != "rootsi/EKE.xls"
        or mismatches[0]["rootsi_source_row"] != "14"
        or mismatches[0]["rootsi_sample_count_claim"] != "25"
        or mismatches[0]["mechanical_data_row_candidates"] != "42"
    ):
        _refuse(
            "sample_review_partition",
            {
                "bindings_sha256": _sha256(_encode(bindings)),
                "expected_bindings_sha256": METADATA_WORKBOOK_BINDINGS_SHA256,
                "agreements": agreements,
                "expected_agreements": SAMPLE_DENOMINATOR_AGREEMENTS,
                "mismatches": mismatches,
            },
        )
    return identity


def _validate_report(directory: Path) -> JsonObject:
    content = (directory / _REPORT).read_bytes()
    identity = {"sha256": _sha256(content), "bytes": len(content)}
    report = _object(content, _REPORT)
    expected_denominators = {
        "workbooks": WORKBOOKS,
        "sheets": SHEETS,
        "rectangle_positions_streamed": RECTANGLE_POSITIONS,
        "workbook_profiles": WORKBOOKS,
        "header_field_positions": HEADER_FIELDS,
        "data_row_candidates": DATA_ROW_CANDIDATES,
        "sample_denominator_records": SAMPLE_DENOMINATOR_RECORDS,
        "sample_denominator_agreements": SAMPLE_DENOMINATOR_AGREEMENTS,
        "sample_denominator_mismatches": 1,
        "blank_first_header_variants": 1,
        "metadata_rows_without_workbook_claim": 2,
        "data_row_candidate_positions": DATA_ROW_POSITIONS,
        "data_row_numeric_positions": DATA_ROW_NUMERIC_POSITIONS,
        "data_row_empty_positions": DATA_ROW_EMPTY_POSITIONS,
        "data_row_text_positions": DATA_ROW_TEXT_POSITIONS,
    }
    expected_source_hashes = {
        "typed_cell_review_manifest_sha256": TYPED_CELL_REVIEW_MANIFEST_SHA256,
        "native_inventory_sha256": NATIVE_INVENTORY_SHA256,
        "workbook_roster_sha256": WORKBOOK_ROSTER_SHA256,
        "rootsi_metadata_sha256": METADATA_SHA256,
        "candidate_closure_manifest_sha256": CANDIDATE_CLOSURE_MANIFEST_SHA256,
        "candidate_pair_identity_sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
    }
    expected_rules = {
        "nonempty_sheet": "contains_at_least_one_nonempty_decoded_cell",
        "sheet_selection": "exactly_one_nonempty_sheet_per_workbook",
        "header": "unique_row_with_global_maximum_nonempty_text_cells",
        "header_fields": "every_source_column_position_on_selected_header_row",
        "data_rows": "every_later_nonempty_row",
        "empty_auxiliary_sheets": "allowed",
        "header_ties": "refused",
        "multiple_nonempty_sheets": "refused",
    }
    expected_variants = {
        "sample_denominator_mismatch": {
            "archive_member": "rootsi/EKE.xls",
            "metadata_sample_count_raw": "25",
            "metadata_sample_count_claim": 25,
            "mechanical_data_row_candidates": 42,
            "status": "mismatch_preserved",
            "landclim_candidate_publication_rows": [981],
            "landclim_candidate_reported_sample_count": 42,
            "candidate_count_coincidence_resolves_revision_identity": False,
        },
        "blank_first_header_field": {
            "archive_member": "rootsi/GIL.xls",
            "preserved": True,
            "interpretation": "structural_variant_only",
        },
        "metadata_without_workbook_claim": [
            {
                "rootsi_source_row": 3,
                "rootsi_site_name_raw": "Åbodasjön",
                "rootsi_sequence_label_raw": "ABO",
                "observation_workbook_claim": None,
                "status": "source_metadata_no_workbook_claim",
            },
            {
                "rootsi_source_row": 46,
                "rootsi_site_name_raw": "Lindhultsgöl",
                "rootsi_sequence_label_raw": "LIND",
                "observation_workbook_claim": None,
                "status": "source_metadata_no_workbook_claim",
            },
        ],
        "whitespace_data_cell": {
            "archive_member": "rootsi/RASH.xls",
            "row_index": 11,
            "column_index": 53,
            "decoded_value": "  ",
            "interpretation": "preserved_source_text_not_missingness_decision",
        },
    }
    expected_pair = {
        "sha256": CANDIDATE_PAIR_IDENTITY_SHA256,
        "accepted_pairs": WORKBOOKS,
        "interpretation": "metadata_candidate_not_historical_input_identity",
    }
    expected_blockers = [
        "historical workbook revision identity",
        "selected chronology and sample identity",
        "taxon and count-denominator review",
        "axis and unit review",
        "formula provenance",
        "per-sequence rights",
        "basin and publication-profile semantics",
        "qualified scientific review",
    ]
    if (
        set(report)
        != {
            "schema_version",
            "profile",
            "status",
            "source_hashes",
            "observed_denominators",
            "mechanical_rules",
            "preserved_variants",
            "candidate_pair",
            "claims",
            "blocking_dependencies",
        }
        or report.get("schema_version")
        != "essd-rootsi-retained-workbook-replay-report.v1"
        or report.get("profile") != PROFILE
        or report.get("status") != STATUS
        or report.get("source_hashes") != expected_source_hashes
        or report.get("observed_denominators") != expected_denominators
        or report.get("mechanical_rules") != expected_rules
        or report.get("preserved_variants") != expected_variants
        or report.get("candidate_pair") != expected_pair
        or report.get("claims") != _claims()
        or report.get("blocking_dependencies") != expected_blockers
    ):
        _refuse("report_contract", "source, rules, variants, or blockers changed")
    return identity


def _validate_peer_contracts(
    directory: Path, manifest: JsonObject
) -> dict[str, JsonObject]:
    profiles, profile_identity = _read_profiles(directory, manifest)
    return {
        _WORKBOOK_PROFILES: profile_identity,
        _HEADER_FIELDS: _validate_headers(directory, profiles),
        _DATA_ROWS: _validate_data_rows(directory, profiles),
        _SAMPLE_REVIEW: _validate_sample_review(directory, profiles),
        _REPORT: _validate_report(directory),
    }


def read_rootsi_workbook_replay(
    destination: Path, *, expected_manifest_sha256: str
) -> RootsiWorkbookReplayBundle:
    """Authenticate one exact structural replay without source reinterpretation."""
    try:
        target = _checked_path(destination)
        manifest, _ = _read_output_manifest(target, expected_manifest_sha256)
        _manifest_contract(manifest)
        before = _output_identity_map(target)
        _validate_artifacts(manifest, before)
        _validate_peer_contracts(target, manifest)
        if _output_identity_map(target) != before:
            _refuse("bundle_changed", target)
        return RootsiWorkbookReplayBundle(
            target,
            expected_manifest_sha256,
            WORKBOOKS,
            HEADER_FIELDS,
            DATA_ROW_CANDIDATES,
            SAMPLE_DENOMINATOR_RECORDS,
            CANDIDATE_PAIR_IDENTITY_SHA256,
        )
    except RootsiWorkbookReplayError:
        raise
    except (OSError, KeyError, TypeError, ValueError, OverflowError) as exc:
        _refuse("read_failed", exc)


def publish_rootsi_workbook_replay(
    *, source: RootsiWorkbookReplayInput, destination: Path
) -> RootsiWorkbookReplayBundle:
    """Replay 79 workbook byte streams and atomically publish structural evidence."""
    if not isinstance(source, RootsiWorkbookReplayInput):
        _refuse("untyped_input", type(source).__name__)
    target = _destination(source, destination)
    producer = _producer_identity()
    inputs = _load_inputs(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target = _destination(source, target)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.pending-", dir=target.parent))
    manifest_sha256 = _write_stage(inputs, stage, producer)
    read_rootsi_workbook_replay(stage, expected_manifest_sha256=manifest_sha256)
    _require_unchanged(inputs.snapshots)
    if _producer_identity() != producer:
        _refuse("producer_changed", Path(__file__))
    try:
        _publish_new_output_tree(
            final_output_root=target,
            staging_output_root=stage,
        )
    except OSError as exc:
        _refuse("publish_failed", exc)
    _fsync_directory(target.parent)
    return read_rootsi_workbook_replay(target, expected_manifest_sha256=manifest_sha256)


def validate_rootsi_workbook_replay(
    source: RootsiWorkbookReplayInput,
    destination: Path,
    *,
    expected_manifest_sha256: str,
) -> RootsiWorkbookReplayBundle:
    """Rebind a published replay to every exact retained source byte."""
    bundle = read_rootsi_workbook_replay(
        destination, expected_manifest_sha256=expected_manifest_sha256
    )
    inputs = _load_inputs(source)
    manifest = _object((bundle.directory / _MANIFEST).read_bytes(), _MANIFEST)
    if manifest.get("sources") != _source_manifest(inputs):
        _refuse("source_rebind_mismatch", bundle.directory)
    _require_unchanged(inputs.snapshots)
    return read_rootsi_workbook_replay(
        destination, expected_manifest_sha256=expected_manifest_sha256
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Publish the exact retained Rootsi workbook structural replay."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--typed-cell-review", required=True, type=Path)
    parser.add_argument(
        "--typed-cell-review-manifest-sha256",
        default=TYPED_CELL_REVIEW_MANIFEST_SHA256,
    )
    parser.add_argument("--native-inventory", required=True, type=Path)
    parser.add_argument("--native-inventory-sha256", default=NATIVE_INVENTORY_SHA256)
    parser.add_argument("--workbook-directory", required=True, type=Path)
    parser.add_argument("--rootsi-metadata", required=True, type=Path)
    parser.add_argument("--rootsi-metadata-sha256", default=METADATA_SHA256)
    parser.add_argument("--candidate-closure", required=True, type=Path)
    parser.add_argument(
        "--candidate-closure-manifest-sha256",
        default=CANDIDATE_CLOSURE_MANIFEST_SHA256,
    )
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    bundle = publish_rootsi_workbook_replay(
        source=RootsiWorkbookReplayInput(
            args.typed_cell_review,
            args.typed_cell_review_manifest_sha256,
            args.native_inventory,
            args.native_inventory_sha256,
            args.workbook_directory,
            args.rootsi_metadata,
            args.rootsi_metadata_sha256,
            args.candidate_closure,
            args.candidate_closure_manifest_sha256,
        ),
        destination=args.destination,
    )
    print(
        _encode(
            {
                "destination": str(bundle.directory),
                "manifest_sha256": bundle.manifest_sha256,
                "workbook_profiles": bundle.workbook_profiles,
                "header_fields": bundle.header_fields,
                "data_row_candidates": bundle.data_row_candidates,
                "sample_denominator_records": bundle.sample_denominator_records,
                "scientific_acceptance": "not_evaluated",
                "public_release_allowed": False,
            }
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
