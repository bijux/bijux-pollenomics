"""The native Swedish pollen denominator stays visible beside literal PPE leads."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from bijux_pollenomics_dev.source_completion.neotoma_parameter_mass import publish

REPOSITORY = Path(__file__).resolve().parents[4]


def test_parameter_name_mass_closes_real_pollen_bins_without_lra_admission(
    tmp_path: Path,
) -> None:
    report = publish(REPOSITORY, tmp_path)
    rows = list(csv.DictReader((tmp_path / "bins.csv").open(newline="")))
    assert len(rows) == 39
    assert report["candidate_parameter_name_count"] == 20
    assert report["lra_admitted_samples"] == 0
    assert report["scientific_admission_allowed"] is False
    assert all(
        int(row["all_native_nisp"])
        == int(row["literal_parameter_name_nisp"]) + int(row["unmatched_name_nisp"])
        and row["lra_admitted"] == "False"
        for row in rows
    )
    site_rows = report["sites"]
    assert isinstance(site_rows, list)
    assert all(isinstance(row, dict) for row in site_rows)
    sites = {row["site"]: row for row in site_rows}
    assert sites["Abborrtjärnen"]["literal_parameter_name_nisp"] == 81970
    assert sites["Bussjösjön"]["literal_parameter_name_nisp"] == 10752
    assert sites["Bökesjön"]["literal_parameter_name_nisp"] == 14512
    assert sites["Bökesjön"]["leading_unmatched_native_names"][0] == {
        "name": "Corylus",
        "count": 9596,
    }
    governed = REPOSITORY / "docs/report/source-relations/neotoma/parameter-coverage"
    assert (tmp_path / "bins.csv").read_bytes() == (governed / "bins.csv").read_bytes()
    assert json.loads((tmp_path / "report.json").read_text()) == json.loads(
        (governed / "report.json").read_text()
    )
