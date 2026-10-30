"""Bind the prepared version and original six rows to unchanged AADR conflicts."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from bijux_pollenomics.collection.intake.workbooks import cell_value
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .aadr import IDS, source_rows
from .workbook import literal_rows

SOURCES = {
    "2024.03.13.584607v2.full.pdf": (
        13244027,
        "e00f32c25897bfef313db79521c5bdbd5addee393faee1d2dd7de7be8ff75a7e",
    ),
    "media-1.xlsx": (
        2651210,
        "b94c214e2b018c0446d718bab910505df3b4fb7ce4cd128c7f021edea2e75bf3",
    ),
    "media-2.pdf": (
        3679221,
        "1ae31ccdd1dc624346a3270d95907580b8cb6c90782a7dd88acf810007eeef97",
    ),
    "media-15.pdf": (
        133531740,
        "f263322161ef2617f009d001d247c0c224dde817f8d32128c23c56bb541b26c1",
    ),
}
COUNTRY = Path("reports/science/aadr-nordic-entities/country-support")


def identity(path: Path) -> dict[str, Any]:
    """Hash original large PDFs incrementally without creating a source copy."""
    if not path.is_file() or path.resolve() != path:
        raise ValueError("Source is not a regular original file")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def revision(repository: Path) -> str:
    """Require committed reader source, without a separate first-party hash chain."""
    paths = [*Path(__file__).parent.glob("*.py"), Path(inspect.getfile(cell_value))]
    relative = [str(p.resolve().relative_to(repository)) for p in paths]
    command = ["git", "-C", str(repository)]
    current = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True
    ).strip()
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", current, "--", *relative],
        check=True,
        capture_output=True,
    )
    return current


def publish(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Save scoped source context; never write coordinates, dates or admissions."""
    start = time.monotonic()
    repository, source_root = repository.resolve(), source_root.resolve()
    destination = require_absent_artifact_output(repository, output)
    commit = revision(repository)
    original = []
    for name, (size, digest) in SOURCES.items():
        actual = identity(source_root / name)
        if actual != {"bytes": size, "sha256": digest}:
            raise ValueError("Prepared McColl original identity differs")
        original.append({"path": name, **actual})
    before = {
        name: identity(repository / COUNTRY / name)
        for name in ("decisions.csv", "report.json")
    }
    existing = json.loads((repository / COUNTRY / "report.json").read_bytes())
    aadr, aadr_inputs = [], []
    for expected in existing["source_inputs"]:
        if not expected["path"].endswith(".anno"):
            continue
        path = repository / expected["path"]
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise ValueError(
                "AADR source identity differs from existing country account"
            )
        panel = "1240k" if "/1240k/" in expected["path"] else "ho"
        aadr.extend(source_rows(path, panel))
        aadr_inputs.append(expected)
    with (repository / COUNTRY / "decisions.csv").open(newline="") as stream:
        conflicts = [row for row in csv.DictReader(stream) if row["genetic_id"] in IDS]
    if len(conflicts) != 2 or any(
        row["spatial_reason"] != "raw_country_conflict" for row in conflicts
    ):
        raise ValueError("Existing two-conflict country decisions differ")
    workbook = (source_root / "media-1.xlsx").read_bytes()
    if (len(workbook), hashlib.sha256(workbook).hexdigest()) != SOURCES["media-1.xlsx"]:
        raise ValueError("Parsed McColl workbook identity differs")
    rows = literal_rows(workbook)
    result: dict[str, Any] = {
        "schema_version": "mccoll-country-source-context.v1",
        "source_commit": commit,
        "status": "literal_source_context_without_admission",
        "prepared_source_inputs": original,
        "aadr_source_inputs": aadr_inputs,
        "workbook_rows": rows,
        "selected_descriptive_cells": sum(len(row["fields"]) for row in rows),
        "aadr_rows": aadr,
        "existing_country_conflicts": conflicts,
        "existing_country_account": before,
        "pdf_evidence_scope": {"media-2.pdf": [161, 174, 175], "media-15.pdf": [22]},
        "date_conversion_performed": False,
        "coordinate_correction_performed": False,
        "merged_samples_counted_as_independent": False,
        "scientific_admission": False,
        "publisher_sources_redistributed": False,
    }
    for expected in original:
        if identity(source_root / expected["path"]) != {
            key: expected[key] for key in ("bytes", "sha256")
        }:
            raise ValueError("Prepared McColl original changed during reading")
    for expected in aadr_inputs:
        if identity(repository / expected["path"]) != {
            key: expected[key] for key in ("bytes", "sha256")
        }:
            raise ValueError("AADR source changed during reading")
    if (
        before != {name: identity(repository / COUNTRY / name) for name in before}
        or revision(repository) != commit
    ):
        raise ValueError("Source or existing country account changed during reading")
    result["elapsed_seconds"] = time.monotonic() - start
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if result["elapsed_seconds"] > 60 or len(body.encode()) > 1_000_000:
        raise ValueError("Scoped source context exceeds resource/output budget")
    destination.mkdir(parents=True)
    (destination / "context.json").write_text(body)
    return result
