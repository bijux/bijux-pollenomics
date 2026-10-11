"""Check the retained LandClim metadata leads against the native sequence sites."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from bijux_pollenomics_dev.source_completion.swedish_pollen_overlap import build

REPOSITORY = Path(__file__).resolve().parents[4]
SEQUENCES = REPOSITORY / "docs/report/pollen-reconstruction/swedish-native-sequences"


def test_overlap_replays_and_refuses_independent_corroboration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPOSITORY)
    with TemporaryDirectory(dir=REPOSITORY / "artifacts") as directory:
        output = Path(directory) / "overlap"
        result = build(
            Path(
                "docs/report/pollen-reconstruction/swedish-native-sequences/sites.json"
            ),
            Path("data/landclim/normalized/nordic_pollen_site_sequences.csv"),
            output,
        )
        assert (output / "report.json").read_bytes() == (
            SEQUENCES / "source-overlap.json"
        ).read_bytes()
    assert result["neotoma_site_count"] == 3
    assert result["landclim_site_metadata_lead_count"] == 8
    assert {row["neotoma_dataset_id"] for row in result["matches"]} == {
        "19913",
        "53995",
        "54001",
    }
    assert all(row["point_distance_m"] < 0.5 for row in result["matches"])
    assert result["independent_corroboration_admitted"] is False
    assert result["same_core_or_sample_identity_admitted"] is False
