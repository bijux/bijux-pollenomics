"""Deterministic private review members and no-replace publication."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import os
from pathlib import Path
from tempfile import mkdtemp

from bijux_pollenomics.core import owned_tree

from .. import authority, normalization
from ..normalization import rootsi_intake_posture
from .decoding import Parser, workbook_records
from .inputs import output_path, read_bytes, verify_capture
from .models import MEMBERS, PARSER_VERSION, SCHEMA, Capture, ReviewBundle, encoded
from .projection import Accounting


def file_identity(path: Path) -> dict[str, object]:
    """Hash large cell streams without loading them into memory."""
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        size = os.fstat(stream.fileno()).st_size
    return {"sha256": digest, "bytes": size}


def producer_identity() -> dict[str, object]:
    """Bind the implemented decoder/projection and reused custody/publication owners."""
    paths = {f"cells/{path.name}": path for path in Path(__file__).parent.glob("*.py")}
    paths.update(
        {
            "rootsi/authority.py": Path(authority.__file__),
            "rootsi/normalization.py": Path(normalization.__file__),
            "core/owned_tree.py": Path(owned_tree.__file__),
        }
    )
    return {name: file_identity(path) for name, path in sorted(paths.items())}


def publish(capture: Capture, output_directory: Path, decoder: Parser) -> ReviewBundle:
    """Publish all selected positions, preserving incomplete stages on failure."""
    output = output_path(output_directory, capture)
    before = producer_identity()
    verify_capture(capture)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(mkdtemp(prefix=f".{output.name}.pending-", dir=output.parent))
    with (stage / "capture-inventory.json").open("xb") as stream:
        stream.write(
            read_bytes(
                capture.inventory_path,
                capture.inventory_sha256,
                capture.inventory_bytes,
            )
        )
        stream.flush()
        os.fsync(stream.fileno())
    accounting = Accounting()
    workbooks: list[dict[str, object]] = []
    with (
        (stage / "sheets.jsonl").open("xb") as sheets,
        (stage / "cells.jsonl").open("xb") as cells,
    ):
        for item in capture.workbooks:
            for kind, record in workbook_records(item, capture.archive_sha256, decoder):
                if kind == "workbook":
                    workbooks.append(record)
                    accounting.workbooks += 1
                elif kind == "sheet":
                    sheets.write(encoded(record))
                    accounting.sheets += 1
                    accounting.empty_sheets += int(record["rectangle_positions"] == 0)
                else:
                    cells.write(encoded(record))
                    accounting.add(record)
        for stream in (sheets, cells):
            stream.flush()
            os.fsync(stream.fileno())
    for name, value in (
        ("workbooks.json", workbooks),
        ("accounting.json", accounting.as_dict()),
    ):
        with (stage / name).open("xb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
    verify_capture(capture)
    if producer_identity() != before:
        from .models import refuse

        refuse("producer_changed", str(stage))
    manifest = {
        "schema": SCHEMA,
        "capture": capture.as_dict(),
        "parser": {"name": "xlrd", "version": PARSER_VERSION, "formatting_info": True},
        "source_posture": asdict(rootsi_intake_posture()),
        "scientific_admission": "refused",
        "value_contract": {
            "numeric_representation": "decoded_binary64_hex",
            "numeric_decimal_lexeme": "unavailable",
            "formula_origin": "unavailable",
            "physical_biff_record_presence": "unavailable",
            "unit": "unreviewed",
            "chronology": "unreviewed",
            "taxonomy": "unreviewed",
        },
        "producer": before,
        "members": {name: file_identity(stage / name) for name in MEMBERS},
    }
    with (stage / "manifest.json").open("xb") as stream:
        stream.write(encoded(manifest))
        stream.flush()
        os.fsync(stream.fileno())
    manifest_sha = str(file_identity(stage / "manifest.json")["sha256"])
    owned_tree.publish_new_output_tree(
        final_output_root=output, staging_output_root=stage
    )
    return ReviewBundle(output, manifest_sha, encoded(accounting.as_dict()))
