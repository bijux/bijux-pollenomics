"""Pure type-sensitive retained-metadata predicates; no host tool access."""

from __future__ import annotations

from pathlib import Path

GIT = Path("/Library/Developer/CommandLineTools/usr/bin/git")


def require(value: object, message: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ValueError(message)


def strict_equal(left: object, right: object) -> bool:
    """Compare nested source values while preserving types and nulls."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return list(left) == list(right) and all(
            strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            (strict_equal(a, b) for a, b in zip(left, right, strict=True))
        )
    return left == right
