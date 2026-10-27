"""Independent physical-packet/browser parity on manually declared logical fields."""

from __future__ import annotations

import base64
from copy import deepcopy
import gzip
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    build_index_bundle,
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (
    decode_index_payloads,
)
from bijux_pollenomics.reporting.map_document.static_assets.search import (
    validate_search_membership,
)
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from ..support import run_node_json, template_block

PART_SCHEMA = "atlas-static-index-part.v1"
SEARCH_TRANSPORT = "atlas-search-documents.v1"


def logical_fields(mode: str = "legacy") -> dict[str, Any]:
    intervals = [[100, 110, "pollen", 0], [300, 310, "pollen", 1]]
    if mode == "components":
        intervals = [
            [100, 110, "pollen", 0],
            [300, 310, "pollen", 0],
            [500, 510, "pollen", 1],
        ]
    if mode == "signed":
        intervals = [[-55, -50, "pollen", 0], [100, 110, "pollen", 1]]
    return {
        "schema_version": "atlas-static-signed-indexes.v1"
        if mode == "signed"
        else "atlas-static-indexes.v2",
        "scope_slug": "fixture",
        "version": "v66",
        "build_id": "atlas-" + "a" * 64,
        **({"component_time_support": True} if mode == "components" else {}),
        **(
            {"temporal_profile": "calendar-bp1950-signed.v1", "temporal_axis": "BP1950"}
            if mode == "signed"
            else {}
        ),
        "country_feature_indexes": {"Sweden": {"pollen": [0, 1]}},
        "spatial_degree_feature_indexes": {"55:13": {"pollen": [0, 1]}},
        "time_interval_feature_indexes": intervals,
        "signal_layer_indexes": {"pollen-signal": ["pollen"]},
        "detail_record_asset_keys": {"site:1": "details:4", "site:2": "details:4"},
        "search_index_abi": "atlas-substring-postings.v1",
        "text_search_index": {
            "d:0:0": {
                "layer_index": 0,
                "feature_index": 0,
                "layer_key": "pollen",
                "record_id": "site:1",
                "text": "a",
            },
            "d:0:1": {
                "layer_index": 0,
                "feature_index": 1,
                "layer_key": "pollen",
                "record_id": "site:2",
                "text": "b",
            },
            "p:0061": ["d:0:0"],
            "p:0062": ["d:0:1"],
        },
    }


