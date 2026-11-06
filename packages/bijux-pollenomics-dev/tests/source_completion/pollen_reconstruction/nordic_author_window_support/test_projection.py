"""Source ownership, author assignment and complete-window refusal controls."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.author_window_support.projection import (
    project,
)

from .fixtures import cell, lookup_fixture, native_fixture, native_samples


@pytest.mark.parametrize("index", range(7))
def test_complete_native_owners_windows_and_original_chronology(index: int) -> None:
    source, core, profile = native_fixture(index)
    before = deepcopy(source)
    ledger = project(source, core, profile, lookup_fixture())
    assert source == before
    samples = native_samples(source)
    assert [r["sample_id"] for r in ledger["samples"]] == [
        r["sampleid"] for r in samples
    ]
    assert len(ledger["samples"]) == core["identity"]["source_sample_count"]
    assert (
        ledger["chronology"]["native_chronology_declarations"]
        == source["rows"][0]["site"]["collectionunit"]["chronologies"]
    )
    assert (
        ledger["chronology"]["native_collection_default_reference"]
        == core["chronology"]["native_collection_default_reference"]
    )
    for window in ledger["windows"]:
        expected = [
            r["sampleid"]
            for r in samples
            if window["window"][0] <= r["ages"][0]["age"] < window["window"][1]
        ]
        assert window["sample_ids"] == expected
        assert window["panel_counts"] == [4 * len(expected), 2 * len(expected)]
        assert window["pollen_N"] == 9 * len(expected)
        assert window["excluded_pollen_N"] == 3 * len(expected)
    row = ledger["samples"][0]
    assert row["native_ages"] == samples[0]["ages"]
    assert [r["native"] for r in row["datum_accounting"]] == samples[0]["datum"]
    assert [r["disposition"] for r in row["datum_accounting"]] == [
        "selected_author_target",
        "selected_author_target",
        "unmapped_native_name",
        "non_pollen",
    ]
    assert row["taxa"][0]["lookup_rows"] == lookup_fixture()[:2]
    assert ledger["taxon_axis"] == ["Betula", "Pinus"]
    assert ledger["physical_family"] == core["physical_family"]
    assert ledger["scientific_or_field_admission"] is False


def test_signed_outside_age_and_alternate_claim_are_not_admission_or_missing_point() -> (
    None
):
    source, core, profile = native_fixture(3)
    sample = native_samples(source)[8]
    sample["ages"][0]["ageyounger"] = -41
    sample["ages"][0]["ageolder"] = None
    result = project(source, core, profile, lookup_fixture())
    row = result["samples"][8]
    assert row["selected_age_status"] == "selected_typed_point"
    assert row["age_disposition"] == "outside_requested_windows"
    assert row["native_ages"] == sample["ages"]
    assert row["selected_age"]["ageyounger"] == -41
    assert all(w["status"] == "supported" for w in result["windows"])


@pytest.mark.parametrize(
    "value,status",
    [
        (None, "null_native_value"),
        (True, "invalid_count"),
        (1.0, "invalid_count"),
        (-1, "invalid_count"),
        (0, "measured_zero"),
        (10**80, "measured"),
    ],
)
def test_native_count_types_and_zero_are_not_repaired(
    value: object, status: str
) -> None:
    source, core, profile = native_fixture()
    native_samples(source)[0]["datum"][1]["value"] = value
    result = project(source, core, profile, lookup_fixture())
    row = result["samples"][0]
    assert row["taxa"][1]["status"] == status
    assert row["datum_accounting"][1]["native"]["value"] is value
    if type(value) is int and value >= 0:
        assert row["panel_N"] == 4 + value and row["pollen_N"] == 7 + value
        assert result["windows"][0]["status"] == "supported"
    else:
        assert row["panel_N"] is None and row["pollen_N"] is None
        assert result["windows"][0]["status"] == "suppressed_incomplete_panel"


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "missing_value", "wrong_unit", "wrong_context"]
)
def test_incomplete_required_axis_retains_all_owners(damage: str) -> None:
    source, core, profile = native_fixture()
    datum = native_samples(source)[0]["datum"]
    if damage == "missing":
        datum.pop(1)
    elif damage == "duplicate":
        datum.append(deepcopy(datum[1]))
    elif damage == "missing_value":
        datum[1].pop("value")
    elif damage == "wrong_unit":
        datum[1]["units"] = "percent"
    else:
        datum[1]["context"] = "technical context"
    result = project(source, core, profile, lookup_fixture())
    assert result["windows"][0]["status"] == "suppressed_incomplete_panel"
    assert result["windows"][0]["panel_counts"] is None
    assert len(result["samples"]) == 107
    assert result["source_totals"]["panel_counts"] is None


def test_unexpected_author_mapped_concept_is_hard_refusal() -> None:
    source, core, profile = native_fixture()
    native_samples(source)[0]["datum"].append(cell("Other pine", 777, 3))
    lookup = lookup_fixture() + [
        {"row_number": 99, "oldvar": "Other pine", "author_target": "Pinus"}
    ]
    with pytest.raises(ValueError, match="Unexpected additional"):
        project(source, core, profile, lookup)


@pytest.mark.parametrize(
    "damage", ["sample_id", "dataset", "reference", "extra_declaration", "flag"]
)
def test_exact_ownership_and_full_declaration_flags_refuse(damage: str) -> None:
    source, core, profile = native_fixture()
    unit = source["rows"][0]["site"]["collectionunit"]
    if damage == "sample_id":
        native_samples(source)[1]["sampleid"] = native_samples(source)[0]["sampleid"]
    elif damage == "dataset":
        unit["dataset"]["datasetid"] += 1
    elif damage == "reference":
        unit["defaultchronology"] += 1
    elif damage == "extra_declaration":
        declaration = deepcopy(unit["chronologies"][0])
        declaration["chronology"]["chronologyid"] += 100
        unit["chronologies"].append(declaration)
    else:
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = 1
    with pytest.raises(ValueError):
        project(source, core, profile, lookup_fixture())


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "wrong_type", "bad_bounds", "null_age"]
)
def test_unassignable_owner_suppresses_every_own_window(damage: str) -> None:
    source, core, profile = native_fixture()
    ages = native_samples(source)[-1]["ages"]
    if damage == "missing":
        ages.clear()
    elif damage == "duplicate":
        ages.append(deepcopy(ages[0]))
    elif damage == "wrong_type":
        ages[0]["agetype"] = "Radiocarbon years BP"
    elif damage == "bad_bounds":
        ages[0]["ageolder"] = ages[0]["age"] - 1
    else:
        ages[0]["age"] = None
    result = project(source, core, profile, lookup_fixture())
    assert len(result["samples"]) == 107
    assert all(r["status"] == "suppressed_unassignable_age" for r in result["windows"])
    assert result["source_totals"]["panel_N"] == 107 * 6


def test_invalid_excluded_mass_does_not_invent_full_denominator() -> None:
    source, core, profile = native_fixture()
    native_samples(source)[0]["datum"].append(cell("Unmapped source label", 99999, 5))
    row = project(source, core, profile, lookup_fixture())["samples"][0]
    assert row["panel_counts"] == [4, 2] and row["pollen_N"] is None
    assert row["known_valid_pollen_cell_sum"] == 14
    assert len(row["datum_accounting"]) == 5


def test_all_measured_zero_panel_is_not_missing_or_a_composition() -> None:
    source, core, profile = native_fixture()
    for sample in native_samples(source):
        sample["datum"][0]["value"] = sample["datum"][1]["value"] = 0
    result = project(source, core, profile, lookup_fixture())
    assert all(
        r["status"] == "suppressed_zero_panel"
        and r["panel_N"] == 0
        and r["panel_counts"] == [0, 0]
        and r["pollen_N"] > 0
        for r in result["windows"]
    )
    assert result["samples"][0]["taxa"][0]["status"] == "measured_zero"


def test_legacy_literal_wrapper_matches_independent_old_packet_exactly() -> None:
    from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support.projection import (
        project as literal,
    )
    from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
        same,
    )
    from tests.source_completion.pollen_reconstruction.nordic_literal_window_support.fixtures import (
        fixture,
    )
    from tests.source_completion.pollen_reconstruction.nordic_literal_window_support.population import (
        expected_core,
    )

    for index in (0, 1):
        source, core, profile = fixture(index)
        same(literal(source, core, profile), expected_core(source, core, profile))


def test_projected_evidence_does_not_alias_source() -> None:
    source, core, profile = native_fixture()
    before = deepcopy(source)
    result = project(source, core, profile, lookup_fixture())
    result["samples"][0]["datum_accounting"][0]["native"]["value"] = 999
    result["samples"][0]["native_ages"][0]["age"] = 999
    assert source == before


@pytest.mark.parametrize("stomate_count", [0, 10**80, None, True])
def test_pollen_and_same_taxon_stomate_have_one_pollen_axis_owner(
    stomate_count: object,
) -> None:
    source, core, profile = native_fixture(1)
    sample = native_samples(source)[0]
    stomate = {
        **cell("Pinus", 385, stomate_count),
        "element": "stomate",
        "elementtype": "stomate",
    }
    sample["datum"].insert(1, stomate)
    before = deepcopy(source)
    result = project(source, core, profile, lookup_fixture())
    row = result["samples"][0]
    assert source == before
    assert row["taxa"][1]["status"] == "measured"
    assert row["taxa"][1]["native_matches"] == [
        {"datum_index": 2, "native": sample["datum"][2]}
    ]
    assert row["panel_counts"] == [4, 2]
    assert row["panel_N"] == 6 and row["pollen_N"] == 9
    assert row["excluded_pollen_N"] == 3
    assert result["windows"][0]["status"] == "supported"
    assert [r["native"] for r in row["datum_accounting"]] == sample["datum"]
    assert row["datum_accounting"][1]["disposition"] == "non_pollen"
    assert row["datum_accounting"][1]["author_target"] == "Pinus"
    assert row["datum_accounting"][1]["lookup_row_numbers"] == [4, 5]
    assert row["non_pollen_row_count"] == 2


def test_stomate_only_does_not_supply_pollen_count_or_zero() -> None:
    source, core, profile = native_fixture(1)
    sample = native_samples(source)[0]
    sample["datum"][1].update(element="stomate", elementtype="stomate")
    result = project(source, core, profile, lookup_fixture())
    row = result["samples"][0]
    assert row["taxa"][1]["status"] == "missing_native_axis"
    assert row["taxa"][1]["native_matches"] == []
    assert row["panel_counts"] == [4, None] and row["panel_N"] is None
    assert row["pollen_N"] == 7 and row["excluded_pollen_N"] is None
    assert row["datum_accounting"][1]["native"] == sample["datum"][1]
    assert row["datum_accounting"][1]["disposition"] == "non_pollen"
    assert result["windows"][0]["status"] == "suppressed_incomplete_panel"


@pytest.mark.parametrize("beside_pollen", [False, True])
@pytest.mark.parametrize(
    "roles",
    [
        {},
        {"element": "pollen"},
        {"elementtype": "pollen"},
        {"element": None, "elementtype": "pollen"},
        {"element": "stomate", "elementtype": "pollen"},
        {"element": "pollen", "elementtype": "stomate"},
        {"element": "stomate", "elementtype": "volume"},
        {"element": "", "elementtype": ""},
        {"element": " ", "elementtype": " "},
        {"element": 1, "elementtype": 1},
    ],
)
def test_uncertain_or_contradictory_roles_are_not_silently_ignored(
    roles: dict[str, object],
    beside_pollen: bool,
) -> None:
    source, core, profile = native_fixture(1)
    sample = native_samples(source)[0]
    malformed = cell("Pinus", 385, 100)
    malformed.pop("element")
    malformed.pop("elementtype")
    malformed.update(roles)
    if beside_pollen:
        sample["datum"].append(malformed)
    else:
        sample["datum"][1] = malformed
    row = project(source, core, profile, lookup_fixture())["samples"][0]
    assert row["taxa"][1]["status"] == (
        "duplicate_native_axis" if beside_pollen else "incompatible_metadata"
    )
    assert row["panel_counts"] == [4, None]
    assert row["panel_N"] is None
    assert row["datum_accounting"][-1 if beside_pollen else 1]["native"] == malformed


def test_true_pollen_duplicates_still_refuse_beside_stomate_context() -> None:
    source, core, profile = native_fixture(1)
    sample = native_samples(source)[0]
    sample["datum"].extend(
        [
            cell("Pinus", 385, 5),
            {
                **cell("Pinus", 385, 10**30),
                "element": "stomate",
                "elementtype": "stomate",
            },
        ]
    )
    result = project(source, core, profile, lookup_fixture())
    row = result["samples"][0]
    assert row["taxa"][1]["status"] == "duplicate_native_axis"
    assert [r["datum_index"] for r in row["taxa"][1]["native_matches"]] == [1, 4]
    assert row["pollen_N"] is None and row["panel_N"] is None
    assert row["datum_status_counts"]["duplicate_pollen_identity"] == 2
    assert row["datum_accounting"][5]["disposition"] == "non_pollen"
    assert result["windows"][0]["status"] == "suppressed_incomplete_panel"
