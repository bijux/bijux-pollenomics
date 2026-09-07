"""Lossless compact encoding for positive integer source keys."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .serialization import canonical_sha256


def encode_positive_integer_ranges(values: Iterable[object]) -> list[list[int]]:
    """Encode unique positive integers as canonical inclusive ranges."""
    keys: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("SEAD source keys must be positive integers")
        keys.append(value)
    ordered = sorted(keys)
    if len(ordered) != len(set(ordered)):
        raise ValueError("SEAD source keys must be unique within each table")
    ranges: list[list[int]] = []
    for key in ordered:
        if not ranges or key > ranges[-1][1] + 1:
            ranges.append([key, key])
        else:
            ranges[-1][1] = key
    return ranges


def decode_positive_integer_ranges(value: object) -> list[int]:
    """Decode canonical inclusive ranges and reject ambiguous encodings."""
    if not isinstance(value, list):
        raise TypeError("SEAD source-key ranges must be a list")
    result: list[int] = []
    previous_end: int | None = None
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise TypeError("Each SEAD source-key range must contain two integers")
        start, end = item
        if any(
            isinstance(bound, bool) or not isinstance(bound, int) or bound <= 0
            for bound in (start, end)
        ):
            raise ValueError("SEAD source-key range bounds must be positive integers")
        if start > end:
            raise ValueError("SEAD source-key range start must not exceed its end")
        if previous_end is not None and start <= previous_end + 1:
            raise ValueError("SEAD source-key ranges must be ordered and coalesced")
        result.extend(range(start, end + 1))
        previous_end = end
    return result


def positive_integer_key_set_sha256(values: Sequence[int]) -> str:
    """Digest an expanded, numerically ordered source-key set."""
    return canonical_sha256(list(values))


def positive_integer_ranges_sha256(ranges: Sequence[Sequence[int]]) -> str:
    """Digest a canonical inclusive-range representation."""
    return canonical_sha256([list(item) for item in ranges])


__all__ = [
    "decode_positive_integer_ranges",
    "encode_positive_integer_ranges",
    "positive_integer_key_set_sha256",
    "positive_integer_ranges_sha256",
]
