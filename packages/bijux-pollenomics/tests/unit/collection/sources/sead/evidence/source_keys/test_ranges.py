"""Tests for lossless SEAD primary-key range encoding."""

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.source_keys import (
    decode_positive_integer_ranges,
    encode_positive_integer_ranges,
)


@pytest.mark.parametrize(
    ("keys", "ranges"),
    (
        ([], []),
        ([7], [[7, 7]]),
        ([9, 2, 3, 4, 11], [[2, 4], [9, 9], [11, 11]]),
    ),
)
def test_positive_integer_ranges_round_trip(
    keys: list[int], ranges: list[list[int]]
) -> None:
    assert encode_positive_integer_ranges(keys) == ranges
    assert decode_positive_integer_ranges(ranges) == sorted(keys)


@pytest.mark.parametrize("key", [True, False, 0, -1, "1", None])
def test_range_encoder_rejects_non_positive_integer_keys(key: object) -> None:
    with pytest.raises(ValueError, match="positive integers"):
        encode_positive_integer_ranges([key])


def test_range_encoder_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="unique"):
        encode_positive_integer_ranges([1, 1])


@pytest.mark.parametrize(
    "ranges",
    (
        [[2, 1]],
        [[0, 1]],
        [[1, 2], [2, 3]],
        [[1, 2], [3, 4]],
        [[5, 5], [3, 3]],
    ),
)
def test_range_decoder_rejects_noncanonical_ranges(ranges: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        decode_positive_integer_ranges(ranges)
