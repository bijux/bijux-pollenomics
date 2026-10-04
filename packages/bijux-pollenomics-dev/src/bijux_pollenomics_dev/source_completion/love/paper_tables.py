"""Derive printed LOVE article tables from an authenticated public source packet."""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any

from ..publication.json_outputs import publish_json_outputs

_MANIFEST = "data/love/paper/source.json"
_MANIFEST_SHA256 = "a31e1b1a6b2e3090d0a043b6f00a914d712de8dac6d52e22e1ed9dfbddc4fd9d"
_COLUMNS = (
    "Lakes",
    "Alnus",
    "Betula",
    "Corylus",
    "Fagus",
    "Fraxinus",
    "Pinus",
    "Tilia",
    "Ulmus",
    "Grasses",
    "Secale",
)
_NUMBER = r"(?:0|[1-9]\d*)(?:\.\d+)?"


def _read(repository: Path, name: str) -> bytes:
    """Reject source aliases and shared inodes before opening a confined member."""
    if (
        not name
        or "\\" in name
        or name.startswith("/")
        or any(part in {"", ".", ".."} for part in name.split("/"))
    ):
        raise ValueError("Public article source path must be confined")
    path = repository
    for part in name.split("/")[:-1]:
        path /= part
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError("Public article source directory must be real")
    path /= name.split("/")[-1]
    status = path.lstat()
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise ValueError("Public article source must be an independently owned file")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (status.st_dev, status.st_ino):
            raise ValueError("Public article source inode changed")
        content = stream.read()
    final = path.lstat()
    if (final.st_dev, final.st_ino) != (status.st_dev, status.st_ino):
        raise ValueError("Public article source inode changed")
    return content


