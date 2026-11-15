"""Selected Swedish responses cannot borrow another dataset or core's counts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import (
    nordic_direct_pollen,
    swedish_direct_pollen,
    swedish_pollen_sequences,
)

from .test_pollen_element_consumers import native_sources as native_sources


@pytest.mark.parametrize("consumer", ["direct", "nordic_training", "sequences"])
@pytest.mark.parametrize(
    ("owner", "field", "value"),
    [
        ("nested", "datasetid", 999999),
        ("outer", "datasetid", 999999),
        ("nested", "datasettype", "geochronologic"),
        ("outer", "datasettype", "geochronologic"),
        ("nested", "database", "another source database"),
        ("outer", "database", "another source database"),
        ("site", "siteid", 999999),
        ("unit", "collectionunitid", 999999),
    ],
)
def test_selected_response_refuses_source_owner_contradictions(
    native_sources: tuple[Path, Path],
    tmp_path: Path,
    consumer: str,
    owner: str,
    field: str,
    value: object,
) -> None:
    raw, config = native_sources
    part = raw / "part-008.json"
    document = json.loads(part.read_bytes())
    site = next(
        row["site"]
        for row in document["rows"]
        if row["site"]["dataset"]["datasetid"] == 54001
    )
    unit = site["collectionunit"]
    owners = {
        "site": site,
        "unit": unit,
        "outer": site["dataset"],
        "nested": unit["dataset"],
    }
    owners[owner][field] = value
    part.write_text(json.dumps(document))

    with pytest.raises(ValueError):
        if consumer == "direct":
            swedish_direct_pollen.prepare(raw, tmp_path / "result", config)
        elif consumer == "nordic_training":
            nordic_direct_pollen._swedish_training(raw)
        else:
            swedish_pollen_sequences.build(raw, tmp_path / "result")
