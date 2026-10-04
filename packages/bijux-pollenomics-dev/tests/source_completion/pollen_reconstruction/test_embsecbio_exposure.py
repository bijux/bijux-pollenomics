"""Check exposure proxy priority, axes and explicit reference exclusions."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.exposure import (
    category,
    exposure_product,
    filtered,
    measures,
    partition,
    CATEGORIES,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.publication import (
    run,
)


def test_exposure_priority_preserves_distinct_proxy_causes():
    points = {"train": (1, 2), "same": (1, 2), "name": (3, 4), "clean": (5, 6)}
    names = {"train": "opaque", "same": "other", "name": "opaque", "clean": "clean"}
    scope = {"train"}, {(1, 2)}, {"opaque"}
    assert [category(s, points, names, scope) for s in points] == list(CATEGORIES)


def test_entity_partition_keeps_any_training_member_exposure():
    row = {"sample_ids": ["other", "train"]}
    groups = partition([row], {"other": CATEGORIES[3], "train": CATEGORIES[0]})
    assert groups[CATEGORIES[0]] == [row]
    assert groups[CATEGORIES[3]] == []


def test_reference_rows_control_balanced_agreement():
    rows = [
        {"dominant": "TEDE", "subdominant": "", "prediction": "TEDE"},
        {"dominant": "TEDE", "subdominant": "", "prediction": "CENF"},
        {"dominant": "TEDE", "subdominant": "CENF", "prediction": "CENF"},
        {"dominant": "CENF", "subdominant": "", "prediction": "CENF"},
    ]
    result = measures(rows)
    assert result["dominant_correct"] == 2
    assert result["composite_correct"] == 3
    assert result["balanced_dominant_agreement_present_classes"] == pytest.approx(2 / 3)
    assert {
        tuple(r[k] for k in ("reference", "prediction", "n"))
        for r in result["reference_row_prediction_column_matrix"]
    } == {("TEDE", "TEDE", 1), ("TEDE", "CENF", 2), ("CENF", "CENF", 1)}


def test_masks_exclude_both_reference_and_prediction():
    rows = [
        {"dominant": "CENF", "prediction": "TEDE"},
        {"dominant": "TEDE", "prediction": "TUND"},
        {"dominant": "TEDE", "prediction": "TEDE"},
    ]
    assert filtered(rows) == [rows[2]]
    assert measures([])["dominant_agreement"] is None


def test_changed_captured_input_is_refused(tmp_path):
    (tmp_path / "members.csv").write_text("changed")
    with pytest.raises(ValueError, match="dependency changed"):
        exposure_product(
            tmp_path,
            {
                "schema_version": "qualified-embsecbio-training-exposure-capture.v1",
                "source_sha256": {"members.csv": "0" * 64},
            },
            {},
            {},
            {},
        )


def test_prediction_population_is_not_inferred_from_proximity(tmp_path):
    with pytest.raises(ValueError, match="population differs"):
        exposure_product(
            tmp_path,
            {
                "schema_version": "qualified-embsecbio-training-exposure-capture.v1",
                "source_sha256": {},
            },
            {"id": {}},
            {},
            {},
        )


def test_scoped_producer_modes_cannot_be_combined():
    with pytest.raises(ValueError, match="mutually exclusive"):
        run(
            Path("absent"),
            Path("absent"),
            Path("absent"),
            Path("absent"),
            training_only=True,
            exposure_only=True,
        )
