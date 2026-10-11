"""Keep published PPE comparison separate from author source substitution."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_dev.source_completion.landclim_parameter_correspondence import (
    publish,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / "docs/report/source-relations/neotoma/parameter-correspondence"


def test_all_author_parameters_pair_with_published_rows_and_keep_sd_exceptions(
    tmp_path: Path,
) -> None:
    report = publish(REPOSITORY, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
    assert json.loads((tmp_path / "report.json").read_text()) == report
    assert report["parameter_count"] == 31
    assert report["exact_fsp_count"] == 31
    assert report["alpha_within_display_count"] == 31
    assert report["sd_within_display_count"] == 28
    assert report["lra_admitted_samples"] == 0
    assert {row["author_target"] for row in report["sd_exceptions"]} == {
        "Cerealia-t",
        "Cyperaceae",
        "Phillyrea",
    }
    rows = {row["author_target"]: row for row in report["rows"]}
    assert rows["Picea"]["published_parameter_name"] == "Picea abies"
    assert rows["Quercus deciduous"]["published_parameter_name"] == (
        "Quercus deciduous t."
    )
    assert rows["Alnus glutinosa"]["published_parameter_name"] == ("Alnus glutinosa")
