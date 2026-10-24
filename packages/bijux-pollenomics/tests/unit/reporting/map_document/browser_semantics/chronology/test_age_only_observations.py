"""Exact source ages can align observations without inventing sample depth."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma as projection,
)
from tests.support.neotoma.relational_shapes import nested, rows

from ...evidence_projection.fixtures.neotoma import _neotoma_fixture
from ...evidence_projection.test_neotoma_chronology_models import (
    materialized,
    native_source,
)
from ..pollen.test_pollen_diagram import add_row
from ..pollen.test_pollen_diagram import decoded as decoded_observations
from ..pollen.test_pollen_small_multiples import script
from ..support import run_node_json
from . import test_age_depth_diagram as age
from .test_observation_age_alignment import add_claim


def projected_without_depth(
    root: Path, monkeypatch: pytest.MonkeyPatch, depth: object = None
) -> dict[str, Any]:
    """Change the authenticated controlled source before its real projection."""
    original = _neotoma_fixture

    def fixture(path: Path, patch: pytest.MonkeyPatch) -> None:
        original(path, patch)
        relational = path / "neotoma/relational"
        reader = cast(
            Callable[[Path], dict[str, object]],
            vars(projection)["read_validated_neotoma_relational_manifest"],
        )
        manifest = reader(relational)
        part = relational / "surfaces/samples/part-00001.json"
        payload = json.loads(part.read_text())
        payload["rows"][0]["source_depth"] = depth
        payload["rows"][0]["source_payload"]["depth"] = depth
        body = json.dumps(payload).encode()
        part.write_bytes(body)
        cast(dict[str, Any], manifest)["surfaces"]["samples"]["parts"][0]["sha256"] = (
            hashlib.sha256(body).hexdigest()
        )

    monkeypatch.setattr(age, "_neotoma_fixture", fixture)
    return cast(dict[str, Any], age.projected_tabs(root, monkeypatch))


def observe(tabs: dict[str, Any], expression: str) -> Any:
    return run_node_json(
        script()
        + "const tabs="
        + json.dumps(tabs)
        + ";const before=JSON.stringify(tabs);const source=pollenObservationDiagramData(tabs);"
        + "const key=source.groups[0]?.key;const depth=pollenAgeAxisData(tabs,key);"
        + "const value=("
        + expression
        + ");if(before!==JSON.stringify(tabs))throw Error('source mutated');"
        + "console.log(JSON.stringify(value));"
    )


@pytest.mark.parametrize("depth", [None, True, "12 cm"])
def test_real_producer_keeps_age_only_source_values_and_refuses_depth_plot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, depth: object
) -> None:
    tabs = projected_without_depth(tmp_path, monkeypatch, depth)
    output = observe(
        tabs,
        "({source,depth,nativeDepth:pollenDepthDiagramData(tabs),"
        "ageDepth:ageDepthDiagramData(tabs),ageSource:sourceAgeAssignmentData(tabs),"
        "html:renderPollenDepthDiagram(tabs,key,(g)=>renderPollenAgeDiagram(tabs,g.key,null,false)+renderPollenSmallMultiples(tabs,g.key))})",
    )
    assert output["source"]["total"] == 1
    assert output["source"]["groups"][0]["rows"][0]["depth"] == depth
    assert output["source"]["groups"][0]["rows"][0]["value"] == 3
    assert output["nativeDepth"]["groups"] == []
    assert output["nativeDepth"]["omitted"] == {"source_depth_not_numeric": 1}
    assert output["ageDepth"]["groups"] == []
    assert output["ageDepth"]["omitted"] == {"source_depth_not_numeric": 3}
    assert len(output["ageSource"]["groups"]) == 3
    assert output["depth"]["rows"] == []
    assert output["depth"]["total"] == 1
    assert output["depth"]["omitted"] == {"source_depth_not_numeric": 1}
    assert len(output["depth"]["options"]) == 3
    assert "<svg" not in output["html"]
    assert "0 of 1 observations have numeric source depth; 1 do not" in output["html"]
    assert "native-value-age-group" in output["html"]
    assert "missing or not a finite number: 1" in output["html"]


@pytest.mark.parametrize("posture", ["comparable", "context_only", "refused"])
def test_explicit_age_uses_literal_point_interval_and_refusal_without_depth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, posture: str
) -> None:
    output = observe(
        projected_without_depth(tmp_path, monkeypatch),
        "(()=>{const chosen=depth.options.find(o=>o.identity[6]==="
        + json.dumps(posture)
        + ");return {data:pollenAgeAxisData(tabs,key,chosen.key),"
        + "panels:pollenSmallMultiplesData(tabs,key,chosen.key),"
        + "html:renderPollenAgeDiagram(tabs,key,chosen.key,true,['neotoma:observation:40:50:1'])};})()",
    )
    row = output["data"]["rows"][0]
    assert row["depth"] is None and row["value"] == 3
    assert output["data"]["omitted"] == {}
    assert output["data"]["sourceAgeOmitted"] == {}
    assert output["panels"]["panels"][0]["alignment"]["rows"] == [row]
    assert (
        row["age"]["point"]
        == {"comparable": 125.5, "context_only": None, "refused": 0}[posture]
    )
    assert row["age"]["endpoints"] == ([-10, 20] if posture == "context_only" else None)
    assert 'data-selected-observation="true"' in output["html"]
    assert "<svg" in output["html"]
    if posture == "refused":
        assert "&lt;img" in output["html"]
    assert "no inferred point or midpoint" in output["html"]
    assert "Source age (year)" in output["html"]


@pytest.mark.parametrize("change", ["duplicate", "foreign", "missing", "text"])
def test_age_only_rows_preserve_ambiguity_and_missingness_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    tabs = cast(
        dict[str, Any], age.decoded(projected_without_depth(tmp_path, monkeypatch))
    )
    if change == "duplicate":
        add_claim(tabs, 0, chronology_claim_id="second-claim")
    elif change == "foreign":
        age.set_claim(tabs, "dataset_id", "foreign")
    elif change == "missing":
        age.set_claim(tabs, "source_age_value", None)
    else:
        age.set_claim(tabs, "source_age_value", "125.5")
    output = observe(
        tabs,
        "({native:source,depth,ages:sourceAgeAssignmentData(tabs),"
        "chosen:pollenAgeAxisData(tabs,key,JSON.stringify(['neotoma:collection-unit:20','neotoma:dataset:30','neotoma:chronology:20:1','Calibrated radiocarbon years BP','year','calibrated','comparable']))})",
    )
    assert len(output["native"]["groups"]) == 1
    assert output["chosen"]["rows"] == []
    if change == "duplicate":
        assert output["chosen"]["omitted"] == {"ambiguous_sample_age_assignment": 1}
    else:
        assert output["chosen"]["status"] == "unavailable"
        reason = {
            "foreign": "sample_source_relation_mismatch",
            "missing": "source_age_not_provided",
            "text": "source_age_not_numeric",
        }[change]
        assert output["ages"]["omitted"] == {reason: 1}


def test_actual_drawer_age_only_choice_survives_rerender_and_new_record_resets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_without_depth(tmp_path, monkeypatch)
    output = run_node_json(
        age.diagram_script()
        + "const tabs="
        + json.dumps(tabs)
        + r""";
