"""NFI geometry leads remain separate from temporal and vegetation admission."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from pyproj import Transformer
import pytest

from bijux_pollenomics_dev.source_completion.empd2_nfi import (
    main,
    screen_empd2_nfi_geometry,
)

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _json(path: Path, value: object) -> str:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, str, Path, str, Path, str, Path, str]:
    to_nfi = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    positions = [to_nfi.transform(18.0, 60.0), to_nfi.transform(20.0, 60.0)]
    headers = ("Year", "TractID", "PlotID", "Inventory_Date", "Easting", "Northing")
    strings = list(headers) + [
        "tract-1",
        "tract-2",
        "plot-1",
        "2020-08-01",
        "secret final vegetation",
    ]
    shared = (
        f'<sst xmlns="{_NS}">'
        + "".join(f"<si><t>{value}</t></si>" for value in strings)
        + "</sst>"
    )

    def row(index: int, values: tuple[str, ...]) -> str:
        cells = []
        for column, value in zip("ABCDEF", values, strict=True):
            if value in strings:
                cells.append(
                    f'<c r="{column}{index}" t="s"><v>{strings.index(value)}</v></c>'
                )
            else:
                cells.append(f'<c r="{column}{index}"><v>{value}</v></c>')
        cells.append(f'<c r="G{index}" t="s"><v>10</v></c>')
        return f'<row r="{index}">' + "".join(cells) + "</row>"

    data = [
        headers,
        ("2020", "tract-1", "plot-1", "2020-08-01", *map(str, positions[0])),
        ("2020", "tract-2", "plot-1", "2020-08-01", *map(str, positions[1])),
    ]
    worksheet = (
        f'<worksheet xmlns="{_NS}"><sheetData>'
        + "".join(row(index, values) for index, values in enumerate(data, 1))
        + "</sheetData></worksheet>"
    )
    workbook = tmp_path / "nfi.xlsx"
    with ZipFile(workbook, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet2.xml", worksheet)
    workbook_hash = sha256(workbook.read_bytes()).hexdigest()
    schema = tmp_path / "schema.json"
    schema_hash = _json(
        schema,
        {
            "source_sha256": workbook_hash,
            "selected_readme_descriptions": {
                "Easting": "Meters. Sweref99TM",
                "Northing": "Meters. Sweref99TM",
            },
        },
    )
    eligibility = tmp_path / "eligibility.json"
    eligibility_hash = _json(
        eligibility,
        {
            "source_sha256": workbook_hash,
            "schema_report_sha256": schema_hash,
            "data_rows_counted": 2,
            "distinct_tract_plot_keys": 2,
        },
    )
    pollen = tmp_path / "pollen.json"
    pollen_hash = _json(
        pollen,
        {
            "schema_version": "empd2-nordic-candidate-screen.v1",
            "scientific_admission": "candidate_only",
            "source_sha256": "a" * 64,
            "country_counts": {"Sweden": {"metadata_samples": 1}},
            "samples": [
                {
                    "country": "Sweden",
                    "source_sample_name": "source-pollen",
                    "source_longitude": 18.0,
                    "source_latitude": 60.0,
                    "source_agebp": "NULL",
                    "source_ageuncertainty": "A",
                    "mechanical_count_candidate": True,
                    "review_reason_codes": [],
                }
            ],
        },
    )
    return (
        workbook,
        workbook_hash,
        schema,
        schema_hash,
        eligibility,
        eligibility_hash,
        pollen,
        pollen_hash,
    )


def test_exact_point_is_only_spatial_lead_with_unresolved_time(tmp_path: Path) -> None:
    report = screen_empd2_nfi_geometry(*_fixture(tmp_path))
    assert report["nfi_plot_year_rows"] == 2
    assert report["swedish_pollen_samples"] == 1
    assert report["thresholds_descriptive_only"]["1000"] == {
        "candidate_plot_year_sample_pairs": 1,
        "pollen_samples": 1,
        "nfi_plot_years": 1,
        "nfi_plots": 1,
    }
    assert (
        report["thresholds_mechanical_count_candidates_only"]["1000"]
        == (report["thresholds_descriptive_only"]["1000"])
    )
    lead = report["nearest_nfi_row_by_pollen_sample"][0]
    assert lead["distance_m_wgs84"] < 0.001
    assert lead["nearest_row_selection"] == (
        "distance_only; NFI year is not temporally matched"
    )
    assert lead["time_support"] == "unresolved_collection_time"
    assert report["independent_vegetation_pair_count"] == 0
    assert report["scientific_admission"] == "candidate_only"
    assert "secret" not in json.dumps(report)


def test_input_change_refuses_candidate_claim(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    pollen = fixture[6]
    pollen.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        screen_empd2_nfi_geometry(*fixture)


def test_count_refusal_remains_in_spatial_total_but_not_candidate_subset(
    tmp_path: Path,
) -> None:
    fixture = list(_fixture(tmp_path))
    pollen = fixture[6]
    value = json.loads(pollen.read_text(encoding="utf-8"))
    refused = dict(value["samples"][0])
    refused["source_sample_name"] = "fractional-count"
    refused["mechanical_count_candidate"] = False
    refused["review_reason_codes"] = ["invalid_count_value"]
    value["samples"].append(refused)
    value["country_counts"]["Sweden"]["metadata_samples"] = 2
    fixture[7] = _json(pollen, value)
    report = screen_empd2_nfi_geometry(*fixture)
    assert report["thresholds_descriptive_only"]["1000"]["pollen_samples"] == 2
    assert (
        report["thresholds_mechanical_count_candidates_only"]["1000"]["pollen_samples"]
        == 1
    )
    assert report["independent_vegetation_pair_count"] == 0


def test_unproven_coordinate_system_refuses_distance(tmp_path: Path) -> None:
    fixture = list(_fixture(tmp_path))
    schema = fixture[2]
    value = json.loads(schema.read_text(encoding="utf-8"))
    value["selected_readme_descriptions"]["Easting"] = "unknown"
    fixture[3] = _json(schema, value)
    eligibility = fixture[4]
    value = json.loads(eligibility.read_text(encoding="utf-8"))
    value["schema_report_sha256"] = fixture[3]
    fixture[5] = _json(eligibility, value)
    with pytest.raises(ValueError, match="source_identity_or_posture_mismatch"):
        screen_empd2_nfi_geometry(*fixture)


def test_cli_publishes_once_without_replacing_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _fixture(tmp_path)
    output = tmp_path / "report.json"
    options = [
        "--workbook",
        str(source[0]),
        "--workbook-sha256",
        source[1],
        "--schema",
        str(source[2]),
        "--schema-sha256",
        source[3],
        "--eligibility",
        str(source[4]),
        "--eligibility-sha256",
        source[5],
        "--pollen-screen",
        str(source[6]),
        "--pollen-screen-sha256",
        source[7],
        "--output",
        str(output),
    ]
    monkeypatch.setattr(sys, "argv", ["empd2-nfi", *options])
    main()
    first = output.read_bytes()
    with pytest.raises(FileExistsError):
        main()
    assert output.read_bytes() == first
    assert not tuple(tmp_path.glob(".report.json.pending-*"))
