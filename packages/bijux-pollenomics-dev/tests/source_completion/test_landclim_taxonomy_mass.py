"""Check the source-bound LandClim author taxonomy screen."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import (
    _lookup,
    publish,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE = Path(
    os.environ.get(
        "POLLENOMICS_LANDCLIM_AUTHOR_SOURCE_ROOT",
        REPOSITORY.parent / "bijux-pollenomics-data/landclim/author-reference",
    )
)
GOVERNED = REPOSITORY / "docs/report/source-relations/neotoma/author-taxonomy-mass"


def test_actual_author_lookup_closes_swedish_native_bins(tmp_path: Path) -> None:
    if not SOURCE.exists():
        pytest.skip("External LandClim author source is unavailable")
    replay = tmp_path / "replay"
    report = publish(REPOSITORY, SOURCE, replay)
    for filename in ("bins.csv", "report.json"):
        assert (replay / filename).read_bytes() == (GOVERNED / filename).read_bytes()
    assert report["source_lookup_rows"] == 10788
    assert report["source_lookup_nonexcluded_targets"] == 31
    assert report["lra_admitted_samples"] == 0
    assert report["scientific_admission_allowed"] is False
    with (replay / "bins.csv").open(encoding="utf-8", newline="") as handle:
        bins = list(csv.DictReader(handle))
    assert len(bins) == 39
    for row in bins:
        assert int(row["all_native_nisp"]) == sum(
            int(row[key])
            for key in ("author_assigned_nisp", "author_excluded_nisp", "unmapped_nisp")
        )
    by_dataset = {site["dataset_id"]: site for site in report["sites"]}
    assert by_dataset["19913"]["author_target_counts"]["Alnus glutinosa"] == 3904
    assert by_dataset["53995"]["author_target_counts"]["Corylus avellana"] == 8391
    assert by_dataset["54001"]["author_target_counts"]["Quercus deciduous"] == 6192
    assert by_dataset["53995"]["unmapped_nisp"] == 6258
    assert by_dataset["53995"]["size_variant_candidate_nisp"] == 6254
    assert by_dataset["53995"]["size_variant_candidate_targets"] == {
        "Cerealia-t": 158,
        "Poaceae": 6096,
    }
    assert by_dataset["53995"]["assigned_plus_size_candidate_fraction"] == 0.835589
    assert all(
        site["size_variant_candidate_nisp"] == 0
        for dataset, site in by_dataset.items()
        if dataset != "53995"
    )
    assert json.loads((replay / "report.json").read_text()) == report


def test_changed_author_lookup_refused(tmp_path: Path) -> None:
    if not SOURCE.exists():
        pytest.skip("External LandClim author source is unavailable")
    source = SOURCE / "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"
    changed = tmp_path / "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"
    changed.parent.mkdir(parents=True)
    changed.write_bytes(
        source.read_bytes().replace(b"Alnus glutinosa", b"Alnus unknown", 1)
    )
    with pytest.raises(ValueError, match="identity changed"):
        _lookup(changed)
