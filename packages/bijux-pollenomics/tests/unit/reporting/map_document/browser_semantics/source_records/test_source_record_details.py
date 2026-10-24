"""Actual native relationships reach overview and paginated observation tables."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection import neotoma
from tests.support.neotoma.relational_shapes import nested, rows

from ...evidence_projection.test_neotoma_chronology_models import (
    materialized,
    native_source,
)
from ..chronology.test_age_depth_diagram import diagram_script
from ..support import check_javascript_syntax, run_node_json


@pytest.fixture
def source(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    native = native_source()
    sample = rows(nested(native, "site", "collectionunit", "dataset")["samples"])[0]
    rows(sample["datum"])[0]["value"] = 3
    rows(sample["ages"])[0].update(age=0, ageyounger=0, ageolder=0)
    tabs, _ = materialized(tmp_path, native)
    _, _, layers = neotoma._project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    feature = next(
        feature
        for layer in layers
        for feature in cast(list[dict[str, Any]], layer["features"])
        if feature["node_level"] == "source_taxon"
    )
    return tabs, feature


def script() -> str:
    return diagram_script()


def observe(
    source: tuple[dict[str, Any], dict[str, Any]], expression: str = "null"
) -> dict[str, Any]:
    tabs, feature = source
    return cast(
        dict[str, Any],
        run_node_json(
            script()
            + "const tabs="
            + json.dumps(tabs)
            + ",feature="
            + json.dumps(feature)
            + ";const original=JSON.stringify([tabs,feature]);const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;"
            + "const extra="
            + expression
            + ";console.log(JSON.stringify({overview:renderSelectedSourceOverview(tabs,feature),observations:renderSourceSampleObservations(tabs),extra,unchanged:original===JSON.stringify([tabs,feature])}));"
        ),
    )


def fields(html: str) -> dict[str, str]:
    return {
        str(row.find("span").text): " ".join(list(row)[1].itertext())  # type: ignore[union-attr]
        for row in ET.fromstring(html).findall("div")
    }


def test_actual_native_projection_and_feature_join_all_source_relations(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    tabs, feature = source
    original = deepcopy(source)
    output = observe(source)
    overview = ET.fromstring(output["overview"])
    assert overview.get("data-source-record-details") == "matched"
    values = fields(output["overview"])
    assert values["Native sample ID"] == feature["source_record_id"]
    assert values["Native dataset ID"] == "neotoma:dataset:201"
    assert values["Native collection-unit ID"] == "neotoma:collection-unit:301"
    assert values["Map age claim ID"] == feature["chronology_claim_id"]
    assert values["Map chronology ID"] == "neotoma:chronology:301:7001"
    assert values["Source measurement unit"] == "NISP"
    assert values["Source age unit"] == "year"
    assert values["Source age value"] == "0"
    assert values["Source younger endpoint"] == values["Source older endpoint"] == "0"
    assert (
        values["Map source-default assertion"]
        == values["Age-claim default flag"]
        == "true"
    )
    assert values["Source chronology selection posture"] == "selected_source_default"
    assert values["Candidate-generation status"] == "refused"
    assert values["Propagation eligible"] == "false"
    assert values["Age refusal reason"] == "null (source null)"
    assert "do not select an analysis chronology" in output["overview"]
    assert tabs["chronology"]["record_count"] == 2
    assert source == original and output["unchanged"]


def test_overview_preserves_coordinate_zero_nulls_and_distinct_source_flags(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    source[1].update(
        latitude=0,
        longitude=-0.25,
        coordinate_quality=None,
        is_default_chronology=False,
    )
    output = observe(source)
    values = fields(output["overview"])
    assert values["Latitude"] == "0" and values["Longitude"] == "-0.25"
    assert values["Coordinate quality"] == "null (source null)"
    assert "not a numerical uncertainty estimate" in output["overview"]
    assert values["Map source-default assertion"] == "false"
    assert values["Age-claim default flag"] == "true"
    assert output["unchanged"]


@pytest.mark.parametrize(
    "field", ["record_id", "source_snapshot_id", "build_id", "source_record_id"]
)
def test_missing_or_foreign_source_identity_never_selects_a_default(
    source: tuple[dict[str, Any], dict[str, Any]], field: str
) -> None:
    source[1][field] = "foreign"
    output = observe(source)
    assert (
        ET.fromstring(output["overview"]).get("data-source-record-details")
        == "unavailable"
    )
    assert output["unchanged"]


@pytest.mark.parametrize("table", ["samples", "datasets", "collection_units"])
def test_ambiguous_native_parent_relations_are_unavailable(
    source: tuple[dict[str, Any], dict[str, Any]], table: str
) -> None:
    target = source[0]["samples"][table]
    target["records"].append(deepcopy(target["records"][0]))
    target["record_count"] += 1
    output = observe(source)
    assert (
        ET.fromstring(output["overview"]).get("data-source-record-details")
        == "unavailable"
    )
    assert output["unchanged"]


@pytest.mark.parametrize(
    "field",
    [
        "subject_id",
        "source_record_id",
        "dataset_id",
        "collection_unit_id",
        "chronology_id",
    ],
)
def test_claim_must_join_the_same_sample_dataset_unit_and_model(
    source: tuple[dict[str, Any], dict[str, Any]], field: str
) -> None:
    output = observe(
        source,
        "(()=>{const table=tabs.chronology;table.records=table.records.map(r=>{const row=decodeDetailTableRow(table,r);if(row.chronology_claim_id===feature.chronology_claim_id)row["
        + json.dumps(field)
        + "]='foreign';return table.fields.map(f=>row[f]);});delete table.identifier_prefixes;return renderSelectedSourceOverview(tabs,feature);})()",
    )
    assert (
        ET.fromstring(output["extra"]).get("data-source-record-details") == "unmatched"
    )
    assert "no exact unique" in output["extra"]


def test_duplicate_claim_and_source_refusal_remain_explicit(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    output = observe(
        source,
        "(()=>{const t=tabs.chronology;const row=t.records.find(r=>decodeDetailTableRow(t,r).chronology_claim_id===feature.chronology_claim_id);t.records.push([...row]);t.record_count++;const duplicate=renderSelectedSourceOverview(tabs,feature);t.records.pop();t.record_count--;row[t.fields.indexOf('comparability_status')]='refused';row[t.fields.indexOf('refusal_reason')]='source calibration refused';return {duplicate,refused:renderSelectedSourceOverview(tabs,feature)};})()",
    )["extra"]
    assert (
        ET.fromstring(output["duplicate"]).get("data-source-record-details")
        == "unmatched"
    )
    assert (
        ET.fromstring(output["refused"]).get("data-source-record-details") == "refused"
    )
    assert "source calibration refused" in output["refused"]


def test_samples_reuses_original_observation_table_units_and_nulls(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    output = observe(source)
    html = output["observations"]
    assert "NISP" in html and "grains/cm3" in html
    assert "not_provided_by_source" in html and "null (source null)" in html
    assert source[1]["source_record_id"] in html
    assert "reported_value" in html and "No cross-unit sum" in html
    assert 'data-detail-table-page="samples.observations"' in html
    assert "Showing 1–2 of 2" in html
    assert output["unchanged"]


def test_observation_pagination_uses_existing_table_without_mutation(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    table = source[0]["pollen_composition"]
    for index in range(28):
        row = deepcopy(table["records"][0])
        row[table["fields"].index("observation_id")] = f"observation-{index}"
        row[table["fields"].index("source_value")] = 0 if index == 27 else None
        row[table["fields"].index("detection_status")] = (
            "source_null" if index != 27 else "reported_value"
        )
        table["records"].append(row)
    table["record_count"] = len(table["records"])
    output = observe(
        source,
        "(()=>{detailTablePages.set('samples.observations',1);return renderSourceSampleObservations(tabs);})()",
    )
    assert "Showing 26–30 of 30" in output["extra"]
    assert "null (source null)" in output["extra"] and ">0</td>" in output["extra"]
    assert "source_null" in output["extra"] and output["unchanged"]


def test_unsupported_sources_and_missing_tables_are_named_unavailable(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    output = observe(
        source,
        "(()=>{const other={overview:{source_family:'sead'}};return [renderSelectedSourceOverview(other,feature),renderSourceSampleObservations(other),renderSourceSampleObservations({overview:{source_family:'neotoma'}})];})()",
    )
    assert "Neotoma source features only" in output["extra"][0]
    assert "source family sead" in output["extra"][1]
    assert "Neotoma sample observation values" in output["extra"][2]
    assert output["unchanged"]


def test_source_labels_escape_and_packaged_helpers_parse(
    source: tuple[dict[str, Any], dict[str, Any]], tmp_path: Path
) -> None:
    source[1]["chronology_name"] = '<img src=x onerror="bad">'
    source[1]["candidate_refusal_reason"] = "<source refusal>"
    output = observe(source)
    assert ET.fromstring(output["overview"]).find(".//img") is None
    assert "&lt;source refusal&gt;" in output["overview"]
    assert output["unchanged"]
    check_javascript_syntax(script(), tmp_path / "source-record-details.js")


@pytest.mark.parametrize("mode", ["missing_claim", "unavailable_claims"])
def test_missing_claim_never_substitutes_another_source_default(
    source: tuple[dict[str, Any], dict[str, Any]], mode: str
) -> None:
    if mode == "missing_claim":
        source[1]["chronology_claim_id"] = "foreign-claim"
    else:
        source[0]["chronology"] = {"status": "unavailable"}
    output = observe(source)
    assert (
        ET.fromstring(output["overview"]).get("data-source-record-details")
        == "unmatched"
    )
    assert "Age-claim default flag" not in output["overview"]
    assert output["unchanged"]


def test_missing_epoch_on_both_sides_does_not_authenticate_a_source(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    del source[0]["provenance"]["source_snapshot_id"]
    del source[1]["source_snapshot_id"]
    output = observe(source)
    assert (
        ET.fromstring(output["overview"]).get("data-source-record-details")
        == "unavailable"
    )
    assert output["unchanged"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 91),
        ("longitude", -181),
        ("latitude", True),
        ("longitude", "0"),
        ("latitude", None),
        ("latitude", float("inf")),
        ("longitude", float("nan")),
    ],
)
def test_invalid_representative_coordinates_remain_unavailable(
    source: tuple[dict[str, Any], dict[str, Any]], field: str, value: object
) -> None:
    source[1][field] = value
    output = observe(source)
    assert (
        ET.fromstring(output["overview"]).get("data-source-record-details")
        == "unavailable"
    )
    assert "representative coordinates" in output["overview"]
    assert output["unchanged"]


def test_actual_drawer_mounts_selected_overview_and_pages_sample_observations(
    source: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    tabs, feature = source
    table = tabs["pollen_composition"]
    for index in range(28):
        row = deepcopy(table["records"][0])
        row[table["fields"].index("observation_id")] = f"additional-{index}"
        row[table["fields"].index("source_value")] = None if index < 27 else 0
        row[table["fields"].index("detection_status")] = (
            "source_null" if index < 27 else "reported_value"
        )
        table["records"].append(row)
    table["record_count"] = len(table["records"])
    output = run_node_json(
        script()
        + "const tabs="
        + json.dumps(tabs)
        + ",feature="
        + json.dumps(feature)
        + r""";
