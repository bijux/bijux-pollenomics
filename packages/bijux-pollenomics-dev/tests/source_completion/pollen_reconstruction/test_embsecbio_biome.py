"""Independent numerical and source-refusal contracts for fixed biome reconstruction."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.numerical import (
    ORDER,
    evaluate,
    matrix,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.source import (
    keyed,
    pollen,
)


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="latin1", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_row(**changes: str) -> dict:
    return {
        "entity_name": "opaque\xe9",
        "ID_SAMPLE": "1",
        "latitude": "60",
        "longitude": "20",
        "taxon_name": "A",
        "taxon_percent": "40",
        **changes,
    }


def test_two_taxon_scalar_equation_and_literal_percentages() -> None:
    means = {b: [10.0, 20.0] for b in ORDER}
    sd = {b: [1.5, 0.0] for b in ORDER}
    distance, score, winner = evaluate([14.0, 23.0], means, sd)
    assert distance["TUND"] == pytest.approx(math.sqrt(40))
    assert score["TUND"] == pytest.approx(math.exp(-math.sqrt(40) / 100))
    assert winner == "TUND"
    assert sum(score.values()) > 1
    assert evaluate([0, 0], means, sd)[0]["TUND"] != distance["TUND"]


@pytest.mark.parametrize("bad", [-1.0, math.inf, math.nan])
def test_saved_negative_or_nonfinite_sd_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match="sample SD"):
        evaluate([1], {b: [0] for b in ORDER}, {b: [bad] for b in ORDER})


def test_source_class_tie_order_and_taxon_dimensions() -> None:
    distance, _, winner = evaluate(
        [2], {b: [2] for b in ORDER}, {b: [0] for b in ORDER}
    )
    assert winner == "TUND" and all(v == 0 for v in distance.values())
    with pytest.raises(ValueError, match="dimensions"):
        evaluate([1, 2], {b: [0] for b in ORDER}, {b: [1] for b in ORDER})


def test_asymmetric_matrix_keeps_reference_rows_prediction_columns() -> None:
    rows = [
        {"dominant": "TEDE", "subdominant": "DESE", "prediction": "DESE"},
        {"dominant": "TEDE", "subdominant": "NA", "prediction": "DESE"},
        {"dominant": "DESE", "subdominant": "GRAM", "prediction": "GRAM"},
    ]
    assert matrix(rows, "Dominant") == {("TEDE", "DESE"): 2, ("DESE", "GRAM"): 1}
    assert matrix(rows, "Composit") == {
        ("DESE", "DESE"): 1,
        ("TEDE", "DESE"): 1,
        ("GRAM", "GRAM"): 1,
    }
    assert matrix(rows, "Subdominant") == {("DESE", "DESE"): 1, ("GRAM", "GRAM"): 1}


def test_opaque_name_transport_and_literal_percentage_sum(tmp_path: Path) -> None:
    write(tmp_path / "Modern_pollen_perc_emb_smpds.csv", [source_row()])
    samples, count = pollen(tmp_path, ["A", "B"])
    assert count == 1 and samples["1"]["metadata"]["entity_name"] == "opaque\xe9"
    assert samples["1"]["values"] == {"A": 40.0}


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"taxon_name": "unknown"}, "unsupported positive"),
        ({"taxon_percent": "nan"}, "finite"),
        ({"taxon_percent": "101"}, "[0,100]"),
        ({"ID_SAMPLE": "\xe9"}, "literal ASCII"),
    ],
)
def test_invalid_curated_source_is_refused(
    tmp_path: Path, changes: dict, reason: str
) -> None:
    write(tmp_path / "Modern_pollen_perc_emb_smpds.csv", [source_row(**changes)])
    with pytest.raises(
        ValueError, match=reason.replace("[", r"\[").replace("]", r"\]")
    ):
        pollen(tmp_path, ["A"])


def test_duplicate_pollen_pair_and_inconsistent_sample_metadata(tmp_path: Path) -> None:
    path = tmp_path / "Modern_pollen_perc_emb_smpds.csv"
    write(path, [source_row(), source_row()])
    with pytest.raises(ValueError, match="duplicate native sample/taxon"):
        pollen(tmp_path, ["A"])
    write(path, [source_row(), source_row(taxon_name="B", longitude="21")])
    with pytest.raises(ValueError, match="metadata is inconsistent"):
        pollen(tmp_path, ["A", "B"])


def test_duplicate_native_reference_key_is_refused(tmp_path: Path) -> None:
    write(tmp_path / "labels.csv", [{"ID_SAMPLE": "1", "Dominant": "DESE"}] * 2)
    with pytest.raises(ValueError, match="duplicate native sample key"):
        keyed(tmp_path, "labels.csv")
