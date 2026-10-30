"""Literal source age/depth assignments survive projection and drawer rendering."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma as projection,
)

from ...evidence_projection.fixtures.neotoma import _neotoma_fixture
from ..support import run_node_json, template_block


def projected_tabs(root: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Use the existing source fixture and real compact-table producer."""
    _neotoma_fixture(root, monkeypatch)
    relational = root / "neotoma" / "relational"
    reader = cast(
        Callable[[Path], dict[str, object]],
        vars(projection)["read_validated_neotoma_relational_manifest"],
    )
    manifest = reader(relational)
    surfaces = cast(dict[str, dict[str, object]], manifest["surfaces"])
    path = relational / "surfaces/age_claims/part-00001.json"
    payload = json.loads(path.read_text())
    original = payload["rows"][0]
    alternative = original | {
        "chronology_claim_id": "neotoma:age-claim:40:2",
        "chronology_id": "neotoma:chronology:20:2",
        "chronology_name": "Uncalibrated <source>",
        "source_age_type": "Radiocarbon years BP",
        "source_age_value": None,
        "source_age_younger": -10,
        "source_age_older": 20,
        "younger_bp": None,
        "older_bp": None,
        "calibration_status": "uncalibrated",
        "comparability_status": "context_only",
        "is_default_chronology": False,
    }
    refused = original | {
        "chronology_claim_id": "neotoma:age-claim:40:3",
        "source_age_value": 0,
        "comparability_status": "refused",
        "refusal_reason": "<img src=x onerror=alert(1)>",
        "is_default_chronology": None,
    }
    payload = {"row_count": 3, "rows": [original, alternative, refused]}
    body = json.dumps(payload).encode()
    path.write_bytes(body)
    surface = surfaces["age_claims"]
    surface["row_count"] = 3
    cast(list[dict[str, object]], surface["parts"])[0]["sha256"] = hashlib.sha256(
        body
    ).hexdigest()
    records, _, _ = projection._project_neotoma(
        root, {"features": [{"evidence_row_id": "10"}]}
    )
    return cast(dict[str, object], records[0]["tabs"])


def diagram_script() -> str:
    """Actual packaged decoder, chart and drawer functions; no chart replacement."""
    return (
        template_block("const DETAIL_TAB_DEFINITIONS", "const DEFAULT_COUNTRIES")
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function detailTableShape", "function renderFocusCard")
        + template_block(
            "function createSourceRecordDetails", "/* atlas-evidence-tools:end */"
        )
        + """
const evidenceToolsError=null;
function currentEvidenceTools(){return {sourceDetails:createSourceRecordDetails}}
const boundSourceDetails=createSourceRecordDetails({detailTableShape,decodeDetailTableRow,detailTableText,
 renderDetailTable:(...args)=>renderDetailTable(...args),escapeHtml});
const {overview:renderSelectedSourceOverview,samples:renderSourceSampleObservations,
 classification:renderNativeClassificationContext,provenance:renderSourceProvenanceContext}=boundSourceDetails;
"""
    )


def render_drawer(
    tabs: dict[str, object], active: str = "chronology"
) -> dict[str, object]:
    return cast(
        dict[str, object],
        run_node_json(
            diagram_script()
            + """
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return [];}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false;},setAttribute(k,v){this[k]=v;},querySelectorAll(){return [];}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={};
const document={activeElement:null};
const detailTablePages=new Map(), DETAIL_TABLE_PAGE_SIZE=25;
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
const tabs="""
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const focusState={kind:'point',detailTabs:tabs};let activeFocusTab="
            + json.dumps(active)
            + ";renderFocusDetail();console.log(JSON.stringify({html:focusDetail.innerHTML,data:ageDepthDiagramData(tabs),unchanged:original===JSON.stringify(tabs),label:focusDetail['aria-labelledby']}));"
        ),
    )


def decoded(tabs: dict[str, object]) -> dict[str, object]:
    """Mutations below exercise decoded inputs without duplicating prefix logic."""
    return cast(
        dict[str, object],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";for(const table of [tabs.samples.samples,tabs.chronology]){table.records=table.records.map(row=>{const decoded=decodeDetailTableRow(table,row);return table.fields.map(field=>decoded[field]);});delete table.identifier_prefixes;delete table.column_dictionaries;}console.log(JSON.stringify(tabs));"
        ),
    )


def set_claim(
    tabs: dict[str, object], field: str, value: object, index: int = 0
) -> None:
    table = cast(dict[str, object], tabs["chronology"])
    fields = cast(list[str], table["fields"])
    cast(list[list[object]], table["records"])[index][fields.index(field)] = value


def set_sample(tabs: dict[str, object], field: str, value: object) -> None:
    table = cast(dict[str, object], cast(dict[str, object], tabs["samples"])["samples"])
    cast(list[list[object]], table["records"])[0][
        cast(list[str], table["fields"]).index(field)
    ] = value


