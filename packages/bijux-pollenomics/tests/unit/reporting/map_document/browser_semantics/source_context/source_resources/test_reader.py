"""Resource metadata queries preserve roles, literal versions and missing states."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from .browser_invocation import invoke


def test_version_status_filter_does_not_hide_protected_metadata(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{const all=await reader.search('');const protectedRows=await reader.search('',{version:'current',statusField:'acquisition_status',status:'not_attempted_exposure_role'});
console.log(JSON.stringify({all:all.map(row=>row.record_id),protected:protectedRows.map(row=>row.record_id),calls}));})();
""",
    )
    assert observed["all"] == ["201", "202", "203", "204"]
    assert observed["protected"] == ["203", "204"]
    assert observed["calls"] == []


def test_index_inventory_is_complete_and_detached_from_later_queries(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
(async()=>{const supported=typeof reader.inventory==='function';let count=null,sites=null,ids=null;
if(supported){const first=await reader.inventory();count=first.resources.length;sites=first.sites.length;first.resources[0].record_id='999';ids=(await reader.search('')).map(row=>row.record_id);}
console.log(JSON.stringify({supported,count,sites,ids,calls}));})();
""",
    )
    assert observed["supported"] is True
    assert observed["count"] == 4 and observed["sites"] == 3
    assert observed["ids"] == ["201", "202", "203", "204"]
    assert observed["calls"] == []


def test_packaged_reader_opens_searchable_metadata_without_source_body_fetch(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe("""(async()=>{const button=document.getElementById('source-resources-open');if(!button)return {supported:false};button.click();
for(let i=0;i<150&&document.querySelectorAll('[data-resource-dataset]').length!==4;i++)await new Promise(ok=>setTimeout(ok,20));
const dialog=document.getElementById('source-resources-dialog');const initial=dialog?.textContent;const search=dialog?.querySelector('input[type=search]');
if(search){search.value='201';search.dispatchEvent(new Event('input'));for(let i=0;i<150&&!dialog.querySelector('[data-resource-status]')?.textContent.startsWith('1 matching');i++)await new Promise(ok=>setTimeout(ok,20));}
return {supported:true,open:dialog?.open,initial,rows:[...dialog.querySelectorAll('[data-resource-dataset]')].map(row=>row.dataset.resourceDataset),scientific:document.querySelector('#topbar-state-pill')?.textContent};})()""")
    assert observed["result"]["supported"] is True
    assert observed["result"]["open"] is True
    assert observed["result"]["rows"] == ["201"]
    assert "metadata" in observed["result"]["initial"].lower()
    assert "Source qualification:" in observed["result"]["initial"]
    assert "Metadata only; numerical requests blocked." in observed["result"]["initial"]
    assert "source terminal status:" not in observed["result"]["initial"]
    assert "reserved candidate confirmation" in observed["result"]["initial"]
    assert '{"acquisition_status"' not in observed["result"]["initial"]
    assert not any(path.endswith(".body") for path in observed["calls"])
    assert observed["failures"] == []


def test_source_detail_entry_requires_matching_native_namespace(
    resource_browser: dict[str, Any],
) -> None:
    observed = invoke(
        resource_browser,
        """
const details=tools.sourceDetails({detailTableShape:()=>false,decodeDetailTableRow:()=>({}),detailTableText:String,renderDetailTable:()=>'',escapeHtml:String,resourceCatalogueAvailable:true});
const tabs={overview:{source_family:'neotoma',source_site_id:'12',site_id:'neotoma:site:12'}};
const valid=details.provenance(tabs);tabs.overview.site_id='sead:site:12';const foreign=details.provenance(tabs);
tabs.overview={source_family:'sead',source_site_id:'12',site_id:'neotoma:site:12'};const wrongFamily=details.provenance(tabs);
const legacy=tools.sourceDetails({detailTableShape:()=>false,decodeDetailTableRow:()=>({}),detailTableText:String,renderDetailTable:()=>'',escapeHtml:String}).provenance({overview:{source_family:'neotoma',source_site_id:'12',site_id:'neotoma:site:12'}});
console.log(JSON.stringify({valid,foreign,wrongFamily,legacy}));
""",
    )
    assert 'data-source-resources="neotoma:site:12"' in observed["valid"]
    assert all(
        "data-source-resources" not in observed[key]
        for key in ["foreign", "wrongFamily", "legacy"]
    )


@pytest.mark.parametrize("resource_browser", ["wide"], indirect=True)
def test_real_metadata_pages_do_not_duplicate_records_or_interpret_native_markup(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe("""(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<150&&document.querySelectorAll('[data-resource-dataset]').length!==25;i++)await new Promise(ok=>setTimeout(ok,20));
const first=[...document.querySelectorAll('[data-resource-dataset]')].map(row=>row.dataset.resourceDataset);
[...document.querySelectorAll('#source-resources-dialog button')].find(node=>node.textContent==='Next metadata page').click();
for(let i=0;i<100&&document.querySelectorAll('[data-resource-dataset]').length!==10;i++)await new Promise(ok=>setTimeout(ok,20));
const second=[...document.querySelectorAll('[data-resource-dataset]')].map(row=>row.dataset.resourceDataset);
document.querySelector('[data-resource-dataset] button').click();
for(let i=0;i<100&&!document.querySelector('[data-resource-detail] details');i++)await new Promise(ok=>setTimeout(ok,20));
return {first,second,images:document.querySelectorAll('#source-resources-dialog img').length,raw:document.querySelector('[data-resource-detail]')?.textContent};})()""")
    result = observed["result"]
    assert len(result["first"]) == 25 and len(result["second"]) == 10
    assert len(set(result["first"] + result["second"])) == 35
    assert result["images"] == 0
    assert "<img src=x onerror=alert(1)> Native extent" in result["raw"]
    assert observed["failures"] == []


@pytest.mark.parametrize(
    ("width", "height"),
    [(320, 568), (390, 844), (568, 320), (768, 1024), (844, 390), (1440, 900)],
)
def test_reader_controls_remain_bounded_and_reachable(
    browser_probe: Callable[..., dict[str, Any]], width: int, height: int
) -> None:
    observed = browser_probe(
        """(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<150&&!document.querySelectorAll('[data-resource-dataset]').length;i++)await new Promise(ok=>setTimeout(ok,20));
