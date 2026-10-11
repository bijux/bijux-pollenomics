"""Pinned review consistency and distinct workbook-byte replay checks."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict
from itertools import zip_longest
from pathlib import Path

from ..authority import ARCHIVE_SHA256
from ..normalization import rootsi_intake_posture
from .decoding import Parser, workbook_records
from .inputs import (
    RETAINED_INVENTORY_SHA256,
    inventory_workbooks,
    local_path,
    member_name,
    read_bytes,
    verify_capture,
)
from .models import (
    MEMBERS,
    PARSER_VERSION,
    SCHEMA,
    Capture,
    ReviewBundle,
    decoded,
    digest,
    encoded,
    integer,
    object_value,
    refuse,
    sequence,
    text,
)
from .projection import Accounting, source_id, validate_cell
from .publication import file_identity


def json_lines(path: Path) -> Iterator[dict[str, object]]:
    """Read complete JSON rows; blank or malformed positions are refusals."""
    with path.open("rb") as stream:
        for line in stream:
            yield object_value(decoded(line), path.name)


def _capture(value: object, directory: Path) -> dict[str, object]:
    capture = object_value(value, "capture")
    if set(capture) != {
        "inventory_sha256",
        "inventory_bytes",
        "archive_sha256",
        "scope",
        "available_workbooks",
        "archive_membership_verification",
        "selected_workbooks",
    }:
        refuse("capture_fields", "exact capture contract required")
    if (
        digest(capture.get("inventory_sha256"), "inventory")
        != RETAINED_INVENTORY_SHA256
    ):
        refuse("unrecognized_capture", "retained inventory digest")
    native_inventory = read_bytes(
        directory / "capture-inventory.json",
        RETAINED_INVENTORY_SHA256,
        integer(capture.get("inventory_bytes"), "inventory_bytes", minimum=1),
    )
    roster = inventory_workbooks(native_inventory)
    available = integer(
        capture.get("available_workbooks"), "available_workbooks", minimum=1
    )
    if available != 79:
        refuse("inventory_count", "retained capture has exactly 79 workbooks")
    if (
        capture.get("archive_sha256") != ARCHIVE_SHA256
        or capture.get("archive_membership_verification")
        != "retained_receipt_bound_not_replayed"
    ):
        refuse("capture_posture", "archive provenance")
    scope = text(capture.get("scope"), "scope")
    if scope not in {"selected_workbooks", "complete_retained_capture"}:
        refuse("invalid_scope", scope)
    selected = sequence(capture.get("selected_workbooks"), "selected_workbooks")
    if not selected or len(selected) > available:
        refuse("selection_count", str(len(selected)))
    if scope == "complete_retained_capture" and (
        available != 79 or len(selected) != 79
    ):
        refuse("selection_count", "complete scope requires 79")
    names: list[str] = []
    for entry in selected:
        row = object_value(entry, "selected workbook")
        if set(row) != {"archive_member", "sha256", "bytes"}:
            refuse("workbook_fields", repr(row))
        name = member_name(row.get("archive_member"))
        names.append(name)
        binding = (
            digest(row.get("sha256"), "workbook sha256"),
            integer(row.get("bytes"), "workbook bytes", minimum=1),
        )
        if roster.get(name) != binding:
            refuse("workbook_not_in_retained_roster", name)
    if names != sorted(set(names)):
        refuse("duplicate_or_unordered_members", repr(names))
    return capture


def _workbooks(directory: Path, capture: dict[str, object]) -> list[dict[str, object]]:
    rows = sequence(decoded((directory / "workbooks.json").read_bytes()), "workbooks")
    selected = sequence(capture["selected_workbooks"], "selected")
    if len(rows) != len(selected):
        refuse("workbook_count", str(len(rows)))
    result = []
    for raw, native in zip(rows, selected, strict=True):
        row = object_value(raw, "workbook")
        binding = object_value(native, "native")
        mode = integer(row.get("excel_date_mode"), "excel_date_mode")
        if mode not in (0, 1):
            refuse("invalid_date_mode", str(mode))
        expected = {
            **binding,
            "workbook_id": source_id(
                ARCHIVE_SHA256, binding["archive_member"], binding["sha256"]
            ),
            "excel_date_mode": mode,
            "sheet_count": integer(row.get("sheet_count"), "sheet_count"),
        }
        if encoded(expected) != encoded(row):
            refuse("workbook_identity_mismatch", str(row.get("workbook_id")))
        result.append(row)
    return result


def _sheet(row: dict[str, object], workbook: dict[str, object], ordinal: int) -> None:
    if set(row) != {
        "workbook_id",
        "sheet_ordinal",
        "name",
        "nrows",
        "ncols",
        "rectangle_positions",
        "merged_ranges",
    }:
        refuse("sheet_fields", repr(row))
    if (
        row["workbook_id"] != workbook["workbook_id"]
        or integer(row["sheet_ordinal"], "ordinal") != ordinal
    ):
        refuse("sheet_identity", repr(row))
    text(row["name"], "name")
    rows, columns = integer(row["nrows"], "nrows"), integer(row["ncols"], "ncols")
    if (
        rows > 65536
        or columns > 256
        or integer(row["rectangle_positions"], "rectangle_positions") != rows * columns
    ):
        refuse("sheet_extent", repr(row))
    for raw in sequence(row["merged_ranges"], "merged_ranges"):
        bounds = [
            integer(value, "merged bound") for value in sequence(raw, "merged range")
        ]
        if len(bounds) != 4 or not (
            bounds[0] < bounds[1] <= 65536 and bounds[2] < bounds[3] <= 256
        ):
            refuse("merged_range", repr(bounds))


def _account(directory: Path, workbooks: list[dict[str, object]]) -> dict[str, object]:
    counts = Accounting()
    sheets = iter(json_lines(directory / "sheets.jsonl"))
    cells = iter(json_lines(directory / "cells.jsonl"))
    for workbook in workbooks:
        counts.workbooks += 1
        names: set[str] = set()
        for ordinal in range(integer(workbook["sheet_count"], "sheet_count")):
            sheet = next(sheets, None)
            if sheet is None:
                refuse("missing_sheet", str(ordinal))
            _sheet(sheet, workbook, ordinal)
            name = text(sheet["name"], "name")
            if name in names:
                refuse("duplicate_sheet", name)
            names.add(name)
            counts.sheets += 1
            counts.empty_sheets += int(sheet["rectangle_positions"] == 0)
            for row in range(integer(sheet["nrows"], "nrows")):
                for column in range(integer(sheet["ncols"], "ncols")):
                    cell = next(cells, None)
                    if cell is None:
                        refuse("missing_cell", f"{name}:{row}:{column}")
                    validate_cell(cell)
                    expected = source_id(workbook["workbook_id"], ordinal, row, column)
                    if cell["cell_id"] != expected:
                        refuse("cell_position", str(cell["cell_id"]))
                    counts.add(cell)
    if next(sheets, None) is not None or next(cells, None) is not None:
        refuse("extra_positions", str(directory))
    result = counts.as_dict()
    if encoded(decoded((directory / "accounting.json").read_bytes())) != encoded(
        result
    ):
        refuse("accounting_mismatch", str(directory))
    return result


def read_bundle(directory: Path, expected_manifest_sha256: str) -> ReviewBundle:
    """Validate pinned internal consistency; native replay is a separate operation."""
    directory = local_path(directory)
    if not directory.is_dir() or {path.name for path in directory.iterdir()} != {
        *MEMBERS,
        "manifest.json",
    }:
        refuse("bundle_inventory", str(directory))
    manifest_bytes = read_bytes(
        directory / "manifest.json", digest(expected_manifest_sha256, "manifest_sha256")
    )
    manifest = object_value(decoded(manifest_bytes), "manifest")
    if set(manifest) != {
        "schema",
        "capture",
        "parser",
        "source_posture",
        "scientific_admission",
        "value_contract",
        "producer",
        "members",
    }:
        refuse("manifest_fields", str(directory))
    if (
        manifest["schema"] != SCHEMA
        or manifest["scientific_admission"] != "refused"
        or encoded(manifest["source_posture"])
        != encoded(asdict(rootsi_intake_posture()))
    ):
        refuse("scientific_posture", str(directory))
    if encoded(manifest["parser"]) != encoded(
        {"name": "xlrd", "version": PARSER_VERSION, "formatting_info": True}
    ):
        refuse("parser_contract", str(directory))
    value_contract = {
        "numeric_representation": "decoded_binary64_hex",
        "numeric_decimal_lexeme": "unavailable",
        "formula_origin": "unavailable",
        "physical_biff_record_presence": "unavailable",
        "unit": "unreviewed",
        "chronology": "unreviewed",
        "taxonomy": "unreviewed",
    }
    if manifest["value_contract"] != value_contract:
        refuse("value_posture", str(directory))
    producer = object_value(manifest["producer"], "producer")
    if not producer:
        refuse("producer_identity", "missing source inventory")
    for value in producer.values():
        row = object_value(value, "producer member")
        digest(row.get("sha256"), "producer sha256")
        integer(row.get("bytes"), "producer bytes", minimum=1)
    members = object_value(manifest["members"], "members")
    if set(members) != set(MEMBERS):
        refuse("bundle_inventory", str(directory))
    before = {}
    for name in MEMBERS:
        path = local_path(directory / name)
        if not path.is_file():
            refuse("missing_input", str(path))
        before[name] = file_identity(path)
        if encoded(members[name]) != encoded(before[name]):
            refuse("member_digest_mismatch", name)
    capture = _capture(manifest["capture"], directory)
    accounting = _account(directory, _workbooks(directory, capture))
    if any(
        file_identity(local_path(directory / name)) != before[name] for name in MEMBERS
    ):
        refuse("bundle_changed", str(directory))
    read_bytes(directory / "manifest.json", expected_manifest_sha256)
    return ReviewBundle(directory, expected_manifest_sha256, encoded(accounting))


def replay_bundle(bundle: ReviewBundle, capture: Capture, decoder: Parser) -> None:
    """Compare every record to exact workbook decoding, without claiming 7z replay."""
    manifest = object_value(
        decoded(read_bytes(bundle.directory / "manifest.json", bundle.manifest_sha256)),
        "manifest",
    )
    if encoded(manifest["capture"]) != encoded(capture.as_dict()):
        refuse("replay_capture_mismatch", str(bundle.directory))
    actual_workbooks: list[dict[str, object]] = []
    with (
        (bundle.directory / "sheets.jsonl").open("rb") as sheets,
        (bundle.directory / "cells.jsonl").open("rb") as cells,
    ):
        for item in capture.workbooks:
            for kind, record in workbook_records(item, capture.archive_sha256, decoder):
                if kind == "workbook":
                    actual_workbooks.append(record)
                else:
                    stream = sheets if kind == "sheet" else cells
                    if stream.readline() != encoded(record):
                        refuse(
                            "workbook_replay_mismatch", f"{item.archive_member}:{kind}"
                        )
        if sheets.read(1) or cells.read(1):
            refuse("workbook_replay_mismatch", "extra records")
    saved = sequence(
        decoded((bundle.directory / "workbooks.json").read_bytes()), "workbooks"
    )
    if any(
        encoded(left) != encoded(right)
        for left, right in zip_longest(saved, actual_workbooks)
    ):
        refuse("workbook_replay_mismatch", "workbook metadata")
    verify_capture(capture)
    read_bundle(bundle.directory, bundle.manifest_sha256)
