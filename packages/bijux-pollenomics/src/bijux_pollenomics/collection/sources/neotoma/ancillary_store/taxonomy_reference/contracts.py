"""Dated Git projections carry reference facts, never current collection authority."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha1
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

REPOSITORY = "https://github.com/NeotomaDB/Taxonomy-Viewer"
API = "https://api.github.com/repos/NeotomaDB/Taxonomy-Viewer/git/"
RAW = "https://raw.githubusercontent.com/NeotomaDB/Taxonomy-Viewer/"
NAMES = ("taxa_snapshot.json", "taxon_metadata.json", "all_synonyms.json")
SCHEMA = "neotoma-dated-taxonomy-reference.v1"
MAX_BYTES = 64 * 1024**2
MAX_FILES = 16
MAX_METADATA = 1024**2
MAX_ROWS = 200000
POSTURE = {
    "source_protocol": "pinned_official_git_projection",
    "scientific_admission": "not_asserted",
    "current_roles_revalidated": False,
    "source_status_available": False,
    "native_detail_captures_added": 0,
    "Neotoma_API_calls": 0,
    "database_dates_are_sample_ages": False,
    "snapshot_consistency": "separate_upstream_queries_not_transactionally_asserted",
}


def digest(value: object, length: int = 64) -> bool:
    """Require a literal lowercase content identity."""
    return (
        type(value) is str
        and re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value) is not None
    )


def native_id(value: object) -> int:
    """Keep native identifiers distinct from booleans and numeric strings."""
    if type(value) is not int or value <= 0:
        raise ValueError("Taxonomy reference needs a positive native integer ID")
    return value


def utc(value: object) -> str:
    """Validate transport/refresh timestamps without treating them as sample ages."""
    if type(value) is not str:
        raise ValueError("Taxonomy reference timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("Taxonomy reference timestamp needs a timezone")
    return value


def immutable(value: Any) -> Any:
    """Detach recursively immutable JSON-shaped reference facts."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(immutable(item) for item in value)
    return value


def decode(raw: bytes) -> Any:
    """Reject duplicate keys, nonfinite numbers and excessive JSON nesting."""
    depth = maximum = 0
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            maximum = max(maximum, depth)
        elif byte in (93, 125):
            depth -= 1
        if maximum > 16:
            raise ValueError("Taxonomy reference JSON exceeds its nesting bound")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError("Taxonomy reference JSON object has duplicate keys")
            result[key] = item
        return result

    def constant(value: str) -> None:
        raise ValueError("Taxonomy reference JSON contains nonfinite " + value)

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Taxonomy reference JSON is malformed") from error


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceFile:
    """An independently supplied local file identity is an input, not authority."""

    path: Path
    bytes: int
    sha256: str

    def __post_init__(self) -> None:
        """Require finite ordinary-file declarations before opening anything."""
        if (
            type(self.bytes) is not int
            or not 0 < self.bytes <= MAX_BYTES
            or not digest(self.sha256)
        ):
            raise ValueError("Taxonomy reference file pin differs")
        object.__setattr__(self, "path", Path(self.path).absolute())


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceSource:
    """Separate original projections, pinned Git evidence and genuine transport."""

    revision: str
    files: Mapping[str, NeotomaTaxonomyReferenceFile]
    git_metadata: Mapping[str, NeotomaTaxonomyReferenceFile]
    transport: Mapping[str, NeotomaTaxonomyReferenceFile]
    intake_intervals: Mapping[str, tuple[str, str]]
    attribution: str

    def __post_init__(self) -> None:
        """Copy borrowed bindings and refuse unclassified input populations."""
        if (
            not digest(self.revision, 40)
            or set(self.files) != set(NAMES)
            or set(self.transport) != set(NAMES)
            or set(self.git_metadata) != {"commit", "root_tree", "data_tree"}
            or set(self.intake_intervals) != set(NAMES)
            or type(self.attribution) is not str
            or not self.attribution.strip()
        ):
            raise ValueError("Taxonomy reference source binding differs")
        for name in ("files", "git_metadata", "transport"):
            values = dict(getattr(self, name))
            if any(
                type(pin) is not NeotomaTaxonomyReferenceFile for pin in values.values()
            ):
                raise ValueError(
                    "Taxonomy reference needs explicit pinned file records"
                )
            object.__setattr__(self, name, MappingProxyType(values))
        intervals = {}
        for name, pair in self.intake_intervals.items():
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError("Taxonomy reference intake interval differs")
            start, end = utc(pair[0]), utc(pair[1])
            if datetime.fromisoformat(
                start.replace("Z", "+00:00")
            ) > datetime.fromisoformat(end.replace("Z", "+00:00")):
                raise ValueError("Taxonomy reference intake interval is reversed")
            intervals[name] = (start, end)
        object.__setattr__(self, "intake_intervals", MappingProxyType(intervals))


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceManifest:
    """A closed reference manifest asserts identity and source posture only."""

    manifest_sha256: str
    manifest: Mapping[str, Any]
    scientific_admission: str = field(default="not_asserted", init=False)

    def __post_init__(self) -> None:
        """Own the returned declaration rather than a caller's mutable mapping."""
        object.__setattr__(self, "manifest", immutable(self.manifest))


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceInventory:
    """Metadata authentication deliberately leaves original entity bodies unread."""

    manifest: Mapping[str, Any]
    provenance: Mapping[str, Any]
    source_entity_bodies_verified: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Detach metadata without extending its input lease."""
        object.__setattr__(self, "manifest", immutable(self.manifest))
        object.__setattr__(self, "provenance", immutable(self.provenance))


@dataclass(frozen=True)
class NeotomaTaxonomySynonymAssertion:
    """Preserve directional source assertion identity, dates and source positions."""

    group_position: int
    assertion_position: int
    valid_id: int
    valid_name: str
    taxagroupid: str
    fields: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Copy the original assertion fields without biological interpretation."""
        object.__setattr__(self, "fields", immutable(self.fields))


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceTaxon:
    """One dated native-ID lookup; database dates are not sample chronology."""

    native_id: int
    taxon: Mapping[str, Any]
    metadata: Mapping[str, Any]
    synonyms: tuple[NeotomaTaxonomySynonymAssertion, ...]
    source_generated_at: str
    source_revision: str

    def __post_init__(self) -> None:
        """Own every returned field independently from decoder scratch state."""
        object.__setattr__(self, "taxon", immutable(self.taxon))
        object.__setattr__(self, "metadata", immutable(self.metadata))
        object.__setattr__(self, "synonyms", tuple(self.synonyms))


