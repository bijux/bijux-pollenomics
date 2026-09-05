"""Scientific chronology invariants for duplicate AADR sample rows."""

from collections.abc import Callable

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.species.homo_sapiens import (
    merge_duplicate_samples,
    merge_sample_time_interval,
)


def test_duplicate_merge_preserves_null_chronology(
    human_sample: Callable[..., AdnaSampleRecord],
) -> None:
    left = human_sample(dataset="1240k")
    right = human_sample(dataset="ho")

    merged = merge_duplicate_samples(left, right)

    assert merge_sample_time_interval(left, right) is None
    assert merged.time_start_bp is None
    assert merged.time_end_bp is None
    assert merged.time_mean_bp is None
    assert merged.time_label == ""
    assert merged.datasets == ("1240k", "ho")


def test_duplicate_merge_preserves_zero_and_younger_older_bp_order(
    human_sample: Callable[..., AdnaSampleRecord],
) -> None:
    left = human_sample(dataset="1240k", younger_bp=0, older_bp=0)
    right = human_sample(dataset="ho", younger_bp=100, older_bp=300)

    merged = merge_duplicate_samples(left, right)

    assert (merged.time_start_bp, merged.time_end_bp) == (0, 300)
    assert merged.time_mean_bp == 150
    assert merged.time_label == "0-300 BP"


def test_duplicate_merge_prefers_source_mean_and_label(
    human_sample: Callable[..., AdnaSampleRecord],
) -> None:
    left = human_sample(
        dataset="1240k",
        younger_bp=200,
        older_bp=400,
        mean_bp=275,
        label="source chronology",
    )
    right = human_sample(dataset="ho", younger_bp=100, older_bp=500, mean_bp=300)

    merged = merge_duplicate_samples(left, right)

    assert (merged.time_start_bp, merged.time_end_bp) == (100, 500)
    assert merged.time_mean_bp == 275
    assert merged.time_label == "source chronology"
