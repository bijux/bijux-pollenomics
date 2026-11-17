"""Source-only catalogues can opt into metadata geometry without scientific rows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest


@pytest.mark.parametrize("resource_browser", ["source_only"], indirect=True)
def test_source_only_published_metadata_points_do_not_need_scientific_country_layers(
    resource_browser: dict[str, Any], browser_probe: Callable[..., dict[str, Any]]
) -> None:
    domain = resource_browser["manifest"]["domains"]["resources"]
    assert domain["legacy_site_reference_count"] == 0
    sites = [
        row
        for payload in resource_browser["payloads"].values()
        if payload.get("kind") == "index"
        for row in payload["records"]
        if row["entity_type"] == "sites"
    ]
    assigned = [
        s
        for s in sites
        if s["country_code"] == "SE"
        and s["geometry_status"] == "native_point_consensus"
    ]
    assert assigned, (
        "Generated authority must actually contain assigned metadata points"
    )
    observed = browser_probe(
        """(async()=>{document.getElementById('source-resources-open').click();for(let i=0;i<150&&!document.querySelector('[data-resource-list]')?.children.length;i++)await new Promise(ok=>setTimeout(ok,20));const show=document.querySelector('[aria-label="Show metadata geometry"]');const initiallyOff=show.checked===false;show.checked=true;show.dispatchEvent(new Event('change'));for(let i=0;i<100&&!document.querySelector('[data-resource-geometry-status]')?.textContent.startsWith('Metadata geometry:');i++)await new Promise(ok=>setTimeout(ok,20));return {initiallyOff,points:document.querySelectorAll('.neotoma-metadata-geometry').length,status:document.querySelector('[data-resource-geometry-status]')?.textContent};})()"""
    )
    assert observed["result"]["initiallyOff"] is True
    assert observed["result"]["points"] >= len(assigned)
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])