def test_real_projection_decoder_and_drawer_retain_all_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    original = deepcopy(tabs)
    output = render_drawer(tabs)
    html = str(output["html"])
    # HTML tables include boolean button attributes, so parse only the SVG fragments.
    import re

    svgs = [ET.fromstring(svg) for svg in re.findall(r"<svg .*?</svg>", html)]
    assert len(svgs) == 3
    assert all(svg.get("viewBox") == "0 0 640 300" for svg in svgs)
    assert all(svg.get("role") == "img" for svg in svgs)
    assert all(
        svg.find("title") is not None and svg.find("desc") is not None for svg in svgs
    )
    assert sum(len(svg.findall("g")) for svg in svgs) == 3
    assert 'aria-label="neotoma:age-claim:40:1; sample neotoma:sample:40' in html
    assert "neotoma:collection-unit:20" in html and "neotoma:dataset:30" in html
    assert "neotoma:chronology:20:2" in html
    assert "3 of 3 claims" in html and "Showing 1–3 of 3" in html
    assert "No preferred chronology is selected" in html
    assert (
        "Source depth (unit not supplied)" in html and "Source depth (cm)" not in html
    )
    assert "not confidence intervals" in html and "not an interpolated curve" in html
    assert "<img" not in html and "Uncalibrated &lt;source&gt;" in html
    assert 'stroke-dasharray="2 3"' in html and 'stroke-dasharray="7 4"' in html
    assert "reported age point 0;" in html
    assert output["unchanged"] is True and output["label"] == "focus-tab-chronology"
    assert tabs == original
    assert "Source age–depth assignments" not in str(
        render_drawer(tabs, "overview")["html"]
    )


def test_interval_only_has_no_inferred_midpoint_and_default_shapes_are_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    output = render_drawer(tabs)
    data = cast(dict[str, object], output["data"])
    groups = cast(list[dict[str, object]], data["groups"])
    interval = next(
        group for group in groups if group["names"] == ["Uncalibrated <source>"]
    )
    rows = cast(list[dict[str, object]], interval["rows"])
    assert rows[0]["point"] is None and rows[0]["endpoints"] == [-10, 20]
    html = str(output["html"])
    import re

    span = next(
        svg
        for svg in re.findall(r"<svg .*?</svg>", html)
        if "reported endpoints -10, 20" in svg
    )
    tree = ET.fromstring(span)
    assert len(tree.findall("g/path")) == 1
    assert not tree.findall("g/circle") and not tree.findall("g/rect")
    assert "l5,5l-5,5l-5,-5z" in html  # Source-default diamond.
    assert "<rect " in html  # Null default flag is a square, not a selected model.
    set_claim(tabs, "source_age_value", -5, 1)
    assert "<circle " in str(render_drawer(tabs)["html"])


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("subject_type", "collection_unit", "non_sample_age_claim"),
        ("subject_id", "neotoma:sample:missing", "sample_depth_identity_unavailable"),
        ("source_record_id", "other", "sample_source_relation_mismatch"),
        ("collection_unit_id", "other", "sample_source_relation_mismatch"),
        ("dataset_id", "other", "sample_source_relation_mismatch"),
        ("chronology_id", None, "chronology_identity_unavailable"),
        ("source_age_value", None, "source_age_not_provided"),
        ("source_age_value", True, "source_age_not_numeric"),
        ("source_age_value", "125.5", "source_age_not_numeric"),
        ("source_age_younger", 0, "source_age_endpoint_missing"),
        ("is_default_chronology", 1, "source_default_flag_invalid"),
    ],
)
def test_unplotable_claims_are_counted_and_still_in_source_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    reason: str,
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_claim(tabs, field, value)
    output = render_drawer(tabs)
    data = cast(dict[str, object], output["data"])
    assert data["omitted"] == {reason: 1} and data["total"] == 3
    assert "Showing 1–3 of 3" in str(output["html"])
    assert output["unchanged"] is True


