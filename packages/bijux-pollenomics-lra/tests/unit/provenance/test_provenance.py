from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.provenance import manifest as provenance
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


def test_runtime_dependency_reads_are_cached_without_sharing_manifest_mappings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    versions = {"numpy": "2.4.6", "scipy": "1.17.1", "pandas": "2.3.3"}

    def read_version(distribution: str) -> str:
        calls.append(distribution)
        return versions[distribution]

    provenance._version_or_unknown.cache_clear()
    monkeypatch.setattr(importlib.metadata, "version", read_version)
    try:
        first = build_manifest("fixed", {}, {}, stochastic=False, seed=None)
        second = build_manifest("fixed", {}, {}, stochastic=False, seed=None)
        assert calls == ["numpy", "scipy", "pandas"]
        assert first.scientific_identity() == second.scientific_identity()
        cast(dict[str, str], first.runtime)["numpy"] = "caller mutation"
        assert second.runtime["numpy"] == versions["numpy"]
        third = build_manifest("fixed", {}, {}, stochastic=False, seed=None)
        assert third.runtime["numpy"] == versions["numpy"]
        assert calls == ["numpy", "scipy", "pandas"]
    finally:
        provenance._version_or_unknown.cache_clear()


def test_missing_dependency_status_is_preserved_and_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def missing(distribution: str) -> str:
        calls.append(distribution)
        raise importlib.metadata.PackageNotFoundError(distribution)

    provenance._version_or_unknown.cache_clear()
    monkeypatch.setattr(importlib.metadata, "version", missing)
    try:
        first = build_manifest("fixed", {}, {}, stochastic=False, seed=None)
        second = build_manifest("fixed", {}, {}, stochastic=False, seed=None)
        for distribution in ("numpy", "scipy", "pandas"):
            assert (
                first.runtime[distribution] == second.runtime[distribution] == "unknown"
            )
        assert calls == ["numpy", "scipy", "pandas"]
    finally:
        provenance._version_or_unknown.cache_clear()
