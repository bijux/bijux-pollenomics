"""Current dictionary joins preserve raw unit tokens and whole-unit custody."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.reference_tables import (
    NeotomaReferenceTablePlan,
    capture_neotoma_reference_tables,
)
from bijux_pollenomics.collection.sources.neotoma.capture.unit_resources import (
    capture_neotoma_unit_resources,
)

from ..resources.native_payloads import response
from .test_capture import limits, prepared
from .test_profiles import payload


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.unit_resources.references"
    )


def dictionary() -> dict[str, Any]:
    return {
        "status": "success",
        "data": [
            {
                "variableunitsid": 37,
                "variableunits": "m",
                "recdatecreated": "native date",
                "recdatemodified": None,
            },
            {
                "variableunitsid": 38,
                "variableunits": "cm",
                "recdatecreated": "native date",
                "recdatemodified": None,
            },
        ],
    }


def fixture(
    root: Path,
    *,
    native: dict[str, Any] | None = None,
    reference: dict[str, Any] | None = None,
    protected: bool = False,
) -> dict[str, Any]:
    plan, roster, sources = prepared(root, protected=protected)
    unit_dir, reference_dir = root / "units", root / "reference"
    unit = capture_neotoma_unit_resources(
        unit_dir,
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda url, **k: response(
            url, json.dumps(payload() if native is None else native).encode()
        ),
    )
    reference_capture = capture_neotoma_reference_tables(
        reference_dir,
        plan=NeotomaReferenceTablePlan(("variableunits",)),
        fetch=lambda url, **k: response(
            url, json.dumps(dictionary() if reference is None else reference).encode()
        ),
    )
    return {
        "directory": unit_dir,
        "expected_manifest_sha256": unit.manifest_sha256,
        "collection_unit_id": 100,
        "roster_path": roster,
        "metadata_captures": sources,
        "reference_directory": reference_dir,
        "expected_reference_manifest_sha256": reference_capture.manifest_sha256,
        "limits": limits(),
    }


def resolve(settings: dict[str, Any]) -> dict[str, Any]:
    result = owner().resolve_neotoma_entrance_distance_reference(**settings)
    assert isinstance(result, dict)
    return result


def test_matching_current_reference_label_keeps_original_token_and_both_epochs(
    tmp_path: Path,
) -> None:
    settings = fixture(tmp_path)
    files = [
        p
        for name in ("directory", "reference_directory")
        for p in settings[name].iterdir()
    ]
    before = {p: p.read_bytes() for p in files}
    result = resolve(settings)
    assert result["source_capture_relabelled"] is False
    assert result["dictionary_rows"] == 2 and result["distinct_reference_ids"] == 2
    assert result["dictionary_completeness"] == "not_established"
    assert (
        result["unit_source"]["capture_manifest_sha256"]
        == settings["expected_manifest_sha256"]
    )
    assert (
        result["reference_source"]["capture_manifest_sha256"]
        == settings["expected_reference_manifest_sha256"]
    )
    assert result["reference_source"]["content_version"] == "current"
    assert result["reference_source"]["utc_start"]
    row = result["records"][0]
    assert row["raw_reference_token"] == 37
    assert row["reference_resolution_status"] == "resolved_current_reference_label"
    assert row["reference_native_row"]["variableunits"] == "m"
    assert row["native_record_pointer"] == "/data/0/speleothem"
    assert row["reference_record_pointer"] == "/data/0"
    assert (
        result["source_intended_reference_binding"]["deployed_version_equivalence"]
        == "not_established"
    )
    assert result["physical_measurement_unit_admission"] == "not_asserted"
    assert result["unit_inheritance_to_other_fields"] is False
    assert before == {p: p.read_bytes() for p in files}


@pytest.mark.parametrize(
    "token,expected",
    [
        (None, "unavailable_explicit_null_reference"),
        (999, "unavailable_reference_token_not_returned"),
        (38, "resolved_current_reference_label"),
    ],
)
def test_null_missing_and_other_native_ids_never_substitute_token37(
    tmp_path: Path, token: object, expected: str
) -> None:
    value = payload()
    value["data"][0]["speleothem"]["entrancedistanceunits"] = token
    result = resolve(fixture(tmp_path, native=value))
    row = result["records"][0]
    assert (
        row["raw_reference_token"] == token
        and row["reference_resolution_status"] == expected
    )
    assert row["absence_certified"] is False
    if token == 38:
        assert row["reference_native_row"]["variableunits"] == "cm"
    else:
        assert "reference_native_row" not in row


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate_selected",
        "duplicate_unselected",
        "bool_id",
        "fractional_id",
        "string_id",
        "missing_id",
        "missing_label",
        "null_label",
        "foreign_table",
        "missing_date",
        "source_failure",
        "unknown_wrapper",
    ],
)
def test_whole_dictionary_population_must_be_native_unique_and_exactly_owned(
    tmp_path: Path, damage: str
) -> None:
    value = dictionary()
    row = value["data"][0]
    if damage == "duplicate_selected":
        value["data"].append(dict(row))
    elif damage == "duplicate_unselected":
        value["data"].append(dict(value["data"][1]))
    elif damage == "bool_id":
        row["variableunitsid"] = True
    elif damage == "fractional_id":
        row["variableunitsid"] = 37.2
    elif damage == "string_id":
        row["variableunitsid"] = "37"
    elif damage == "missing_id":
        del row["variableunitsid"]
    elif damage == "missing_label":
        del row["variableunits"]
    elif damage == "null_label":
        row["variableunits"] = None
    elif damage == "foreign_table":
        value["data"] = [{"geopoliticalid": 37, "geopoliticalname": "m"}]
    elif damage == "missing_date":
        del row["recdatecreated"]
    elif damage == "source_failure":
        value["status"] = "failure"
    else:
        value["data"] = [{"variableunit": row}]
    settings = fixture(tmp_path, reference=value)
    with pytest.raises(ValueError):
        resolve(settings)


@pytest.mark.parametrize(
    "damage",
    ["foreign_unit", "foreign_site", "bool_token", "fractional_token", "missing_token"],
)
def test_reference_lookup_never_bypasses_native_unit_ownership(
    tmp_path: Path, damage: str
) -> None:
    value = payload()
    row = value["data"][0]["speleothem"]
    if damage == "foreign_unit":
        row["collectionunitid"] = 101
    elif damage == "foreign_site":
        row["siteid"] = 13
    elif damage == "bool_token":
        row["entrancedistanceunits"] = True
    elif damage == "fractional_token":
        row["entrancedistanceunits"] = 37.9
    else:
        del row["entrancedistanceunits"]
    settings = fixture(tmp_path, native=value)
    with pytest.raises(ValueError):
        resolve(settings)


def test_protected_whole_unit_refuses_before_any_numerical_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = fixture(tmp_path, protected=True)
    original = Path.open

    def guard(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.suffix != ".body" or path.parent not in {
            settings["directory"],
            settings["reference_directory"],
        }, "protected unit or reference body opened"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(ValueError):
        resolve(settings)


@pytest.mark.parametrize(
    "key", ["expected_manifest_sha256", "expected_reference_manifest_sha256"]
)
def test_both_explicit_source_capture_hashes_are_enforced(
    tmp_path: Path, key: str
) -> None:
    settings = fixture(tmp_path)
    settings[key] = "0" * 64
    with pytest.raises(ValueError):
        resolve(settings)


def test_every_received_native_join_variant_has_its_own_reference_locator(
    tmp_path: Path,
) -> None:
    value = payload()
    second = dict(value["data"][0]["speleothem"])
    second["entrancedistanceunits"] = 38
    value["data"].append({"speleothem": second})
    result = resolve(fixture(tmp_path, native=value))
    assert [r["raw_reference_token"] for r in result["records"]] == [37, 38]
    assert [r["native_record_pointer"] for r in result["records"]] == [
        "/data/0/speleothem",
        "/data/1/speleothem",
    ]
