"""Actual packaged resource tools and finite authenticated source archives."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document import render
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

from ....source_resources.archive_reference.native_archives import (
    archive_inputs as archive_inputs,
)
from ....source_resources.archive_reference.native_archives import (
    publish_catalogue as publish_catalogue,
)
from ....source_resources.catalogue_inputs import catalogue_sources as catalogue_sources


@pytest.fixture
def resource_browser(
    archive_inputs: tuple[Path, str, Path, str],
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> dict[str, Any]:
    """Publish generated source archives through the maintained renderer."""
    catalogue, digest, archive, archive_pin = (
        wide_metadata_archive(tmp_path)
        if getattr(request, "param", None) == "wide"
        else archive_inputs
    )
    from ....source_resources.catalogue_inputs import legacy_site

    projected = load_atlas_resource_catalogue(
        AtlasResourceCatalogueInput(
            catalogue,
            digest,
            archive=AtlasResourceArchiveInput(
                archive, archive_pin, "/data/neotoma/source-resources/"
            ),
        ),
        legacy_neotoma_records=[legacy_site("12")],
    )
    output = tmp_path / "resource-browser"
    output.mkdir()
    assets = write_static_atlas_assets(
        output,
        slug="metadata",
        version="source-resource-reader",
        point_layers=[],
        polygon_layers=[],
        source_resources=projected,
    )
    html, _ = render.write_static_map_document(
        output / "index.html",
        title="Controlled source resource metadata",
        version="source-resource-reader",
        generated_on="Controlled fixture",
        countries=("Sweden", "Norway", "Denmark", "Finland"),
        policy=MAP_SCOPE_POLICIES["custom"],
        point_layers=[],
        polygon_layers=[],
        asset_base_path="_map_assets",
        static_assets=assets,
    )
    rows = cast(
        list[dict[str, Any]], normalize_asset_inventory(assets.manifest["assets"])
    )
    payloads = {
        row["asset_key"]: decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row["decoded_byte_count"],
        )
        for row, path in zip(rows, assets.asset_paths, strict=True)
    }
    routes = {
        "/data/neotoma/source-resources/" + path.relative_to(archive).as_posix(): list(
            path.read_bytes()
        )
        for path in archive.rglob("*")
        if path.is_file()
    }
    assert (
        sha256(
            bytes(routes["/data/neotoma/source-resources/manifest.json"])
        ).hexdigest()
        == archive_pin
    )
    return {
        "source": render.static_map_optional_controller_paths(html)[0].read_text(),
        "manifest": {**assets.manifest, "assets": rows},
        "payloads": payloads,
        "routes": routes,
        "root": output,
        "archive": archive,
    }


@pytest.fixture
def browser_probe(
    resource_browser: dict[str, Any], tmp_path: Path
) -> Callable[..., dict[str, Any]]:
    """Exercise the packaged document through the maintained Chrome transport."""
    from importlib.resources import files
    import json
    import os
    import subprocess

    from bijux_pollenomics.reporting.rendering.artifacts import copy_map_assets

    binary = os.environ.get("BIJUX_TEST_BROWSER")
    if not binary:
        pytest.skip("BIJUX_TEST_BROWSER must name an existing Chrome installation")
    copy_map_assets(resource_browser["root"])
    transport = files("bijux_pollenomics_dev.ci.atlas_browser").joinpath(
        "browser-transport.mjs"
    )

    def probe(
        expression: str,
        *,
        query: str = "",
        width: int = 390,
        height: int = 844,
        transport_mode: str = "ordinary",
        driver: str | None = None,
    ) -> dict[str, Any]:
        profile = tmp_path / "chrome-profile"
        profile.mkdir(exist_ok=True)
        operator = tmp_path / "browser-probe.mjs"
        operator.write_text(
            """
