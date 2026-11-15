"""Source-selected downloads bind both metadata paths to one native owner."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import client


def download() -> dict[str, Any]:
    dataset = {"datasetid": 12, "datasettype": "diatom", "database": "source archive"}
    return {
        "site": {
            "siteid": 3,
            "dataset": dict(dataset),
            "collectionunit": {"collectionunitid": 4, "dataset": dict(dataset)},
        }
    }


def validate(row: object) -> None:
    client.validate_neotoma_selected_download(
        row,
        expected_dataset_id=12,
        expected_site_id=3,
        expected_collection_unit_id=4,
        expected_dataset_type="diatom",
        expected_database="source archive",
    )


def test_selected_download_accepts_declared_source_without_pollen_assumptions() -> None:
    row = download()
    original = deepcopy(row)
    validate(row)
    assert row == original


@pytest.mark.parametrize(
    ("owner", "field", "value"),
    [
        ("nested", "datasetid", 13),
        ("outer", "datasetid", True),
        ("nested", "datasettype", None),
        ("outer", "datasettype", "pollen"),
        ("nested", "database", "other database"),
        ("outer", "database", None),
        ("site", "siteid", True),
        ("site", "siteid", 13),
        ("unit", "collectionunitid", True),
        ("unit", "collectionunitid", 13),
    ],
)
def test_selected_download_refuses_mismatched_or_missing_owner_fields(
    owner: str, field: str, value: object
) -> None:
    row = download()
    site = row["site"]
    unit = site["collectionunit"]
    owners = {
        "site": site,
        "unit": unit,
        "outer": site["dataset"],
        "nested": unit["dataset"],
    }
    owners[owner][field] = value
    with pytest.raises(ValueError, match="Neotoma"):
        validate(row)


@pytest.mark.parametrize("missing", ["site", "collectionunit", "outer", "nested"])
def test_selected_download_requires_both_dataset_metadata_paths(missing: str) -> None:
    row = download()
    if missing == "site":
        row.pop("site")
    elif missing == "collectionunit":
        row["site"].pop("collectionunit")
    elif missing == "outer":
        row["site"].pop("dataset")
    else:
        row["site"]["collectionunit"].pop("dataset")
    with pytest.raises(ValueError, match="Neotoma"):
        validate(row)
