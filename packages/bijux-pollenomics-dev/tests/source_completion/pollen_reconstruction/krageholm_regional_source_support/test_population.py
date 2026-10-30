"""Complete-owner and aggregate-suppression controls without real native counts."""

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path

import pytest

from .fixtures import fixture, samples
from .population import expected_result
from .verification import decode, same, source_bytes


def test_complete_population_preserves_native_order_and_both_default_claims() -> None:
    source, protocol = fixture()
    before = deepcopy(source)
    result = expected_result(source, protocol)
    assert source == before
    assert result["population"] == {
        "samples": 96,
        "age_disposition_counts": {
            "negative_native_age_retained": 1,
            "outside_requested_windows": 1,
            "in_requested_window": 94,
        },
        "selected_age_status_counts": {"selected_typed_point": 96},
        "panel_complete_samples": 96,
        "full_mass_complete_samples": 96,
    }
    assert [row["sample_id"] for row in result["samples"]] == list(range(10000, 10096))
    assert result["chronology"]["native_collection_default_reference"] == 13365
    assert result["chronology"]["selected_chronology_id"] == 13366
    assert [
        row["native_metadata"]["isdefault"]
        for row in result["chronology"]["source_chronology_declarations"]
    ] == [True, True]
    assert result["source_totals"]["panel_counts"] == [384, 192]
    assert (
        result["source_totals"]["pollen_N"] == 864
        and result["source_totals"]["excluded_pollen_N"] == 288
    )
    assert [row["member_count"] for row in result["windows"]] == [
        15,
        15,
        16,
        16,
        16,
        16,
    ]
    assert all(row["status"] == "supported" for row in result["windows"])
    assert result["engine_calls"] == result["model_fits"] == 0


def test_one_unassignable_age_suppresses_every_window_without_losing_source_mass() -> (
    None
):
    source, protocol = fixture()
    samples(source)[0]["ages"].pop()
    result = expected_result(source, protocol)
    assert len(result["samples"]) == 96
    assert all(
        row["status"] == "suppressed_unassignable_age"
        and row["unassignable_source_sample_ids"] == [10000]
        and row["panel_N"] is None
        and row["pollen_N"] is None
        for row in result["windows"]
    )
    assert (
        result["source_totals"]["member_count"] == 96
        and result["source_totals"]["pollen_N"] == 864
    )
    assert result["source_totals"]["panel_N"] == 576


@pytest.mark.parametrize(
    "state,status",
    [
        ("incomplete_panel", "suppressed_incomplete_panel"),
        ("zero_panel", "suppressed_zero_panel"),
        ("incomplete_full", "suppressed_full_mass"),
        ("empty", "empty_window"),
    ],
)
def test_no_complete_case_window_subset_can_replace_its_whole_membership(
    state: str, status: str
) -> None:
    source, protocol = fixture()
    members = samples(source)
    if state == "incomplete_panel":
        members[6]["datum"].pop(0)
    elif state == "zero_panel":
        for row in members:
            if row["ages"][1]["age"] == 2700:
                row["datum"][0]["value"] = row["datum"][1]["value"] = 0
    elif state == "incomplete_full":
        members[6]["datum"][2]["units"] = "%"
    else:
        for row in members:
            row["ages"][1]["age"] = 5700
    result = expected_result(source, protocol)
    window = result["windows"][0]
    assert window["status"] == status
    assert window["member_count"] == (0 if state == "empty" else 15)
    if state == "incomplete_panel":
        assert window["panel_counts"] is None and window["pollen_N"] == 131
    elif state == "zero_panel":
        assert window["panel_counts"] == [0, 0] and window["pollen_N"] == 45
    elif state == "incomplete_full":
        assert window["panel_counts"] == [60, 30] and window["pollen_N"] is None


@pytest.mark.parametrize(
    "defect",
    [
        "sample_duplicate",
        "sample_bool",
        "sample_missing",
        "collection_default",
        "false_flag",
        "numeric_flag",
        "wrong_selected_name",
        "duplicate_declaration",
        "wrong_nested_dataset",
        "outer_decimal_dataset",
        "duplicate_owner",
    ],
)
def test_native_ownership_and_chronology_ambiguity_cannot_be_rewritten(
    defect: str,
) -> None:
    source, protocol = fixture()
    site = source["rows"][0]["site"]
    unit = site["collectionunit"]
    if defect == "sample_duplicate":
        samples(source)[1]["sampleid"] = samples(source)[0]["sampleid"]
    elif defect == "sample_bool":
        samples(source)[0]["sampleid"] = True
    elif defect == "sample_missing":
        samples(source).pop()
    elif defect == "collection_default":
        unit["defaultchronology"] = 13366
    elif defect == "false_flag":
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = False
    elif defect == "numeric_flag":
        unit["chronologies"][1]["chronology"]["chronology"]["isdefault"] = 1
    elif defect == "wrong_selected_name":
        unit["chronologies"][1]["chronology"]["chronology"]["chronologyname"] = (
            "Fossilva"
        )
    elif defect == "duplicate_declaration":
        unit["chronologies"].append(deepcopy(unit["chronologies"][1]))
    elif defect == "wrong_nested_dataset":
        unit["dataset"]["datasetid"] = 999
    elif defect == "outer_decimal_dataset":
        site["dataset"]["datasetid"] = Decimal("23013.0")
    else:
        source["rows"].append(deepcopy(source["rows"][0]))
    with pytest.raises(ValueError):
        expected_result(source, protocol)


def test_literal_json_keeps_count_token_types_and_rejects_duplicate_keys() -> None:
    value = decode(b'{"integer":4,"decimal":4.0,"flag":true,"null":null}')
    assert type(value["integer"]) is int and type(value["decimal"]) is Decimal
    assert type(value["flag"]) is bool and value["null"] is None
    with pytest.raises(ValueError):
        decode(b'{"value":4,"value":5}')
    with pytest.raises(ValueError):
        decode(b'{"value":NaN}')


@pytest.mark.parametrize("replacement", [True, 4.0, Decimal("4"), "4", None])
def test_result_comparison_cannot_relabel_integer_counts(replacement: object) -> None:
    with pytest.raises(ValueError):
        same({"count": replacement}, {"count": 4})
    same({"value": Decimal("3199.9999999999999")}, {"value": 3200.0})


def test_byte_reader_checks_both_identity_and_physical_aliases(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.json"
    body = b'{"synthetic":true}'
    path.write_bytes(body)
    pin = {"bytes": len(body), "sha256": sha256(body).hexdigest()}
    assert source_bytes(path, pin, 128) == body
    with pytest.raises(ValueError):
        source_bytes(path, {**pin, "sha256": "0" * 64}, 128)
    alias = tmp_path / "alias.json"
    alias.symlink_to(path)
    with pytest.raises(ValueError):
        source_bytes(alias, pin, 128)
    alias.unlink()
    os.link(path, alias)
    with pytest.raises(ValueError):
        source_bytes(path, pin, 128)
