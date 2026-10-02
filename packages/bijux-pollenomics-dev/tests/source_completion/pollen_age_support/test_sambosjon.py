"""Check matched age support, refusals and immutable input guards."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support import sambosjon


def example() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    support = {
        "retained": {"bin_id": 1, "status": "contained"},
        "crossing": {"bin_id": 1, "status": "crosses_boundary"},
        "empty": {"bin_id": 2, "status": "crosses_boundary"},
    }
    source = {}
    for sid, taxon in (
        ("retained", "Alnus"),
        ("crossing", "Betula"),
        ("empty", "Alnus"),
    ):
        counts = dict.fromkeys(sambosjon.TAXA, 0)
        counts[taxon] = 100
        source[sid] = {"native_nisp": 120, "counts": counts, "direct_count_rows": 2}
    fractions = dict.fromkeys(sambosjon.TAXA, 0.0)
    fractions["Alnus"] = 1.0
    predictions = {
        "predictions": [
            {"bin_id": b, "method": m, "fractions": fractions}
            for b in (1, 2)
            for m in sambosjon.BASELINE_METHODS
        ]
    }
    return support, source, predictions


def test_compares_identical_predictions_on_matched_bins_and_preserves_mass() -> None:
    support, source, predictions = example()
    samples, coverage, scores = sambosjon._aggregate(support, source, predictions)
    assert sum(r["native_nisp"] for r in samples) == 360
    assert sum(r["closed_nisp"] for r in samples) == 300
    assert sum(r["outside_axis_nisp"] for r in samples) == 60
    assert coverage[0]["contained_samples"] == 1
    assert coverage[0]["boundary_crossing_samples"] == 1
    for row in scores[:3]:
        assert row["mae_fraction"] == 0.0
        assert row["parent_same_bin_mae_fraction"] == 1 / 16
        assert row["hellinger_distance"] == 0.0
    assert coverage[1]["status"] == "refused_no_contained_samples"
    for row in scores[3:]:
        assert row["status"] == "refused_no_contained_samples"
        assert row["mae_fraction"] is None
        assert row["hellinger_distance"] is None


@pytest.mark.parametrize("case", ["missing", "zero"])
def test_contained_bin_refuses_unusable_counts(case: str) -> None:
    support, source, predictions = example()
    if case == "missing":
        source["retained"]["direct_count_rows"] = 0
    else:
        source["retained"]["counts"] = dict.fromkeys(sambosjon.TAXA, 0)
    _, coverage, scores = sambosjon._aggregate(support, source, predictions)
    expected = (
        "refused_missing_target_counts"
        if case == "missing"
        else "refused_zero_closed_axis"
    )
    assert coverage[0]["status"] == expected
    assert all(row["mae_fraction"] is None for row in scores[:3])


def test_refuses_duplicate_predictions_and_mismatched_sample_support() -> None:
    support, source, predictions = example()
    predictions["predictions"].append(predictions["predictions"][0])
    with pytest.raises(ValueError, match="duplicate frozen prediction"):
        sambosjon._aggregate(support, source, predictions)
    source.pop("retained")
    with pytest.raises(ValueError, match="sample count and age support differ"):
        sambosjon._aggregate(support, source, predictions)


def test_input_drift_is_refused_before_target_counts(tmp_path: Path) -> None:
    study = tmp_path / sambosjon.STUDY
    study.mkdir(parents=True)
    (study / "protocol.json").write_text("{}")
    with pytest.raises(ValueError, match="sensitivity input changed: protocol.json"):
        sambosjon._verified_inputs(tmp_path)
