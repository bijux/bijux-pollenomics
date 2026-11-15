"""Behavioral checks for published-model landscape history."""

from __future__ import annotations

import json
from pathlib import Path


def test_public_input_dispositions_do_not_turn_zero_mass_into_zero_cover() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.inputs import load_cells

    repository = Path(__file__).resolve().parents[5]
    cells = load_cells(repository)
    assert len(cells) == 650
    assert sum(c.status == "eligible" for c in cells) == 567
    assert sum(c.status == "no_data" for c in cells) == 82
    refused = [c for c in cells if c.status == "invalid"]
    assert len(refused) == 1
    assert (
        refused[0].grid_id,
        refused[0].younger_bp,
        refused[0].older_bp,
        refused[0].reason,
    ) == ("1336", 350, 700, "zero_mass")


def test_no_data_exclusion_precedes_native_cover_interpretation(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.inputs import (
        SOURCE,
        load_cells,
    )

    repository = Path(__file__).resolve().parents[5]
    source = json.loads((repository / SOURCE).read_text())
    source["features"] = [
        f
        for f in source["features"]
        if f["properties"].get("dataset_id") == "937075"
        and f["properties"].get("country") == "Sweden"
    ]
    p = next(
        f["properties"]
        for f in source["features"]
        if f["properties"]["quality_class"] == "no_pollen_data"
    )
    p["reconstruction_values"]["Pinus"] = -100.0
    key = (p["parent_grid_record_id"], p["time_start_bp"], p["time_end_bp"])
    destination = tmp_path / SOURCE
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(source))
    cells = load_cells(tmp_path)
    excluded = next(c for c in cells if (c.grid_id, c.younger_bp, c.older_bp) == key)
    assert excluded.status == "no_data"
    assert excluded.reason == "no_pollen_data"
    assert excluded.estimates["Pinus"] == -100
