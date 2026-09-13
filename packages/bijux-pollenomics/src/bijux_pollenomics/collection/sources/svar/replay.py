"""Strict raw SVAR response admission and hash-bound offline replay."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

SVAR_WFS_URL = "https://vattenwebb.smhi.se/svarwebb/svar.map"
SVAR_TYPENAME = "lakes"
SVAR_PAGE_SIZE = 250
CAPTURE_SCHEMA = "svar-wfs-capture.v1"


def request_parameters(start: int | None) -> dict[str, str]:
    """Return the one supported, explicit WFS request profile."""
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAME": SVAR_TYPENAME,
    }
    if start is None:
        params["RESULTTYPE"] = "hits"
    else:
        params.update(
            COUNT=str(SVAR_PAGE_SIZE),
            STARTINDEX=str(start),
            SRSNAME="urn:ogc:def:crs:EPSG::3006",
        )
    return params


WFS = "{http://www.opengis.net/wfs/2.0}"
GML = "{http://www.opengis.net/gml/3.2}"
MS = "{http://mapserver.gis.umn.edu/mapserver}"
SUPPORTED_CRS = {
    "EPSG:3006": "EPSG:3006",
    "urn:ogc:def:crs:EPSG::3006": "EPSG:3006",
}


def _count(value: object) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError("svar_missing_or_invalid_count")
    return int(value)


def _root(payload: bytes) -> Element:
    root: Element = ET.fromstring(payload)
    if root.tag != WFS + "FeatureCollection":
        raise ValueError("svar_unexpected_response")
    if any(child.tag not in {WFS + "member", GML + "boundedBy"} for child in root):
        raise ValueError("svar_unsupported_response_member")
    return root


def read_hits(payload: bytes) -> int:
    """Require an explicit nonnegative hits count, retaining genuine zero."""
    root = _root(payload)
    if _count(root.get("numberReturned")) != 0 or root.findall(WFS + "member"):
        raise ValueError("svar_invalid_hits_response")
    return _count(root.get("numberMatched"))


def validate_page(payload: bytes, *, matched: int, expected: int) -> tuple[str, ...]:
    """Account every member or refuse the page; no geometry is silently skipped."""
    root = _root(payload)
    members = root.findall(WFS + "member")
    if (
        _count(root.get("numberMatched")) != matched
        or _count(root.get("numberReturned")) != expected
        or len(members) != expected
    ):
        raise ValueError("svar_page_count_mismatch")
    ids = []
    for member in members:
        if len(member) != 1 or member[0].tag != MS + "lakes":
            raise ValueError("svar_unsupported_member")
        lake = member[0]
        if (
            len(lake.findall(MS + "SJOID")) != 1
            or len(lake.findall(MS + "msGeometry")) != 1
        ):
            raise ValueError("svar_ambiguous_member_fields")
        identity = lake.findtext(MS + "SJOID")
        if identity is None or not identity.strip() or identity != identity.strip():
            raise ValueError("svar_missing_record_id")
        ids.append(identity)
        _validate_geometry(lake)
    if len(set(ids)) != len(ids):
        raise ValueError("svar_duplicate_record_id")
    return tuple(ids)


def _validate_geometry(lake: Element) -> None:
    container = lake.find(MS + "msGeometry")
    if container is None or len(container) != 1:
        raise ValueError("svar_missing_or_unsupported_geometry")
    shape = container[0]
    if shape.tag == GML + "Polygon":
        polygons = [shape]
    elif shape.tag == GML + "MultiSurface":
        members = list(shape)
        if not members or any(
            m.tag != GML + "surfaceMember" or len(m) != 1 or m[0].tag != GML + "Polygon"
            for m in members
        ):
            raise ValueError("svar_unsupported_multisurface")
        polygons = [m[0] for m in members]
    else:
        raise ValueError("svar_unsupported_geometry")
    for polygon in polygons:
        crs = polygon.get("srsName", shape.get("srsName"))
        if crs not in SUPPORTED_CRS:
            raise ValueError("svar_unsupported_or_missing_crs")
        if (
            shape.get("srsName") is not None
            and SUPPORTED_CRS.get(shape.get("srsName", "")) != SUPPORTED_CRS[crs]
        ):
            raise ValueError("svar_conflicting_crs")
        boundaries = list(polygon)
        if (
            not boundaries
            or boundaries[0].tag != GML + "exterior"
            or any(b.tag != GML + "interior" for b in boundaries[1:])
        ):
            raise ValueError("svar_unsupported_polygon_boundary")
        for boundary in boundaries:
            if len(boundary) != 1 or boundary[0].tag != GML + "LinearRing":
                raise ValueError("svar_unsupported_ring")
            ring = boundary[0]
            if len(ring) != 1 or ring[0].tag != GML + "posList":
                raise ValueError("svar_unsupported_coordinates")
            pos = ring[0]
            for node in (shape, polygon, ring, pos):
                if node.get("srsDimension", "2") != "2":
                    raise ValueError("svar_unsupported_coordinate_dimension")
                if (
                    node.get("srsName") is not None
                    and SUPPORTED_CRS.get(node.get("srsName", "")) != SUPPORTED_CRS[crs]
                ):
                    raise ValueError("svar_conflicting_crs")
            values = [float(v) for v in (pos.text or "").split()]
            if (
                len(values) < 8
                or len(values) % 2
                or not all(math.isfinite(v) for v in values)
                or values[:2] != values[-2:]
            ):
                raise ValueError("svar_invalid_ring_coordinates")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("svar_duplicate_json_key")
        result[key] = value
    return result


def replay_svar_capture(directory: Path, *, expected_sha256: str) -> Iterator[bytes]:
    """Verify a completed capture and yield admitted pages without any network IO."""
    for p in (directory, *directory.parents):
        if p.is_symlink():
            raise ValueError("svar_symlink_capture")
    if any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError("svar_capture_inventory_mismatch")
    manifest_bytes = (directory / "capture.json").read_bytes()
    if sha256(manifest_bytes).hexdigest() != expected_sha256:
        raise ValueError("svar_capture_digest_mismatch")
    manifest = json.loads(manifest_bytes, object_pairs_hook=_unique_object)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != CAPTURE_SCHEMA
        or manifest.get("wfs_url") != SVAR_WFS_URL
        or manifest.get("page_size") != SVAR_PAGE_SIZE
        or manifest.get("source") != "SMHI SVAR"
        or manifest.get("scientific_review") != "not_asserted"
        or manifest.get("rights_verification") != "not_asserted"
    ):
        raise ValueError("svar_capture_contract_mismatch")
    matched = manifest.get("matched_count")
    if type(matched) is not int or matched < 0:
        raise ValueError("svar_missing_or_invalid_count")
    members = manifest.get("members")
    expected_member_count = 1 + (matched + SVAR_PAGE_SIZE - 1) // SVAR_PAGE_SIZE
    if not isinstance(members, list) or len(members) != expected_member_count:
        raise ValueError("svar_capture_inventory_mismatch")
    expected_names = {"capture.json"}
    if len(list(directory.iterdir())) != 1 + 2 * len(members):
        raise ValueError("svar_capture_inventory_mismatch")
    seen: set[str] = set()
    readset: dict[Path, bytes] = {}
    for index, record in enumerate(members):
        start = None if index == 0 else (index - 1) * SVAR_PAGE_SIZE
        name = "hits.xml" if start is None else f"page-{start:09d}.xml"
        expected_names.update((name, name + ".json"))
        if (
            not isinstance(record, dict)
            or record.get("path") != name
            or record.get("parameters") != request_parameters(start)
        ):
            raise ValueError("svar_capture_request_mismatch")
        receipt_bytes = (directory / (name + ".json")).read_bytes()
        receipt = json.loads(receipt_bytes, object_pairs_hook=_unique_object)
        canonical_receipt = json.dumps(
            record, sort_keys=True, ensure_ascii=False, allow_nan=False
        ).encode()
        if receipt_bytes != canonical_receipt:
            raise ValueError("svar_capture_receipt_mismatch")
        retrieved = record.get("retrieved_at")
        if (
            not isinstance(retrieved, str)
            or datetime.fromisoformat(retrieved).tzinfo is None
        ):
            raise ValueError("svar_capture_retrieval_time_missing")
        readset[directory / (name + ".json")] = sha256(receipt_bytes).digest()
        payload = (directory / name).read_bytes()
        readset[directory / name] = sha256(payload).digest()
        if (
            receipt != record
            or type(record.get("byte_count")) is not int
            or record.get("byte_count") != len(payload)
            or record.get("sha256") != sha256(payload).hexdigest()
        ):
            raise ValueError("svar_capture_member_mismatch")
        if start is None:
            if read_hits(payload) != matched:
                raise ValueError("svar_capture_hits_mismatch")
        else:
            ids = validate_page(
                payload, matched=matched, expected=min(SVAR_PAGE_SIZE, matched - start)
            )
            if seen.intersection(ids):
                raise ValueError("svar_duplicate_record_id")
            seen.update(ids)
            yield payload
    if {p.name for p in directory.iterdir()} != expected_names or any(
        p.is_symlink() or sha256(p.read_bytes()).digest() != digest
        for p, digest in readset.items()
    ):
        raise ValueError("svar_capture_changed_during_replay")
    if (directory / "capture.json").read_bytes() != manifest_bytes:
        raise ValueError("svar_capture_changed_during_replay")
