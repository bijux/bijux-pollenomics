"""The distributed optional factory binds its explicit presentation dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bijux_pollenomics.reporting.map_document import render as subject

from ..browser_semantics.support import run_node_json
from .test_runtime_packaging import request_args as request_args


def test_optional_factory_binds_escape_and_supplied_glyph_callback(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    html, _ = subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    evidence = subject.static_map_optional_controller_paths(html)[0]
    evidence_raw = evidence.read_bytes()
    observed = run_node_json(
        evidence_raw.decode()
        + """
const tools=BijuxPollenomicsEvidenceTools(value=>String(value),cue=>'supplied-glyph-'+cue);
const catalog=tools.pickerCatalog([{signal_id:'exact',label:'Exact',feature_key:'taxon:exact',resolution:'taxon',status:'accepted',color:'#112233',non_color_cue:'circle'}]);
const source=tools.sourceDetails({detailTableShape:()=>false,decodeDetailTableRow:()=>null,
detailTableText:value=>String(value),renderDetailTable:()=>'',escapeHtml:value=>String(value)});
console.log(JSON.stringify({frozen:Object.isFrozen(tools),methods:Object.keys(tools),
country:tools.countryData([]),time:tools.timeData([]),picker:tools.pickerCatalog([]),
sourceFrozen:Object.isFrozen(source),sourceMethods:Object.keys(source),sourceHtml:source.overview({},{}),
html:tools.pickerHtml(catalog,{pinnedIds:[],visibleIds:[]})}));
"""
    )
    assert observed["frozen"] is True
    assert observed["methods"] == [
        "countryData",
        "countryHtml",
        "timeData",
        "timeHtml",
        "pickerCatalog",
        "pickerSearch",
        "pickerInitial",
        "pickerAction",
        "pickerHtml",
        "pickerMount",
        "sourceDetails",
        "selectionExport",
    ]
    assert all(
        observed[key]["status"] == "available" for key in ("country", "time", "picker")
    )
    assert "supplied-glyph-circle" in observed["html"]
    assert observed["sourceFrozen"] is True
    assert observed["sourceMethods"] == [
        "overview",
        "samples",
        "classification",
        "provenance",
    ]
    assert "Selected sample metadata is supported for Neotoma" in observed["sourceHtml"]