import {createServer} from 'node:http';
import {readFile,readdir,mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
"""
            f"import {{launchChromium,debuggerEndpoint,connectCdp,evaluate}} from {json.dumps(Path(str(transport)).as_uri())};\n"
            "const root="
            + json.dumps(str(resource_browser["root"]))
            + ";const transportMode="
            + json.dumps(transport_mode)
            + ";const routes="
            + json.dumps(resource_browser["routes"])
            + ";\n"
            + """
const calls=[],failures=[];let releaseTools;const toolsGate=new Promise(ok=>releaseTools=ok);let toolsAttempt=0,indexAttempt=0;
const server=createServer(async(req,res)=>{const path=new URL(req.url,'http://localhost').pathname;calls.push(path);
if(path==='/release-metadata'){releaseTools();res.end('released');return;}
if(path==='/release-tools'){releaseTools();res.end('released');return;}
if(path==='/probe-state'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({toolsAttempt,indexAttempt}));return;}
if(path.includes('.atlas-evidence-tools.')){toolsAttempt++;if(transportMode==='hold_tools')await toolsGate;if(transportMode==='fail_tools_once'&&toolsAttempt===1){res.writeHead(404);res.end('Controlled optional tools failure');return;}}
if(path.includes('.atlas-resources.')&&path.endsWith('.js')){indexAttempt++;if(transportMode==='hold_metadata')await toolsGate;if(transportMode==='fail_metadata_once'&&indexAttempt===1){res.writeHead(404);res.end('Controlled metadata failure');return;}}
try{let bytes;if(routes[path])bytes=Buffer.from(routes[path]);else{const file=resolve(root,'.'+decodeURIComponent(path));if(!file.startsWith(root+'/'))throw Error('Outside root');bytes=await readFile(file);}
if(transportMode==='corrupt_body'&&path.endsWith('.body')){bytes=Buffer.from(bytes);bytes[0]^=1;}
res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.html')?'text/html':path.endsWith('.css')?'text/css':'application/octet-stream');res.setHeader('Content-Length',bytes.length);res.end(bytes);
}catch{res.writeHead(404);res.end('Missing fixture file');}});
await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
const origin=`http://127.0.0.1:${server.address().port}`;
"""
            + "const runtime=await launchChromium("
            + json.dumps(binary)
            + ","
            + json.dumps(str(profile))
            + ");\n"
            + """
