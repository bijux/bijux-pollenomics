"""Production lazy tools load authenticated resource metadata without native bodies."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document import template

from ..support import run_node_json
from .source_resources.native_transport import atlas_catalogue as atlas_catalogue
from .source_resources.native_transport import catalogue_sources as catalogue_sources
from .source_resources.native_transport import resource_script as resource_script


def invoke(
    resource_script: tuple[str, dict[str, Any], dict[str, Any]],
    probe: str,
    *,
    failed_load: bool = False,
) -> dict[str, Any]:
    source, manifest, payloads = resource_script
    result = run_node_json(
        source
        + "\nconst manifest="
        + json.dumps(manifest)
        + ";const payloads="
        + json.dumps(payloads)
        + ";const failedLoad="
        + json.dumps(failed_load)
        + """;
const tools=BijuxPollenomicsEvidenceTools(String,String);let calls=[];let loaded=new Map();
const reader=tools.sourceResources({manifest,loadAsset:async row=>{calls.push(row.asset_key);if(failedLoad)throw Error('Controlled metadata asset failure');loaded.set(row.asset_key,payloads[row.asset_key]);},payloadForAsset:key=>loaded.get(key)});
"""
        + probe
    )
    assert isinstance(result, dict)
    return result


def test_actual_optional_factory_keeps_metadata_lazy_and_all_roles_findable(
    resource_script: tuple[str, dict[str, Any], dict[str, Any]],
) -> None:
    assert "__SOURCE_RESOURCE_BROWSER_FACTORY__" not in template.MAP_DOCUMENT_TEMPLATE
    assert "function createSourceResourceBrowser(" in template.MAP_DOCUMENT_TEMPLATE
    observed = invoke(
        resource_script,
        """
(async()=>{const initial=calls.length,all=await reader.search(''),indexLoads=calls.length;
const reserved=await reader.resource('203'),native=await reader.resource('201'),site=await reader.site('12'),missing=await reader.resource('999');
console.log(JSON.stringify({initial,indexLoads,calls,ids:all.map(row=>row.record_id),roles:all.map(row=>row.exposure_role),reserved,native,site,missing,frozen:Object.isFrozen(reader),filtered:await reader.search('Native site 12',{country:'UNASSIGNED'})}));})().catch(e=>{console.error(e);process.exit(1)});
""",
    )
    assert observed["initial"] == 0
    assert observed["indexLoads"] == len(
        resource_script[1]["domains"]["resources"]["index_asset_keys"]
    )
    assert observed["ids"] == ["201", "202", "203", "204"]
    assert set(observed["roles"]) == {
        "development_resource_discovery",
        "reserved_candidate_confirmation",
        "heldout_no_numerical_access",
    }
    assert (
        observed["reserved"]["versions"]["current"]["acquisition_status"]
        == "not_attempted_exposure_role"
    )
    assert (
        "native_body" not in observed["native"]
        and "native_payload" not in observed["native"]
    )
    assert (
        observed["site"]["site_id"] == "12"
        and observed["site"]["country_code"] == "UNASSIGNED"
    )
    assert observed["missing"] is None and observed["frozen"] is True
    assert {row["record_id"] for row in observed["filtered"]} == {"201", "202"}
    assert all(
        next(row for row in resource_script[1]["assets"] if row["asset_key"] == key)[
            "domain"
        ]
        == "resources"
        for key in observed["calls"]
    )


@pytest.mark.parametrize(
    "damage",
    [
        "pin",
        "duplicate_index",
        "dangling_index",
        "wrong_count",
        "missing_payload",
        "failed_load",
    ],
)
def test_metadata_failure_never_becomes_successful_empty_search(
    resource_script: tuple[str, dict[str, Any], dict[str, Any]], damage: str
) -> None:
    source, manifest, payloads = deepcopy(resource_script)
    index_key = manifest["domains"]["resources"]["index_asset_keys"][0]
    part = payloads[index_key]
    if damage == "pin":
        part["catalogue_manifest_sha256"] = "0" * 64
    elif damage == "duplicate_index":
        part["records"].append(deepcopy(part["records"][0]))
    elif damage == "dangling_index":
        part["records"][0]["part_id"] = "resources:missing"
    elif damage == "wrong_count":
        manifest["domains"]["resources"]["record_count"] += 1
    elif damage == "missing_payload":
        del payloads[index_key]
    probe = """
(async()=>{try {await reader.search('');console.log(JSON.stringify({refused:false}));}catch(error){console.log(JSON.stringify({refused:true,reason:String(error.message)}));}})();
"""
    observed = invoke(
        (source, manifest, payloads), probe, failed_load=damage == "failed_load"
    )
    assert observed["refused"] is True
    assert observed["reason"]
