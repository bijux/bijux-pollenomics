"""Reconcile a native HYDE cropland grid with source country totals."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
from typing import IO
from zipfile import ZipFile

from .hyde_country_cropland import (
    COUNTRIES,
    GENERAL,
    SCENARIOS,
    TABLE,
    YEARS,
    _country_codes,
    _table,
)

ZIP_PATH = "original/gbc2025_7apr_{scenario}/zip/{year}AD_lu.zip"
ISO_MEMBER = "general_files/iso_cr.asc"
CROP_MEMBER = "cropland{year}AD.asc"
HEADER = (
    ("ncols", "4320"),
    ("nrows", "2160"),
    ("xllcorner", "-180"),
    ("yllcorner", "-90"),
    ("cellsize", "0.0833333"),
    ("NODATA_value", "-9999"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _header(stream: IO[bytes]) -> None:
    for expected in HEADER:
        line = stream.readline()
        if tuple(line.decode("ascii").split()) != expected:
            raise ValueError(f"HYDE native grid header changed: {expected[0]}")


def _require_unique_member(archive: bytes, name: str) -> None:
    with ZipFile(BytesIO(archive)) as zipped:
        if sum(info.filename == name for info in zipped.infolist()) != 1:
            raise ValueError(f"HYDE archive member occurrence is ambiguous: {name}")


def _iso_positions(
    archive: bytes, codes: dict[str, str]
) -> tuple[list[dict[str, list[int]]], dict[str, int]]:
    positions: list[dict[str, list[int]]] = []
    counts = dict.fromkeys(COUNTRIES, 0)
    by_code = {code: country for country, code in codes.items()}
    _require_unique_member(archive, ISO_MEMBER)
    with ZipFile(BytesIO(archive)) as zipped, zipped.open(ISO_MEMBER) as stream:
        _header(stream)
        for _ in range(2160):
            tokens = stream.readline().split()
            if len(tokens) != 4320:
                raise ValueError("HYDE ISO grid row width changed")
            selected: dict[str, list[int]] = defaultdict(list)
            for column, token in enumerate(tokens):
                country = by_code.get(token.decode("ascii"))
                if country is not None:
                    selected[country].append(column)
                    counts[country] += 1
            positions.append(selected)
        if stream.read():
            raise ValueError("HYDE ISO grid has trailing data")
    if any(count == 0 for count in counts.values()):
        raise ValueError("HYDE ISO grid lacks a Nordic country")
    return positions, counts


def _crop_totals(
    archive: bytes, positions: list[dict[str, list[int]]], member: str
) -> tuple[dict[str, Decimal], dict[str, int], dict[str, int]]:
    totals = {country: Decimal(0) for country in COUNTRIES}
    valid = dict.fromkeys(COUNTRIES, 0)
    zeros = dict.fromkeys(COUNTRIES, 0)
    _require_unique_member(archive, member)
    with ZipFile(BytesIO(archive)) as zipped, zipped.open(member) as stream:
        _header(stream)
        for selected in positions:
            tokens = stream.readline().split()
            if len(tokens) != 4320:
                raise ValueError("HYDE cropland grid row width changed")
            for country, columns in selected.items():
                for column in columns:
                    try:
                        value = Decimal(tokens[column].decode("ascii"))
                    except InvalidOperation as exc:
                        raise ValueError(
                            "HYDE cropland grid value is not numeric"
                        ) from exc
                    if not value.is_finite() or value < 0:
                        raise ValueError(
                            "Missing or negative HYDE cropland inside selected ISO country"
                        )
                    totals[country] += value
                    valid[country] += 1
                    zeros[country] += value == 0
        if stream.read():
            raise ValueError("HYDE cropland grid has trailing data")
    return totals, valid, zeros


def publish(source_root: Path, output: Path) -> dict[str, object]:
    root = source_root.resolve()
    inputs: list[dict[str, str]] = []
    general = (root / GENERAL).read_bytes()
    inputs.append({"path": GENERAL, "sha256": _sha(general), "member": ISO_MEMBER})
    codes = _country_codes(general)
    positions, cells = _iso_positions(general, codes)
    rows: list[dict[str, str | int]] = []
    for scenario in SCENARIOS:
        table_path = TABLE.format(scenario=scenario)
        table = (root / table_path).read_bytes()
        inputs.append({"path": table_path, "sha256": _sha(table)})
        source_totals = _table(table, codes)
        for year in YEARS:
            zip_path = ZIP_PATH.format(scenario=scenario, year=year)
            member = CROP_MEMBER.format(year=year)
            archive = (root / zip_path).read_bytes()
            inputs.append({"path": zip_path, "sha256": _sha(archive), "member": member})
            totals, valid, zeros = _crop_totals(archive, positions, member)
            for country in COUNTRIES:
                expected = source_totals[(country, year)]
                difference = totals[country] - expected
                if valid[country] != cells[country] or abs(difference) > Decimal(
                    "0.000001"
                ):
                    raise ValueError(
                        f"HYDE {scenario} {country} {year} grid/country conservation failed: {difference}"
                    )
                rows.append(
                    {
                        "scenario": scenario,
                        "country": country,
                        "hyde_iso_code": codes[country],
                        "source_year_ce_label": year,
                        "iso_grid_cells": cells[country],
                        "valid_cropland_cells": valid[country],
                        "zero_cropland_cells": zeros[country],
                        "grid_cropland_km2": str(totals[country]),
                        "source_country_cropland_km2": str(expected),
                        "grid_minus_country_km2": str(difference),
                    }
                )
    report: dict[str, object] = {
        "schema_version": "hyde-nordic-native-country-conservation.v1",
        "measure": "Native cropland km2 per source ISO country, seven CE labels and three scenarios",
        "country_codes": codes,
        "scenario_count": len(SCENARIOS),
        "country_count": len(COUNTRIES),
        "source_year_ce_labels": list(YEARS),
        "rows": len(rows),
        "inputs": inputs,
        "conservation_tolerance_km2": "0.000001",
        "interpretation": "The native ISO and cropland ASCII grids have identical literal headers, every selected ISO cell has a nonnegative cropland value, and its exact decimal sum agrees with the source country table at the stated tolerance for seven CE labels. This checks four countries and cropland only; it does not resolve formal CRS, BP calendar, release rights or independent vegetation truth.",
    }
    output.mkdir(parents=True, exist_ok=False)
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (output / "grid-conservation.csv").write_text(buffer.getvalue(), encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.source_root, args.output), indent=2))


if __name__ == "__main__":
    main()
