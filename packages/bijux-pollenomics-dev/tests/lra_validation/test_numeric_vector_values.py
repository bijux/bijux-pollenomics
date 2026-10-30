"""R decimal vectors retain binary64 rounding, lexical refusals and coordinates."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_dev.lra_validation.live_reference_comparison import _read_vector
from bijux_pollenomics_dev.lra_validation.reference_replay import (
    compare_vectors,
    numeric_vector_values,
)
from bijux_pollenomics_dev.lra_validation.retained_reference.comparison import (
    read_vector,
)

Reader = Literal["shared", "live", "retained"]


def _read(tmp_path: Path, reader: Reader, tokens: list[str]) -> np.ndarray:
    if reader == "shared":
        return numeric_vector_values(pd.Series(tokens, dtype=str))
    payload = (
        "kind,value\n" + "".join(f"numeric,{token}\n" for token in tokens)
    ).encode()
    path = tmp_path / "vector.csv"
    path.write_bytes(payload)
    if reader == "live":
        return _read_vector(path)
    identity = {
        "files": {
            path.name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
        }
    }
    return read_vector(tmp_path, path.name, identity, numeric=True)


@pytest.mark.parametrize("reader", ["shared", "live", "retained"])
def test_native_r_decimal_tokens_round_to_their_exact_binary64_coordinates(
    tmp_path: Path, reader: Reader
) -> None:
    # Literal tokens from native R C0000/C0001/C0002/C0003 output. Their
    # nearest binary64 values differ from pandas' numeric-conversion results.
    tokens = [
        "0.93264230016746308",
        "0.87039084075965356",
        "0.38632841034797649",
        "0.27939548250707813",
        "0.47900915446742248",
    ]
    expected = np.array(
        [
            float.fromhex(value)
            for value in [
                "0x1.dd834aa42bc2ap-1",
                "0x1.bda3de4799ef9p-1",
                "0x1.8b99acbfd745cp-2",
                "0x1.1e19d97012794p-2",
                "0x1.ea816033b0531p-2",
            ]
        ]
    )
    actual = _read(tmp_path, reader, tokens)
    compare_vectors(actual, expected, rtol=0, atol=0, exact_indices=tuple(range(5)))
    assert [value.hex() for value in actual] == [value.hex() for value in expected]


@pytest.mark.parametrize("reader", ["shared", "live", "retained"])
def test_explicit_nonfinite_missing_and_integer_positions_survive(
    tmp_path: Path, reader: Reader
) -> None:
    tokens = [
        "0",
        "1",
        "42",
        "9007199254740991",
        "NaN",
        "NA",
        "Inf",
        "-Inf",
        "",
        "1e-9999",
    ]
    actual = _read(tmp_path, reader, tokens)
    expected = np.array(
        [0, 1, 42, 9007199254740991, np.nan, np.nan, np.inf, -np.inf, np.nan, 0]
    )
    np.testing.assert_equal(actual, expected)


@pytest.mark.parametrize("reader", ["shared", "live", "retained"])
@pytest.mark.parametrize(
    "token",
    [
        "1_0",
        "1e309",
        "-1e9999",
        "18446744073709551616",
        "-9223372036854775809",
        "nan",
        "NAN",
        "NA ",
        " ",
        "0x1p1",
    ],
)
def test_original_lexical_refusals_are_not_broadened_by_float_conversion(
    tmp_path: Path, reader: Reader, token: str
) -> None:
    with pytest.raises(ValueError):
        _read(tmp_path, reader, [token])


@pytest.mark.parametrize("reader", ["live", "retained"])
def test_character_vectors_preserve_source_tokens_without_numeric_interpretation(
    tmp_path: Path, reader: Reader
) -> None:
    tokens = ["NA", "NaN", "Inf", "001", "1_0", "1e309"]
    payload = (
        "kind,value\n" + "".join(f"character,{token}\n" for token in tokens)
    ).encode()
    path = tmp_path / "vector.csv"
    path.write_bytes(payload)
    identity = {
        "files": {
            path.name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
        }
    }
    actual = (
        _read_vector(path)
        if reader == "live"
        else read_vector(tmp_path, path.name, identity, numeric=False)
    )
    assert actual.tolist() == tokens
