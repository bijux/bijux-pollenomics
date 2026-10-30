"""Numerical comparisons preserve labels, masks, rounding and real refusals."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_dev.native_backend.love_comparison import comparison
from bijux_pollenomics_dev.native_backend.love_comparison.inputs import NAMES, frame

from .test_inputs import shared_inputs


def products(directory: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shared_inputs(directory / "input", monkeypatch)
    for name in NAMES:
        exact = frame(directory / "input" / f"{name}-hex.csv")
        (directory / f"r-input-{name}-hex.txt").write_text(
            "\n".join(exact.to_numpy().ravel(order="F"))
        )
        if name != "candidates":
            (directory / f"r-input-{name}.csv").write_bytes(
                (directory / "input" / f"{name}.csv").read_bytes()
            )
    for name, shape in comparison.SHAPES.items():
        values = np.ones(shape)
        if name != "k":
            values[:6] = np.nan
        table = pd.DataFrame(values)
        table.to_csv(directory / f"r-{name}.csv", index=False, na_rep="NaN")
        table.to_csv(directory / f"python-{name}.csv", index=False)
    trace = pd.DataFrame({"best_index": [1] * 8, "nfev": [32] * 8})
    for engine in ("r", "python"):
        trace.to_csv(directory / f"{engine}-trace.csv", index=False)


def test_source_undefined_cells_and_exact_first_candidate_are_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    products(tmp_path, monkeypatch)
    result = comparison.compare(tmp_path, tmp_path / "input")
    assert result["passed"]
    assert result["selected_indices_one_based"] == [1] * 8
    assert result["products"]["cover"]["missing_pairs"] == 60
    assert result["products"]["objective"]["finite_pairs"] == 8


@pytest.mark.parametrize(
    "kind", ["label", "mask", "shape", "candidate", "budget", "raw_hex"]
)
def test_structural_or_input_mismatch_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    products(tmp_path, monkeypatch)
    path = tmp_path / "r-cover.csv"
    if kind == "label":
        path.write_text(path.read_text().replace("0,1,2", "foreign,1,2", 1))
    elif kind == "mask":
        path.write_text(path.read_text().replace("NaN", "0", 1))
    elif kind == "shape":
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
    elif kind in {"candidate", "budget"}:
        path = tmp_path / "r-trace.csv"
        path.write_text(
            path.read_text().replace(
                "1,32", "2,32" if kind == "candidate" else "1,31", 1
            )
        )
    else:
        (tmp_path / "r-input-local-hex.txt").write_text("0x0.0p+0\n0x1.0p+0\n")
    with pytest.raises(ValueError, match="differ"):
        comparison.compare(tmp_path, tmp_path / "input")


def test_numerical_failure_remains_false_at_original_tolerance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    products(tmp_path, monkeypatch)
    path = tmp_path / "r-k.csv"
    path.write_text(path.read_text().replace("1.0", "1.01", 1))
    assert comparison.compare(tmp_path, tmp_path / "input")["passed"] is False


@pytest.mark.parametrize(
    "token", ["NA", "nan", "Inf", "-Inf", " 1", "1 ", "1_000", "1e9999", ""]
)
def test_native_writer_lexical_refusals_are_not_missing_or_zero(
    tmp_path: Path, token: str
) -> None:
    path = tmp_path / "values.csv"
    path.write_text("A,B\n" + token + ",1\n")
    with pytest.raises((ValueError, TypeError)):
        comparison.numeric(path)


def test_decimal_conversion_is_correctly_rounded_not_pandas_approximation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "values.csv"
    path.write_text("A\n3.1415926535897931\n")
    assert comparison.numeric(path)[1][0, 0] == float("3.1415926535897931")
