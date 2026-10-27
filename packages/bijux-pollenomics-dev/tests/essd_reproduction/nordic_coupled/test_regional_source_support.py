"""Artificial native owners distinguish missing support from measured zero."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    regional_source_support as audit,
)


def datum(label: str, taxon_id: int, value: object) -> dict[str, Any]:
    return {
        "variablename": label,
        "taxonid": taxon_id,
        "value": value,
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "context": None,
    }


def artificial() -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads(
        (Path(__file__).resolve().parents[5] / audit.PROTOCOL).read_bytes()
    )
    samples = []
    for index in range(96):
        point = [2700, 3200, 3700, 4200, 4700, 5200, 5700, -1][index % 8]
        samples.append(
            {
                "sampleid": 1000 + index,
                "analysisunitid": 2000 + index,
                "depth": index,
                "thickness": None,
                "ages": [
                    {
                        "chronologyid": 13365,
                        "chronologyname": "Fossilva",
                        "agetype": "Radiocarbon years BP",
                        "age": 9999,
                        "ageyounger": None,
                        "ageolder": None,
                    },
                    {
                        "chronologyid": 13366,
                        "chronologyname": audit.CHRONOLOGY["selected_name"],
                        "agetype": audit.CHRONOLOGY["selected_native_type"],
                        "age": point,
                        "ageyounger": None,
                        "ageolder": None,
                    },
                ],
                "datum": [
                    datum("Betula", 29, 4),
                    datum("Ulmus", 310, 2),
                    datum("Pinus", 385, 3),
                    {
                        **datum("Unknown", 999, 7),
                        "element": "pollen/spore",
                        "elementtype": "pollen/spore",
                    },
                ],
            }
        )
    unit = {
        "collectionunitid": 16622,
        "handle": "KRAGMJNY",
        "defaultchronology": 13365,
        "chronologies": [
            {
                "chronology": {
                    "chronologyid": code,
                    "chronology": {
                        "isdefault": True,
                        "chronologyname": name,
                        "modelagetype": kind,
                    },
                }
            }
            for code, name, kind in (
                (13365, "Fossilva", "Radiocarbon years BP"),
                (
                    13366,
                    audit.CHRONOLOGY["selected_name"],
                    audit.CHRONOLOGY["selected_native_type"],
                ),
            )
        ],
        "dataset": {"datasetid": 23013, "datasettype": "pollen", "samples": samples},
    }
    return {
        "rows": [
            {
                "site": {
                    "siteid": 3204,
                    "dataset": {"datasetid": 23013},
                    "collectionunit": unit,
                }
            }
        ]
    }, protocol


def native_samples(source: dict[str, Any]) -> list[dict[str, Any]]:
    return source["rows"][0]["site"]["collectionunit"]["dataset"]["samples"]  # type: ignore[no-any-return]


def test_full_census_half_open_windows_and_nonpanel_mass() -> None:
    source, protocol = artificial()
    result = audit.project(source, protocol)
    assert len(result["samples"]) == 96 and [
        row["native_sample_index"] for row in result["samples"]
    ] == list(range(96))
    assert result["chronology"]["native_collection_default_reference"] == 13365
    assert result["chronology"]["selected_chronology_id"] == 13366
    assert [
        row["native_metadata"]["isdefault"]
        for row in result["chronology"]["source_chronology_declarations"]
    ] == [True, True]
    assert result["population"]["age_disposition_counts"] == {
        "in_requested_window": 72,
        "outside_requested_windows": 12,
        "negative_native_age_retained": 12,
    }
    for row, window in zip(result["windows"], audit.WINDOWS, strict=True):
        assert (
            row["window"] == list(window)
            and row["member_count"] == 12
            and row["status"] == "supported"
        )
        assert (
            row["panel_counts"] == [48, 24]
            and row["panel_N"] == 72
            and row["pollen_N"] == 108
            and row["excluded_pollen_N"] == 36
        )
    assert result["source_totals"]["panel_counts"] == [384, 192]
    assert result["source_totals"]["pollen_N"] == 864
    assert result["support_summary"]["datum_status_counts"] == {
        "valid_pollen_NISP": 288,
        "non_pollen": 96,
    }
    assert result["engine_calls"] == result["model_fits"] == 0
    assert not result["scientific_or_field_admission"]


@pytest.mark.parametrize(
    ("value", "status"),
    [
        (0, "measured_zero"),
        (None, "null_native_value"),
        (True, "invalid_count"),
        (1.0, "invalid_count"),
        (-1, "invalid_count"),
        ("1", "invalid_count"),
        (2**80, "measured"),
    ],
)
def test_native_count_type_and_exact_integer_arithmetic(
    value: object, status: str
) -> None:
    row = datum("Betula", 29, value)
    result = audit.literal_panel([row, datum("Ulmus", 310, 2)])
    assert result["taxa"][0]["status"] == status
    assert result["panel_counts"][0] == (
        value if status in {"measured", "measured_zero"} else None
    )
    if status == "measured":
        assert result["panel_N"] == 2**80 + 2


@pytest.mark.parametrize(
    ("extra", "status"),
    [
        (datum("Betula", 999, 8), "duplicate_literal"),
        (datum("Other", 29, 8), "id_label_conflict"),
    ],
)
def test_duplicate_and_conflicting_id_precedence(
    extra: dict[str, Any], status: str
) -> None:
    result = audit.literal_panel(
        [datum("Betula", 29, 4), datum("Ulmus", 310, 2), extra]
    )
    assert (
        result["taxa"][0]["status"] == status
        and len(result["taxa"][0]["native_matches"]) == 2
    )
    assert result["panel_N"] is None


@pytest.mark.parametrize(
    ("mutation", "status"),
    [
        ("missing_label", "missing_literal"),
        ("wrong_id", "id_label_conflict"),
        ("units", "incompatible_metadata"),
        ("context", "incompatible_metadata"),
        ("missing_value", "missing_native_value"),
    ],
)
def test_literal_source_problem_is_not_zero(mutation: str, status: str) -> None:
    rows = [datum("Betula", 29, 4), datum("Ulmus", 310, 2)]
    if mutation == "missing_label":
        rows.pop(0)
    elif mutation == "wrong_id":
        rows[0]["taxonid"] = 30
    elif mutation == "missing_value":
        del rows[0]["value"]
    else:
        rows[0][mutation] = "incompatible"
    result = audit.literal_panel(rows)
    assert result["taxa"][0]["status"] == status and result["panel_counts"] == [None, 2]


def test_duplicate_nonpanel_cells_preserve_subtotal_but_refuse_denominator() -> None:
    rows = [
        datum("Betula", 29, 4),
        datum("Ulmus", 310, 2),
        datum("Pinus", 385, 3),
        datum("Pinus", 385, 5),
    ]
    result = audit.pollen_mass(rows)
    assert result["known_valid_pollen_cell_sum"] == 14 and result["pollen_N"] is None
    assert result["datum_status_counts"] == {
        "valid_pollen_NISP": 2,
        "duplicate_pollen_identity": 2,
        "non_pollen": 0,
    }
    assert audit.literal_panel(rows)["panel_N"] == 6


@pytest.mark.parametrize(
    ("mutation", "status"),
    [
        ("missing", "missing_selected_age"),
        ("duplicate", "duplicate_selected_age"),
        ("wrong_type", "incompatible_selected_age_type_or_name"),
        ("bounds", "conflicting_selected_age_bounds"),
        ("boolean", "invalid_selected_age_value"),
        ("overflow", "invalid_selected_age_value"),
    ],
)
def test_unassignable_owners_retained_and_all_windows_suppressed(
    mutation: str, status: str
) -> None:
    source, protocol = artificial()
    sample = native_samples(source)[0]
    if mutation == "missing":
        sample["ages"].pop()
    elif mutation == "duplicate":
        sample["ages"].append(deepcopy(sample["ages"][-1]))
    elif mutation == "wrong_type":
        sample["ages"][-1]["agetype"] = "Radiocarbon years BP"
    elif mutation == "bounds":
        sample["ages"][-1]["ageyounger"] = 3000
    else:
        sample["ages"][-1]["age"] = True if mutation == "boolean" else 10**400
    result = audit.project(source, protocol)
    assert (
        len(result["samples"]) == 96
        and result["samples"][0]["selected_age_status"] == status
    )
    assert result["samples"][0]["native_ages"] == sample["ages"]
    assert all(
        row["status"] == "suppressed_unassignable_age"
        and row["panel_counts"] is None
        and row["unassignable_source_sample_ids"] == [1000]
        for row in result["windows"]
    )
    assert result["source_totals"]["panel_counts"] == [384, 192]


def test_zero_panel_and_bad_full_mass_have_distinct_dispositions() -> None:
    source, protocol = artificial()
    for sample in native_samples(source):
        if sample["ages"][-1]["age"] == 2700:
            sample["datum"][0]["value"] = sample["datum"][1]["value"] = 0
        if sample["ages"][-1]["age"] == 3200:
            sample["datum"][2]["value"] = None
    result = audit.project(source, protocol)
    first, second = result["windows"][:2]
    assert (
        first["status"] == "suppressed_zero_panel"
        and first["panel_counts"] == [0, 0]
        and first["pollen_N"] == 36
    )
    assert (
        second["status"] == "suppressed_full_mass"
        and second["panel_counts"] == [48, 24]
        and second["pollen_N"] is None
    )


@pytest.mark.parametrize(
    "mutation", ["census", "owner", "reference", "flag", "identity", "protocol"]
)
def test_native_identity_and_chronology_conflicts_refused(mutation: str) -> None:
    source, protocol = artificial()
    unit = source["rows"][0]["site"]["collectionunit"]
    if mutation == "census":
        native_samples(source).pop()
    elif mutation == "owner":
        native_samples(source)[0]["sampleid"] = native_samples(source)[1]["sampleid"]
    elif mutation == "reference":
        unit["defaultchronology"] = 13366
    elif mutation == "flag":
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = False
    elif mutation == "identity":
        unit["collectionunitid"] = 16623
    else:
        protocol["windows"][0][0] = 2600
    with pytest.raises(ValueError):
        audit.project(source, protocol)
