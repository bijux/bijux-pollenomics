"""Independent native-prefix and closed-polynomial chronology observations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from .sampler_accuracy.independent_native import exact_prefix, polynomial_ages
from .sampler_accuracy.independent_result import verify_result


def test_exact_prefix_preserves_blank_and_unterminated_native_rows(
    tmp_path: Path,
) -> None:
    original, extended = tmp_path / "original.out", tmp_path / "extended.out"
    before = b"\n-52 2 4 .25\n-51 3 5 .30"
    original.write_bytes(before)
    extended.write_bytes(before + b"\n-50 4 6 .35")
    digest = hashlib.sha256(before).hexdigest()
    assert exact_prefix(original, extended, digest) == len(before)
    extended.write_bytes(before.replace(b"-52", b"-52.0") + b"\n-50 4 6 .35")
    with pytest.raises(ValueError, match="exact prefix"):
        exact_prefix(original, extended, digest)


@pytest.mark.parametrize("suffix", [b"", b"\n", b"\n \n", b"0 1 2"])
def test_prefix_observer_requires_an_added_row(tmp_path: Path, suffix: bytes) -> None:
    original, extended = tmp_path / "original.out", tmp_path / "extended.out"
    original.write_bytes(b"\n1 2 3")
    extended.write_bytes(original.read_bytes() + suffix)
    with pytest.raises(ValueError):
        exact_prefix(
            original, extended, hashlib.sha256(original.read_bytes()).hexdigest()
        )


def test_closed_polynomial_matches_an_analytical_three_section_example() -> None:
    # With w=1/2 and innovations (2,4,8), physical rates are (4,6,8).
    states = np.array([[-52, 2, 4, 8, 0.5], [10, 1, 1, 1, 0.25]], dtype=float)
    depths = np.array([648, 650.5, 653, 655.5, 658, 663], dtype=float)
    result = polynomial_ages(states, depths)
    np.testing.assert_allclose(
        result[0], [-52, -42, -32, -17, -2, 38], rtol=0, atol=1e-14
    )
    np.testing.assert_allclose(result[1], 10 + depths - 648, rtol=0, atol=1e-14)


@pytest.mark.parametrize("memory", [0.001, 0.2, 0.9, 0.999])
def test_constant_innovations_give_constant_rates_across_block_boundaries(
    memory: float,
) -> None:
    states = np.tile(np.array([-52, 7, 7, 7, memory]), (513, 1))
    depths = np.array([648, 649, 653, 660, 663], dtype=float)
    expected = np.tile(-52 + 7 * (depths - 648), (len(states), 1))
    np.testing.assert_allclose(
        polynomial_ages(states, depths), expected, rtol=0, atol=3e-14
    )


@pytest.mark.parametrize("mutation", ["memory", "innovation", "depth", "nonfinite"])
def test_independent_polynomial_refuses_unsupported_saved_states(mutation: str) -> None:
    states, depths = np.array([[-52, 2, 4, 0.5]], dtype=float), np.array([648.0])
    if mutation == "memory":
        states[0, -1] = 1
    elif mutation == "innovation":
        states[0, 1] = 0
    elif mutation == "depth":
        depths[0] = 659
    else:
        states[0, 0] = np.nan
    with pytest.raises(ValueError, match="support"):
        polynomial_ages(states, depths)


def main() -> int:
    """Observe a saved result without executing a native fit or prediction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Independent result destination already exists")
    result = verify_result(args.repository.resolve(), args.directory.resolve())
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
