"""Check exact time, taxon and percentage-unit joins for the ESSD slice."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_correspondence import (
    MEAN_MEMBER,
    SE_MEMBER,
    _candidate_values,
    _exact_author_window,
    _published_rows,
)


def test_exact_window_accepts_only_source_100_to_350_bp(tmp_path: Path) -> None:
    bins = tmp_path / "bins.csv"
    lookup = tmp_path / "TWlookup.csv"
    edges = [-65, 100, 350, *range(750, 11751, 500)]
    assert len(edges) == 26
    bins.write_text("\n".join(map(str, edges)) + "\n")
    with lookup.open("w", newline="") as stream:
        csv.writer(stream).writerows(
            [
                ["TW", "class"],
                *[[str(index), str(index * 500 - 775)] for index in range(1, 26)],
            ]
        )
    rows = list(csv.reader(lookup.open(newline="")))
    rows[2][1] = "225"
    with lookup.open("w", newline="") as stream:
        csv.writer(stream).writerows(rows)
    assert _exact_author_window(bins, lookup)[1] == "225"
    bins.write_text(
        "\n".join(map(str, [-65, 100, 400, *range(750, 11751, 500)])) + "\n"
    )
    with pytest.raises(ValueError, match="time-window bounds"):
        _exact_author_window(bins, lookup)


def test_fraction_candidate_is_explicitly_converted_to_percentage_points(
    tmp_path: Path,
) -> None:
    path = tmp_path / "regional-cover.csv"
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows([["bin_id", "Abies alba"], ["225", "0.125"]])
    assert _candidate_values(path, ["225"], ["Abies alba"]) == {
        "Abies alba": Decimal("12.500")
    }


def test_archive_reader_rejects_mean_se_taxon_axis_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "archive.zip"
    prepared = [f"Taxon{i}" for i in range(31)]

    def table(taxa: list[str]) -> str:
        header = ["LCGRID_ID", "lonDD", "latDD", *taxa]
        rows = [
            [grid, "-3.5", latitude, *(["1"] * 31)]
            for grid, latitude in (("512", "50.5"), ("562", "51.5"))
        ]
        return ",".join(header) + "\n" + "\n".join(",".join(row) for row in rows) + "\n"

    with ZipFile(path, "w") as archive:
        archive.writestr(MEAN_MEMBER, table(prepared))
        archive.writestr(SE_MEMBER, table(prepared))
    with ZipFile(path) as archive:
        means, errors, locators = _published_rows(archive, prepared)
    assert means["512"]["Taxon0"] == errors["512"]["Taxon0"] == "1"
    locator = locators["562"]
    assert isinstance(locator, dict)
    assert locator["latitude"] == "51.5"

    with ZipFile(path, "w") as archive:
        archive.writestr(MEAN_MEMBER, table(prepared))
        archive.writestr(SE_MEMBER, table([*reversed(prepared)]))
    with ZipFile(path) as archive, pytest.raises(ValueError, match="axes differ"):
        _published_rows(archive, prepared)
