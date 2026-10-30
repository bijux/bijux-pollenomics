"""Preserve signed memberships, absent observations and saved age identities."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.chronology import (
    age_rows,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.inputs import (
    membership,
)


def sample(
    number: int, counts: list[int] | None = None, missing: list[str] | None = None
) -> dict[str, Any]:
    vector = [1, 2, 3, 4, 5] if counts is None else counts
    return {
        "sample_id": number,
        "depth_native": number,
        "source_point_age_bp": None,
        "missing_taxa": missing or [],
        "counts": None if missing else vector,
        "reported_panel_subtotal": sum(vector),
        "panel_mass": None if missing else sum(vector),
        "all_reported_pollen_nisp": sum(vector) + 2,
        "omitted_reported_pollen_nisp": 2,
    }


def test_half_open_membership_retains_negative_age_outside() -> None:
    samples = [sample(i) for i in range(4)]
    record, counts = membership(samples, [-1.0, 1500.0, 1999.999, 2000.0], 3)
    assert record["sample_ids"] == [1, 2] and counts == (2, 4, 6, 8, 10)
    assert membership(samples, [-1.0, 1500.0, 1999.999, 2000.0], 4)[0][
        "sample_ids"
    ] == [3]


def test_missing_one_member_refuses_whole_panel_without_silent_subset() -> None:
    record, counts = membership(
        [sample(1), sample(2, [3, 0, 0, 1, 0], ["Poaceae"])], [1600.0, 1700.0], 3
    )
    assert record["status"] == "missing_explicit_five_taxon_member"
    assert record["sample_ids"] == [1, 2] and record["reported_panel_subtotal"] == 19
    assert record["panel_mass"] is None and counts is None
    assert record["missing_members"] == {"2": ["Poaceae"]}


def test_empty_zero_mass_and_measured_zero_axis_remain_distinct() -> None:
    assert membership([sample(1)], [0.0], 3)[0]["status"] == "empty_native_window"
    assert (
        membership([sample(1, [0] * 5)], [1600.0], 3)[0]["status"]
        == "nonempty_zero_panel_mass"
    )
    assert (
        membership([sample(1, [1, 0, 2, 3, 4])], [1600.0], 3)[0]["status"] == "defined"
    )


@pytest.mark.parametrize("corrupt", ["none", "header", "nonmonotone", "truncated"])
def test_saved_age_columns_rows_and_signs(tmp_path: Path, corrupt: str) -> None:
    ids = [f"neotoma:sample:{i}" for i in range(107)]
    path = tmp_path / "ages.csv.gz"
    first = [-1.0, *map(float, range(1, 107))]
    second = [-0.5, *map(float, range(1, 107))]
    if corrupt == "nonmonotone":
        second[1] = -2.0
    with gzip.open(path, "wt", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(ids if corrupt != "header" else ["other", *ids[1:]])
        writer.writerow(first)
        if corrupt != "truncated":
            writer.writerow(second)
    entry = {"path": path.name, "retained_rows": 2, "first_native_row": 3502}
    if corrupt == "none":
        rows = list(age_rows(tmp_path, entry, ids))
        assert [r[0] for r in rows] == [3502, 3503] and rows[0][1][0] == -1.0
    else:
        with pytest.raises(ValueError, match="identity|nonmonotone|truncated"):
            list(age_rows(tmp_path, entry, ids))
