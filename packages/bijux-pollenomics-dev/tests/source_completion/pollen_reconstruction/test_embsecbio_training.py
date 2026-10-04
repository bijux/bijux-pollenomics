"""Exercise sample-statistic and native training-member refusal contracts."""

from __future__ import annotations

import math

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_biome.training import (
    member_labels,
    statistics,
    within,
)


def test_sample_sd_uses_n_minus_one() -> None:
    assert statistics([1.0, 3.0, 5.0]) == (3.0, 2.0)
    mean, sd = statistics([0.0, 1.0, 1.0])
    assert mean == pytest.approx(2.0 / 3.0)
    assert sd == pytest.approx(math.sqrt(1.0 / 3.0))


def test_zero_variation_and_single_sample_are_distinct() -> None:
    assert statistics([0.0, 0.0]) == (0.0, 0.0)
    with pytest.raises(ValueError, match="at least two"):
        statistics([0.0])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_training_observation_refused(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        statistics([0.0, value])


def test_native_training_ids_must_be_unique(tmp_path) -> None:
    (tmp_path / "members.csv").write_text("ID_SAMPLE,Dominant\n1,CENF\n1,TEDE\n")
    with pytest.raises(ValueError, match="duplicate"):
        member_labels(tmp_path, "members.csv")


def test_native_training_class_must_be_supported(tmp_path) -> None:
    (tmp_path / "members.csv").write_text("ID_SAMPLE,Dominant\n1,unknown\n")
    with pytest.raises(ValueError, match="unsupported"):
        member_labels(tmp_path, "members.csv")


def test_small_publication_rounding_does_not_hide_a_model_difference() -> None:
    assert within(1.0 + 1e-13, 1.0)
    assert not within(1.0 + 1e-6, 1.0)