const dialog=document.getElementById('source-resources-dialog'),bounds=dialog.getBoundingClientRect();const controls=[...dialog.querySelectorAll('input,select,button')];const failures=[];
for(const node of controls){if(node.disabled)continue;node.scrollIntoView({block:'center',inline:'nearest'});const box=node.getBoundingClientRect(),hit=document.elementFromPoint(box.x+box.width/2,box.y+box.height/2);if(box.left<bounds.left-1||box.right>bounds.right+1||box.top<bounds.top-1||box.bottom>bounds.bottom+1||!(hit===node||node.contains(hit)))failures.push({label:node.getAttribute('aria-label')||node.textContent,box:{left:box.left,right:box.right,top:box.top,bottom:box.bottom},hit:hit?.tagName});}
return {bounded:bounds.left>=0&&bounds.top>=0&&bounds.right<=innerWidth&&bounds.bottom<=innerHeight,overflow:dialog.scrollWidth>dialog.clientWidth+1,failures};})()""",
        width=width,
        height=height,
    )
    assert observed["result"] == {"bounded": True, "overflow": False, "failures": []}
    assert observed["failures"] == []


def test_transient_index_failure_can_retry_actual_unchanged_metadata(
    resource_browser: dict[str, Any],
) -> None:
    import json

    from ...support import run_node_json

    observed = run_node_json(
        resource_browser["source"]
        + "\nconst manifest="
        + json.dumps(resource_browser["manifest"])
        + ";const payloads="
        + json.dumps(resource_browser["payloads"])
        + """;
