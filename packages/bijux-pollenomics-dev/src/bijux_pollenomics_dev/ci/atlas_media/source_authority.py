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

from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)

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
    label: str | None
    site_count: int
    node_count: int
    observation_denominator: int
    time_min_bp: float | int
    time_max_bp: float | int
    intervals: tuple[tuple[float | int, float | int], ...]
    site_intervals: tuple[tuple[str, float | int, float | int], ...]
    observation_intervals: tuple[tuple[int, float | int, float | int], ...]
    member_taxon_ids: tuple[int, ...] | None = None
    source_preset_catalog_sha256: str | None = None

    def visible_count(self, younger_bp: float, older_bp: float) -> int:
        """Count closed source intervals overlapping one closed playback frame."""
        return sum(
            feature_older >= younger_bp and feature_younger <= older_bp
            for feature_younger, feature_older in self.intervals
        )

    def visible_site_count(self, younger_bp: float, older_bp: float) -> int:
        """Count unique source sites whose closed intervals overlap one frame."""
        return len(
            {
                site_id
                for site_id, feature_younger, feature_older in self.site_intervals
                if feature_older >= younger_bp and feature_younger <= older_bp
            }
        )

    def visible_observation_count(self, younger_bp: float, older_bp: float) -> int:
        """Sum observations from source nodes overlapping one closed frame."""
        return sum(
            count
            for count, feature_younger, feature_older in self.observation_intervals
            if feature_older >= younger_bp and feature_younger <= older_bp
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


def bind_source_label_preset_authority(
    authority: SourceChronologyAuthority,
    *,
    catalog: object,
    accountability: object,
) -> SourceChronologyAuthority:
    """Bind governed literal-label definitions to asset-derived source facts."""
    catalog_row = _object(catalog, "source-label preset catalog")
    accountability_row = _object(
        accountability, "source-label preset accountability"
    )
    expected_catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=_text(
            catalog_row.get("source_snapshot_id"), "preset source snapshot identity"
        ),
        build_id=_text(catalog_row.get("build_id"), "preset build identity"),
    )
    if catalog_row != expected_catalog:
        raise AtlasMediaError("source-label preset catalog differs from its contract")
    content_identity = _content_identity(
        catalog_row.get("content_sha256"), "source-label preset catalog"
    )
    if (
        accountability_row.get("schema_version")
        != "neotoma-source-label-preset-accountability.v1"
        or accountability_row.get("catalog_content_sha256")
        != catalog_row["content_sha256"]
        or accountability_row.get("membership_semantics") != MEMBERSHIP_SEMANTICS
        or accountability_row.get("source_taxon_count")
        != len(NEOTOMA_SOURCE_LABEL_TAXA)
        or accountability_row.get("preset_count")
        != len(NEOTOMA_SOURCE_LABEL_PRESETS)
        or accountability_row.get("membership_count")
        != sum(
            len(preset.member_taxon_ids)
            for preset in NEOTOMA_SOURCE_LABEL_PRESETS
        )
    ):
        raise AtlasMediaError("source-label preset accountability differs")
    _require_literal_refusal(accountability_row)
    rows = _object_rows(accountability_row.get("presets"), "preset rows")
    if len(rows) != len(NEOTOMA_SOURCE_LABEL_PRESETS):
        raise AtlasMediaError("source-label preset inventory differs")
    rows_by_key = {_text(row.get("key"), "preset key"): row for row in rows}
    if len(rows_by_key) != len(rows):
        raise AtlasMediaError("source-label preset keys are not unique")
    labels_by_id = {
        taxon.source_taxon_id: taxon.source_reported_name
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
    }
    facets = dict(authority.facets)
    for preset in NEOTOMA_SOURCE_LABEL_PRESETS:
        row = rows_by_key.get(preset.key)
        if row is None:
            raise AtlasMediaError(f"source-label preset is absent: {preset.key}")
        _require_literal_refusal(row)
        if (
            row.get("label") != preset.label
            or row.get("membership_semantics") != MEMBERSHIP_SEMANTICS
            or row.get("member_taxon_count") != len(preset.member_taxon_ids)
            or row.get("member_taxon_ids") != list(preset.member_taxon_ids)
        ):
            raise AtlasMediaError(
                f"source-label preset membership differs: {preset.key}"
            )
        members: list[SourceFacetAuthority] = []
        for taxon_id in preset.member_taxon_ids:
            facet = authority.require(
                "source_taxon", f"source:neotoma:taxon:{taxon_id}"
            )
            if facet.label != labels_by_id[taxon_id]:
                raise AtlasMediaError(
                    f"source-label preset member label differs: {taxon_id}"
                )
            members.append(facet)
        intervals = tuple(
            interval for member in members for interval in member.intervals
        )
        site_intervals = tuple(
            interval for member in members for interval in member.site_intervals
        )
        observation_intervals = tuple(
            interval
            for member in members
            for interval in member.observation_intervals
        )
        derived = SourceFacetAuthority(
            selector_kind="source_label_preset",
            selector_value=preset.key,
            label=preset.label,
            site_count=len({site_id for site_id, _younger, _older in site_intervals}),
            node_count=sum(member.node_count for member in members),
            observation_denominator=sum(
                member.observation_denominator for member in members
            ),
            time_min_bp=min(member.time_min_bp for member in members),
            time_max_bp=max(member.time_max_bp for member in members),
            intervals=intervals,
            site_intervals=site_intervals,
            observation_intervals=observation_intervals,
            member_taxon_ids=preset.member_taxon_ids,
            source_preset_catalog_sha256=content_identity,
        )
        if any(
            row.get(field) != getattr(derived, field)
            for field in (
                "node_count",
                "site_count",
                "observation_denominator",
                "time_min_bp",
                "time_max_bp",
            )
        ):
            raise AtlasMediaError(
                f"source-label preset denominators differ from governed atlas assets: {preset.key}"
            )
        facets[(derived.selector_kind, derived.selector_value)] = derived
    return SourceChronologyAuthority(
        build_id=authority.build_id,
        digest=authority.digest,
        asset_sha256=authority.asset_sha256,
        facets=facets,
    )


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
            _SOURCE_LAYER_LEVELS.get(layer_key) if isinstance(layer_key, str) else None
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
                "label": facet.label,
                "site_count": facet.site_count,
                "node_count": facet.node_count,
                "observation_denominator": facet.observation_denominator,
                "time_min_bp": facet.time_min_bp,
                "time_max_bp": facet.time_max_bp,
                "intervals": facet.intervals,
                "site_intervals": facet.site_intervals,
                "observation_intervals": facet.observation_intervals,
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
    site_intervals: list[tuple[str, float | int, float | int]] = []
    observation_intervals: list[tuple[int, float | int, float | int]] = []
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
        site_intervals.append(
            (_text(row.get("record_id"), "source site record ID"), younger, older)
        )
        denominator += observation_count
        observation_intervals.append((observation_count, younger, older))
    labels = (
        {
            _text(row.get("source_reported_name"), "source-reported taxon name")
            for row in rows
        }
        if key[0] == "source_taxon"
        else set()
    )
    if len(labels) > 1:
        raise AtlasMediaError("static source taxon has inconsistent labels")
    return SourceFacetAuthority(
        selector_kind=key[0],
        selector_value=key[1],
        label=next(iter(labels), None),
        site_count=len({site_id for site_id, _younger, _older in site_intervals}),
        node_count=len(rows),
        observation_denominator=denominator,
        time_min_bp=min(younger for younger, _older in intervals),
        time_max_bp=max(older for _younger, older in intervals),
        intervals=tuple(intervals),
        site_intervals=tuple(site_intervals),
        observation_intervals=tuple(observation_intervals),
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


def _content_identity(value: object, label: str) -> str:
    text = _text(value, label)
    if (
        not text.startswith("sha256:")
        or len(text) != 71
        or any(character not in "0123456789abcdef" for character in text[7:])
    ):
        raise AtlasMediaError(f"{label} content identity is invalid")
    return text[7:]


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AtlasMediaError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _object_rows(value: object, label: str) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise AtlasMediaError(f"{label} must be an array")
    return tuple(_object(row, label) for row in value)


def _require_literal_refusal(row: dict[str, object]) -> None:
    if any(
        row.get(field) is not False
        for field in (
            "accepted_classification",
            "aggregation_is_abundance",
            "propagation_allowed",
        )
    ):
        raise AtlasMediaError("source-label preset refusal posture differs")


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
    "bind_source_label_preset_authority",
    "load_source_chronology_authority",
]
