from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import stat
from typing import cast
from zipfile import ZipFile
from zipfile import ZipInfo

import pytest

from bijux_pollenomics.collection.sources.rootsi import normalization
from bijux_pollenomics.collection.sources.rootsi import authority, ooxml
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

_SHARED = (
    "Country",
    "Site name",
    "site_ID",
    "R_ID",
    "nr_samples",
    "Site label",
    "File name",
    "LatDMS",
    "LatDD",
    "LongDMS",
    "LongDD",
    "Elevation",
    "Site area (ha)",
    "Site radius (m)",
    "No. of dates1",
    "Basin type",
    "SWE",
    "Example site",
    "l_1",
    "a1",
    "EXAMPLE",
    "EXAMPLE.xls",
    "55.30.00N",
    "12.30.00E",
    "Lake",
    "review note",
)


def _workbook(path: Path) -> None:
    shared = "".join(f"<si><t>{value}</t></si>" for value in _SHARED)
    header = "".join(
        f'<c r="{chr(65 + index)}1" t="s"><v>{index}</v></c>' for index in range(16)
    )
    values = (
        16,
        17,
        18,
        19,
        None,
        20,
        21,
        22,
        "55.5",
        23,
        "12.5",
        "100",
        "2.5",
        "178",
        None,
        24,
        25,
    )
    cells = []
    for index, value in enumerate(values):
        column = chr(65 + index)
        if isinstance(value, int):
            cells.append(f'<c r="{column}2" t="s"><v>{value}</v></c>')
        elif value is not None:
            cells.append(f'<c r="{column}2"><v>{value}</v></c>')
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f"{shared}</sst>",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData><row r="1">{header}</row>'
            f'<row r="2">{"".join(cells)}</row></sheetData></worksheet>',
        )


