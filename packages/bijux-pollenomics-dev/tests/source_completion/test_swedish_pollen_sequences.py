"""Verify the published native sequence against its source and consumer tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from bijux_pollenomics_dev.source_completion.swedish_pollen_sequences import build


REPOSITORY = Path(__file__).resolve().parents[4]
PUBLISHED = REPOSITORY / "docs/report/pollen-reconstruction/swedish-native-sequences"
DATA = REPOSITORY / "data/neotoma/raw/neotoma_pollen_dataset_downloads"


def test_published_sequence_replays_and_reconciles_with_scored_cohort() -> None:
    (REPOSITORY / "artifacts").mkdir(exist_ok=True)
    with TemporaryDirectory(dir=REPOSITORY / "artifacts") as directory:
        generated = Path(directory) / "sequences"
        manifest = build(DATA, generated)
        for name, digest in manifest["files_sha256"].items():
            assert (generated / name).read_bytes() == (PUBLISHED / name).read_bytes(), (
                digest
            )
        assert (generated / "manifest.json").read_bytes() == (
            PUBLISHED / "manifest.json"
        ).read_bytes()
        observations = json.loads((generated / "observations.json").read_text())
        samples = json.loads((generated / "samples.json").read_text())
        controls = json.loads((generated / "chronology-controls.json").read_text())
        map_summary = json.loads((generated / "map-summary.geojson").read_text())
    with (
        REPOSITORY
        / "docs/report/pollen-reconstruction/swedish-direct-pollen/cohort.csv"
    ).open() as stream:
        cohort = {row["neotoma_dataset_id"]: row for row in csv.DictReader(stream)}
    assert len(samples) == 228
    assert len(controls) == 46
    assert len(observations) == manifest["observation_count"] == 5464
    for feature in map_summary["features"]:
        props = feature["properties"]
        dataset_id = props["dataset_id"]
        expected = cohort[dataset_id]
        actual = [row for row in observations if row["dataset_id"] == dataset_id]
        assert props["sample_count"] == int(expected["sample_count"])
        assert props["reported_pollen_nisp"] == int(expected["native_nisp_count"])
        assert sum(row["count"] for row in actual) == props["reported_pollen_nisp"]
        assert all(
            row["source_locator"].startswith(
                expected["source_file"].split("/")[-1] + "#"
            )
            for row in actual
        )
    by_sample = {row["sample_id"]: row for row in samples}
    assert all(
        row["denominator"] == by_sample[row["sample_id"]]["reported_nisp_denominator"]
        and abs(
            row["percent_of_reported_pollen_nisp"]
            - 100 * row["count"] / row["denominator"]
        )
        < 1e-12
        for row in observations
    )
