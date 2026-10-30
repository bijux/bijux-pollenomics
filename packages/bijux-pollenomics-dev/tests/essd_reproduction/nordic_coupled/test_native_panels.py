"""Artificial native shapes exercise literal panels without a model or real source read."""

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.native_panel_rows import (
    AGE_TYPE,
    IDENTITY,
    NEGATIVE_SAMPLES,
    SOURCE,
    TAXA,
    WINDOWS,
    encoded,
    read_native,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.native_panel_source import (
    buffer,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.native_panels import project
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import digest


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """Use the actual wire schema with artificial ages/counts, never native outcomes."""
    ids = [
        *NEGATIVE_SAMPLES,
        *[n for n in range(552982, 553091) if n not in NEGATIVE_SAMPLES],
    ]
    samples = []
    for index, sample_id in enumerate(ids):
        point = (
            [-50, -33.3, -9.4][index]
            if index < 3
            else [2700, 3200, 3700, 4200, 4700, 5200, 5700][index - 3]
            if index < 10
            else 3300
        )
        datum = [
            {
                "taxonid": taxon_id,
                "variablename": label,
                "value": value,
                "element": element,
                "elementtype": element,
                "units": units,
                "context": None,
            }
            for taxon_id, label, value, element, units in (
                (29, "Betula", 4, "pollen", "NISP"),
                (310, "Ulmus", 2, "pollen", "NISP"),
                (385, "Pinus", 3, "pollen", "NISP"),
                (276, "Sample quantity", 2.5, "volume", "cm3"),
                (35429, "Indeterminable (unknown)", 7, "pollen/spore", "NISP"),
            )
        ]
        samples.append(
            {
                "sampleid": sample_id,
                "analysisunitid": 400000 + index,
                "depth": 70 + index,
                "thickness": None,
                "ages": [
                    {
                        "age": point,
                        "agetype": AGE_TYPE,
                        "ageolder": None,
                        "ageyounger": None,
                        "chronologyid": 38438,
                        "chronologyname": "Cal yr BP",
                    }
                ],
                "datum": datum,
            }
        )
    metadata = {
        "isdefault": True,
        "modelagetype": AGE_TYPE,
        "chronologyname": "Cal yr BP",
        "agemodel": "linear interpolation",
        "agerange": {"ageboundolder": 12050, "ageboundyounger": -50},
    }
    unit = {
        "collectionunitid": 39258,
        "handle": "FLINK",
        "defaultchronology": 38438,
        "chronologies": [
            {
                "chronology": {
                    "chronologyid": 38438,
                    "chronology": metadata,
                    "chroncontrols": [],
                }
            }
        ],
        "dataset": {"datasetid": 54024, "datasettype": "pollen", "samples": samples},
    }
    source = {
        "rows": [
            {
                "site": {
                    "siteid": 28889,
                    "dataset": {"datasetid": 54024},
                    "collectionunit": unit,
                }
            }
        ]
    }
    protocol = {
        "schema_version": "flink-native-panel-projection.v1",
        "source": dict(SOURCE),
        "identity": dict(IDENTITY),
        "sample_ids": ids,
        "negative_age_sample_ids": list(NEGATIVE_SAMPLES),
        "taxa": list(TAXA),
        "age": {"native_type": AGE_TYPE, "reference_epoch_ad": 1950},
        "windows": [list(w) for w in WINDOWS],
    }
    return source, protocol


def samples(source: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        source["rows"][0]["site"]["collectionunit"]["dataset"]["samples"],
    )


def test_complete_population_and_half_open_membership_without_imputation() -> None:
    source, protocol = fixture()
    original = deepcopy((source, protocol))
    result = project(source, protocol)
    assert (source, protocol) == original
    assert result["sample_count"] == 109 and result["nonnegative_age_count"] == 106
    assert result["negative_age_sample_ids"] == list(NEGATIVE_SAMPLES)
    assert result["samples"][0]["selected_age"]["age"] == -50
    assert result["samples"][0]["selected_age"]["ageolder"] is None
    assert result["samples"][0]["native_depth"] == 70
    assert result["samples"][3]["window"] == [2700, 3200]
    assert result["samples"][4]["window"] == [3200, 3700]
    assert result["samples"][9]["window"] is None
    assert result["windows"][0]["panel_counts"] == [4, 2]
    assert result["windows"][0]["pollen_N"] == 9
    assert result["windows"][0]["excluded_pollen_N"] == 3
    assert result["engine_calls"] == 0


@pytest.mark.parametrize(
    "state", ["zero", "missing", "duplicate", "near_label", "wrong_id"]
)
def test_literal_states_are_not_zero_filled_or_synonym_mapped(state: str) -> None:
    source, protocol = fixture()
    row = samples(source)[3]
    if state == "zero":
        row["datum"][0]["value"] = 0
    elif state == "missing":
        row["datum"].pop(0)
    elif state == "duplicate":
        row["datum"].append(deepcopy(row["datum"][0]))
    elif state == "near_label":
        row["datum"][0]["variablename"] = "Betula cf."
    else:
        row["datum"][0]["taxonid"] = 999
    result = project(source, protocol)
    selected = result["samples"][3]
    if state == "zero":
        assert selected["literal_states"][0]["status"] == "measured_zero"
        assert result["windows"][0]["panel_counts"] == [0, 2]
    else:
        assert (
            selected["literal_states"][0]["status"]
            == {
                "missing": "missing_literal",
                "duplicate": "duplicate_literal",
                "near_label": "missing_literal",
                "wrong_id": "incompatible_literal",
            }[state]
        )
        assert result["windows"][0]["status"] == "refused_incomplete_literal_panel"
        assert result["windows"][0]["panel_counts"] is None
        assert result["windows"][0]["excluded_pollen_N"] is None


@pytest.mark.parametrize("value", [-1, 0.5, True, "4", float("nan"), float("inf")])
def test_invalid_pollen_counts_refused(value: object) -> None:
    source, protocol = fixture()
    samples(source)[3]["datum"][0]["value"] = value
    with pytest.raises(ValueError, match="integer"):
        project(source, protocol)


@pytest.mark.parametrize(
    "field,value", [("units", "%"), ("elementtype", "seed"), ("context", "male")]
)
def test_pollen_denominator_unit_context_guards(field: str, value: str) -> None:
    source, protocol = fixture()
    samples(source)[3]["datum"][0][field] = value
    with pytest.raises(ValueError, match="pollen/NISP"):
        project(source, protocol)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_age",
        "wrong_chronology",
        "wrong_age_type",
        "duplicate_sample",
        "wrong_nested_dataset",
        "nonfinite_depth",
    ],
)
def test_identity_chronology_and_depth_refusals(mutation: str) -> None:
    source, protocol = fixture()
    rows = samples(source)
    if mutation == "duplicate_age":
        rows[3]["ages"].append(deepcopy(rows[3]["ages"][0]))
    elif mutation == "wrong_chronology":
        source["rows"][0]["site"]["collectionunit"]["defaultchronology"] = 9
    elif mutation == "wrong_age_type":
        rows[3]["ages"][0]["agetype"] = "Radiocarbon years BP"
    elif mutation == "duplicate_sample":
        rows[4]["sampleid"] = rows[3]["sampleid"]
    elif mutation == "wrong_nested_dataset":
        source["rows"][0]["site"]["collectionunit"]["dataset"]["datasetid"] = 1
    else:
        rows[3]["depth"] = float("nan")
    with pytest.raises(ValueError):
        project(source, protocol)