def test_metadata_claims_remain_unadmitted_and_source_native(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "metadata.xlsx"
    _workbook(path)
    monkeypatch.setattr(
        normalization, "METADATA_SHA256", hashlib.sha256(path.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(normalization, "METADATA_SIZE_BYTES", path.stat().st_size)
    monkeypatch.setattr(normalization, "METADATA_SITE_COUNT", 1)

    claims = normalization.normalize_rootsi_site_metadata(path)

    assert len(claims) == 1
    claim = claims[0]
    assert claim.sample_count_claim is None
    assert str(claim.latitude_decimal_claim) == "55.5"
    assert str(claim.longitude_decimal_claim) == "12.5"
    assert claim.coordinate_status == "unadmitted_conflicting_claims"
    assert claim.chronology_status == "not_present_in_metadata"
    assert claim.rights_status == "per_sequence_unresolved"
    assert claim.source_archive_sha256 == normalization.ARCHIVE_SHA256
    assert claim.source_member.endswith("Metadata table_SWE_climate.xlsx")
    assert claim.unsupported_values == (("Q", "review note"),)
    assert not claim.public_release_allowed
    assert not claim.propagation_use_allowed
    assert claim.as_dict()["source_values"]["nr_samples"] is None
    first = json.dumps(claim.as_dict(), sort_keys=True, separators=(",", ":"))
    second = json.dumps(claims[0].as_dict(), sort_keys=True, separators=(",", ":"))
    assert first == second


def test_production_receipt_constants_are_exact() -> None:
    assert authority.ARCHIVE_SHA256 == (
        "f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c"
    )
    assert authority.ARCHIVE_SIZE_BYTES == 509_919
    assert authority.ARCHIVE_MEMBER_COUNT == 82
    assert authority.ARCHIVE_REGULAR_FILE_COUNT == 81
    assert authority.ARCHIVE_EXPANDED_BYTES == 4_522_477
    assert authority.METADATA_MEMBER == "rootsi/Metadata table_SWE_climate.xlsx"
    assert authority.METADATA_SHA256 == (
        "08c928407aa1c70c38be8a310a1d9d5e6215434a96ee7fbbd3ba849184e9ee47"
    )
    assert authority.METADATA_SIZE_BYTES == 54_688
    assert authority.METADATA_SITE_COUNT == 81


def test_duplicate_site_ids_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "metadata.xlsx"
    _workbook(path)
    rows = ooxml.read_first_worksheet(BytesIO(path.read_bytes()))
    monkeypatch.setattr(
        normalization, "METADATA_SHA256", hashlib.sha256(path.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(normalization, "METADATA_SIZE_BYTES", path.stat().st_size)
    monkeypatch.setattr(normalization, "METADATA_SITE_COUNT", 2)
    monkeypatch.setattr(
        normalization, "read_first_worksheet", lambda _stream: rows + rows[1:]
    )

    with pytest.raises(IntakeRefusal, match="duplicate_rootsi_site_id"):
        normalization.normalize_rootsi_site_metadata(path)


def test_ooxml_member_collisions_and_resource_hazards_fail_closed() -> None:
    collision = BytesIO()
    with ZipFile(collision, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", "one")
        archive.writestr("XL/WORKSHEETS/SHEET1.XML", "two")
    with pytest.raises(IntakeRefusal, match="colliding_workbook_member"):
        ooxml.read_first_worksheet(collision)

    encrypted = ZipInfo("xl/sharedStrings.xml")
    encrypted.flag_bits |= 1
    with pytest.raises(IntakeRefusal, match="encrypted_workbook_member"):
        ooxml._validate_parts([encrypted])

    special = ZipInfo("xl/worksheets/sheet1.xml")
    special.create_system = 3
    special.external_attr = (stat.S_IFIFO | 0o600) << 16
    with pytest.raises(IntakeRefusal, match="workbook_special_file"):
        ooxml._validate_parts([special])

    oversized = ZipInfo("xl/sharedStrings.xml")
    oversized.file_size = ooxml._MAXIMUM_MEMBER_BYTES + 1
    oversized.compress_size = oversized.file_size
    with pytest.raises(IntakeRefusal, match="workbook_member_size_limit"):
        ooxml._validate_parts([oversized])

    compressed = ZipInfo("xl/sharedStrings.xml")
    compressed.file_size = 1_000
    compressed.compress_size = 1
    with pytest.raises(IntakeRefusal, match="workbook_compression_ratio_limit"):
        ooxml._validate_parts([compressed])


@pytest.mark.parametrize(
    "name",
    (
        "xl/vbaProject.bin",
        "xl/externalLinks/link1.xml",
        "xl\\externalLinks\\link1.xml",
    ),
)
def test_ooxml_active_content_paths_fail_closed(name: str) -> None:
    with pytest.raises(IntakeRefusal, match="active_workbook_content"):
        ooxml._validate_parts([ZipInfo(name)])


@pytest.mark.parametrize(
    "name", ("../escape.xml", "/absolute.xml", "C:/drive.xml", "C:\\drive.xml")
)
def test_ooxml_unsafe_paths_fail_closed(name: str) -> None:
    with pytest.raises(IntakeRefusal, match="unsafe_workbook_path"):
        ooxml._validate_parts([ZipInfo(name)])


def test_ooxml_symlinks_and_all_resource_limits_fail_closed() -> None:
    symlink = ZipInfo("xl/worksheets/link.xml")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(IntakeRefusal, match="workbook_symlink"):
        ooxml._validate_parts([symlink])

    too_many = [ZipInfo(f"part-{index}.xml") for index in range(1_001)]
    with pytest.raises(IntakeRefusal, match="workbook_member_limit"):
        ooxml._validate_parts(too_many)

    aggregate = [ZipInfo("first.xml"), ZipInfo("second.xml")]
    for info in aggregate:
        info.file_size = ooxml._MAXIMUM_EXPANDED_BYTES // 2 + 1
        info.compress_size = info.file_size
    with pytest.raises(IntakeRefusal, match="workbook_expanded_size_limit"):
        ooxml._validate_parts(aggregate)


def test_ooxml_formulae_and_actual_output_mismatch_fail_closed() -> None:
    workbook = BytesIO()
    with ZipFile(workbook, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main"><sheetData><row r="1">'
            '<c r="A1"><f>1+1</f><v>2</v></c>'
            "</row></sheetData></worksheet>",
        )
    with pytest.raises(IntakeRefusal, match="workbook_formula_not_supported"):
        ooxml.read_first_worksheet(workbook)

    class ShortArchive:
        def open(self, _info: ZipInfo) -> BytesIO:
            return BytesIO(b"short")

    declared = ZipInfo("part.xml")
    declared.file_size = len(b"short") + 1
    with pytest.raises(IntakeRefusal, match="workbook_output_size_mismatch"):
        ooxml._read_part(cast(ZipFile, ShortArchive()), declared)
