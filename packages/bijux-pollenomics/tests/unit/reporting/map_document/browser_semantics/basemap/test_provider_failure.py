"""Actual tile failure callbacks preserve evidence while exhausting providers."""

from __future__ import annotations

import re

import pytest

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import run_node_json, template_block


@pytest.mark.parametrize("_fixture_id", ["MAP-008"])
def test_repeated_tile_errors_reach_no_basemap_without_changing_evidence(
    _fixture_id: str,
) -> None:
    threshold = re.search(
        r"const MAX_PROVIDER_TILE_ERRORS = (\d+);", MAP_DOCUMENT_TEMPLATE
    )
    assert threshold is not None
    limit = int(threshold.group(1))
    assert limit == 3
    callbacks = template_block(
        "function nextBasemapAfter",
        "document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === currentBasemap));",
    )
    observed = run_node_json(
        f"const MAX_PROVIDER_TILE_ERRORS={limit};\n"
        """
const BASEMAP_FALLBACK_ORDER=['street','terrain','none'];
const BASEMAP_NAMES=[...BASEMAP_FALLBACK_ORDER];
const failedBasemaps=new Set(),basemapErrorCounts=new Map(),handlers={};
let activeBasemap='street',currentBasemap='street',readout='';
const evidence=[{record_id:'source:1',latitude:0,longitude:0,source_attribution:'Fixture source'}];
const before=JSON.stringify(evidence);
const map={removed:[],removeLayer(layer){this.removed.push(layer.name)}};
const basemaps=Object.fromEntries(['street','terrain'].map(name=>[name,{
  name,on(event,callback){handlers[`${name}:${event}`]=callback},addTo(){},
}]));
const document={querySelectorAll(){return []}};
function updateBasemapReadout(message){readout=message}
function syncHashState(){}
"""
        + callbacks
        + """
const states=[];
handlers['street:tileerror']();states.push(currentBasemap);
handlers['street:tileerror']();states.push(currentBasemap);
handlers['street:tileerror']();states.push(currentBasemap);
handlers['street:tileerror']();states.push(currentBasemap);
handlers['terrain:tileerror']();states.push(currentBasemap);
handlers['terrain:tileerror']();states.push(currentBasemap);
handlers['terrain:tileerror']();states.push(currentBasemap);
console.log(JSON.stringify({states,currentBasemap,activeBasemap,readout,
  removed:map.removed,failed:[...failedBasemaps],
  errorCounts:[...basemapErrorCounts],evidenceUnchanged:JSON.stringify(evidence)===before}));
"""
    )
    assert observed == {
        "states": [
            "street",
            "street",
            "terrain",
            "terrain",
            "terrain",
            "terrain",
            "none",
        ],
        "currentBasemap": "none",
        "activeBasemap": None,
        "readout": "Basemap degraded: terrain unavailable; no-basemap mode active. Evidence data unaffected.",
        "removed": ["street", "terrain"],
        "failed": ["street", "terrain"],
        "errorCounts": [["street", 3], ["terrain", 3]],
        "evidenceUnchanged": True,
    }
