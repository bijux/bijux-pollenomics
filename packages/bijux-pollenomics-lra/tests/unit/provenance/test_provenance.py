from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.provenance.identity import (
    canonical_json,
    sha256_file,
    sha256_object,
)
from bijux_pollenomics_lra.provenance.manifest import build_manifest


def test_canonical_hash_is_stable_for_equivalent_frames() -> None:
    first = pd.DataFrame({"A": [1, 2], "B": [3.0, np.nan]}, index=["x", "y"])
    second = first.copy(deep=True)
    assert canonical_json(first) == canonical_json(second)
    assert sha256_object(first) == sha256_object(second)
    second.iloc[0, 0] = 9
    assert sha256_object(first) != sha256_object(second)


def test_mapping_key_order_does_not_change_hash() -> None:
    assert sha256_object({"a": 1, "b": 2}) == sha256_object({"b": 2, "a": 1})


def test_file_hash_and_manifest_write(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("abc", encoding="utf-8")
    assert (
        sha256_file(source)
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    manifest = build_manifest(
        "test",
        {"parameter": 1},
        {"table": pd.DataFrame({"A": [1]})},
        stochastic=False,
        seed=None,
    )
    path = manifest.write(tmp_path / "manifest.json")
    parsed = json.loads(path.read_text())
    assert parsed["algorithm"] == "test"
    assert len(parsed["inputs"]["table"]) == 64
