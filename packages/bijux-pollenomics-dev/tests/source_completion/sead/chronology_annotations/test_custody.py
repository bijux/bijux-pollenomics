"""Native chronology field, uncertainty, parent, method and reference refusal guards."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead import chronology_annotations as core


def fixture(
    kind: str = "dating_range",
) -> tuple[dict[str, Any], dict[str, dict[int, dict[str, Any]]]]:
    tables: dict[str, dict[int, dict[str, Any]]] = {
        name: {} for name in core.TABLE_KEYS
    }
    native: dict[str, Any] = {"dating_uncertainty_id": 1}
    if kind == "dating_range":
        native.update(
            analysis_dating_range_id=11,
            analysis_value_id=5,
            age_type_id=1,
            low_value=1845,
            high_value=None,
            low_is_uncertain=False,
            high_is_uncertain=True,
            low_qualifier="at least",
            high_qualifier="",
        )
    elif kind == "dendrochronology":
        native.update(
            dendro_date_id=11,
            analysis_entity_id=6,
            age_older=1845,
            age_younger=None,
            age_range=2,
            age_type_id=1,
            season_id=3,
            dendro_lookup_id=4,
        )
    elif kind == "relative_period":
        native.update(
            relative_date_id=11,
            analysis_entity_id=6,
            relative_age_id=19,
            method_id=3,
            notes="source text",
        )
    elif kind == "geochronology":
        native.update(
            geochron_id=11,
            analysis_entity_id=6,
            age=1000,
            error_older=50,
            error_younger=75,
            dating_lab_id=17,
            lab_number="lab",
            notes=None,
        )
    else:
        native = {
            "analysis_entity_age_id": 11,
            "analysis_entity_id": 6,
            "age": 1000,
            "age_older": 1010,
            "age_younger": 990,
            "age_range": None,
            "chronology_id": 44,
            "dating_specifier": "unresolved model",
        }
    table, key = core.SOURCES[kind]
    tables[table][11] = native
    tables["tbl_analysis_values"][5] = {"analysis_value_id": 5, "analysis_entity_id": 6}
    tables["tbl_analysis_entities"][6] = {
        "analysis_entity_id": 6,
        "physical_sample_id": 7,
        "dataset_id": 17,
    }
    tables["tbl_physical_samples"][7] = {"physical_sample_id": 7, "sample_group_id": 9}
    tables["tbl_sample_groups"][9] = {"sample_group_id": 9, "site_id": 8}
    tables["tbl_sites"][8] = {"site_id": 8, "site_uuid": "native-u"}
    tables["tbl_datasets"][17] = {"dataset_id": 17, "method_id": 3, "biblio_id": 4}
    tables["tbl_methods"][3] = {"method_id": 3, "method_name": "Source method"}
    tables["tbl_biblio"][4] = {"biblio_id": 4, "title": "Source reference"}
    tables["tbl_dating_uncertainty"][1] = {
        "dating_uncertainty_id": 1,
        "uncertainty": "From",
        "description": "Open-ended source qualifier",
    }
    for name, parent, identifier in [
        ("tbl_site_references", "site_id", 8),
        ("tbl_sample_group_references", "sample_group_id", 9),
        ("tbl_relative_age_refs", "relative_age_id", 19),
    ]:
        tables[name][1] = {core.TABLE_KEYS[name]: 1, parent: identifier, "biblio_id": 4}
    source = copy.deepcopy(native)
    source.update(
        analysis_entity_id=6, physical_sample_id=7, sample_group_id=9, dataset_id=17
    )
    if "dating_uncertainty_id" in native:
        source.update(
            uncertainty_label="From",
            uncertainty_description="Open-ended source qualifier",
        )
    if kind == "relative_period":
        source["method_name"] = "Source method"
    path = [
        {"table": t, "key": k, "value": v}
        for t, k, v in [
            ("tbl_sites", "site_id", "8"),
            ("tbl_sample_groups", "sample_group_id", 9),
            ("tbl_physical_samples", "physical_sample_id", 7),
            ("tbl_analysis_entities", "analysis_entity_id", 6),
            ("tbl_datasets", "dataset_id", 17),
        ]
    ]
    if kind == "dating_range":
        path.append(
            {"table": "tbl_analysis_values", "key": "analysis_value_id", "value": 5}
        )
    path.append({"table": table, "key": key, "value": 11})
    claim = {
        "claim_type": kind,
        "source_record_id": "11",
        "source_native_record_id": "11",
        "source_table": table,
        "source_age_value": source,
        "analysis_entity_id": 6,
        "analysis_value_id": 5 if kind == "dating_range" else None,
        "physical_sample_id": 7,
        "sample_group_id": 9,
        "dataset_id": 17,
        "source_site_id": "8",
        "site_uuid": "native-u",
        "source_relation_path": path,
        "selection_status": "retained_unselected",
        "propagation_eligibility": "refused",
        "calibration_status": {
            "dating_range": "not_applicable",
            "dendrochronology": "not_applicable",
            "relative_period": "not_calibrated",
            "geochronology": "unknown",
            "analysis_entity_age": "unknown",
        }[kind],
        "chronology_claim_id": "sead:native-u:" + kind + ":11",
    }
    return claim, tables


@pytest.mark.parametrize("kind", core.SOURCES)
def test_every_native_annotation_field_is_typed_and_bound(kind: str) -> None:
    claim, tables = fixture(kind)
    actual = core.audit_claim(claim, tables)
    assert actual["eligible_event"] is False
    assert actual["calibration_status"] == claim["calibration_status"]
    assert actual["dataset_method_name"] == "Source method"
    assert actual["reference_ids"]["dataset"] == [4]
    table, _ = core.SOURCES[kind]
    for field in tables[table][11]:
        altered = copy.deepcopy(claim)
        altered["source_age_value"][field] = ["changed"]
        try:
            observed = core.audit_claim(altered, tables)
        except ValueError:
            continue
        item = next(
            row for row in observed["field_comparisons"] if row["field"] == field
        )
        assert item["category"] != "exact"
        assert observed["raw_annotations"] == tables[table][11]
        assert observed["eligible_event"] is False
        del altered["source_age_value"][field]
        try:
            observed = core.audit_claim(altered, tables)
        except ValueError:
            continue
        item = next(
            row for row in observed["field_comparisons"] if row["field"] == field
        )
        assert item["category"] == "omitted"


@pytest.mark.parametrize(
    "field",
    [
        "analysis_entity_id",
        "analysis_value_id",
        "physical_sample_id",
        "sample_group_id",
        "dataset_id",
        "site_uuid",
        "source_site_id",
    ],
)
def test_other_physical_or_dataset_owner_refused(field: str) -> None:
    claim, tables = fixture()
    claim[field] = "another-owner"
    with pytest.raises(ValueError, match="differs"):
        core.audit_claim(claim, tables)


@pytest.mark.parametrize("field", ["uncertainty_label", "uncertainty_description"])
def test_uncertainty_lookup_does_not_follow_changed_display(field: str) -> None:
    claim, tables = fixture()
    claim["source_age_value"][field] = "different"
    observed = core.audit_claim(claim, tables)
    item = next(row for row in observed["lookup_comparisons"] if row["field"] == field)
    assert item["category"] == "text_value_changed"
    assert observed["eligible_event"] is False


@pytest.mark.parametrize(
    "kind,field,value",
    [
        ("dating_range", "low_is_uncertain", 0),
        ("dating_range", "high_is_uncertain", 1),
        ("dating_range", "high_value", 0),
        ("dendrochronology", "age_older", 1845.0),
    ],
)
def test_boolean_integer_float_and_null_values_do_not_collapse(
    kind: str, field: str, value: object
) -> None:
    claim, tables = fixture(kind)
    claim["source_age_value"][field] = value
    observed = core.audit_claim(claim, tables)
    item = next(row for row in observed["field_comparisons"] if row["field"] == field)
    assert item["category"] != "exact"
    assert observed["raw_annotations"] == tables[core.SOURCES[kind][0]][11]
    assert observed["eligible_event"] is False


@pytest.mark.parametrize(
    "table",
    [
        "tbl_analysis_entities",
        "tbl_physical_samples",
        "tbl_sample_groups",
        "tbl_sites",
        "tbl_datasets",
        "tbl_methods",
        "tbl_biblio",
        "tbl_dating_uncertainty",
    ],
)
def test_missing_native_owner_or_definition_refused(table: str) -> None:
    claim, tables = fixture()
    tables[table].clear()
    with pytest.raises(ValueError, match="Missing or invalid native parent"):
        core.audit_claim(claim, tables)


def test_nullable_native_method_and_bibliography_stay_unknown() -> None:
    claim, tables = fixture()
    tables["tbl_datasets"][17].update(method_id=None, biblio_id=None)
    tables["tbl_site_references"][1]["biblio_id"] = None
    result = core.audit_claim(claim, tables)
    assert result["dataset_method_id"] is None and result["dataset_method_name"] is None
    assert result["bibliography_status"] == "source_null"
    assert result["reference_ids"]["dataset"] == []
    assert result["reference_ids"]["site"] == [None]


def test_model_identifier_does_not_create_a_known_age_model() -> None:
    claim, tables = fixture("analysis_entity_age")
    result = core.audit_claim(claim, tables)
    assert result["source_chronology_id"] == 44
    assert result["calibration_status"] == "unknown" and not result["eligible_event"]


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, -1])
def test_invalid_native_identifier_cannot_bind_integer_row(value: object) -> None:
    with pytest.raises(ValueError, match="Invalid or duplicated native identifier"):
        core.index_rows([{"id": value}], "id")


def test_duplicate_native_identity_refused() -> None:
    with pytest.raises(ValueError, match="Invalid or duplicated native identifier"):
        core.index_rows([{"id": 1}, {"id": 1}], "id")


@pytest.mark.parametrize(
    "field,value",
    [
        ("calibration_status", "calibrated"),
        ("propagation_eligibility", "eligible"),
        ("selection_status", "selected"),
    ],
)
def test_annotation_custody_never_promotes_chronology_or_events(
    field: str, value: str
) -> None:
    claim, tables = fixture()
    claim[field] = value
    with pytest.raises(ValueError):
        core.audit_claim(claim, tables)


def test_direct_method_name_and_relation_order_are_bound() -> None:
    claim, tables = fixture("relative_period")
    claim["source_age_value"]["method_name"] = "inferred technique"
    result = core.audit_claim(claim, tables)
    assert (
        next(
            row for row in result["lookup_comparisons"] if row["field"] == "method_name"
        )["category"]
        == "text_value_changed"
    )
    assert result["eligible_event"] is False
    claim, tables = fixture()
    claim["source_relation_path"].reverse()
    with pytest.raises(ValueError, match="relation path"):
        core.audit_claim(claim, tables)


def test_other_native_claim_alias_cannot_share_correct_numeric_owner() -> None:
    claim, tables = fixture()
    claim["chronology_claim_id"] = "sead:another-site:dating_range:11"
    with pytest.raises(ValueError, match="composite chronology identity"):
        core.audit_claim(claim, tables)
