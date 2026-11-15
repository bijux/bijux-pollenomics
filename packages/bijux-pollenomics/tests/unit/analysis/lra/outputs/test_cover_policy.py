"""Saved LOVE products enforce their declared cover assumption."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from bijux_pollenomics.analysis.lra.execution.service import run_lra_request
from bijux_pollenomics.analysis.lra.outputs.contracts import validate_numerical_tables
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product

from ..support import request_fixture


@pytest.mark.parametrize("operation", ["love", "lra", "series"])
def test_installed_host_carries_closed_cover_and_raw_diagnostics(
    tmp_path: Path, operation: str
) -> None:
    payload = request_fixture(tmp_path, operation)
    payload["local"]["samples"][0]["counts"] = [0, 100]
    product = run_lra_request(
        payload, input_root=tmp_path, destination=tmp_path / "product"
    )
    manifest = read_lra_product(product.directory).manifest()
    assert manifest["scientific_identity"]["engine_scientific_manifest"][
        "compatibility_mode"
    ] == ("analytical-love-clip-and-renormalize")
    tables = list((product.directory / "numerical").rglob("cover_mean.csv"))
    assert len(tables) == 1
    cover = pd.read_csv(tables[0], index_col=0)
    assert cover.iloc[0].tolist() == [0, 1]
    raw = pd.read_csv(tables[0].with_name("aux_raw_cover_mean.csv"), index_col=0)
    raw_values = raw.to_numpy(dtype=float)
    assert raw_values[0, 0] < 0 and raw_values[0, 1] > 1


@pytest.mark.parametrize("values", [[-0.1, 1.1], [0.2, 0.3], [None, 1]])
def test_saved_adjusted_cover_refuses_bounds_mass_or_partial_missingness(
    tmp_path: Path, values: list[float | None]
) -> None:
    payload = request_fixture(tmp_path, "love")
    product = run_lra_request(
        payload, input_root=tmp_path, destination=tmp_path / "product"
    )
    path = product.directory / "numerical/cover_mean.csv"
    table = pd.read_csv(path, index_col=0)
    table.iloc[0] = values
    table.to_csv(path, index_label="index")
    with pytest.raises(ValueError, match="cover"):
        validate_numerical_tables(product.directory, payload)


def test_explicit_source_replay_keeps_signed_saved_cover(tmp_path: Path) -> None:
    payload = request_fixture(tmp_path, "love")
    payload["configuration"]["love"]["analytical_cover_policy"] = "source-raw"
    payload["local"]["samples"][0]["counts"] = [0, 100]
    product = run_lra_request(
        payload, input_root=tmp_path, destination=tmp_path / "product"
    )
    cover = pd.read_csv(product.directory / "numerical/cover_mean.csv", index_col=0)
    assert cover.to_numpy(dtype=float)[0, 0] < 0
    assert (
        read_lra_product(product.directory).manifest()["scientific_acceptance"]
        == "not_evaluated"
    )
    contract = json.loads(
        (product.directory / "numerical/result_contract.json").read_text()
    )
    assert contract["analytical_cover_policy"] == "source-raw"
