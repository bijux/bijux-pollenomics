"""Complete downloads retain issue records and every dated-specimen variant."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from ..support import run_node_json
from .test_source_record_export import source_export_script


def export_issues(action: str = "") -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            source_export_script()
            + r"""
const table=(fields,records)=>({fields,records,record_count:records.length});
const variant={geochronid:35606,age:0,ageerror:null,material:'soluble humus'};
const issues={
 semantics:'Retained native source issues, not new observations or date selection.',
 control_multiplicity_contract:{key:['chroncontrolid','geochronid'],adjudicated:false},
 canonical_control_posture:'All constituent variants retained; canonical serialization does not select a date.',
 conflicts:{...table(['conflict_id','source_record'],[['c1',{detail:{variants:[variant]}}]]),source_locator_contract:'conflicts#{conflict_id}'},
 orphans:table(['orphan_id','source_record'],[['o1',{source_value:null,reason:'missing_source_identifier'}]]),
 chronology_control_variants:{...table(['conflict_id','variant_index','source_record'],[['c1',0,variant],['c1',1,{...variant,geochronid:35607,age:440,material:'lake mud'}]]),source_locator_contract:'conflicts#{conflict_id}/detail/variants/{variant_index}'},
};
const tabs={overview:{source_family:'neotoma'},samples:{samples:table(['sample_id'],[['s1']])},
 chronology:{...table(['comparability_status'],[['comparable']]),source_issues:issues},
 pollen_composition:table(['sample_id','source_value','source_unit'],[['s1',1,'NISP']]),provenance:{build_id:'retained'}};
const decodeRow=(table,row)=>Object.fromEntries(table.fields.map((field,index)=>[field,row[index]]));
"""
            + action
            + r"""
const original=JSON.stringify(tabs);
let result,quality,temporalSupport,error;
try { const exported=buildSourcePollenRecordExport({kind:'point',recordId:'neotoma:site:12',detailTabs:tabs},{},decodeRow); result=exported.source_chronology_issues; quality=exported.source_chronology_quality; temporalSupport=exported.temporal_support; }
catch(observed){error=String(observed.message)}
console.log(JSON.stringify({result,quality,temporalSupport,error,unchanged:original===JSON.stringify(tabs)}));
"""
        ),
    )


def test_download_retains_every_variant_and_issue_owner_without_adjudication() -> None:
    observed = export_issues()
    assert observed["unchanged"] is True
    result = observed["result"]
    assert isinstance(result, dict)
    assert result["control_multiplicity_contract"] == {
        "key": ["chroncontrolid", "geochronid"],
        "adjudicated": False,
    }
    assert result["conflicts"]["records"][0]["source_record"]["detail"]["variants"][
        0
    ] == {"geochronid": 35606, "age": 0, "ageerror": None, "material": "soluble humus"}
    variants = result["chronology_control_variants"]
    assert variants["record_count"] == 2
    assert [row["variant_index"] for row in variants["records"]] == [0, 1]
    assert [row["source_record"]["age"] for row in variants["records"]] == [0, 440]
    assert variants["source_locator_contract"].endswith(
        "/detail/variants/{variant_index}"
    )
    assert result["orphans"]["records"][0]["source_record"]["source_value"] is None


@pytest.mark.parametrize(
    "surface", ["conflicts", "orphans", "chronology_control_variants"]
)
def test_download_refuses_inconsistent_issue_tables(surface: str) -> None:
    observed = export_issues("issues[" + json.dumps(surface) + "].record_count += 1;")
    assert "table" in str(observed.get("error"))
    assert "result" not in observed


@pytest.mark.parametrize("state", ["missing", "unavailable"])
def test_legacy_issue_surface_unavailability_is_explicit(state: str) -> None:
    action = (
        "delete tabs.chronology.source_issues;"
        if state == "missing"
        else "tabs.chronology.source_issues={status:'unavailable',reason_code:'retained_source_issue_surface_unavailable'};"
    )
    observed = export_issues(action)
    assert observed["result"] == {
        "status": "unavailable",
        "reason_code": "source_chronology_issues_not_available"
        if state == "missing"
        else "retained_source_issue_surface_unavailable",
    }


def test_complete_download_retains_reference_verification_qualification() -> None:
    observed = export_issues(
        "tabs.chronology.reference_verification_posture='Original flag retained; missing native identifier refuses effective selection.';"
    )
    assert observed["temporalSupport"]["reference_verification_posture"] == (
        "Original flag retained; missing native identifier refuses effective selection."
    )
    legacy = export_issues()
    assert "reference_verification_posture" not in legacy["temporalSupport"]
