"""Readers distinguish retained date variants and unsupported default references."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from ..chronology.test_age_depth_diagram import diagram_script, render_drawer
from ..support import run_node_json


def review(action: str = "") -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + r"""
const table=(fields,records)=>({fields,records,record_count:records.length});
const tabs={overview:{source_family:'neotoma'},chronology:{
 models:table(['chronology_id','selected_by_collection_unit_reference','effective_reference_selected','reference_verification_status'],[['unknown',true,false,'refused_missing_source_identifier']]),
 source_issues:{conflicts:table(['conflict_id'],[['c1']]),orphans:table(['orphan_id'],[['o1']]),chronology_control_variants:table(['conflict_id','variant_index'],[['c1',0],['c1',1]])},
}};
"""
            + action
            + r"""
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const original=JSON.stringify(tabs);
const html=boundSourceDetails.chronology?.(tabs) ?? null;
console.log(JSON.stringify({html,tabs,unchanged:original===JSON.stringify(tabs)}));
"""
        ),
    )


def test_visible_review_explains_constituents_and_missing_reference() -> None:
    observed = review()
    assert observed["unchanged"] is True
    html = observed["html"]
    assert isinstance(html, str)
    for text in (
        "Source chronology review",
        "2 constituent dated-specimen variants",
        "1 model lacks an identified native reference",
        "does not select a specimen",
        "Original projection flags",
        "download",
    ):
        assert text in html


def test_missing_review_surface_is_unavailable_without_zero_issue_inference() -> None:
    observed = review("delete tabs.chronology.source_issues;")
    assert observed["unchanged"] is True
    assert 'data-source-chronology-review="unavailable"' in str(observed["html"])
    assert "does not establish that no source issues exist" in str(observed["html"])


def test_reference_caveat_precedes_raw_chronology_tables_in_actual_drawer() -> None:
    rendered = render_drawer(cast(dict[str, object], review()["tabs"]))
    html = str(rendered["html"])
    assert html.index("Source chronology review") < html.index("<table")
    assert rendered["unchanged"] is True


def paged_reader(
    tabs: dict[str, object],
    actions: list[str],
    *,
    table_path: str = "chronology.source_issues.chronology_control_variants",
) -> dict[str, Any]:
    """Run the production drawer and its actual pager callbacks against DOM sinks."""
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + r"""
const focusTabs={innerHTML:'',contains(){return false},querySelectorAll(){return []}};
let buttons=[];
const focusDetail={innerHTML:'',dataset:{},contains(){return false},setAttribute(){},
 querySelectorAll(selector){
  if(selector!=='[data-detail-table-page]')return [];
  buttons=[...this.innerHTML.matchAll(/<button[^>]*data-detail-table-page="([^"]+)"[^>]*data-page-direction="([^"]+)"[^>]*>/g)].map(match=>({
   dataset:{detailTablePage:match[1],pageDirection:match[2]},disabled:/ disabled(?:[ >])/.test(match[0]),
   addEventListener(event,callback){this.click=callback},focus(){},
  }));return buttons;
 }};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={};
const COUNTRIES=['Sweden'],activeCountries=new Set(COUNTRIES),document={activeElement:null};
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
function sourcePollenExportAvailable(){return false}
function syncHashState(){}
const tabs="""
            + json.dumps(tabs)
            + ";const actions="
            + json.dumps(actions)
            + ";const tablePath="
            + json.dumps(table_path)
            + r""";
