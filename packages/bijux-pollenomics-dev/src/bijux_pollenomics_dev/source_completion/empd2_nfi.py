"""Screen EMPD2 pollen against NFI plot geometry without admitting reference pairs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import tempfile
from typing import Any, cast
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pyproj import Geod, Transformer

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COLUMNS = ("A", "B", "C", "D", "E", "F")
_HEADERS = ("Year", "TractID", "PlotID", "Inventory_Date", "Easting", "Northing")
_DISTANCES_M = (1_000, 5_000, 10_000)


@dataclass
class _LeadCounts:
    pairs: int = 0
    pollen: set[str] = field(default_factory=set)
    plot_year: set[tuple[str, str, str]] = field(default_factory=set)
    plot: set[tuple[str, str]] = field(default_factory=set)

    def add(self, sample: str, row: tuple[str, str, str, str, float, float]) -> None:
        self.pairs += 1
        self.pollen.add(sample)
        self.plot_year.add((row[1], row[2], row[0]))
        self.plot.add((row[1], row[2]))

    def summary(self) -> dict[str, int]:
        return {
            "candidate_plot_year_sample_pairs": self.pairs,
            "pollen_samples": len(self.pollen),
            "nfi_plot_years": len(self.plot_year),
            "nfi_plots": len(self.plot),
        }


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_pinned_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    if _digest(path) != expected_sha256:
        raise ValueError("input_digest_mismatch")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid_input_report")
    return cast(dict[str, Any], value)


def _cell(cell: ET.Element, strings: list[str]) -> str | None:
    value = cell.find(_NS + "v")
    if value is None or value.text is None:
        return None
    return strings[int(value.text)] if cell.get("t") == "s" else value.text


def _selected(row: ET.Element, strings: list[str]) -> tuple[str | None, ...]:
    values: dict[str, str | None] = {}
    for cell in row.findall(_NS + "c"):
        column = cell.get("r", "").rstrip("0123456789")
        if column in _COLUMNS:
            values[column] = _cell(cell, strings)
    return tuple(values.get(column) for column in _COLUMNS)


def _nfi_rows(source: Path) -> list[tuple[str, str, str, str, float, float]]:
    rows: list[tuple[str, str, str, str, float, float]] = []
    keys: set[tuple[str, str, str]] = set()
    with ZipFile(source) as archive:
        strings_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = [
            "".join(node.text or "" for node in item.iter(_NS + "t"))
            for item in strings_root.findall(_NS + "si")
        ]
        with archive.open("xl/worksheets/sheet2.xml") as stream:
            root: ET.Element | None = None
            for event, element in ET.iterparse(stream, events=("start", "end")):
                if root is None and event == "start":
                    root = element
                if event != "end" or element.tag != _NS + "row":
                    continue
                values = _selected(element, strings)
                if element.get("r") == "1":
                    if values != _HEADERS:
                        raise ValueError("nfi_columns_changed")
                else:
                    if any(value in (None, "") for value in values):
                        raise ValueError("nfi_geometry_identity_missing")
                    year, tract, plot, date, easting, northing = values
                    assert year and tract and plot and date and easting and northing
                    key = (tract, plot, year)
                    if key in keys:
                        raise ValueError("nfi_plot_year_duplicate")
                    keys.add(key)
                    x, y = float(easting), float(northing)
                    if not (isfinite(x) and isfinite(y)):
                        raise ValueError("nfi_geometry_nonfinite")
                    rows.append((year, tract, plot, date, x, y))
                element.clear()
                if root is not None:
                    root.clear()
    return rows


def screen_empd2_nfi_geometry(
    workbook: Path,
    workbook_sha256: str,
    schema_path: Path,
    schema_sha256: str,
    eligibility_path: Path,
    eligibility_sha256: str,
    pollen_path: Path,
    pollen_sha256: str,
) -> dict[str, object]:
    """Count spatial leads; source pollen age never becomes NFI collection time."""
    schema = _read_pinned_json(schema_path, schema_sha256)
    eligibility = _read_pinned_json(eligibility_path, eligibility_sha256)
    pollen = _read_pinned_json(pollen_path, pollen_sha256)
    if (
        _digest(workbook) != workbook_sha256
        or schema.get("source_sha256") != workbook_sha256
        or schema.get("selected_readme_descriptions", {}).get("Easting")
        != "Meters. Sweref99TM"
        or schema.get("selected_readme_descriptions", {}).get("Northing")
        != "Meters. Sweref99TM"
        or eligibility.get("source_sha256") != workbook_sha256
        or eligibility.get("schema_report_sha256") != schema_sha256
        or pollen.get("schema_version") != "empd2-nordic-candidate-screen.v1"
        or pollen.get("scientific_admission") != "candidate_only"
    ):
        raise ValueError("source_identity_or_posture_mismatch")
    rows = _nfi_rows(workbook)
    if len(rows) != eligibility.get("data_rows_counted") or len(
        {(row[1], row[2]) for row in rows}
    ) != eligibility.get("distinct_tract_plot_keys"):
        raise ValueError("nfi_cohort_denominator_mismatch")
    transformer = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)
    coordinates = [transformer.transform(row[4], row[5]) for row in rows]
    if any(
        not (isfinite(lon) and isfinite(lat) and 10 <= lon <= 25 and 54 <= lat <= 70)
        for lon, lat in coordinates
    ):
        raise ValueError("nfi_projected_coordinate_outside_sweden_screen")
    lons = [point[0] for point in coordinates]
    lats = [point[1] for point in coordinates]
    geod = Geod(ellps="WGS84")
    thresholds = {distance: _LeadCounts() for distance in _DISTANCES_M}
    count_candidates = {distance: _LeadCounts() for distance in _DISTANCES_M}
    nearest: list[dict[str, object]] = []
    swedish = [
        sample
        for sample in pollen.get("samples", [])
        if isinstance(sample, dict) and sample.get("country") == "Sweden"
    ]
    if len(swedish) != pollen.get("country_counts", {}).get("Sweden", {}).get(
        "metadata_samples"
    ):
        raise ValueError("pollen_country_denominator_mismatch")
    invalid_pollen_coordinates = 0
    for sample in swedish:
        lon, lat = sample.get("source_longitude"), sample.get("source_latitude")
        if (
            isinstance(lon, bool)
            or isinstance(lat, bool)
            or not isinstance(lon, (int, float))
            or not isinstance(lat, (int, float))
            or not (
                isfinite(lon)
                and isfinite(lat)
                and -180 <= lon <= 180
                and -90 <= lat <= 90
            )
        ):
            invalid_pollen_coordinates += 1
            continue
        _, _, distances = geod.inv([lon] * len(rows), [lat] * len(rows), lons, lats)
        closest = min(range(len(rows)), key=lambda index: distances[index])
        source = rows[closest]
        nearest.append(
            {
                "pollen_sample": sample["source_sample_name"],
                "pollen_agebp_source_native": sample["source_agebp"],
                "pollen_ageuncertainty_source_native": sample["source_ageuncertainty"],
                "mechanical_count_candidate": sample["mechanical_count_candidate"],
                "pollen_review_reason_codes": sample["review_reason_codes"],
                "nfi_tract": source[1],
                "nfi_plot": source[2],
                "nfi_year": source[0],
                "nfi_inventory_date_source_native": source[3],
                "distance_m_wgs84": distances[closest],
                "nearest_row_selection": "distance_only; NFI year is not temporally matched",
                "time_support": "unresolved_collection_time",
                "pair_admission": "candidate_only",
            }
        )
        for distance in _DISTANCES_M:
            for index, value in enumerate(distances):
                if value <= distance:
                    row = rows[index]
                    name = str(sample["source_sample_name"])
                    thresholds[distance].add(name, row)
                    if sample["mechanical_count_candidate"] is True:
                        count_candidates[distance].add(name, row)
    if _digest(workbook) != workbook_sha256:
        raise ValueError("source_changed_during_screen")
    return {
        "schema_version": "empd2-nfi-spatial-feasibility.v2",
        "evidence_role": "candidate_spatial_leads_only",
        "source_hashes": {
            "nfi_workbook": workbook_sha256,
            "nfi_schema": schema_sha256,
            "nfi_eligibility": eligibility_sha256,
            "empd2_screen": pollen_sha256,
            "empd2_source": pollen["source_sha256"],
        },
        "nfi_plot_year_rows": len(rows),
        "nfi_distinct_plots": len({(row[1], row[2]) for row in rows}),
        "swedish_pollen_samples": len(swedish),
        "pollen_invalid_coordinate_count": invalid_pollen_coordinates,
        "thresholds_descriptive_only": {
            str(distance): counts.summary() for distance, counts in thresholds.items()
        },
        "thresholds_mechanical_count_candidates_only": {
            str(distance): counts.summary()
            for distance, counts in count_candidates.items()
        },
        "nearest_nfi_row_by_pollen_sample": nearest,
        "nfi_source_crs": "SWEREF99TM (source ReadMe); EPSG:3006 for candidate transform",
        "distance_method": "unrounded WGS84 inverse geodesic on transformed NFI and source EMPD2 points",
        "worksheet_access": "entire XML streamed; only first six identity/geometry cells selected, no tree measurements displayed or scored",
        "collection_time_comparability": "unresolved_for_all_pollen_samples",
        "independent_vegetation_pair_count": 0,
        "scientific_admission": "candidate_only",
    }


def main() -> None:
    """Write a source-bound feasibility report at a new caller-owned path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--workbook-sha256", required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--schema-sha256", required=True)
    parser.add_argument("--eligibility", type=Path, required=True)
    parser.add_argument("--eligibility-sha256", required=True)
    parser.add_argument("--pollen-screen", type=Path, required=True)
    parser.add_argument("--pollen-screen-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = screen_empd2_nfi_geometry(
        args.workbook,
        args.workbook_sha256,
        args.schema,
        args.schema_sha256,
        args.eligibility,
        args.eligibility_sha256,
        args.pollen_screen,
        args.pollen_screen_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=args.output.parent,
            prefix=f".{args.output.name}.pending-",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, args.output)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    print(
        json.dumps(
            {"thresholds": report["thresholds_descriptive_only"]}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
