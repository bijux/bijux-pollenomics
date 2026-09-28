"""Check the author's model inputs against the harmonized Swedish count mass."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.landclim_parameter_binding import publish

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE = Path(
    os.environ.get(
        "POLLENOMICS_LANDCLIM_AUTHOR_SOURCE_ROOT",
        REPOSITORY.parent / "bijux-pollenomics-data/landclim/author-reference",
    )
)
GOVERNED = REPOSITORY / "docs/report/source-relations/neotoma/author-parameter-binding"


def test_author_parameter_profile_matches_harmonized_swedish_counts(
    tmp_path: Path,
) -> None:
    if not SOURCE.exists():
        pytest.skip("External LandClim author source is unavailable")
    report = publish(REPOSITORY, SOURCE, tmp_path)
    assert (tmp_path / "report.json").read_bytes() == (
        GOVERNED / "report.json"
    ).read_bytes()
    assert json.loads((tmp_path / "report.json").read_text()) == report
    assert report["author_target_count"] == 31
    assert report["targets_with_swedish_native_nisp"] == 24
    assert report["swedish_author_assigned_nisp"] == 169013
    assert report["swedish_all_native_nisp"] == 187002
    assert report["covariance_nonzero_offdiagonal_cells"] == 0
    assert report["lra_admitted_samples"] == 0
    parameters = {row["author_target"]: row for row in report["parameters"]}
    assert parameters["Alnus glutinosa"] == {
        "author_target": "Alnus glutinosa",
        "alpha_source_text": "13.562",
        "fall_speed_source_text": "0.021",
        "alpha_variance_source_text": "0.085936336",
        "swedish_native_nisp_assigned": 22341,
    }
    assert parameters["Quercus deciduous"]["swedish_native_nisp_assigned"] == 9500
    assert parameters["Poaceae"]["alpha_source_text"] == "1"