(async()=>{let first=true;const loaded=new Map(),tools=BijuxPollenomicsEvidenceTools(String,String);
const reader=tools.sourceResources({manifest,loadAsset:async row=>{if(first){first=false;throw Error('Controlled transient index failure')}loaded.set(row.asset_key,payloads[row.asset_key])},payloadForAsset:key=>loaded.get(key)});
let refused=false;try{await reader.search('')}catch{refused=true}let ids=null;try{ids=(await reader.search('')).map(row=>row.record_id)}catch{}
console.log(JSON.stringify({refused,ids}));})();
"""
    )
    assert observed["refused"] is True
    assert observed["ids"] == ["201", "202", "203", "204"]


def test_optional_factory_failure_has_real_user_retry(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{const button=document.getElementById('source-resources-open');button.click();
for(let i=0;i<150&&!button.textContent.startsWith('Retry source resources');i++)await new Promise(ok=>setTimeout(ok,20));const refused=button.textContent;
button.click();for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.startsWith('4 matching');i++)await new Promise(ok=>setTimeout(ok,20));
return {refused,status:document.querySelector('[data-resource-status]')?.textContent};})()""",
        transport_mode="fail_tools_once",
    )
    assert observed["result"]["refused"].startswith("Retry source resources")
    assert observed["result"]["status"].startswith("4 matching")
    assert observed["failures"] == []


def test_metadata_chunk_failure_preserves_reader_and_can_retry(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{const button=document.getElementById('source-resources-open');button.click();
for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.includes('unavailable');i++)await new Promise(ok=>setTimeout(ok,20));const refused=document.querySelector('[data-resource-status]')?.textContent;
button.click();for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.startsWith('4 matching');i++)await new Promise(ok=>setTimeout(ok,20));return {refused,status:document.querySelector('[data-resource-status]')?.textContent};})()""",
        transport_mode="fail_metadata_once",
    )
    assert "unavailable" in observed["result"]["refused"]
    assert observed["result"]["status"].startswith("4 matching")
    assert not any(path.endswith(".body") for path in observed["calls"])
    assert observed["failures"] == []


def test_selected_resource_has_readable_version_rights_and_policy_access(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{document.getElementById('source-resources-open').click();for(let i=0;i<150&&!document.querySelector('[data-resource-dataset="201"] button');i++)await new Promise(ok=>setTimeout(ok,20));document.querySelector('[data-resource-dataset="201"] button').click();for(let i=0;i<150&&!document.querySelector('[data-resource-detail] h3');i++)await new Promise(ok=>setTimeout(ok,20));return {versions:document.querySelector('[data-source-versions]')?.textContent,rights:document.querySelector('[data-source-rights]')?.textContent,links:[...document.querySelectorAll('[data-source-rights] a')].map(node=>node.href)};})()"""
    )
    assert (
        "current" in observed["result"]["versions"]
        and "doi_frozen" in observed["result"]["versions"]
    )
    assert "CC BY 4.0" in observed["result"]["rights"]
    assert observed["result"]["links"] == [
        "https://www.neotomadb.org/data/data-use-and-embargo-policy"
    ]
    assert not any(path.endswith(".body") for path in observed["calls"])
    assert observed["failures"] == []


def test_input_queued_during_metadata_initialization_is_rendered_after_loading(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{document.getElementById('source-resources-open').click();
for(let i=0;i<200;i++){if((await(await fetch('/probe-state')).json()).indexAttempt)break;await new Promise(ok=>setTimeout(ok,10));}
const input=document.querySelector('[aria-label="Search source metadata"]');input.value='201';input.dispatchEvent(new Event('input'));await fetch('/release-metadata');
for(let i=0;i<200&&!document.querySelector('[data-resource-status]')?.textContent.startsWith('1 matching');i++)await new Promise(ok=>setTimeout(ok,10));
return {status:document.querySelector('[data-resource-status]')?.textContent,rows:[...document.querySelectorAll('[data-resource-dataset]')].map(row=>row.dataset.resourceDataset)};})()""",
        transport_mode="hold_metadata",
    )
    assert observed["result"]["status"].startswith("1 matching")
    assert observed["result"]["rows"] == ["201"]
    assert observed["failures"] == []


def test_listing_qualifier_keeps_derived_snapshot_and_absent_postures_separate() -> (
    None
):
    from importlib.resources import files

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/reader.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
const supported=typeof sourceResourceQualification==='function',base={exposure_role:'development_resource_discovery'};
const cases=[['current',{current_source_qualification_status:'parsed_current_source',qualification_status:'not_qualified',acquisition_status:'unsupported_dataset_type',source_terminal_status:'unsupported_dataset_type'}],['doi_frozen',{snapshot_qualification_status:'parsed_frozen_snapshot',strict_current_binding_status:'matches_current_metadata',qualification_status:'parsed_frozen_native'}],['current',{qualification_status:null,acquisition_status:'parsed_native'}],['current',{acquisition_status:'parsed_native'}]];
const rows=supported?cases.map(([version,fields])=>sourceResourceQualification({...base,version_statuses:{[version]:fields}},version)):[];
const protectedRow=supported?sourceResourceQualification({exposure_role:'heldout_no_numerical_access',version_statuses:{current:{qualification_status:'parsed_native'}}},'current'):null;
console.log(JSON.stringify({supported,rows,protectedRow}));
"""
    )
    assert observed["supported"] is True
    assert observed["rows"] == [
        {
            "field": "current_source_qualification_status",
            "value": "parsed_current_source",
            "metadataOnly": False,
        },
        {
            "field": "snapshot_qualification_status",
            "value": "parsed_frozen_snapshot",
            "metadataOnly": False,
        },
        {"field": "qualification_status", "value": None, "metadataOnly": False},
        {"field": "qualification_status", "metadataOnly": False},
    ]
    assert observed["protectedRow"] == {"metadataOnly": True}


