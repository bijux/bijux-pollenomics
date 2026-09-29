"""Keep original count categories separate in the Swedish core comparison."""

from __future__ import annotations

from zipfile import ZipFile

import pytest

from bijux_pollenomics_dev.source_completion.abborrtjarne_core import (
    _count_labels,
    _workbook_row,
)


def test_counts_preserve_indeterminable_pollen_and_nonpollen_mass() -> None:
    rows = [
        {
            "variablename": "Betula",
            "value": 12,
            "units": "NISP",
            "element": "pollen",
            "elementtype": "pollen",
        },
        {
            "variablename": "Indeterminable",
            "value": 3,
            "units": "NISP",
            "element": "pollen",
            "elementtype": "pollen",
        },
        {
            "variablename": "Sphagnum",
            "value": 2,
            "units": "NISP",
            "element": "spore",
            "elementtype": "spore",
        },
    ]
    result = _count_labels(rows)
    assert result["pollen_observations"] == 2
    assert result["pollen_count_sum"] == 15
    assert result["indeterminable_pollen_count"] == 3
    assert result["nonpollen_observations"] == 1
    assert result["nonpollen_count_sum"] == 2
    with pytest.raises(ValueError, match="exact nonnegative NISP"):
        _count_labels([{**rows[0], "units": "percent"}])
    with pytest.raises(ValueError, match="unresolved source element"):
        _count_labels([{**rows[0], "elementtype": "spore"}])


def test_published_radius_needs_documented_metre_unit(tmp_path) -> None:
    path = tmp_path / "metadata.xlsx"
    namespace = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    shared = f"<sst {namespace}><si><t>siteradius</t></si></sst>"
    sheet2 = (
        f"<worksheet {namespace}><sheetData>"
        '<row r="1"><c r="A1"><v>SiteName</v></c></row>'
        '<row r="968"><c r="A968"><v>Abborrtjärnen</v></c></row>'
        "</sheetData></worksheet>"
    )

    def write(definition: str) -> None:
        sheet1 = (
            f'<worksheet {namespace}><sheetData><row r="6">'
            '<c r="A6" t="s"><v>0</v></c>'
            f'<c r="B6"><v>{definition}</v></c>'
            "</row></sheetData></worksheet>"
        )
        with ZipFile(path, "w") as archive:
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet1)
            archive.writestr("xl/worksheets/sheet2.xml", sheet2)

    write("radius of the site in meters")
    assert _workbook_row(path, 968)[1]["A"] == "Abborrtjärnen"
    write("depth of the site in meters")
    with pytest.raises(ValueError, match="site-radius unit"):
        _workbook_row(path, 968)