const before=JSON.stringify([tabs,feature]),callbacks={};
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return ['overview','samples'].map(key=>({dataset:{focusTab:key},addEventListener(event,cb){callbacks[key]=cb;}}));}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false;},setAttribute(){},querySelectorAll(selector){
  if(selector!=='[data-detail-table-page]')return [];
  return [...this.innerHTML.matchAll(/data-detail-table-page="([^"]+)" data-page-direction="([^"]+)"/g)].map(match=>({dataset:{detailTablePage:match[1],pageDirection:match[2]},disabled:false,focus(){},addEventListener(event,cb){callbacks[match[1]+':'+match[2]]=cb;}}));
}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
let focusState={kind:'point',sourceSignal:feature,detailTabs:tabs},activeFocusTab='overview';
renderFocusDetail();const overview=focusDetail.innerHTML;
callbacks.samples();const samples=focusDetail.innerHTML;
callbacks['samples.observations:next']();const next=focusDetail.innerHTML;
callbacks.overview();const returnedOverview=focusDetail.innerHTML;
callbacks.samples();const returnedSamples=focusDetail.innerHTML;
focusState={...focusState,sourceSignal:{...feature,source_snapshot_id:'foreign'}};
callbacks.overview();
console.log(JSON.stringify({overview,samples,next,returnedOverview,returnedSamples,foreign:focusDetail.innerHTML,unchanged:before===JSON.stringify([tabs,feature])}));
"""
    )
    assert 'data-source-record-details="matched"' in output["overview"]
    assert (
        "Source age value" in output["overview"] and ">0</span>" in output["overview"]
    )
    assert "Candidate-generation status" in output["overview"]
    assert output["overview"] == output["returnedOverview"]
    assert "Showing 1–25 of 30" in output["samples"]
    assert "NISP" in output["samples"] and "grains/cm3" in output["samples"]
    assert "Showing 26–30 of 30" in output["next"]
    assert "source_null" in output["next"] and ">0</td>" in output["next"]
    assert output["next"] == output["returnedSamples"]
    assert 'data-source-record-details="unavailable"' in output["foreign"]
    assert 'data-source-record-details="matched"' not in output["foreign"]
    assert output["unchanged"]