@dataclass(frozen=True)
class NeotomaTaxonomyReferenceContrast:
    """A frozen recorded-frontier contrast does not qualify source capture duties."""

    reference_manifest_sha256: str
    chain_manifest_sha256: str
    source_revision: str
    source_generated_at: str
    rows: tuple[Mapping[str, Any], ...]
    summary: Mapping[str, int]
    recorded_new_capture_manifest_sha256s: tuple[str, ...]
    reference_commit_utc: str
    reference_intake_intervals: Mapping[str, tuple[str, str]]
    current_roles_revalidated: bool = field(default=False, init=False)
    native_source_fields_revalidated: bool = field(default=False, init=False)
    GET_authorized: bool = field(default=False, init=False)
    scientific_admission: str = field(default="not_asserted", init=False)
    integrity_scope: str = field(
        default="explicit_stored_frontier_parts_and_dated_reference_only", init=False
    )

    def __post_init__(self) -> None:
        """Own source positions and every literal outcome without a live input lease."""
        object.__setattr__(self, "rows", immutable(self.rows))
        object.__setattr__(self, "summary", immutable(self.summary))
        object.__setattr__(
            self,
            "reference_intake_intervals",
            immutable(self.reference_intake_intervals),
        )
        object.__setattr__(
            self,
            "recorded_new_capture_manifest_sha256s",
            tuple(self.recorded_new_capture_manifest_sha256s),
        )


def checked_tree(value: Any) -> dict[str, Any]:
    """Reconstruct a retained Git tree rather than trust a file listing label."""
    if (
        not isinstance(value, dict)
        or value.get("truncated") is not False
        or not isinstance(value.get("tree"), list)
    ):
        raise ValueError("Complete retained Git tree evidence required")
    rows = value["tree"]
    if len(rows) > 10000:
        raise ValueError("Taxonomy reference Git tree exceeds its bound")
    seen = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("type") not in {"tree", "blob"}
            or row.get("mode") not in {"040000", "100644", "100755"}
            or (row["type"] == "tree") != (row["mode"] == "040000")
            or not digest(row.get("sha"), 40)
            or type(row.get("path")) is not str
            or not row["path"]
            or "/" in row["path"]
            or "\0" in row["path"]
            or row["path"] in seen
        ):
            raise ValueError("Taxonomy reference Git tree member differs")
        seen.add(row["path"])
    raw = b"".join(
        (row["mode"].lstrip("0") + " " + row["path"]).encode()
        + b"\0"
        + bytes.fromhex(row["sha"])
        for row in sorted(
            rows, key=lambda row: row["path"] + ("/" if row["type"] == "tree" else "")
        )
    )
    pin = sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if value.get("sha") != pin or value.get("url") != API + "trees/" + pin:
        raise ValueError("Taxonomy reference Git tree identity differs")
    return value


def git_membership(
    evidence: Mapping[str, bytes], revision: str
) -> dict[str, dict[str, Any]]:
    """Bind official paths through independently pinned commit and tree evidence.

    The commit JSON is supplied evidence, not a reconstructed or signed commit
    object, and no live GitHub or native permission verification is implied.
    """
    commit = decode(evidence["commit"])
    root, data = (
        checked_tree(decode(evidence["root_tree"])),
        checked_tree(decode(evidence["data_tree"])),
    )
    if (
        not isinstance(commit, dict)
        or commit.get("sha") != revision
        or commit.get("url") != API + "commits/" + revision
        or commit.get("tree") != {"sha": root["sha"], "url": root["url"]}
    ):
        raise ValueError("Taxonomy reference retained commit membership differs")
    utc(commit["committer"]["date"])
    links = [row for row in root["tree"] if row["path"] == "data"]
    if len(links) != 1 or links[0]["type"] != "tree" or links[0]["sha"] != data["sha"]:
        raise ValueError("Taxonomy reference data tree is foreign to pinned commit")
    result = {row["path"]: row for row in data["tree"] if row["path"] in NAMES}
    if set(result) != set(NAMES) or any(
        row["type"] != "blob"
        or row["mode"] != "100644"
        or type(row.get("size")) is not int
        or not 0 < row["size"] <= MAX_BYTES
        for row in result.values()
    ):
        raise ValueError("Taxonomy reference original Git members differ")
    return result