let cdp;
try{const endpoint=await debuggerEndpoint(runtime.browser,15000);const debuggerOrigin=new URL(endpoint);debuggerOrigin.protocol='http:';
const target=await(await fetch(`${debuggerOrigin.origin}/json/new?about:blank`,{method:'PUT'})).json();cdp=await connectCdp(target.webSocketDebuggerUrl);
cdp.onEvent(event=>{if(event.method==='Runtime.exceptionThrown')failures.push(event.params.exceptionDetails);if(event.method==='Fetch.requestPaused'){const {requestId,request}=event.params;void cdp.send(request.url.startsWith(origin+'/')?'Fetch.continueRequest':'Fetch.failRequest',request.url.startsWith(origin+'/')?{requestId}:{requestId,errorReason:'BlockedByClient'});}});
const downloadDirectory=root+'/verified-downloads';await mkdir(downloadDirectory,{recursive:true});
await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadDirectory});
await cdp.send('Page.enable');await cdp.send('Runtime.enable');await cdp.send('Fetch.enable',{patterns:[{urlPattern:'http*',requestStage:'Request'}]});
"""
            + f"await cdp.send('Emulation.setDeviceMetricsOverride',{{width:{width},height:{height},deviceScaleFactor:1,mobile:false}});\n"
            + "const loaded=cdp.waitFor('Page.loadEventFired',15000);await cdp.send('Page.navigate',{url:origin+'/index.html' + "
            + json.dumps(query)
            + " + '#basemap=none'});if(transportMode!=='hold_tools')await loaded;else for(let n=0;n<200;n++){if(await evaluate(cdp,\"Boolean(document.getElementById('source-resources-open'))\"))break;await new Promise(ok=>setTimeout(ok,10));}\n"
            + (
                "const result=await(async()=>{" + driver + "})();"
                if driver is not None
                else "const result=await evaluate(cdp," + json.dumps(expression) + ");"
            )
            + "const downloads=[];for(const name of await readdir(downloadDirectory)){downloads.push({name,bytes:[...await readFile(downloadDirectory+'/'+name)]});}const screenshot=root+'/reader.png';await writeFile(screenshot,Buffer.from((await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})).data,'base64'));console.log(JSON.stringify({result,calls,failures,downloads,screenshot}));\n"
            + "}finally{cdp?.close();await runtime.close();await new Promise(ok=>server.close(ok));}\n"
        )
        completed = subprocess.run(
            ["node", str(operator)],
            capture_output=True,
            text=True,
            timeout=90,
            check=True,
        )
        return cast(dict[str, Any], json.loads(completed.stdout))

    return probe


def wide_metadata_archive(root: Path) -> tuple[Path, str, Path, str]:
    """Capture 35 controlled metadata resources; never request numerical bodies."""
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataPlan,
        NeotomaMetadataResponse,
        capture_neotoma_metadata,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
        build_neotoma_resource_catalogue,
        write_neotoma_resource_catalogue,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    polygon = {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [[11, 61], [13, 61], [13, 62], [11, 62], [11, 61]],
                [[11.5, 61.2], [12, 61.2], [12, 61.5], [11.5, 61.5], [11.5, 61.2]],
            ],
            [[[14, 61], [15, 61], [15, 62], [14, 62], [14, 61]]],
        ],
    }
    datasets: list[dict[str, Any]] = [
        {
            "datasetid": identity,
            "datasettype": "pollen" if identity % 2 else "charcoal",
            "database": None,
            "doi": [],
            "datasetpi": [],
        }
        for identity in range(301, 336)
    ]
    document = {
        "status": "success",
        "data": [
            {
                "site": {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "sitename": "<img src=x onerror=alert(1)> Native extent",
                    "geography": json.dumps(polygon),
                    "datasets": datasets,
                }
            }
        ],
    }
    body = json.dumps(document).encode()
    captured = capture_neotoma_metadata(
        root / "wide-metadata",
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
    )
    rows = [
        {
            "dataset_id": row["datasetid"],
            "site_id": 12,
            "collection_unit_id": 100,
            "dataset_type": row["datasettype"],
            "database": None,
            "dataset_doi_values": [],
            "metadata_locator": {
                "response_sha256": sha256(body).hexdigest(),
                "json_pointer": f"/data/0/site/datasets/{offset}",
            },
            "exposure_roles": {
                "current": "development_resource_discovery",
                "doi_frozen": "development_resource_discovery",
            },
            "role_authority": "Controlled metadata-only exposure declaration",
        }
        for offset, row in enumerate(datasets)
    ]
    roster = root / "wide-roster.json"
    roster.write_text(
        json.dumps(
            {
                "schema_version": "neotoma-native-resource-candidate-roster.v1",
                "resource_count": len(rows),
                "resources": rows,
                "source_metadata_capture_manifest_sha256": [captured.manifest_sha256],
                "policy_sources": [
                    "https://www.neotomadb.org/data/data-use-and-embargo-policy"
                ],
            }
        )
    )
    sources = {captured.manifest_sha256: root / "wide-metadata"}
    catalogue = build_neotoma_resource_catalogue(
        roster_path=roster,
        expected_roster_sha256=sha256(roster.read_bytes()).hexdigest(),
        metadata_captures=sources,
        resource_captures={},
        country_boundaries={},
    )
    output = root / "wide-catalogue"
    write_neotoma_resource_catalogue(
        output, catalogue=catalogue, roster_path=roster, capture_sources=sources
    )
    digest = sha256((output / "manifest.json").read_bytes()).hexdigest()
    archive = root / "wide-archive"
    write_neotoma_source_archive(
        archive,
        catalogue_directory=output,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    return (
        output,
        digest,
        archive,
        sha256((archive / "manifest.json").read_bytes()).hexdigest(),
    )
