"""Refuse changed native identities, axes and observations before prediction."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward import inputs


def test_complete_mixed_schema_population(
    artificial_sources: tuple[dict[str, Any], dict[str, Any]], protocol: dict[str, Any]
) -> None:
    cores = inputs.normalize(*artificial_sources, protocol)
    assert len(cores) == 8 and len({c.site for c in cores}) == 7
    assert sum(len(c.cells) for c in cores if c.country == "SE") == 77
    assert {len(c.axis) for c in cores} == {2, 3, 6}


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "dataset",
        "place",
        "missing-core",
        "duplicate-core",
        "taxon",
        "missing-window",
        "duplicate-window",
        "negative",
        "boolean",
        "denominator",
        "kernel",
        "measured",
        "invented-zero",
    ],
)
def test_malformed_complete_source_refuses(
    artificial_sources: tuple[dict[str, Any], dict[str, Any]],
    protocol: dict[str, Any],
    change: str,
) -> None:
    swedish, nordic = copy.deepcopy(artificial_sources)
    row = swedish["cores"][0]
    if change == "epoch":
        swedish["producer_candidate"] = "f" * 40
    elif change == "dataset":
        row["native_dataset_id"] += 1
    elif change == "place":
        row["native_site_id"] = True
    elif change == "missing-core":
        swedish["cores"].pop()
    elif change == "duplicate-core":
        swedish["cores"][1] = copy.deepcopy(row)
    elif change == "taxon":
        row["parameter_taxa"][0] = "unreported"
    elif change == "missing-window":
        row["results"].pop()
    elif change == "duplicate-window":
        row["results"][1] = copy.deepcopy(row["results"][0])
    elif change in {"negative", "boolean"}:
        row["results"][0]["counts"][0][0] = -1 if change == "negative" else True
    elif change == "denominator":
        row["results"][0]["panel_count_denominator"] += 1
    elif change == "kernel":
        row["quadrature"][0]["factors"][0][0] = 0
    elif change == "measured":
        nordic["cases"][0]["results"][0]["actual_source_panel_presence"] = False
    else:
        nordic["cases"][0]["results"][0]["assumed_zero_cells"] = 1
    with pytest.raises(ValueError):
        inputs.normalize(swedish, nordic, protocol)


@pytest.mark.parametrize("change", ["digest", "symlink", "multilink", "special"])
def test_physical_source_buffer_is_not_a_guess(tmp_path: Path, change: str) -> None:
    path = tmp_path / "source.json"
    raw = b'{"declared":"artificial"}\n'
    path.write_bytes(raw)
    checksum = inputs.digest(raw)
    if change == "digest":
        checksum = "0" * 64
    elif change == "symlink":
        other = tmp_path / "other.json"
        path.rename(other)
        path.symlink_to(other)
    elif change == "multilink":
        os.link(path, tmp_path / "other.json")
    else:
        path.unlink()
        os.mkfifo(path)
    with pytest.raises(ValueError):
        inputs.buffer(path, checksum, len(raw))


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'])
def test_ambiguous_or_nonfinite_json_refused(raw: bytes) -> None:
    with pytest.raises(ValueError):
        inputs.decode(raw)
