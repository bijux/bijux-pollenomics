"""Read the pinned Swedish NFI field dictionary without opening plot outcomes."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import stat
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_SOURCE = Path("reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx")
_SOURCE_SHA256 = "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294"
_IDENTITY_HEADERS = (
    "Year",
    "TractID",
    "PlotID",
    "Inventory_Date",
    "Easting",
    "Northing",
)
_BASAL_AREA_HEADERS = (
    "BaPine",
    "BaContorta",
    "BaSpruce",
    "BaBirch",
    "BaOtherDec",
)


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _owned_payload(path: Path, identity: tuple[int, int], digest: str) -> bool:
    """Recognize only the original regular inode with its complete staged bytes."""
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or (before.st_dev, before.st_ino) != identity
            or _digest(path) != digest
        ):
            return False
        after = path.lstat()
    except (FileNotFoundError, OSError):
        return False
    return (
        stat.S_ISREG(after.st_mode)
        and (after.st_dev, after.st_ino) == identity
        and before.st_size == after.st_size
        and before.st_mtime_ns == after.st_mtime_ns
        and before.st_ctime_ns == after.st_ctime_ns
    )


def _source_file(private_source_store: Path) -> Path:
    root = private_source_store.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Swedish NFI source root is not a directory")
    source = root
    for component in _SOURCE.parts:
        source /= component
        if source.is_symlink():
            raise ValueError("Swedish NFI source path contains a symlink")
    if not source.is_file():
        raise ValueError("Swedish NFI source is not a regular file")
    return source


def _require_source(private_source_store: Path) -> Path:
    source = _source_file(private_source_store)
    if _digest(source) != _SOURCE_SHA256:
        raise ValueError("Swedish NFI original source identity changed")
    return source


def _string(cell: ET.Element, strings: list[str]) -> str:
    value = cell.find(_NS + "v")
    if value is None or value.text is None:
        raise ValueError("NFI schema cell has no value")
    return strings[int(value.text)] if cell.get("t") == "s" else value.text


def _shared_strings(archive: ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.iter(_NS + "t"))
        for item in root.findall(_NS + "si")
    ]


def _dictionary(archive: ZipFile, strings: list[str]) -> dict[str, str]:
    root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    result: dict[str, str] = {}
    for row in root.iter(_NS + "row"):
        cells = {
            cell.get("r", "").rstrip("0123456789"): _string(cell, strings)
            for cell in row.findall(_NS + "c")
            if cell.get("r", "").rstrip("0123456789") in {"A", "B"}
        }
        name = cells.get("A")
        if name and name != "Column":
            if name in result or not cells.get("B"):
                raise ValueError("NFI field dictionary is incomplete or duplicated")
            result[name] = cells["B"]
    return result


def _headers(archive: ZipFile, strings: list[str]) -> list[str]:
    with archive.open("xl/worksheets/sheet2.xml") as stream:
        for event, row in ET.iterparse(stream, events=("end",)):
            if event == "end" and row.tag == _NS + "row":
                if row.get("r") != "1":
                    raise ValueError("NFI measurement header is not the first row")
                return [_string(cell, strings) for cell in row.findall(_NS + "c")]
    raise ValueError("NFI measurement header is missing")


def _plot_support(archive: ZipFile, strings: list[str]) -> dict[str, object]:
    land_use: Counter[str] = Counter()
    dates: list[float] = []
    rows = 0
    with archive.open("xl/worksheets/sheet2.xml") as stream:
        root: ET.Element | None = None
        for event, element in ET.iterparse(stream, events=("start", "end")):
            if root is None and event == "start":
                root = element
            if event != "end" or element.tag != _NS + "row":
                continue
            if element.get("r") != "1":
                values = {
                    column: _string(cell, strings)
                    for cell in element.findall(_NS + "c")
                    if (column := cell.get("r", "").rstrip("0123456789"))
                    in {"D", "G", "H"}
                }
                if set(values) != {"D", "G", "H"} or values["G"] != "153.94":
                    raise ValueError("Swedish NFI plot support changed")
                date = float(values["D"])
                if not isfinite(date):
                    raise ValueError("Swedish NFI inventory date is not finite")
                dates.append(date)
                land_use[values["H"]] += 1
                rows += 1
            element.clear()
            if root is not None:
                root.clear()
    if rows != 43_892 or not dates:
        raise ValueError("Swedish NFI plot-year denominator changed")
    return {
        "plot_year_rows": rows,
        "plot_area_m2_each": 153.94,
        "land_use_code_counts": dict(sorted(land_use.items())),
        "inventory_date_excel_serial_min": min(dates),
        "inventory_date_excel_serial_max": max(dates),
        "metadata_cells_decoded": rows * 3,
    }


def build(private_source_store: Path) -> dict[str, object]:
    """Return a source-bound schema receipt without decoding measurement rows."""
    source = _require_source(private_source_store)
    with ZipFile(source) as archive:
        strings = _shared_strings(archive)
        dictionary = _dictionary(archive, strings)
        headers = _headers(archive, strings)
        plot_support = _plot_support(archive, strings)
    if (
        len(headers) != 47
        or tuple(headers[:6]) != _IDENTITY_HEADERS
        or tuple(headers[25:30]) != _BASAL_AREA_HEADERS
        or len(headers) != len(set(headers))
        or any(
            header not in dictionary
            for header in (
                "Inventory_Date",
                "PlotArea",
                "LandUseClass",
                *_BASAL_AREA_HEADERS,
            )
        )
    ):
        raise ValueError("Swedish NFI measurement schema changed")
    basal_area = {name: dictionary[name] for name in _BASAL_AREA_HEADERS}
    if any(not description.endswith("(m2/ha)") for description in basal_area.values()):
        raise ValueError("Swedish NFI basal-area units changed")
    if not dictionary["PlotArea"].startswith("Circular plot r=7 => 153.94 m2"):
        raise ValueError("Swedish NFI plot-area description changed")
    if "Forestland according to FAO-definitions" not in dictionary["LandUseClass"]:
        raise ValueError("Swedish NFI land-use support changed")
    _require_source(private_source_store)
    return {
        "schema_version": "nfi-measurement-schema.1",
        "source_path_in_private_store": _SOURCE.as_posix(),
        "source_sha256": _SOURCE_SHA256,
        "workbook_header_count": len(headers),
        "workbook_headers": headers,
        "headers_without_exact_dictionary_entry": [
            header for header in headers if header not in dictionary
        ],
        "identity_and_geometry_headers": list(_IDENTITY_HEADERS),
        "inventory_date_description": dictionary["Inventory_Date"],
        "plot_area_description": dictionary["PlotArea"],
        "land_use_description": dictionary["LandUseClass"],
        "candidate_tree_basal_area_fields": basal_area,
        "candidate_tree_basal_area_unit": "m2/ha",
        "source_plot_support": plot_support,
        "measurement_outcome_cells_decoded": 0,
        "benchmark_admission": "no_measured_pairs_admitted",
    }


def main() -> None:
    """Run the CLI to read the pinned Swedish NFI field dictionary without opening plot outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Absent output file required")
    result = build(args.private_source_store)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    payload_sha256 = sha256(payload).hexdigest()
    stage: Path | None = None
    identity: tuple[int, int] | None = None
    published = False
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=args.output.parent,
            prefix=f".{args.output.name}.pending-",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            opened = os.fstat(stream.fileno())
            identity = (opened.st_dev, opened.st_ino)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if stage is None or identity is None:
            raise ValueError("NFI publication stage was not created")
        if not _owned_payload(stage, identity, payload_sha256):
            raise ValueError("Owned NFI publication stage changed")
        _require_source(args.private_source_store)
        if not _owned_payload(stage, identity, payload_sha256):
            raise ValueError("Owned NFI publication stage changed")
        os.link(stage, args.output)
        published = True
        if not (
            _owned_payload(stage, identity, payload_sha256)
            and _owned_payload(args.output, identity, payload_sha256)
        ):
            raise ValueError("NFI publication output differs from owned stage")
        _require_source(args.private_source_store)
        if not (
            _owned_payload(stage, identity, payload_sha256)
            and _owned_payload(args.output, identity, payload_sha256)
        ):
            raise ValueError("NFI publication output or stage changed before success")
    except BaseException:
        if (
            published
            and identity is not None
            and _owned_payload(args.output, identity, payload_sha256)
        ):
            args.output.unlink()
        raise
    finally:
        if (
            stage is not None
            and identity is not None
            and _owned_payload(stage, identity, payload_sha256)
        ):
            stage.unlink()
    print(json.dumps({"headers": result["workbook_header_count"], "outcomes": 0}))


if __name__ == "__main__":
    main()