const original=JSON.stringify(tabs),focusState={kind:'point',detailTabs:tabs};let activeFocusTab='chronology';
renderFocusDetail();const snapshots=[focusDetail.innerHTML];
for(const direction of actions){
 const button=buttons.find(node=>node.dataset.detailTablePage===tablePath&&node.dataset.pageDirection===direction);
 if(!button||button.disabled)throw Error('Required variant page action unavailable');
 button.click();snapshots.push(focusDetail.innerHTML);
}
console.log(JSON.stringify({snapshots,unchanged:original===JSON.stringify(tabs),pages:[...detailTablePages]}));
"""
        ),
    )


def test_actual_drawer_decodes_and_pages_native_issue_variants() -> None:
    tabs = cast(dict[str, Any], review()["tabs"])
    variants = tabs["chronology"]["source_issues"]["chronology_control_variants"]
    variants.update(
        {
            "fields": [
                "conflict_id",
                "variant_index",
                "source_record",
                "source_locator",
            ],
            "record_count": 30,
            "records": [
                [
                    0,
                    index,
                    {
                        "geochronid": 35606 + index,
                        "age": index,
                        "material": "<source & peat>",
                    },
                    index,
                ]
                for index in range(30)
            ],
            "column_dictionaries": {
                "conflict_id": ["c1"],
                "source_locator": [f"native-locator-{index}" for index in range(30)],
            },
        }
    )
    observed = paged_reader(tabs, ["next", "previous"])
    first, second, returned = observed["snapshots"]
    assert observed["unchanged"] is True
    assert first.index("Source chronology review") < first.index("<table")
    assert first.count('<table class="focus-detail-table">') == 4
    assert "Showing 1–25 of 30" in first and "native-locator-24" in first
    assert "native-locator-25" not in first
    assert "Showing 26–30 of 30" in second and "native-locator-29" in second
    assert "native-locator-0" not in second
    assert returned == first
    assert "&lt;source &amp; peat&gt;" in first and "<source & peat>" not in first
    assert "&quot;chronology_control_variants&quot;" not in first
    assert observed["pages"] == [
        ["chronology.source_issues.chronology_control_variants", 0]
    ]


@pytest.mark.parametrize(
    "damage", ["count", "duplicate_field", "row_width", "missing", "unavailable"]
)
def test_malformed_or_absent_issue_tables_do_not_claim_zero_issues(damage: str) -> None:
    tabs = cast(dict[str, Any], review()["tabs"])
    issues = tabs["chronology"]["source_issues"]
    variants = issues["chronology_control_variants"]
    if damage == "count":
        variants["record_count"] += 1
    elif damage == "duplicate_field":
        variants["fields"].append("conflict_id")
    elif damage == "row_width":
        variants["records"][0].pop()
    elif damage == "missing":
        del issues["chronology_control_variants"]
    else:
        issues["chronology_control_variants"] = {
            "status": "unavailable",
            "reason_code": "legacy_surface_missing",
        }
    html = str(render_drawer(tabs)["html"])
    assert 'data-source-chronology-review="unavailable"' in html
    assert "does not establish that no source issues exist" in html
    assert "0 retained conflict records" not in html
    assert "&quot;chronology_control_variants&quot;" not in html


def test_legacy_default_flag_is_not_promoted_to_verified_reference_or_preference() -> (
    None
):
    tabs = cast(dict[str, Any], review()["tabs"])
    models = tabs["chronology"]["models"]
    models["fields"].append("source_chronology_id")
    models["records"][0].append(None)
    fields = [
        "chronology_claim_id",
        "subject_type",
        "subject_id",
        "source_record_id",
        "collection_unit_id",
        "dataset_id",
        "chronology_id",
        "chronology_name",
        "source_age_type",
        "source_age_unit",
        "source_age_value",
        "source_age_younger",
        "source_age_older",
        "calibration_status",
        "comparability_status",
        "refusal_reason",
        "is_default_chronology",
        "source_chronology_id",
    ]
    tabs["samples"] = {
        "samples": {
            "fields": ["sample_id", "collection_unit_id", "dataset_id", "source_depth"],
            "records": [["sample:one", "unit:one", "dataset:one", 1]],
            "record_count": 1,
        }
    }
    tabs["chronology"].update(
        {
            "fields": fields,
            "records": [
                [
                    "claim:one",
                    "sample",
                    "sample:one",
                    "sample:one",
                    "unit:one",
                    "dataset:one",
                    "unknown",
                    "Legacy unknown",
                    "Calibrated years BP",
                    "years BP",
                    0,
                    0,
                    0,
                    "calibrated",
                    "comparable",
                    "",
                    True,
                    None,
                ]
            ],
            "record_count": 1,
        }
    )
    html = str(render_drawer(tabs)["html"])
    assert "1 model lacks an identified native reference" in html
    assert "retained default flag: true" in html
    assert "not a verified collection reference or a preferred chronology" in html
    assert "source-default" not in html
    assert "l5,5l-5,5l-5,-5z" in html
    assert render_drawer(tabs)["unchanged"] is True
