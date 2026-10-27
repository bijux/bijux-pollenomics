"""Document wire transport restores the exact complete published search map."""

from __future__ import annotations

import base64
from copy import deepcopy
import gzip
import hashlib
import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import index_bundles
from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (
    decode_index_payloads,
    partition_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.search import (
    SEARCH_KIND,
    build_search_index,
    transport,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
)

from .test_index_transport import inventory, logical


def search_map() -> dict[str, object]:
    return build_search_index(
        [
            {
                "key": "native",
                "label": "Literal source",
                "features": [
                    {
                        "record_id": "repeated" if index in (2, 10) else None,
                        "title": f"A😀é\ud800 source {index}",
                        "subtitle": "ß source",
                        "country": "Sweden",
                    }
                    for index in range(12)
                ],
            }
        ]
    )


def encoded_logical() -> dict[str, Any]:
    data = logical(components=True)
    data[SEARCH_KIND] = search_map()
    return data


def rewrite(
    envelope: dict[str, Any], update: dict[str, object], *, remove: tuple[str, ...] = ()
) -> None:
    shard = json.loads(
        gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"]))
    )
    shard.update(update)
    for key in remove:
        shard.pop(key)
    raw = canonical_json(shard).encode()
    envelope.update(
        decoded_byte_count=len(raw),
        payload_sha256=hashlib.sha256(raw).hexdigest(),
        payload_gzip_base64=base64.b64encode(gzip.compress(raw, mtime=0)).decode(),
    )


def test_documents_preserve_every_literal_and_restore_all_postings() -> None:
    original = search_map()
    before = canonical_json(original)
    documents, counts = transport.encode_search_documents(original)
    assert documents == {
        key: value for key, value in original.items() if key.startswith("d:")
    }
    assert counts["document_count"] == 12
    assert counts["posting_key_count"] == sum(key.startswith("p:") for key in original)
    assert (
        transport.restore_search_documents(
            dict(reversed(list(documents.items()))), counts
        )
        == original
    )
    assert canonical_json(original) == before
    restored = transport.restore_search_documents(documents, counts)
    positions = cast(list[str], restored["p:0020"])
    assert positions.index("d:0:10") < positions.index("d:0:2")


@pytest.mark.parametrize(
    "damage", ["missing_posting", "missing_member", "duplicate_member"]
)
def test_encoder_refuses_invalid_original_full_map(damage: str) -> None:
    rows: dict[str, Any] = deepcopy(search_map())
    posting = next(
        key for key, value in rows.items() if key.startswith("p:") and len(value) > 1
    )
    if damage == "missing_posting":
        del rows[posting]
    elif damage == "missing_member":
        rows[posting].pop()
    else:
        rows[posting].append(rows[posting][0])
    with pytest.raises(ValueError, match="postings"):
        transport.encode_search_documents(rows)


@pytest.mark.parametrize("field", transport.SEARCH_TRANSPORT_COUNT_FIELDS)
@pytest.mark.parametrize("delta", [-1, 1])
def test_each_declared_resource_count_is_exact(field: str, delta: int) -> None:
    documents, counts = transport.encode_search_documents(search_map())
    counts[field] += delta
    with pytest.raises(ValueError, match="search transport"):
        transport.restore_search_documents(documents, counts)


@pytest.mark.parametrize("bad", [None, {}, {"other": 0}, True, 1.0, -1, 2**53])
def test_counts_are_closed_nonnegative_safe_integers(bad: object) -> None:
    _, counts = transport.encode_search_documents(search_map())
    malformed = (
        bad
        if bad is None or isinstance(bad, dict)
        else {**counts, "document_count": bad}
    )
    with pytest.raises(ValueError):
        transport.validate_search_transport_counts(malformed)


def test_document_units_refuse_before_gram_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents, counts = transport.encode_search_documents(search_map())
    counts["utf16_unit_count"] = 0

    def forbidden(_text: str) -> set[str]:
        raise AssertionError(
            "grams must not run after the declared unit count is exceeded"
        )

    monkeypatch.setattr(transport, "grams", forbidden)
    with pytest.raises(ValueError, match="utf16_unit_count"):
        transport.restore_search_documents(documents, counts)


def test_default_encoder_is_legacy_and_nonsearch_shards_are_byte_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = encoded_logical()
    legacy = index_bundles.build_index_bundle(data)
    assert legacy == index_bundles.build_index_bundle(
        data, search_transport_schema=None
    )
    monkeypatch.setattr(index_bundles, "ATLAS_CHUNK_TARGET_BYTES", 900)
    legacy = index_bundles.build_index_bundle(data)
    packed = index_bundles.build_index_bundle(
        data, search_transport_schema=transport.SEARCH_DOCUMENTS_SCHEMA
    )
    legacy_shards = cast(list[dict[str, Any]], legacy["shards"])
    packed_shards = cast(list[dict[str, Any]], packed["shards"])
    assert [row for row in legacy_shards if row["index_kind"] != SEARCH_KIND] == [
        row for row in packed_shards if row["index_kind"] != SEARCH_KIND
    ]
    assert index_bundles.decode_index_bundle(packed) == data
    search_shards = [row for row in packed_shards if row["index_kind"] == SEARCH_KIND]
    assert len(search_shards) > 1
    assert sum(row["record_count"] for row in search_shards) == 12
    for row in packed_shards:
        decoded = json.loads(
            gzip.decompress(base64.b64decode(row["payload_gzip_base64"]))
        )
        if row["index_kind"] == SEARCH_KIND:
            assert (
                decoded["search_transport_schema"] == transport.SEARCH_DOCUMENTS_SCHEMA
            )
            assert all(entry[0].startswith("d:") for entry in decoded["entries"])
        else:
            assert "search_transport_schema" not in decoded


@pytest.mark.parametrize(
    "tamper",
    [
        "null",
        "unknown",
        "missing_counts",
        "null_counts",
        "counts_without_marker",
        "extra_count",
        "search_marker_missing",
        "search_marker_absent",
        "search_marker_foreign",
        "nonsearch_marker",
        "search_counts_null",
        "nonsearch_counts_null",
        "document_count_low",
        "posting_count_high",
    ],
)
def test_tagged_bundle_rejects_mixed_or_false_declarations(tamper: str) -> None:
    bundle: dict[str, Any] = index_bundles.build_index_bundle(
        encoded_logical(), search_transport_schema=transport.SEARCH_DOCUMENTS_SCHEMA
    )
    if tamper == "null":
        bundle["search_transport_schema"] = None
    elif tamper == "unknown":
        bundle["search_transport_schema"] = "unknown"
    elif tamper == "missing_counts":
        del bundle["search_transport_counts"]
    elif tamper == "null_counts":
        bundle["search_transport_counts"] = None
    elif tamper == "counts_without_marker":
        del bundle["search_transport_schema"]
    elif tamper == "extra_count":
        bundle["search_transport_counts"]["other"] = 0
    elif tamper == "document_count_low":
        bundle["search_transport_counts"]["document_count"] = 0
    elif tamper == "posting_count_high":
        bundle["search_transport_counts"]["posting_reference_count"] += 1
    else:
        row = next(
            row
            for row in bundle["shards"]
            if (row["index_kind"] == SEARCH_KIND)
            == (tamper not in {"nonsearch_marker", "nonsearch_counts_null"})
        )
        if tamper.endswith("counts_null"):
            rewrite(row, {"search_transport_counts": None})
        elif tamper == "search_marker_absent":
            rewrite(row, {}, remove=("search_transport_schema",))
        else:
            rewrite(
                row,
                {
                    "search_transport_schema": None
                    if tamper == "search_marker_missing"
                    else "unknown"
                },
            )
    with pytest.raises(ValueError):
        index_bundles.decode_index_bundle(bundle)


def test_compatibility_marker_binds_complete_physical_parts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = encoded_logical()
    bundle = index_bundles.build_index_bundle(
        data, search_transport_schema=transport.SEARCH_DOCUMENTS_SCHEMA
    )
    from bijux_pollenomics.reporting.map_document.static_assets import index_transport

    monkeypatch.setattr(index_transport, "ATLAS_CHUNK_MAX_BYTES", 3500)
    parts = partition_index_bundle(bundle, first_sequence=20)
    rows, payloads, manifest = inventory(bundle, parts)
    manifest["compatibility"]["search_transport_schema"] = (
        transport.SEARCH_DOCUMENTS_SCHEMA
    )
    assert decode_index_payloads(rows, payloads, manifest=manifest) == data
    manifest["compatibility"]["search_transport_counts"] = bundle[
        "search_transport_counts"
    ]
    with pytest.raises(ValueError, match="bundle header"):
        decode_index_payloads(rows, payloads, manifest=manifest)
    del manifest["compatibility"]["search_transport_counts"]
    manifest["compatibility"]["search_transport_schema"] = None
    with pytest.raises(ValueError, match="compatibility"):
        decode_index_payloads(rows, payloads, manifest=manifest)


def test_empty_documents_have_explicit_zero_resource_counts() -> None:
    documents, counts = transport.encode_search_documents({})
    assert counts == dict.fromkeys(transport.SEARCH_TRANSPORT_COUNT_FIELDS, 0)
    assert transport.restore_search_documents(documents, counts) == {}


def test_reserved_counts_cannot_appear_in_legacy_shards() -> None:
    bundle: dict[str, Any] = index_bundles.build_index_bundle(encoded_logical())
    rewrite(bundle["shards"][0], {"search_transport_counts": None})
    with pytest.raises(ValueError, match="bundle header"):
        index_bundles.decode_index_bundle(bundle)
