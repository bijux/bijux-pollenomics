"""Actual generated browser interactions keep captured metadata out of native counts."""

from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any

import pytest


@pytest.mark.parametrize("resource_browser", ["scoped", "supporting"], indirect=True)
def test_v2_opener_filters_and_metadata_details_are_separate_from_native_datasets(
    resource_browser: dict[str, Any], browser_probe: Callable[..., dict[str, Any]]
) -> None:
    domain = resource_browser["manifest"]["domains"]["resources"]
    kind = (
        "supporting_entries"
        if domain["supporting_entry_count"]
        else "linked_occurrences"
    )
    expected = (
        domain["supporting_entry_count"]
        if kind == "supporting_entries"
        else domain["ancillary_linked_occurrence_count"]
    )
    observed = browser_probe(
        """(async()=>{const button=document.getElementById('source-resources-open');for(let ancestor=button.parentElement;ancestor;ancestor=ancestor.parentElement)if(ancestor.tagName==='DETAILS')ancestor.open=true;button.scrollIntoView({block:'center'});const box=button.getBoundingClientRect();const entryVisible=getComputedStyle(button).visibility!=='hidden'&&box.width>0&&box.height>0;button.click();for(let i=0;i<150&&!document.querySelector('[data-resource-list]')?.children.length;i++)await new Promise(ok=>setTimeout(ok,20));const dialog=document.getElementById('source-resources-dialog');const nativeRows=document.querySelectorAll('[data-resource-dataset]').length;const population=document.querySelector('[aria-label="Metadata population"]');if(!population)return {entryVisible,open:dialog?.open,nativeRows,populationAvailable:false};population.value="""
        + json.dumps(kind)
        + """;population.dispatchEvent(new Event('change'));for(let i=0;i<150&&!document.querySelector('[data-ancillary-record]');i++)await new Promise(ok=>setTimeout(ok,20));const rows=[...document.querySelectorAll('[data-ancillary-record]')],first=rows[0];first?.querySelector('button').click();for(let i=0;i<150&&!document.querySelector('[data-resource-detail] pre');i++)await new Promise(ok=>setTimeout(ok,20));const status=document.querySelector('[data-resource-status]')?.textContent;const detail=document.querySelector('[data-resource-detail]')?.textContent;const search=document.querySelector('input[type=search]');search.value=first?.dataset.ancillaryRecord||'';search.dispatchEvent(new Event('input'));await new Promise(ok=>setTimeout(ok,50));return {entryVisible,open:dialog?.open,nativeRows,populationAvailable:true,metadataRows:rows.length,status,detail,downloads:document.querySelectorAll('[data-resource-download]').length,filteredRows:document.querySelectorAll('[data-ancillary-record]').length};})()"""
    )
    result = observed["result"]
    assert result["entryVisible"] is True and result["open"] is True
    assert result["populationAvailable"] is True
    assert result["nativeRows"] == min(25, domain["record_count"])
    assert result["metadataRows"] == min(25, expected)
    assert (
        f"Native catalogue remains {domain['record_count']} resources at {domain['site_count']} sites"
        in result["status"]
    )
    assert result["downloads"] == 0 and result["filteredRows"] >= 1
    assert "Recorded metadata only" in result["detail"]
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])
