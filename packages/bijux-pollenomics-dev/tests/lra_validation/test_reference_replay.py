from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_dev.lra_validation.reference_replay import (
    compare_vectors,
    comparison_outcome,
    normalize_r_numbers,
    replay,
)


def test_r_literal_equivalence_preserves_strings_and_binary64_values() -> None:
    assert normalize_r_numbers('c(0.1,1.0,"taxon1.0")') == normalize_r_numbers(
        'c(0x1.999999999999ap-4,0x1.0000000000000p+0,"taxon1.0")'
    )
    assert normalize_r_numbers('c(0.1,"1.0")') != normalize_r_numbers(
        'c(0.10000000000000002,"1.0")'
    )
    assert normalize_r_numbers('c(1L,"1.0")') != normalize_r_numbers('c(1,"1.0")')


def test_comparison_preserves_nonfinite_positions_and_exact_coordinates() -> None:
    values = np.array([1.0, np.nan, np.inf, -np.inf])
    assert compare_vectors(values, values, rtol=1e-10, atol=1e-10, exact_indices=(0,))[
        "nan_positions"
    ] == [1]
    changed = values.copy()
    changed[0] += 1e-12
    assert (
        comparison_outcome(changed, values, rtol=1e-10, atol=1e-10, exact_indices=(0,))[
            "status"
        ]
        == "failed"
    )
    changed[0], changed[1] = 1.0, 0.0
    assert (
        comparison_outcome(changed, values, rtol=1e-10, atol=1e-10)["status"]
        == "failed"
    )


def test_shapes_strings_and_out_of_range_exact_coordinates_refuse() -> None:
    with pytest.raises(AssertionError, match="dimensions"):
        compare_vectors(np.array([1]), np.array([1, 2]), rtol=0, atol=0)
    with pytest.raises(AssertionError, match="outside"):
        compare_vectors(
            np.array([1]), np.array([1]), rtol=0, atol=0, exact_indices=(1,)
        )
    assert (
        comparison_outcome(np.array(["absent"]), np.array(["present"]), rtol=0, atol=0)[
            "status"
        ]
        == "failed"
    )


def test_certificate_tampering_refuses_before_output(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "certificate.json").write_text("{}\n")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="certificate differs"):
        replay(tmp_path, bundle, output)
    assert not output.exists()