const before=JSON.stringify(tabs),callbacks={},selectors={};let focusCount=0;
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return [];} };
const focusDetail={_html:'',get innerHTML(){return this._html;},set innerHTML(v){this._html=v;for(const key of Object.keys(selectors))delete selectors[key];},dataset:{},contains(){return false;},setAttribute(){},querySelectorAll(selector){
 if(selector!=='[data-pollen-age-group]'&&selector!=='[data-pollen-depth-group]')return [];
 const item={value:'',focus(){focusCount++;},addEventListener(event,cb){callbacks[selector]=cb;}};
 selectors[selector]=item;return [item];
}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}function syncHashState(){}
let activeFocusTab='pollen_composition',focusState={kind:'point',detailTabs:tabs};
renderFocusDetail();const initial=focusDetail.innerHTML;
const key=pollenObservationDiagramData(tabs).groups[0].key;
selectors['[data-pollen-depth-group]'].value=key;callbacks['[data-pollen-depth-group]']();
const options=pollenAgeAxisData(tabs,key).options;
const interval=options.find(o=>o.identity[6]==='context_only');
selectors['[data-pollen-age-group]'].value=interval.key;callbacks['[data-pollen-age-group]']();
const chosen=focusDetail.innerHTML;renderFocusDetail();const rerender=focusDetail.innerHTML;
focusState={kind:'point',detailTabs:JSON.parse(JSON.stringify(tabs))};renderFocusDetail();
console.log(JSON.stringify({initial,chosen,rerender,reset:focusDetail.innerHTML,focusCount,unchanged:before===JSON.stringify(tabs)}));
"""
    )
    assert output["unchanged"] is True and output["focusCount"] == 2
    for key in ("initial", "reset"):
        assert "<svg" not in output[key]
        assert 'data-pollen-age-group="true"' in output[key]
    for key in ("chosen", "rerender"):
        assert "<svg" in output[key]
        assert "Source age (year)" in output[key]
        assert "reported endpoints -10, 20" in output[key]
        assert "reported age point not supplied" in output[key]
        assert "Source depth (unit not supplied)</text>" not in output[key]
    for key in ("initial", "chosen", "rerender", "reset"):
        assert "Showing 1–1 of 1" in output[key]
        assert "NISP" in output[key] and "neotoma:observation:40:50:1" in output[key]


def test_native_builder_strict_materialization_and_projection_keep_zero_without_depth(
    tmp_path: Path,
) -> None:
    source = native_source()
    sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
    sample["depth"] = None
    before = json.dumps(source, sort_keys=True)
    # No patched validator: these are actual governed tables, one row per part.
    tabs, accounting = materialized(tmp_path, source)
    output = observe(
        tabs,
        "({source,depth,nativeDepth:pollenDepthDiagramData(tabs),"
        "ageDepth:ageDepthDiagramData(tabs),"
        "aligned:depth.options.map(o=>pollenAgeAxisData(tabs,key,o.key)),"
        "html:depth.options.map(o=>renderPollenAgeDiagram(tabs,key,o.key)).join('')})",
    )
    assert json.dumps(source, sort_keys=True) == before
    assert accounting["detail_row_counts"]["samples"] == 1
    assert output["source"]["total"] == 2
    assert len(output["source"]["groups"]) == 2
    assert output["nativeDepth"]["groups"] == []
    assert output["nativeDepth"]["omitted"] == {"source_depth_not_numeric": 2}
    assert output["ageDepth"]["groups"] == []
    assert output["ageDepth"]["omitted"] == {"source_depth_not_numeric": 2}
    assert sorted(g["rows"][0]["value"] for g in output["source"]["groups"]) == [
        0,
        12.5,
    ]
    assert len(output["aligned"]) == 2
    for alignment in output["aligned"]:
        assert alignment["omitted"] == {} and len(alignment["rows"]) == 1
        row = alignment["rows"][0]
        assert row["depth"] is None
        assert row["age"]["point"] in (1100, 1200)
        assert row["age"]["claim"]["subject_id"] == row["sample"]
    assert output["html"].count("<svg") == 2
    assert "reported value 0 NISP" in output["html"]
    assert "reported endpoints 1150, 1250" in output["html"]
    assert "Source age (year)" in output["html"]


def test_mixed_depth_panel_retains_original_denominator_in_figure_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded_observations(projected_without_depth(tmp_path, monkeypatch))
    add_row(tabs["samples"]["samples"], sample_id="sample-with-depth", source_depth=12)
    add_row(
        tabs["pollen_composition"],
        observation_id="observation-with-depth",
        sample_id="sample-with-depth",
    )
    output = observe(
        tabs,
        "({data:pollenSmallMultiplesData(tabs,key),html:renderPollenSmallMultiples(tabs,key)})",
    )
    panel = output["data"]["panels"][0]
    assert panel["alignment"]["total"] == 2
    assert len(panel["group"]["rows"]) == 2
    assert len(panel["alignment"]["rows"]) == 1
    assert panel["alignment"]["omitted"] == {"source_depth_not_numeric": 1}
    assert "1 of 1 aligned observations drawn; 2 source observations" in output["html"]
    assert (
        "1 of 2 individual source observations drawn; 1 lack numeric source depth"
        in output["html"]
    )
    assert output["html"].count("<svg") == 1
    assert "source depth 12 (unit not supplied)" in output["html"]
    assert "source depth null" not in output["html"]