def test_authenticated_frozen_snapshot_binding_refusal_is_not_summarized_as_success(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Any, str, dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace
    from importlib.resources import files
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        capture_neotoma_resources,
    )
    from bijux_pollenomics.reporting.map_document.source_resources import (
        AtlasResourceCatalogueInput,
        load_atlas_resource_catalogue,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources.publication import (
        build_source_resource_payloads,
    )

    from ......collection.sources.neotoma.resource_catalogue import native_captures
    from ...support import run_node_json

    original = capture_neotoma_resources
    assert original is vars(native_captures)["capture_neotoma_resources"]

    def capture(*args: Any, fetch: Callable[..., Any], **kwargs: Any) -> Any:
        def frozen_database_difference(url: str, **options: Any) -> Any:
            response = fetch(url, **options)
            if "/frozen/" in url:
                body = json.loads(response.body)
                body["data"][0]["download"]["data"]["site"]["dataset"]["database"] = (
                    "Snapshot database"
                )
                return replace(response, body=json.dumps(body).encode())
            return response

        return original(*args, fetch=frozen_database_difference, **kwargs)

    monkeypatch.setattr(native_captures, "capture_neotoma_resources", capture)
    root, digest, _ = publish_catalogue(
        catalogue_sources(source_database="Current database")
    )
    projected = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    rows = build_source_resource_payloads(projected).payloads
    row = next(
        row
        for part in rows
        if part["kind"] == "index"
        for row in part["records"]
        if row["entity_type"] == "resources" and row["record_id"] == "201"
    )
    statuses = row["version_statuses"]["doi_frozen"]
    assert statuses["qualification_status"] == "refused_frozen_native"
    assert statuses["snapshot_qualification_status"] == "parsed_frozen_snapshot"
    assert statuses["strict_current_binding_status"] == "refused_database_difference"
    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/reader.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + "\nconsole.log(JSON.stringify(sourceResourceQualification("
        + json.dumps(row)
        + ",'doi_frozen')));"
    )
    assert observed == {
        "field": "strict_current_binding_status",
        "value": "refused_database_difference",
        "metadataOnly": False,
    }


@pytest.mark.parametrize(
    "field", ["source_terminal_status", "acquisition_status", "qualification_status"]
)
def test_current_derived_summary_cannot_supersede_native_identity_refusal(
    field: str,
) -> None:
    from importlib.resources import files
    import json

    from ...support import run_node_json

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/reader.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
const statuses={current_source_qualification_status:'parsed_current_source',qualification_status:'not_qualified',acquisition_status:'unsupported_dataset_type',source_terminal_status:'unsupported_dataset_type'};
statuses[FIELD]='refused_native_protocol';console.log(JSON.stringify(sourceResourceQualification({exposure_role:'development_resource_discovery',version_statuses:{current:statuses}},'current')));
""".replace("FIELD", json.dumps(field))
    )
    assert observed == {
        "field": field,
        "value": "refused_native_protocol",
        "metadataOnly": False,
    }
