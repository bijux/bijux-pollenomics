"""Metadata navigation shares URL authority without replacing scientific focus."""

from __future__ import annotations

from collections.abc import Callable
from importlib.resources import files
from typing import Any

from ...support import run_node_json


def test_owned_resource_query_preserves_focus_and_later_scientific_queries() -> None:
    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/url-state.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
let url='https://atlas.example/nordic/?campaign=known#focus_record=neotoma%3Asite%3A12&focus_tab=chronology';
const original=new URL(url),published=[];let replays=0;
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:next=>{url=next;published.push(next)},replayURL:()=>replays++});
const supported=typeof controller.publishResources==='function';
if(supported){controller.publishResources({neotoma_catalogue:'a'.repeat(64),neotoma_site:'12',neotoma_dataset:'201',neotoma_version:'current'});}
const metadata=new URL(url),sameHash=metadata.hash===original.hash;
controller.publish('#countries=Sweden&focus_record=neotoma%3Asite%3A12&focus_tab=chronology');
console.log(JSON.stringify({supported,sameHash,url,published:published.length,replays,canPublish:controller.canPublish()}));
"""
    )
    assert observed["supported"] is True
    assert observed["sameHash"] is True
    assert observed["published"] == 2 and observed["replays"] == 0
    assert observed["canPublish"] is True
    assert "campaign=known" in observed["url"]
    assert "neotoma_dataset=201" in observed["url"]
    assert "neotoma_version=current" in observed["url"]
    assert "#countries=Sweden" in observed["url"]


def test_pending_external_navigation_blocks_delayed_metadata_publication() -> None:
    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/url-state.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
let url='https://atlas.example/nordic/?neotoma_dataset=201#focus_record=old',replays=0,published=[];
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:value=>{url=value;published.push(value)},replayURL:()=>replays++});
url='https://atlas.example/nordic/?neotoma_dataset=202#focus_record=external';const external=url;
const result=controller.publishResources({neotoma_dataset:'201'}),second=controller.publishResources({neotoma_site:'12'});
console.log(JSON.stringify({result,second,url,external,replays,published}));
"""
    )
    assert observed["result"] is False and observed["second"] is False
    assert observed["url"] == observed["external"] and observed["replays"] == 1
    assert observed["published"] == []


def test_resource_url_rejects_unowned_keys_and_preserves_null_patch_authority() -> None:
    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/url-state.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
let url='https://atlas.example/nordic/?neotoma_dataset=201&campaign=kept#focus_record=old';
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:value=>url=value,replayURL:()=>{throw Error('Unexpected replay')}});
const refused=[];for(const values of [{dataset:'202'},{site:'12'},{version:'current'},{neotoma_site:12},{neotoma_site:'x'.repeat(4097)}]){try{controller.publishResources(values);refused.push(false)}catch{refused.push(true)}}
controller.publishResources({neotoma_dataset:null,neotoma_version:'doi_frozen'});console.log(JSON.stringify({refused,url}));
"""
    )
    assert observed["refused"] == [True] * 5
    assert "neotoma_dataset" not in observed["url"]
    assert "neotoma_version=doi_frozen" in observed["url"]
    assert "campaign=kept" in observed["url"] and "#focus_record=old" in observed["url"]


def test_original_shared_metadata_url_opens_exact_dataset_without_rewriting_focus(
    browser_probe: Callable[..., dict[str, Any]], resource_browser: dict[str, Any]
) -> None:
    pin = resource_browser["manifest"]["domains"]["resources"][
        "catalogue_manifest_sha256"
    ]
    observed = browser_probe(
        """(async()=>{for(let i=0;i<150&&!document.querySelector('[data-resource-detail] h3');i++)await new Promise(ok=>setTimeout(ok,20));
return {open:document.getElementById('source-resources-dialog')?.open,heading:document.querySelector('[data-resource-detail] h3')?.textContent,version:document.querySelector('[aria-label="Source version"]')?.value,url:location.href,status:document.querySelector('[data-resource-status]')?.textContent};})()""",
        query=f"?neotoma_catalogue={pin}&neotoma_site=12&neotoma_dataset=201&neotoma_version=doi_frozen",
    )
    result = observed["result"]
    assert result["open"] is True and result["heading"] == "Native dataset 201"
    assert result["version"] == "doi_frozen"
    assert "neotoma_dataset=201" in result["url"] and "#basemap=none" in result["url"]
    assert not any(path.endswith(".body") for path in observed["calls"])
    assert observed["failures"] == []


def test_foreign_catalogue_url_remains_readable_and_unmodified(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe(
        """(async()=>{for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.includes('different catalogue');i++)await new Promise(ok=>setTimeout(ok,20));return {text:document.querySelector('[data-resource-status]')?.textContent,url:location.href};})()""",
        query="?neotoma_catalogue=" + "a" * 64 + "&neotoma_site=12",
    )
    assert "different catalogue" in observed["result"]["text"]
    assert "neotoma_catalogue=" + "a" * 64 in observed["result"]["url"]
    assert observed["failures"] == []


def test_partial_or_duplicate_resource_url_is_not_silently_normalized(
    browser_probe: Callable[..., dict[str, Any]], resource_browser: dict[str, Any]
) -> None:
    pin = resource_browser["manifest"]["domains"]["resources"][
        "catalogue_manifest_sha256"
    ]
    observed = browser_probe(
        """(async()=>{for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.includes('ambiguous');i++)await new Promise(ok=>setTimeout(ok,20));return {text:document.querySelector('[data-resource-status]')?.textContent,url:location.href};})()""",
        query=f"?neotoma_catalogue={pin}&neotoma_site=12&neotoma_site=13",
    )
    assert "ambiguous" in observed["result"]["text"]
    assert "neotoma_site=12&neotoma_site=13" in observed["result"]["url"]
    assert observed["failures"] == []


def test_manual_reader_navigation_supersedes_delayed_startup_metadata(
    browser_probe: Callable[..., dict[str, Any]], resource_browser: dict[str, Any]
) -> None:
    pin = resource_browser["manifest"]["domains"]["resources"][
        "catalogue_manifest_sha256"
    ]
    observed = browser_probe(
        """(async()=>{for(let i=0;i<200;i++){if((await(await fetch('/probe-state')).json()).toolsAttempt)break;await new Promise(ok=>setTimeout(ok,10));}
const loading=document.getElementById('source-resources-open').textContent;document.getElementById('source-resources-open').click();await fetch('/release-tools');
for(let i=0;i<150&&!document.querySelector('[data-resource-status]')?.textContent.startsWith('4 matching');i++)await new Promise(ok=>setTimeout(ok,20));
return {loading,status:document.querySelector('[data-resource-status]')?.textContent,url:location.href,dialogs:document.querySelectorAll('#source-resources-dialog').length};})()""",
        query=f"?neotoma_catalogue={pin}&neotoma_site=12",
        transport_mode="hold_tools",
    )
    assert "Loading source resources" in observed["result"]["loading"]
    assert observed["result"]["status"].startswith("4 matching")
    assert "neotoma_site=" not in observed["result"]["url"]
    assert observed["result"]["dialogs"] == 1 and observed["failures"] == []