@pytest.mark.parametrize("depth", [None, True, "12 cm"])
def test_unknown_or_text_depth_does_not_become_centimetres(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, depth: object
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_sample(tabs, "source_depth", depth)
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert data["groups"] == [] and data["omitted"] == {"source_depth_not_numeric": 3}


@pytest.mark.parametrize(
    "field",
    [
        "chronology_id",
        "source_age_type",
        "source_age_unit",
        "calibration_status",
        "comparability_status",
    ],
)
def test_exact_source_bases_remain_separate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    # Match all other source properties of the first row, change only this basis.
    table = cast(dict[str, object], tabs["chronology"])
    rows = cast(list[list[object]], table["records"])
    rows[1] = rows[0].copy()
    set_claim(tabs, "chronology_claim_id", "alternative", 1)
    set_claim(tabs, field, "different", 1)
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert len(cast(list[object], data["groups"])) == 3


def test_duplicate_identities_and_bad_encoding_refuse_chart_without_hiding_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_claim(tabs, "chronology_claim_id", "neotoma:age-claim:40:1", 1)
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert data["omitted"] == {"ambiguous_claim_identity": 2}
    table = cast(dict[str, object], tabs["chronology"])
    table["record_count"] = 4
    output = render_drawer(tabs)
    assert cast(dict[str, object], output["data"])["status"] == "unavailable"
    assert "encoded_detail_table_invalid" in str(output["html"])


def test_large_group_has_bounded_marks_full_domain_and_all_table_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    table = cast(dict[str, object], tabs["chronology"])
    base = cast(list[list[object]], table["records"])[0]
    table["records"] = [base.copy() for _ in range(501)]
    table["record_count"] = 501
    for index in range(501):
        set_claim(tabs, "chronology_claim_id", f"claim-{index:03}", index)
        set_claim(tabs, "source_age_value", index, index)
    output = render_drawer(tabs)
    html = str(output["html"])
    assert html.count('<g role="img"') == 500
    assert "500 of 501 source claims drawn" in html
    assert "Showing 1–25 of 501" in html and ">500</text>" in html
    assert output["unchanged"] is True


def test_scale_preserves_signed_extremes_constant_zero_and_small_values() -> None:
    output = run_node_json(
        diagram_script()
        + "console.log(JSON.stringify([[-Number.MAX_VALUE,0,Number.MAX_VALUE],[0,0],[Number.MIN_VALUE,2*Number.MIN_VALUE]].map(values=>{const scale=ageDepthScale(values,85,500);return values.map(value=>scale.position(value));})));"
    )
    assert output == [[85, 335, 585], [335, 335], [85, 585]]


def test_distinct_dataset_depth_axes_are_not_merged_even_with_same_chronology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    table = cast(dict[str, object], cast(dict[str, object], tabs["samples"])["samples"])
    samples = cast(list[list[object]], table["records"])
    samples.append(samples[0].copy())
    table["record_count"] = 2
    fields = cast(list[str], table["fields"])
    samples[1][fields.index("sample_id")] = "other-sample"
    samples[1][fields.index("dataset_id")] = "other-dataset"
    samples[1][fields.index("source_depth")] = -100
    claims = cast(dict[str, object], tabs["chronology"])
    rows = cast(list[list[object]], claims["records"])
    rows[1] = rows[0].copy()
    for field, value in [
        ("chronology_claim_id", "other-claim"),
        ("subject_id", "other-sample"),
        ("source_record_id", "other-sample"),
        ("dataset_id", "other-dataset"),
    ]:
        set_claim(tabs, field, value, 1)
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert len(cast(list[object], data["groups"])) == 3
    # Ambiguous same-ID depth assignments cannot be silently picked.
    samples[1][fields.index("sample_id")] = samples[0][fields.index("sample_id")]
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert data["omitted"] == {"sample_depth_identity_unavailable": 3}


def test_chart_does_not_depend_on_map_zoom_or_time_filter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    output = run_node_json(
        diagram_script()
        + "const tabs="
        + json.dumps(tabs)
        + ";let zoom=4,timeStartBp=0;const map={getZoom:()=>zoom};const first=renderAgeDepthDiagram(tabs);zoom=18;timeStartBp=10000;console.log(JSON.stringify({same:first===renderAgeDepthDiagram(tabs),html:first}));"
    )
    assert output["same"] is True
    assert "3 of 3 claims" in output["html"]


def test_source_without_governed_sample_depth_tables_is_explicitly_unavailable() -> (
    None
):
    output = render_drawer(
        {
            "overview": {"source_family": "sead"},
            "chronology": {
                "status": "unavailable",
                "reason_code": "source_age_not_numeric",
            },
        }
    )
    assert "this source has no supported sample/depth tables" in str(output["html"])
    assert "source_age_not_numeric" in str(output["html"])
    assert "<svg" not in str(output["html"])


@pytest.mark.parametrize(
    ("younger", "older", "point", "reason"),
    [
        (20, -10, 0, "source_age_endpoints_reversed"),
        (-10, 20, -11, "source_age_point_outside_endpoints"),
        (-10, 20, 21, "source_age_point_outside_endpoints"),
        (-10, 20, -10, None),
        (-10, 20, 20, None),
    ],
)
def test_inconsistent_source_endpoints_are_not_repaired_into_uncertainty_spans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    younger: int,
    older: int,
    point: int,
    reason: str | None,
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    for field, value in [
        ("source_age_younger", younger),
        ("source_age_older", older),
        ("source_age_value", point),
    ]:
        set_claim(tabs, field, value)
    output = render_drawer(tabs)
    data = cast(dict[str, object], output["data"])
    assert data["omitted"] == ({} if reason is None else {reason: 1})
    assert "Showing 1–3 of 3" in str(output["html"])
    assert output["unchanged"] is True


@pytest.mark.parametrize("identity", [None, "", True, 40])
def test_invalid_matching_sample_keys_do_not_fabricate_a_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, identity: object
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_sample(tabs, "sample_id", identity)
    set_claim(tabs, "subject_id", identity)
    set_claim(tabs, "source_record_id", identity)
    data = cast(dict[str, object], render_drawer(tabs)["data"])
    assert data["groups"] == []
    assert data["omitted"] == {"sample_depth_identity_unavailable": 3}
