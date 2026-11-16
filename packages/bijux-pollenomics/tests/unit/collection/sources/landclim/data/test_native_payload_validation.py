"""Native containers refuse provider error pages before publication."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from bijux_pollenomics.collection.sources.landclim.catalog import (
    validate_landclim_raw_asset,
)


def workbook_bytes() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="source" sheetId="1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>',
        )
    return buffer.getvalue()


def test_accepts_native_workbook_container() -> None:
    validate_landclim_raw_asset("landclim_i_land_cover_types.xlsx", workbook_bytes())


@pytest.mark.parametrize(
    "filename",
    [
        "landclim_i_land_cover_types.xlsx",
        "landclim_ii_reveals_results.zip",
        "landclim_ii_taxa_pft_ppe_fsp_values.csv",
    ],
)
def test_refuses_nonempty_html_as_source(filename: str) -> None:
    with pytest.raises(ValueError, match="LandClim raw asset"):
        validate_landclim_raw_asset(
            filename, b"<!doctype html><html>provider challenge</html>"
        )


@pytest.mark.parametrize(
    "member,body",
    [
        ("xl/workbook.xml", "<broken"),
        ("foreign.txt", "foreign"),
        ("../outside.xml", "<workbook/>"),
    ],
)
def test_refuses_malformed_or_nonworkbook_zip(member: str, body: str) -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(member, body)
    with pytest.raises(ValueError, match="LandClim raw asset"):
        validate_landclim_raw_asset(
            "landclim_i_land_cover_types.xlsx", buffer.getvalue()
        )


def test_refuses_excessive_uncompressed_container() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", b"0" * (9 * 1024 * 1024))
    with pytest.raises(ValueError, match="LandClim raw asset"):
        validate_landclim_raw_asset(
            "landclim_i_land_cover_types.xlsx", buffer.getvalue()
        )


@pytest.mark.parametrize(
    "content",
    [
        b"header\n",
        b"one,two\nonly-one\n",
        b"one,two\n\xff,value\n",
        b"one,two\nforeign,data\n",
    ],
)
def test_refuses_invalid_csv(content: bytes) -> None:
    with pytest.raises(ValueError, match="LandClim raw asset"):
        validate_landclim_raw_asset("landclim_ii_taxa_pft_ppe_fsp_values.csv", content)


def test_refuses_unrelated_csv_zip_as_result_archive() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("foreign.csv", "one,two\nforeign,data\n")
    with pytest.raises(ValueError, match="LandClim raw asset"):
        validate_landclim_raw_asset(
            "landclim_ii_reveals_results.zip", buffer.getvalue()
        )


def test_accepts_complete_native_result_archive() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for family in ("means", "standarderrors"):
            for index in range(1, 26):
                archive.writestr(
                    f"LANDCLIMII.RV.{family}.JUN2021/TW{index}.source.csv",
                    "LCGRID_ID,lonDD,latDD,synthetic\nfixture,0,0,1\n",
                )
        archive.writestr("README.txt", "Synthetic ancillary archive documentation\n")
    validate_landclim_raw_asset("landclim_ii_reveals_results.zip", buffer.getvalue())


def test_accepts_rectangular_native_csv() -> None:
    validate_landclim_raw_asset(
        "landclim_ii_taxa_pft_ppe_fsp_values.csv",
        b"Plant taxa/Pollen-morphological types,FSP (m/s),PPE (SD)\nfixture,metadata,metadata\n",
    )


@pytest.mark.parametrize("count", [0, 1025, 65535])
def test_zip_entry_count_is_refused_before_directory_allocation(count: int) -> None:
    import struct
    from unittest.mock import patch

    payload = bytearray(workbook_bytes())
    end = payload.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", payload, end + 8, count, count)
    with (
        patch(
            "bijux_pollenomics.collection.sources.landclim.raw_assets.validation.ZipFile",
            side_effect=AssertionError("directory allocated"),
        ),
        pytest.raises(ValueError, match="ZIP directory limit"),
    ):
        validate_landclim_raw_asset("landclim_i_land_cover_types.xlsx", bytes(payload))
