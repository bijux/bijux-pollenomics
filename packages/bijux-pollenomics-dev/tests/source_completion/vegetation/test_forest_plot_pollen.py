"""Descriptive different-estimand arithmetic and public-output controls."""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.vegetation import (
    forest_plot_pollen as subject,
)
from bijux_pollenomics_dev.source_completion.vegetation.forest_plot_inputs import (
    AXIS,
    BASAL_FIELDS,
    DevelopmentPair,
    PollenPanel,
)


def pair() -> DevelopmentPair:
    return DevelopmentPair(
        "existing-lead",
        "existing-opaque-plot-year",
        2,
        ("1", "1", "3", "5", "10"),
        (),
        PollenPanel((2, 6, 2), 15, 10, 5, 4, 1, ()),
    )


def test_provisional_crosswalk_and_different_estimand_discordance() -> None:
    row = subject.comparison_row(pair())
    assert tuple(row[name] for name in BASAL_FIELDS) == (
        "1",
        "1",
        "3",
        "5",
        "10",
    )
    assert row["basal_area_five_total_m2_ha"] == "20"
    assert row["basal_area_selected_total_m2_ha"] == "10"
    assert float(str(row["other_deciduous_fraction_of_five"])) == 0.5
    assert float(str(row["selected_fraction_of_five"])) == 0.5
    assert [float(str(row[f"basal_fraction_{name}"])) for name in AXIS] == [
        0.2,
        0.3,
        0.5,
    ]
    assert [float(str(row[f"pollen_fraction_{name}"])) for name in AXIS] == [
        0.2,
        0.6,
        0.2,
    ]
    assert [
        float(str(row[f"basal_minus_pollen_fraction_{name}"])) for name in AXIS
    ] == [0.0, -0.3, 0.3]
    assert float(str(row["descriptive_total_variation"])) == 0.3
    assert row["comparison_status"] == "descriptive_comparison"
    assert row["vegetation_pair_admitted"] == "false"
    assert row["evidence_role"] == "exposed_development_different_estimands"


def test_native_decimal_sums_remain_exact_without_float_overflow() -> None:
    row = subject.comparison_row(
        replace(pair(), basal_area=("0.1", "0.2", "0", "0", "0"))
    )
    assert row["basal_area_five_total_m2_ha"] == "0.3"
    assert row["basal_fraction_Pinus"] == "1"
    row = subject.comparison_row(
        replace(pair(), basal_area=("1e310", "0", "0", "0", "0"))
    )
    assert row["basal_area_five_total_m2_ha"] == "1" + "0" * 310
    assert row["basal_fraction_Pinus"] == "1"


@pytest.mark.parametrize(
    "basal,reason",
    [
        (("0", "0", "0", "0", "7"), "zero_selected_basal_area"),
        (("0",) * 5, "zero_selected_basal_area"),
        ((None, "1", "3", "5", "10"), "incomplete_basal_area"),
    ],
)
def test_missing_and_zero_basal_outcomes_refuse_without_dropping_lead(
    basal: tuple[str | None, ...], reason: str
) -> None:
    row = subject.comparison_row(replace(pair(), basal_area=basal))
    assert row["comparison_status"] == "refused" and reason in str(row["reason_codes"])
    assert row["candidate_id"] == "existing-lead" and row["plot_year_reuse"] == 2
    assert row["descriptive_total_variation"] == ""
    assert row["pollen_fraction_Pinus"] != ""
    assert all(row[f"basal_fraction_{name}"] == "" for name in AXIS)


@pytest.mark.parametrize(
    "pollen,reason",
    [
        (PollenPanel((0, 0, 0), 10, 0, 10, 4, 0, ()), "zero_selected_pollen_count"),
        (
            PollenPanel(
                (None, 2, 3), 5, None, None, 2, 0, ("absent_literal_pollen_genus_row",)
            ),
            "incomplete_selected_pollen",
        ),
        (
            PollenPanel(
                (2, 6, 2),
                15,
                10,
                5,
                4,
                0,
                ("pollen_count_units_or_digitisation_unresolved",),
            ),
            "pollen_count_units_or_digitisation_unresolved",
        ),
    ],
)
def test_undefined_or_noncount_pollen_refuses_without_invented_fractions(
    pollen: PollenPanel, reason: str
) -> None:
    row = subject.comparison_row(replace(pair(), pollen=pollen))
    assert row["comparison_status"] == "refused" and reason in str(row["reason_codes"])
    assert row["basal_fraction_Pinus"] != ""
    assert all(row[f"pollen_fraction_{name}"] == "" for name in AXIS)
    assert row["descriptive_total_variation"] == ""


def test_missing_outside_axis_refuses_comparison_but_retains_known_subcomposition() -> (
    None
):
    pollen = PollenPanel(
        (2, 6, 2), None, 10, None, 4, 0, ("invalid_or_missing_native_pollen_count",)
    )
    row = subject.comparison_row(replace(pair(), pollen=pollen))
    assert row["comparison_status"] == "refused"
    assert row["pollen_reported_count_total"] is None
    assert row["pollen_fraction_Pinus"] != "" and row["basal_fraction_Pinus"] != ""
    assert row["descriptive_total_variation"] == ""


def test_atomic_one_table_keeps_refusals_and_existing_opaque_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = (
        pair(),
        replace(pair(), candidate_id="refused-lead", basal_area=(None,) * 5),
    )
    monkeypatch.setattr(subject, "read_inputs", lambda *_: (cases, 1))
    output = tmp_path / "result.csv"
    rows, physical_plots = subject.build(
        tmp_path / "repository", tmp_path / "shared", output
    )
    assert physical_plots == 1
    assert len(rows) == 2 and [row["comparison_status"] for row in rows] == [
        "descriptive_comparison",
        "refused",
    ]
    with output.open(newline="") as stream:
        written = list(csv.DictReader(stream))
    assert list(written[0]) == list(subject.FIELDS)
    assert [row["candidate_id"] for row in written] == ["existing-lead", "refused-lead"]
    assert all(row["vegetation_pair_admitted"] == "false" for row in written)
    assert "\r" not in output.read_text()
    assert not list(tmp_path.glob(".forest-plot-pollen-*"))
    assert not any(
        word in field
        for field in subject.FIELDS
        for word in (
            "tract",
            "latitude",
            "longitude",
            "inventory_date",
            "easting",
            "northing",
        )
    )
    before = output.read_bytes()
    with pytest.raises(ValueError, match="Absent output"):
        subject.build(tmp_path, tmp_path, output)
    assert output.read_bytes() == before


def test_failed_intake_leaves_no_public_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_: object) -> tuple[tuple[DevelopmentPair, ...], int]:
        raise ValueError("native identity changed")

    monkeypatch.setattr(subject, "read_inputs", refuse)
    output = tmp_path / "result.csv"
    with pytest.raises(ValueError, match="native identity"):
        subject.build(tmp_path, tmp_path, output)
    assert not output.exists()
