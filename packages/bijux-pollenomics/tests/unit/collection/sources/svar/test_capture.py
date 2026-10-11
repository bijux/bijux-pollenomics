"""Counterexamples for single-count, byte-preserving WFS capture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.svar.capture import capture_svar_wfs
from bijux_pollenomics.collection.sources.svar.replay import read_hits, validate_page


def page(
    ids: tuple[str, ...], *, matched: int | None = None, crs: str = "EPSG:3006"
) -> bytes:
    members = "".join(
        f'''<wfs:member><ms:lakes gml:id="lakes.{i}"><ms:SJOID>{i}</ms:SJOID><ms:AREA>0</ms:AREA><ms:msGeometry><gml:Polygon srsName="{crs}"><gml:exterior><gml:LinearRing><gml:posList srsDimension="2">7364709 579976 7364730 579953 7364740 579980 7364709 579976</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></ms:msGeometry></ms:lakes></wfs:member>'''
        for i in ids
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?><wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:ms="http://mapserver.gis.umn.edu/mapserver" numberMatched="{len(ids) if matched is None else matched}" numberReturned="{len(ids)}">{members}</wfs:FeatureCollection>'''.encode()


def hits(count: int) -> bytes:
    return page((), matched=count)


def fixture_capture(path: Path, ids: tuple[str, ...] = ("one", "two")) -> str:
    def fetch(params: dict[str, str]) -> bytes:
        if params.get("RESULTTYPE") == "hits":
            return hits(len(ids))
        start = int(params["STARTINDEX"])
        return page(ids[start : start + 250], matched=len(ids))

    return capture_svar_wfs(path, fetch=fetch)


def test_capture_preserves_exact_bytes_and_fetches_hits_once(tmp_path: Path) -> None:
    calls = []
    ids = tuple(str(i) for i in range(251))

    def fetch(params: dict[str, str]) -> bytes:
        calls.append(params)
        return (
            hits(251)
            if params.get("RESULTTYPE") == "hits"
            else page(
                ids[int(params["STARTINDEX"]) : int(params["STARTINDEX"]) + 250],
                matched=251,
            )
        )

    capture_svar_wfs(tmp_path / "capture", fetch=fetch)
    assert len(calls) == 3
    assert sum(p.get("RESULTTYPE") == "hits" for p in calls) == 1
    assert (tmp_path / "capture/page-000000250.xml").read_bytes() == page(
        ("250",), matched=251
    )
    manifest = json.loads((tmp_path / "capture/capture.json").read_text())
    assert manifest["matched_count"] == 251
    assert manifest["scientific_review"] == "not_asserted"


@pytest.mark.parametrize("raw", [b"", b"unknown", b"-1", b"0.0", b"true"])
def test_hits_refuses_unknown_or_invalid_count(raw: bytes) -> None:
    with pytest.raises(ValueError):
        read_hits(
            hits(0).replace(b'numberMatched="0"', b'numberMatched="' + raw + b'"')
        )


def test_zero_is_an_explicit_capture_without_pages(tmp_path: Path) -> None:
    fixture_capture(tmp_path / "capture", ())
    assert sorted(p.name for p in (tmp_path / "capture").iterdir()) == [
        "capture.json",
        "hits.xml",
        "hits.xml.json",
    ]


@pytest.mark.parametrize(
    "payload",
    [page((), matched=1), page(("x",), matched=2), page(("x", "x"), matched=1)],
)
def test_failed_page_is_retained_without_complete_manifest(
    tmp_path: Path, payload: bytes
) -> None:
    def fetch(params: dict[str, str]) -> bytes:
        return hits(1) if params.get("RESULTTYPE") == "hits" else payload

    with pytest.raises(ValueError):
        capture_svar_wfs(tmp_path / "capture", fetch=fetch)
    assert (tmp_path / "capture/page-000000000.xml").read_bytes() == payload
    assert not (tmp_path / "capture/capture.json").exists()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"EPSG:3006", b"EPSG:4326"),
        (b'srsName="EPSG:3006"', b""),
        (b"gml:Polygon", b"gml:Point"),
        (b'srsDimension="2"', b'srsDimension="3"'),
        (b"7364709 579976 7364730", b"nan 579976 7364730"),
        (b"7364740 579980 7364709 579976", b"7364740 579980 7364709 579977"),
        (b"<ms:SJOID>x</ms:SJOID>", b""),
    ],
)
def test_page_refuses_uninterpretable_member(old: bytes, new: bytes) -> None:
    with pytest.raises(ValueError):
        validate_page(page(("x",)).replace(old, new), matched=1, expected=1)


def test_duplicate_ids_across_pages_refuse(tmp_path: Path) -> None:
    def fetch(params: dict[str, str]) -> bytes:
        if params.get("RESULTTYPE") == "hits":
            return hits(251)
        return page(
            tuple(str(i) for i in range(250))
            if params["STARTINDEX"] == "0"
            else ("0",),
            matched=251,
        )

    with pytest.raises(ValueError, match="duplicate_record_id"):
        capture_svar_wfs(tmp_path / "capture", fetch=fetch)
    assert (tmp_path / "capture/page-000000250.xml").exists()


def test_duplicated_source_identity_element_refuses() -> None:
    payload = page(("one",)).replace(
        b"<ms:SJOID>one</ms:SJOID>",
        b"<ms:SJOID>one</ms:SJOID><ms:SJOID>other</ms:SJOID>",
    )
    with pytest.raises(ValueError, match="ambiguous_member_fields"):
        validate_page(payload, matched=1, expected=1)


def test_world_cylindrical_response_is_not_silently_reinterpreted() -> None:
    with pytest.raises(ValueError, match="unsupported_or_missing_crs"):
        validate_page(page(("one",), crs="EPSG:3786"), matched=1, expected=1)
