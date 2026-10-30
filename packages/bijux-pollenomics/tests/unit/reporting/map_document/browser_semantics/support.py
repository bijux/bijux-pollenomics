from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def template_block(start: str, end: str) -> str:
    start_index = MAP_DOCUMENT_TEMPLATE.index(start)
    return MAP_DOCUMENT_TEMPLATE[
        start_index : MAP_DOCUMENT_TEMPLATE.index(end, start_index)
    ]


def index_transport_helpers(*, common: bool = True) -> str:
    """Execute the packaged index factory with the maintained browser callbacks."""
    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/index-transport.js")
        .read_text()
    )
    search = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/search-index.js")
        .read_text()
    )
    source = (
        search[
            search.index("function atlasSearchGrams") : search.index(
                "function atlasPublishedSearch"
            )
        ]
        + source
    )
    if common:
        source = (
            template_block(
                "async function staticAtlasBoundedGunzip",
                "function indexTransportDescriptor",
            )
            + source
        )
    return (
        source
        + """
const staticAtlasIndexTransport=globalThis.BijuxPollenomicsIndexTransport.create({
 bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,
 temporalIdentity:staticAtlasTemporalIdentity,nonnegativeInteger:staticAtlasNonnegativeInteger,
 nativeCalendarNumber:value=>typeof nativeCalendarNumber==='function'&&nativeCalendarNumber(value),
 boundedGunzip:staticAtlasBoundedGunzip,sha256:staticAtlasSha256,searchGrams:atlasSearchGrams});
const staticAtlasMergeIndexShards=staticAtlasIndexTransport.mergeShards;
"""
    )


def run_node_json(source: str) -> Any:
    node = shutil.which("node")
    assert node is not None, "Node.js is required to verify browser semantics"
    result = subprocess.run(
        [node, "-"],
        input=source,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def check_javascript_syntax(source: str, path: Path) -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required to verify browser syntax"
    path.write_text(source, encoding="utf-8")
    subprocess.run([node, "--check", str(path)], check=True, capture_output=True)


__all__ = [
    "check_javascript_syntax",
    "index_transport_helpers",
    "run_node_json",
    "template_block",
]
