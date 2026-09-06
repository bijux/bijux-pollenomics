"""Minimal XLSX row extraction for curated supplementary tables."""

from __future__ import annotations

import zipfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

from ..models import _XLSX_NS


def _read_xlsx_member_rows(
    bundle_path: Path,
    *,
    member_name: str,
    sheet_name: str,
) -> tuple[tuple[str, ...], ...]:
    bundle_path = Path(bundle_path)
    cache_key = (
        str(bundle_path),
        bundle_path.stat().st_mtime_ns,
        bundle_path.stat().st_size,
        member_name,
        sheet_name,
    )
    return _cached_xlsx_member_rows(cache_key)


@lru_cache(maxsize=128)
def _cached_xlsx_member_rows(
    cache_key: tuple[str, int, int, str, str],
) -> tuple[tuple[str, ...], ...]:
    bundle_path_text, _, _, member_name, sheet_name = cache_key
    bundle_path = Path(bundle_path_text)
    try:
        with zipfile.ZipFile(bundle_path) as outer:
            if member_name not in outer.namelist():
                return ()
            workbook_payload = outer.read(member_name)
        with zipfile.ZipFile(BytesIO(workbook_payload)) as workbook:
            shared_strings = _xlsx_shared_strings(workbook)
            sheet_targets = _xlsx_sheet_targets(workbook)
            target = sheet_targets[sheet_name]
            root = ET.fromstring(workbook.read(target))
            rows = []
            for row in root.findall(".//a:sheetData/a:row", _XLSX_NS):
                values: list[str] = []
                for cell in row.findall("a:c", _XLSX_NS):
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("a:v", _XLSX_NS)
                    if value_node is None or value_node.text is None:
                        values.append("")
                    elif cell_type == "s":
                        values.append(shared_strings[int(value_node.text)])
                    else:
                        values.append(value_node.text.strip())
                rows.append(tuple(values))
    except (KeyError, ValueError, zipfile.BadZipFile):
        return ()
    return tuple(rows)


def _read_xlsx_rows(
    workbook_path: Path,
    *,
    sheet_name: str,
) -> tuple[tuple[str, ...], ...]:
    workbook_path = Path(workbook_path)
    cache_key = (
        str(workbook_path),
        workbook_path.stat().st_mtime_ns,
        workbook_path.stat().st_size,
        sheet_name,
    )
    return _cached_xlsx_rows(cache_key)


@lru_cache(maxsize=256)
def _cached_xlsx_rows(
    cache_key: tuple[str, int, int, str],
) -> tuple[tuple[str, ...], ...]:
    workbook_path_text, _, _, sheet_name = cache_key
    workbook_path = Path(workbook_path_text)
    with zipfile.ZipFile(workbook_path) as workbook:
        shared_strings = _xlsx_shared_strings(workbook)
        sheet_targets = _xlsx_sheet_targets(workbook)
        target = sheet_targets[sheet_name]
        root = ET.fromstring(workbook.read(target))
        rows = []
        for row in root.findall(".//a:sheetData/a:row", _XLSX_NS):
            values: list[str] = []
            for cell in row.findall("a:c", _XLSX_NS):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", _XLSX_NS)
                if value_node is None or value_node.text is None:
                    values.append("")
                elif cell_type == "s":
                    values.append(shared_strings[int(value_node.text)])
                else:
                    values.append(value_node.text.strip())
            rows.append(tuple(values))
    return tuple(rows)


def _xlsx_shared_strings(workbook: zipfile.ZipFile) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return ()
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("a:si", _XLSX_NS):
        texts = [node.text or "" for node in item.iterfind(".//a:t", _XLSX_NS)]
        strings.append("".join(texts))
    return tuple(strings)


def _xlsx_sheet_targets(workbook: zipfile.ZipFile) -> dict[str, str]:
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall("p:Relationship", _XLSX_NS)
    }
    mapping: dict[str, str] = {}
    sheets = workbook_root.find("a:sheets", _XLSX_NS)
    if sheets is None:
        return mapping
    for sheet in sheets:
        relationship_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        mapping[sheet.attrib["name"]] = f"xl/{rel_map[relationship_id]}"
    return mapping
