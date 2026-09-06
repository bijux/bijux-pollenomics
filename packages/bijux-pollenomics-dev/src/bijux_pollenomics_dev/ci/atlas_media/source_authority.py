"""Derive source-story truth from checksummed static atlas node assets."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import cast

from .contracts import AtlasMediaError
from .gallery import canonical_json_bytes, sha256_file

_PREFIX = (
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__="
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];"
    "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
)
_SUFFIX = ");\n"
_SOURCE_LAYER_LEVELS = {
    "neotoma-source-sample-pollen-context": "source_sample_presence",
    "neotoma-source-ecological-code": "source_ecological_code",
    "neotoma-source-exact-taxon": "source_taxon",
}


@dataclass(frozen=True, slots=True)
class SourceFacetAuthority:
    """Exact denominator and temporal facts for one source selector."""

    selector_kind: str
    selector_value: str
    node_count: int
    observation_denominator: int
    intervals: tuple[tuple[float | int, float | int], ...]

    def visible_count(self, younger_bp: float | int, older_bp: float | int) -> int:
        """Count closed source intervals overlapping one closed playback frame."""
        return sum(
            feature_older >= younger_bp and feature_younger <= older_bp
            for feature_younger, feature_older in self.intervals
        )


@dataclass(frozen=True, slots=True)
class SourceChronologyAuthority:
    """Content-addressed selector authority for one immutable atlas build."""

    build_id: str
    digest: str
    asset_sha256: tuple[str, ...]
    facets: dict[tuple[str, str], SourceFacetAuthority]

    def require(self, kind: str, value: str) -> SourceFacetAuthority:
        """Return exactly one governed facet or refuse the selector."""
        try:
            return self.facets[(kind, value)]
        except KeyError as error:
            raise AtlasMediaError(
                f"source selector is absent from governed atlas assets: {kind}/{value}"
            ) from error


def load_source_chronology_authority(
    repository_root: Path,
    atlas_manifest_path: Path,
) -> SourceChronologyAuthority:
    """Load only declared source node chunks without executing JavaScript."""
    root = repository_root.resolve()
    manifest_path = _contained_file(root, atlas_manifest_path, "atlas manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fields = manifest["assets"]["fields"]
        records = manifest["assets"]["records"]
        scope = manifest["scope_slug"]
        build_id = manifest["build_id"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise AtlasMediaError("static atlas asset manifest is invalid") from error
    if (
        manifest.get("schema_version") != "atlas-static-bootstrap.v2"
        or not isinstance(fields, list)
        or len(fields) != len(set(fields))
        or not isinstance(records, list)
        or not isinstance(scope, str)
        or not isinstance(build_id, str)
    ):
        raise AtlasMediaError("static atlas asset manifest is incompatible")

    features: list[dict[str, object]] = []
    asset_digests: list[str] = []
    for sequence, values in enumerate(records):
        if not isinstance(values, list) or len(values) != len(fields):
            raise AtlasMediaError("static atlas asset table row is invalid")
        row = dict(zip(fields, values, strict=True))
        layer_index = row.get("layer_index")
        layer_key = row.get("layer_key")
        expected_level = (
            _SOURCE_LAYER_LEVELS.get(layer_key)
            if isinstance(layer_key, str)
            else None
        )
        if row.get("domain") != "nodes" or expected_level is None:
            continue
        digest = _sha(row.get("sha256"), "static source asset")
        filename = f"{scope}.atlas-nodes.{sequence:04d}.{digest[:16]}.js"
        path = _contained_file(root, manifest_path.parent / filename, filename)
        if sha256_file(path) != digest or path.stat().st_size != row.get("byte_count"):
            raise AtlasMediaError(f"static source asset bytes differ: {filename}")
        payload = _decode_chunk(path, expected_payload_sha=row.get("payload_sha256"))
        if (
            payload.get("build_id") != build_id
            or payload.get("scope_slug") != scope
            or payload.get("layer_index") != layer_index
            or payload.get("layer_key") != row.get("layer_key")
            or not isinstance(payload.get("features"), list)
            or len(cast(list[object], payload["features"])) != row.get("record_count")
        ):
            raise AtlasMediaError(f"static source asset identity differs: {filename}")
        for value in cast(list[object], payload["features"]):
            if not isinstance(value, dict):
                raise AtlasMediaError(f"static source feature is invalid: {filename}")
            feature = cast(dict[str, object], value)
            if feature.get("node_level") != expected_level:
                raise AtlasMediaError(
                    f"static source feature level differs: {filename}"
                )
            features.append(feature)
        asset_digests.append(digest)
    if not asset_digests:
        raise AtlasMediaError("static atlas declares no source chronology assets")

    buckets: dict[tuple[str, str], list[dict[str, object]]] = {}
    for feature in features:
        kind = cast(str, feature["node_level"])
        if kind == "source_sample_presence":
            value = "all"
        elif kind == "source_ecological_code":
            value = _text(feature.get("source_ecological_code"), "ecological code")
        else:
            value = _text(feature.get("feature_key"), "source taxon feature key")
        buckets.setdefault((kind, value), []).append(feature)
    facets = {
        key: _facet(key, rows)
        for key, rows in sorted(buckets.items(), key=lambda item: item[0])
    }
    content = {
        "build_id": build_id,
        "asset_sha256": asset_digests,
        "facets": [
            {
                "selector_kind": facet.selector_kind,
                "selector_value": facet.selector_value,
                "node_count": facet.node_count,
                "observation_denominator": facet.observation_denominator,
                "intervals": facet.intervals,
            }
            for facet in facets.values()
        ],
    }
    return SourceChronologyAuthority(
        build_id=build_id,
        digest=hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
        asset_sha256=tuple(asset_digests),
        facets=facets,
    )


def _facet(key: tuple[str, str], rows: list[dict[str, object]]) -> SourceFacetAuthority:
    intervals: list[tuple[float | int, float | int]] = []
    denominator = 0
    for row in rows:
        younger = _number(row.get("time_start_bp"), "source time_start_bp")
        older = _number(row.get("time_end_bp"), "source time_end_bp")
        if younger > older:
            raise AtlasMediaError("static source feature has reversed BP interval")
        observation_count = row.get("observation_denominator")
        if (
            isinstance(observation_count, bool)
            or not isinstance(observation_count, int)
            or observation_count <= 0
        ):
            raise AtlasMediaError("static source observation denominator is invalid")
        intervals.append((younger, older))
        denominator += observation_count
    return SourceFacetAuthority(
        selector_kind=key[0],
        selector_value=key[1],
        node_count=len(rows),
        observation_denominator=denominator,
        intervals=tuple(intervals),
    )


def _decode_chunk(path: Path, *, expected_payload_sha: object) -> dict[str, object]:
    try:
        source = path.read_text(encoding="utf-8")
        if not source.startswith(_PREFIX) or not source.endswith(_SUFFIX):
            raise AtlasMediaError(f"static source wrapper differs: {path.name}")
        envelope = json.loads(source[len(_PREFIX) : -len(_SUFFIX)])
        encoding = envelope.get("payload_encoding")
        if encoding == "json":
            raw = envelope["payload_json"].encode("utf-8")
        elif encoding == "gzip_base64":
            raw = gzip.decompress(
                base64.b64decode(envelope["payload_gzip_base64"], validate=True)
            )
        else:
            raise AtlasMediaError(f"static source encoding differs: {path.name}")
        digest = _sha(expected_payload_sha, "static source payload")
        if hashlib.sha256(raw).hexdigest() != digest:
            raise AtlasMediaError(f"static source payload bytes differ: {path.name}")
        payload = json.loads(raw)
    except (OSError, UnicodeError, ValueError, KeyError, gzip.BadGzipFile) as error:
        raise AtlasMediaError(
            f"static source asset is unreadable: {path.name}"
        ) from error
    if not isinstance(payload, dict):
        raise AtlasMediaError(f"static source payload is not an object: {path.name}")
    return cast(dict[str, object], payload)


def _contained_file(root: Path, path: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError(f"required governed file is absent: {label}") from error
    if root not in resolved.parents or not resolved.is_file():
        raise AtlasMediaError(f"governed file escapes repository: {label}")
    return resolved


def _sha(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AtlasMediaError(f"{label} SHA-256 is invalid")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AtlasMediaError(f"static source {label} is invalid")
    return value


def _number(value: object, label: str) -> float | int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise AtlasMediaError(f"{label} is invalid")
    return value


__all__ = [
    "SourceChronologyAuthority",
    "SourceFacetAuthority",
    "load_source_chronology_authority",
]