def test_empty_window_and_source_support_preserved() -> None:
    source, protocol = fixture()
    before = project(source, protocol)
    samples(source)[3]["datum"][2]["value"] = 4
    after = project(source, protocol)
    assert after["windows"][0]["panel_counts"] == before["windows"][0]["panel_counts"]
    assert after["windows"][0]["excluded_pollen_N"] == 4
    assert (
        after["windows"][0]["support_sha256"] != before["windows"][0]["support_sha256"]
    )
    samples(source)[8]["ages"][0]["age"] = 5700
    empty = project(source, protocol)["windows"][-1]
    assert empty["status"] == "empty" and empty["sample_ids"] == []
    assert empty["panel_counts"] is None


def test_authenticated_buffer_refuses_changed_or_aliased_file(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    raw = encoded({"artificial": True})
    path.write_bytes(raw)
    assert buffer(path, digest(raw), len(raw), 1024) == raw
    with pytest.raises(ValueError, match="identity"):
        buffer(path, "0" * 64, len(raw), 1024)
    link = tmp_path / "alias.json"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="alias"):
        buffer(link, digest(raw), len(raw), 1024)


def test_native_reader_admits_typed_cells_without_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
        native_panel_rows,
        native_panels,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Projection/count aggregation forbidden")

    monkeypatch.setattr(native_panels, "project", forbidden)
    monkeypatch.setattr(native_panel_rows, "_panel", forbidden)
    source, protocol = fixture()
    chronology, selected = read_native(source, protocol)
    assert chronology["chronologyid"] == 38438
    assert len(selected) == 109 and selected[0]["sampleid"] == 552982
    assert selected[0]["ages"][0]["age"] == -50