def literal_digest(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def packets(
    mode: str = "legacy", *, split: bool = True, unicode_identity: bool = False
) -> dict[str, Any]:
    expected = logical_fields(mode)
    if unicode_identity:
        expected["version"] = "Åland-💠-\x7f"
    bundle = build_index_bundle(expected)
    manifest: dict[str, Any] = {
        "schema_version": "atlas-static-bootstrap.v3"
        if mode == "signed"
        else "atlas-static-bootstrap.v2",
        **{
            key: value
            for key, value in expected.items()
            if key
            in {
                "scope_slug",
                "version",
                "build_id",
                "temporal_profile",
                "temporal_axis",
            }
        },
        "compatibility": {
            "index_schema": bundle["schema_version"],
            "search_index_abi": expected["search_index_abi"],
            **({"index_transport_schema": PART_SCHEMA} if split else {}),
        },
        "domains": {"indexes": {"record_count": 4}},
        "budgets": {"chunk_max_bytes": 4194304},
    }
    rows: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    if split:
        shards = cast(list[dict[str, Any]], bundle["shards"])
        middle = len(shards) // 2
        assert 0 < middle < len(shards)
        header = {key: value for key, value in bundle.items() if key != "shards"}
        for number, (first, stop) in enumerate(((0, middle), (middle, len(shards))), 1):
            key = f"indexes:{11 + number}"
            rows.append(
                {
                    "asset_key": key,
                    "sequence": 11 + number,
                    "domain": "indexes",
                    "record_count": stop - first,
                }
            )
            payloads[key] = {
                **header,
                "schema_version": PART_SCHEMA,
                "bundle_schema": bundle["schema_version"],
                "bundle_sha256": literal_digest(bundle),
                "part_number": number,
                "part_count": 2,
                "first_shard_number": first + 1,
                "last_shard_number": stop,
                "shards": deepcopy(shards[first:stop]),
                "asset_key": key,
            }
    else:
        rows.append(
            {
                "asset_key": "indexes:12",
                "sequence": 12,
                "domain": "indexes",
                "record_count": 4,
            }
        )
        payloads["indexes:12"] = {**bundle, "asset_key": "indexes:12"}
    manifest["assets"] = rows
    return {
        "rows": rows,
        "payloads": payloads,
        "manifest": manifest,
        "expected": expected,
    }


def browser(
    packet: dict[str, Any], *, action: str = "serial", reverse: bool = False
) -> dict[str, Any]:
    assets = files("bijux_pollenomics.reporting.map_document").joinpath("assets")
    native_number = NATIVE_LRA_CONTROLLER[
        NATIVE_LRA_CONTROLLER.index(
            "function nativeCalendarNumber"
        ) : NATIVE_LRA_CONTROLLER.index("function nativeCalendarSame")
    ]
    source = (
        "globalThis.crypto=require('node:crypto').webcrypto;"
        "const data="
        + json.dumps({**packet, "action": action, "reverse": reverse})
        + ";"
        + "const STATIC_ATLAS_BOOTSTRAP=data.manifest;"
        + template_block(
            "function staticAtlasFailure", "function staticAtlasNonnegativeInteger"
        )
        + template_block(
            "function staticAtlasNonnegativeInteger",
            "function staticAtlasNullableFiniteNumber",
        )
        + template_block(
            "function staticAtlasTemporalIdentity",
            "function normalizeStaticAtlasBootstrap",
        )
        + template_block(
            "async function staticAtlasSha256",
            "async function staticAtlasBoundedGunzip",
        )
        + template_block(
            "async function staticAtlasBoundedGunzip",
            "function indexTransportDescriptor",
        )
        + native_number
        + assets.joinpath("index-transport.js").read_text()
        + assets.joinpath("search-index.js").read_text()
        + r"""
(async()=>{
  try {
    const controller=globalThis.BijuxPollenomicsIndexTransport.create({
      bootstrap:STATIC_ATLAS_BOOTSTRAP,failure:staticAtlasFailure,
      temporalIdentity:staticAtlasTemporalIdentity,nonnegativeInteger:staticAtlasNonnegativeInteger,
      nativeCalendarNumber,boundedGunzip:staticAtlasBoundedGunzip,sha256:staticAtlasSha256,
      searchGrams:atlasSearchGrams});
    const rows=data.rows, ordered=data.reverse?[...rows].reverse():rows;
    const consume=row=>controller.consume(row,data.payloads[row.asset_key],rows);
    let results;
    if(data.action==='concurrent') results=await Promise.all(ordered.map(consume));
    else if(data.action==='repeat') {
      results=[await consume(rows[0]),await consume(rows[0])];
      for(const row of rows.slice(1))results.push(await consume(row));
      results.push(await consume(rows[rows.length-1]));
    } else if(data.action==='conflict') {
      await consume(rows[0]);
      const changed=structuredClone(data.payloads[rows[0].asset_key]);
      changed.bundle_sha256='b'.repeat(64);
      await controller.consume(rows[0],changed,rows);
      console.log(JSON.stringify({accepted_conflicting_repeat:true}));
      return;
    } else if(data.action==='partial') results=[await consume(rows[0])];
    else {results=[];for(const row of ordered)results.push(await consume(row));}
    const completed=results.filter(value=>value!==null);
    const decoded=completed[completed.length-1]||null;
    let searches=null;
    let queryCases=null;
    if(decoded && data.action==='decode_only') {
      // Exercise the codec independently of source-layer admission and UI preparation.
    } else if(decoded && data.corpus) {
      const layers=data.corpus.layers;
      const metadata=layers.map((layer,layer_index)=>({layer_kind:'point',layer_index,feature_count:layer.features.length,layer}));
      const published=atlasPublishedSearch(decoded,metadata);
      const entries=layers.flatMap((layer,i)=>layer.features.map((feature,j)=>({layer,feature,key:`d:${i}:${j}`})));
      const subsets=[entries,entries.filter((_,i)=>i%2===0),[...entries].reverse()];
      queryCases=[];
      for(const subset of subsets) {
        // Identity is supplied explicitly, independent of the published postings.
        const fixed=atlasPrepareVisibleSearch(published,subset,feature=>entries.find(row=>row.feature===feature).key,()=> '');
        for(const query of data.corpus.queries) {
          const actual=atlasLookupSearch(fixed,query).map(entry=>entry.key);
          const expected=subset.filter(({layer,feature})=>`${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''} `.toLowerCase().includes(query)).slice(0,12).map(entry=>entry.key);
          queryCases.push({query,actual,expected});
        }
      }
    } else if(decoded) {
      const published=atlasPublishedSearch(decoded,[{layer_kind:'point',layer_index:0,feature_count:2,layer:{key:'pollen'}}]);
      const visible=new Map(['a','b'].map((text,index)=>[`d:0:${index}`,{order:index,text,entry:{record_id:`site:${index+1}`}}]));
      const state={published,visible,fallback:[]};
      searches=Object.fromEntries(['a','b','absent'].map(query=>[query,atlasLookupSearch(state,query).map(row=>row.record_id)]));
    }
    console.log(JSON.stringify({decoded,published:results.map(value=>value!==null),searches,...(queryCases?{queryCases}:{})}));
  } catch(error) {console.log(JSON.stringify({refusal:error.message}));}
})();
"""
    )
    return cast(dict[str, Any], run_node_json(source))


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
@pytest.mark.parametrize("reverse", [False, True])
def test_manual_packets_preserve_logical_fields_and_queries(
    mode: str, reverse: bool
) -> None:
    packet = packets(mode)
    assert (
        decode_index_payloads(
            packet["rows"], packet["payloads"], manifest=packet["manifest"]
        )
        == packet["expected"]
    )
    observed = browser(packet, action="concurrent", reverse=reverse)
    assert "refusal" not in observed
    assert sum(observed["published"]) == 1
    assert {key: observed["decoded"][key] for key in packet["expected"]} == packet[
        "expected"
    ]
    assert observed["decoded"]["reference_count"] == 4
    assert observed["searches"] == {"a": ["site:1"], "b": ["site:2"], "absent": []}


def test_partial_and_authenticated_repeat_do_not_publish_incomplete_or_duplicate_indexes() -> (
    None
):
    packet = packets()
    partial = browser(packet, action="partial")
    assert partial == {"decoded": None, "published": [False], "searches": None}
    repeated = browser(packet, action="repeat")
    assert repeated["published"] == [False, False, True, True]
    assert repeated["decoded"]["country_feature_indexes"] == {
        "Sweden": {"pollen": [0, 1]}
    }
    assert repeated["decoded"]["reference_count"] == 4
    assert "refusal" in browser(packet, action="conflict")


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
def test_singleton_path_keeps_legacy_logical_semantics(mode: str) -> None:
    packet = packets(mode, split=False)
    observed = browser(packet)
    assert "refusal" not in observed
    assert observed["published"] == [True]
    assert {key: observed["decoded"][key] for key in packet["expected"]} == packet[
        "expected"
    ]
    assert "index_transport_schema" not in packet["manifest"]["compatibility"]


def test_python_ascii_escaping_matches_actual_browser_bundle_hash() -> None:
    packet = packets(unicode_identity=True)
    observed = browser(packet)
    assert "refusal" not in observed
    assert observed["decoded"]["version"] == "Åland-💠-\x7f"


@pytest.mark.parametrize(
    "corruption",
    [
        "missing",
        "duplicate_part",
        "manifest_reorder",
        "mixed_build",
        "mixed_abi",
        "mixed_profile",
        "bundle_digest",
        "local_count",
        "global_count",
        "null_transport",
        "gapped_sequence",
        "duplicate_shard",
    ],
)
def test_python_and_actual_browser_refuse_invalid_complete_transport(
    corruption: str,
) -> None:
    packet = packets()
    rows, payloads, manifest = packet["rows"], packet["payloads"], packet["manifest"]
    first, second = (payloads[row["asset_key"]] for row in rows)
    if corruption == "missing":
        del payloads[rows.pop()["asset_key"]]
    elif corruption == "duplicate_part":
        second["part_number"] = first["part_number"]
    elif corruption == "manifest_reorder":
        rows.reverse()
    elif corruption == "mixed_build":
        second["build_id"] = "atlas-" + "b" * 64
    elif corruption == "mixed_abi":
        second["search_index_abi"] = "another-abi"
    elif corruption == "mixed_profile":
        second.update(
            temporal_profile="calendar-bp1950-signed.v1", temporal_axis="BP1950"
        )
    elif corruption == "bundle_digest":
        first["bundle_sha256"] = second["bundle_sha256"] = "b" * 64
    elif corruption == "local_count":
        rows[0]["record_count"] = 4
    elif corruption == "global_count":
        manifest["domains"]["indexes"]["record_count"] = first["shard_count"]
    elif corruption == "null_transport":
        manifest["compatibility"]["index_transport_schema"] = None
    elif corruption == "gapped_sequence":
        old = rows[1]["asset_key"]
        rows[1].update(sequence=14, asset_key="indexes:14")
        payloads["indexes:14"] = payloads.pop(old)
        payloads["indexes:14"]["asset_key"] = "indexes:14"
    else:
        copied = deepcopy(first["shards"][0])
        copied["shard_number"] = second["first_shard_number"]
        second["shards"][0] = copied
    with pytest.raises(ValueError):
        decode_index_payloads(rows, payloads, manifest=manifest)
    assert "refusal" in browser(packet)


def reference_grams(text: str) -> set[str]:
    """Construct code units by arithmetic, independently of the UTF-16 codec."""
    units: list[int] = []
    for character in text:
        point = ord(character)
        if point <= 0xFFFF:
            units.append(point)
        else:
            point -= 0x10000
            units.extend((0xD800 + point // 1024, 0xDC00 + point % 1024))
    return {
        "".join(f"{value:04x}" for value in units[start : start + width])
        for width in (1, 2, 3)
        for start in range(len(units) - width + 1)
    }


def reference_map(documents: dict[str, Any]) -> dict[str, Any]:
    postings: dict[str, list[str]] = {}
    for key in sorted(documents):
        for gram in reference_grams(documents[key]["text"]):
            postings.setdefault("p:" + gram, []).append(key)
    return dict(sorted({**documents, **postings}.items()))


def codec_corpus(mode: str = "legacy") -> tuple[dict[str, Any], dict[str, Any]]:
    titles = [
        "common common aaa",
        "common älg",
        "common 💠",
        "",
        "common \ud83d",
        "common \udca0",
        "common e\u0301",
        "common é",
        "common punctuation.(",
        "common </script>",
        "common 10",
        "common 11",
        "common 12",
        "common 13",
        "common source -55 bp",
        "common refused c14",
    ]
    layers: list[dict[str, Any]] = [
        {
            "key": f"layer:{layer}",
            "label": "",
            "features": [
                {
                    "title": title,
                    "record_id": "repeated-source-id" if position % 2 else None,
                }
                for position, title in enumerate(titles)
            ],
        }
        for layer in range(2)
    ]
    documents: dict[str, Any] = {
        f"d:{layer}:{position}": {
            "layer_index": layer,
            "feature_index": position,
            "layer_key": f"layer:{layer}",
            "record_id": feature["record_id"],
            "text": feature["title"] + "    ",
        }
        for layer, row in enumerate(layers)
        for position, feature in enumerate(row["features"])
    }
    expected = logical_fields(mode)
    expected["text_search_index"] = reference_map(documents)
    corpus = {
        "layers": layers,
        "queries": [
            "c",
            "co",
            "com",
            "common",
            "aaa",
            "💠",
            "\ud83d",
            "\udca0",
            "älg",
            "e\u0301",
            "é",
            ".(",
            "</script>",
            "-55",
            "refused",
            "missing",
        ],
    }
    return expected, corpus


def codec_packet(
    monkeypatch: pytest.MonkeyPatch, mode: str = "legacy"
) -> dict[str, Any]:
    expected, corpus = codec_corpus(mode)
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.map_document.static_assets.index_bundles.ATLAS_CHUNK_TARGET_BYTES",
        1200,
    )
    bundle = cast(
        dict[str, Any],
        build_index_bundle(
            expected,
            search_transport_schema=SEARCH_TRANSPORT,
        ),
    )
    shards = bundle["shards"]
    search_numbers = [
        i for i, row in enumerate(shards) if row["index_kind"] == "text_search_index"
    ]
    assert len(search_numbers) >= 3
    cut = search_numbers[1]
    packet = packets(mode)
    packet.update(expected=expected, corpus=corpus)
    packet["manifest"]["compatibility"]["search_transport_schema"] = SEARCH_TRANSPORT
    header = {key: value for key, value in bundle.items() if key != "shards"}
    for number, (start, stop) in enumerate(((0, cut), (cut, len(shards))), 1):
        key = f"indexes:{11 + number}"
        packet["rows"][number - 1]["record_count"] = stop - start
        packet["payloads"][key] = {
            **header,
            "schema_version": PART_SCHEMA,
            "bundle_schema": bundle["schema_version"],
            "bundle_sha256": literal_digest(bundle),
            "part_number": number,
            "part_count": 2,
            "first_shard_number": start + 1,
            "last_shard_number": stop,
            "shards": deepcopy(shards[start:stop]),
            "asset_key": key,
        }
    packet["bundle"] = bundle
    return packet


def native_corpus_payloads(corpus: dict[str, Any]) -> dict[str, Any]:
    layers = corpus["layers"]
    payloads: dict[str, Any] = {
        "provenance": {
            "schema_version": "atlas-provenance-chunk.v1",
            "layers": [
                {
                    "layer_kind": "point",
                    "layer_index": i,
                    "layer": layer,
                    "feature_count": len(layer["features"]),
                }
                for i, layer in enumerate(layers)
            ],
        }
    }
    for i, layer in enumerate(layers):
        payloads[f"nodes:{i}"] = {
            "schema_version": "atlas-node-chunk.v1",
            "layer_kind": "point",
            "layer_index": i,
            "layer_key": layer["key"],
            "features": layer["features"],
            "feature_indexes": list(range(len(layer["features"]))),
        }
    return payloads


@pytest.mark.parametrize("mode", ["legacy", "signed", "components"])
def test_documents_codec_recovers_full_map_and_literal_query_answers(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    packet = codec_packet(monkeypatch, mode)
    expected = packet["expected"]
    original = cast(dict[str, Any], build_index_bundle(expected))
    documents = {
        key: row
        for key, row in expected["text_search_index"].items()
        if key.startswith("d:")
    }
    postings = {
        key: row
        for key, row in expected["text_search_index"].items()
        if key.startswith("p:")
    }
    assert packet["bundle"]["search_transport_counts"] == {
        "document_count": 32,
        "utf16_unit_count": sum(
            2 if ord(character) > 0xFFFF else 1
            for row in documents.values()
            for character in row["text"]
        ),
        "posting_key_count": len(postings),
        "posting_reference_count": sum(map(len, postings.values())),
    }
    assert packet["bundle"]["build_id"] == original["build_id"] == expected["build_id"]
    assert literal_digest(packet["bundle"]) != literal_digest(original)
    assert [
        row
        for row in packet["bundle"]["shards"]
        if row["index_kind"] != "text_search_index"
    ] == [row for row in original["shards"] if row["index_kind"] != "text_search_index"]
    assert decode_index_bundle(packet["bundle"]) == expected
    assert (
        decode_index_payloads(
            packet["rows"], packet["payloads"], manifest=packet["manifest"]
        )
        == expected
    )
    validate_search_membership(
        native_corpus_payloads(packet["corpus"]),
        expected,
        expected.get("temporal_profile"),
    )
    assert expected["text_search_index"]["p:0063"][:4] == [
        "d:0:0",
        "d:0:1",
        "d:0:10",
        "d:0:11",
    ]
    assert "d83ddca0" in reference_grams("💠")
    assert reference_grams("aaa") == {"0061", "00610061", "006100610061"}
    observed = browser(packet, action="concurrent", reverse=True)
    assert "refusal" not in observed
    assert {key: observed["decoded"][key] for key in expected} == expected
    assert sum(observed["published"]) == 1
    assert len(observed["queryCases"]) == 48
    assert all(row["actual"] == row["expected"] for row in observed["queryCases"])
    assert (
        len(
            next(row for row in observed["queryCases"] if row["query"] == "common")[
                "actual"
            ]
        )
        == 12
    )


def rewrite_search_packet(bundle: dict[str, Any], mutation: str) -> None:
    shard = next(
        row
        for row in bundle["shards"]
        if (row["index_kind"] == "text_search_index")
        != (mutation in {"nonsearch_tag", "nonsearch_counts"})
    )
    body = json.loads(gzip.decompress(base64.b64decode(shard["payload_gzip_base64"])))
    if mutation in {"shard_counts", "nonsearch_counts"}:
        body["search_transport_counts"] = None
    elif mutation == "nonsearch_tag":
        body["search_transport_schema"] = SEARCH_TRANSPORT
    elif mutation == "shard_tag":
        body["search_transport_schema"] = "unsupported"
    elif mutation == "missing_shard_tag":
        del body["search_transport_schema"]
    elif mutation == "posting_in_documents":
        body["entries"].append(["p:0061", ["d:0:0"]])
    elif mutation == "duplicate_document":
        body["entries"].append(deepcopy(body["entries"][0]))
    elif mutation == "missing_document":
        body["entries"].pop(0)
    else:
        body["entries"][0][1]["feature_index"] = 999
    encoded = json.dumps(
        body, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode()
    shard.update(
        decoded_byte_count=len(encoded),
        record_count=len(body["entries"]),
        payload_sha256=sha256(encoded).hexdigest(),
        payload_gzip_base64=base64.b64encode(gzip.compress(encoded, mtime=0)).decode(),
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "shard_tag",
        "missing_shard_tag",
        "posting_in_documents",
        "duplicate_document",
        "missing_document",
        "foreign_position",
        "null_tag",
        "missing_tag",
        "document_count",
        "utf16_unit_count",
        "posting_key_count",
        "posting_reference_count",
        "compat_missing",
        "compat_null",
        "compat_counts",
        "nonsearch_tag",
        "shard_counts",
        "nonsearch_counts",
        "extra_count",
        "null_counts",
        "boolean_count",
        "fractional_count",
    ],
)
def test_documents_codec_refuses_self_consistent_malformed_search_packets(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    packet = codec_packet(monkeypatch)
    bundle = packet["bundle"]
    if mutation.startswith("compat_"):
        compatibility = packet["manifest"]["compatibility"]
        if mutation == "compat_missing":
            del compatibility["search_transport_schema"]
        elif mutation == "compat_null":
            compatibility["search_transport_schema"] = None
        else:
            compatibility["search_transport_counts"] = deepcopy(
                bundle["search_transport_counts"]
            )
    elif mutation == "extra_count":
        bundle["search_transport_counts"]["unknown"] = 1
    elif mutation == "null_counts":
        bundle["search_transport_counts"] = None
    elif mutation in {"boolean_count", "fractional_count"}:
        bundle["search_transport_counts"]["document_count"] = (
            True if mutation == "boolean_count" else 1.25
        )
    elif mutation in {"null_tag", "missing_tag"}:
        if mutation == "null_tag":
            bundle["search_transport_schema"] = None
        else:
            del bundle["search_transport_schema"]
    elif mutation in bundle["search_transport_counts"]:
        bundle["search_transport_counts"][mutation] += 1
    else:
        rewrite_search_packet(bundle, mutation)
    shards = bundle["shards"]
    for payload in packet["payloads"].values():
        start, stop = payload["first_shard_number"] - 1, payload["last_shard_number"]
        for key in ("search_transport_schema", "search_transport_counts"):
            payload.pop(key, None)
            if key in bundle:
                payload[key] = deepcopy(bundle[key])
        payload["shards"] = deepcopy(shards[start:stop])
        payload["bundle_sha256"] = literal_digest(bundle)
    with pytest.raises(ValueError):
        decode_index_payloads(
            packet["rows"], packet["payloads"], manifest=packet["manifest"]
        )
    assert "refusal" in browser(packet)


def test_documents_encoder_rejects_invalid_postings_and_preserves_empty_documents() -> (
    None
):
    from bijux_pollenomics.reporting.map_document.static_assets.search.transport import (
        encode_search_documents,
        restore_search_documents,
    )

    expected, _ = codec_corpus()
    bad = deepcopy(expected["text_search_index"])
    bad["p:0063"] = []
    with pytest.raises(ValueError):
        encode_search_documents(bad)
    documents = {
        "d:0:0": {
            "layer_index": 0,
            "feature_index": 0,
            "layer_key": "empty",
            "record_id": None,
            "text": "",
        }
    }
    encoded, counts = encode_search_documents(documents)
    assert encoded == documents
    assert counts == {
        "document_count": 1,
        "utf16_unit_count": 0,
        "posting_key_count": 0,
        "posting_reference_count": 0,
    }
    assert restore_search_documents(encoded, counts) == documents


def test_actual_browser_codec_retains_empty_document_without_postings() -> None:
    packet = packets(split=False)
    expected = packet["expected"]
    expected["text_search_index"]["d:0:0"]["text"] = ""
    del expected["text_search_index"]["p:0061"]
    bundle = build_index_bundle(expected, search_transport_schema=SEARCH_TRANSPORT)
    packet["payloads"]["indexes:12"] = {**bundle, "asset_key": "indexes:12"}
    packet["manifest"]["compatibility"]["search_transport_schema"] = SEARCH_TRANSPORT
    observed = browser(packet, action="decode_only")
    assert "refusal" not in observed
    assert observed["decoded"]["text_search_index"] == expected["text_search_index"]


@pytest.mark.parametrize("mutation", ["title", "record_id", "position"])
def test_recovered_search_retains_exact_source_join(mutation: str) -> None:
    expected, corpus = codec_corpus()
    sources = native_corpus_payloads(corpus)
    validate_search_membership(sources, expected, None)
    if mutation == "position":
        sources["nodes:0"]["feature_indexes"][0] = 999
    else:
        sources["nodes:0"]["features"][0][mutation] = "foreign-source-value"
    with pytest.raises(ValueError):
        validate_search_membership(sources, expected, None)