def _snapshot(repository: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Authenticate the fixed public PDF and its separately qualified text derivative."""
    manifest = _read(repository, _MANIFEST)
    if hashlib.sha256(manifest).hexdigest() != _MANIFEST_SHA256:
        raise ValueError("Public article source manifest changed")
    source = json.loads(manifest)
    members = {_MANIFEST: manifest}
    for kind in ("pdf", "text"):
        record = source[kind]
        payload = _read(repository, record["path"])
        if (
            len(payload) != record["bytes"]
            or hashlib.sha256(payload).hexdigest() != record["sha256"]
        ):
            raise ValueError("Public article source bytes changed")
        members[record["path"]] = payload
    return source, members


def _numeric(token: str) -> int | float:
    """Retain integer spelling and ordinary decimal values printed in the article."""
    if re.fullmatch(_NUMBER, token) is None:
        raise ValueError("Printed table cell is not a finite nonnegative decimal")
    value = float(token) if "." in token else int(token)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Printed table value is not representable as a finite number")
    return value


def parse_tables(text: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Use positioned wrapped headers and exact row coordinates on printed page six."""
    pages = text.split("\f")
    if not pages[-1].strip():
        pages.pop()
    if len(pages) != 11 or "6 of 11" not in pages[5]:
        raise ValueError("Expected the eleven-page article and printed page six")
    page = pages[5]
    if (
        page.count("Table 1.") != 1
        or page.count("Table 2.") != 1
        or page.count("3. Results") != 1
    ):
        raise ValueError("Printed table section boundaries changed")
    first = page.split("Table 1.", 1)[1].split("Table 2.", 1)[0]
    second = page.split("Table 2.", 1)[1].split("3. Results", 1)[0]
    lines = first.splitlines()
    row_pattern = re.compile(
        r"\s*(\d+)\s+((?:" + _NUMBER + r"\s+){10}" + _NUMBER + r")\s*"
    )
    matched = [(index, row_pattern.fullmatch(line)) for index, line in enumerate(lines)]
    rows = [(index, match) for index, match in matched if match is not None]
    if len(rows) != 11:
        raise ValueError("Expected exactly eleven map-unit rows with eleven fractions")
    header = lines[: rows[0][0]]
    positions = [
        (match.start(), match.group())
        for line in header
        for match in re.finditer(r"\b(?:" + "|".join(_COLUMNS) + r")\b", line)
    ]
    columns = [name for _, name in sorted(positions)]
    if tuple(columns) != _COLUMNS:
        raise ValueError("Printed map-unit column positions changed")
    map_units = []
    for expected, (_, match) in enumerate(rows, 1):
        assert match is not None
        if int(match[1]) != expected:
            raise ValueError(
                "Map-unit coordinates must be unique and ordered one to eleven"
            )
        tokens = match[2].split()
        decimals = [Decimal(token) for token in tokens]
        if any(value < 0 or value > 1 for value in decimals) or sum(decimals) != 1:
            raise ValueError("Printed map-unit fractions must sum exactly to one")
        map_units.append(
            {
                "map_unit": expected,
                "fractions": dict(zip(columns, map(_numeric, tokens), strict=True)),
            }
        )
    parameters = []
    pattern = re.compile(
        r"\s*("
        + "|".join(_COLUMNS[1:])
        + r")\s+("
        + _NUMBER
        + r")\s+("
        + _NUMBER
        + r")\s+("
        + _NUMBER
        + r")\s*"
    )
    for line in second.splitlines():
        parameter_match = pattern.fullmatch(line)
        if parameter_match is None:
            continue
        taxon, fall, ppe, sd = parameter_match.groups()
        if (
            any(Decimal(value) <= 0 for value in (fall, ppe, sd))
            or Decimal(sd) != Decimal(ppe) / 10
        ):
            raise ValueError(
                "Printed parameters must be positive with PPE SD equal to ten percent"
            )
        parameters.append(
            {
                "taxon": taxon,
                "relative_pollen_productivity": _numeric(ppe),
                "ppe_sd": _numeric(sd),
                "fall_speed_as_published": _numeric(fall),
            }
        )
    if [row["taxon"] for row in parameters] != list(_COLUMNS[1:]):
        raise ValueError("Expected the ten printed taxon rows in their source order")
    return {
        "columns": columns,
        "map_units": map_units,
        "fraction_sum_absolute_tolerance": 1e-12,
    }, parameters


def build(repository: Path) -> dict[str, Any]:
    """Derive only printed constants; authenticate all source bytes before and after."""
    repository = repository.resolve(strict=True)
    source, before = _snapshot(repository)
    table_1, table_2 = parse_tables(before[source["text"]["path"]].decode("utf-8"))
    result = {
        "schema_version": "love-paper-parameter-tables.v1",
        "source": {
            "doi": source["doi"],
            "public_source_manifest": _MANIFEST,
            "public_source_manifest_sha256": _MANIFEST_SHA256,
            "publisher_pdf_url": source["publisher_pdf_url"],
            "repository_pdf_path": source["pdf"]["path"],
            "pdf_sha256": source["pdf"]["sha256"],
            "pdf_bytes": source["pdf"]["bytes"],
            "text_sha256": source["text"]["sha256"],
            "license": source["license"],
            "license_url": source["license_url"],
            "pdf_page": 6,
            "tables": ["Table 1", "Table 2"],
            "extraction": "source-bound printed decimal rows from qualified PDF text; wrapped header positions, map-unit sums and PPE SD ratio checked",
            "fall_speed_unit": "not_stated_in_table_2",
        },
        "table_1": table_1,
        "table_2": table_2,
        "derived_checks": {
            "map_unit_rows": 11,
            "map_unit_fraction_sums_all_one": True,
            "parameter_taxa": 10,
            "ppe_sd_equals_ten_percent_of_ppe": True,
        },
        "scope": "Published parameter constants only; no BÜK200 extraction, pond geometry, ring areas, pollen realizations, random draws or Figure 2 result is reconstructed.",
    }
    if _snapshot(repository) != (source, before):
        raise ValueError("Public article source changed during table derivation")
    return result


def main() -> None:
    """Write one new artifact JSON without reading its governed predecessor."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    if output != output.resolve() or not output.is_relative_to(
        repository / "artifacts"
    ):
        raise ValueError(
            "Table publication requires a physical repository artifact path"
        )
    result = build(repository)
    publish_json_outputs([(output, result)])


if __name__ == "__main__":
    main()
