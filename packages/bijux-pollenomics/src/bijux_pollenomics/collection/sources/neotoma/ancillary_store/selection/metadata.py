"""Authenticate only the federation parts and capture declarations a selection needs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import re
import stat
from typing import Any

from ...capture.facets.replay import _control as facet_control
from ...capture.linked_resources.models import EVIDENCE_SCHEMA, SCOPED_LINKED_SCHEMA
from ...capture.linked_resources.replay import _control as linked_control
from ...capture.receipts import _object, _read, _safe_root
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...resource_catalogue.archive.files import _digest, _member
from ...resource_catalogue.source_projection import _same
from ..capsule.inventory import _FIELDS as CAPSULE_FIELDS
from ..capsule.models import (
    CAPSULE_SCHEMA,
    SCOPED_CAPSULE_SCHEMA,
    verify_metadata_population,
)
from ..federation.models import FACETS, INDEX_SCHEMA, SCHEMA, SCOPED_SCHEMA
from ..federation.validation import _FIELDS
from .budgets import _COUNT_LIMITS as _COUNT_LIMITS
from .budgets import _validate_limits as _validate_limits
from .budgets import capture_response_bound

MAX_METADATA = 16 * 1024 * 1024
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
_ID = re.compile(r"([0-9a-f]{64}):/(facets|resources)/(0|[1-9][0-9]*)\Z")


def _evidence_descriptors(document: dict[str, Any]) -> None:
    references = document.get("linked_evidence")
    if (
        not isinstance(references, dict)
        or not references
        or len(references) > MAX_FILES
        or any(
            not _digest(pin) or not _same(value, {"schema_version": EVIDENCE_SCHEMA})
            for pin, value in references.items()
        )
    ):
        raise ValueError("Selected linked evidence state descriptor is malformed")


def pinned(
    path: Path, digest: Any, size: int | None = None, *, bound: int = MAX_METADATA
) -> bytes:
    """Read one ordinary, singly linked member into the buffer its hash authenticates."""
    path = _safe_root(path)
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or (size is not None and info.st_size != size)
    ):
        raise ValueError("Selected ancillary member physical identity differs")
    raw = _read(path, min(bound, size) if size is not None else bound)
    if not _digest(digest) or sha256(raw).hexdigest() != digest:
        raise ValueError("Selected ancillary member digest differs")
    return raw


def members(document: dict[str, Any], raw: bytes) -> None:
    files = document.get("files")
    if not isinstance(files, dict) or len(files) + 1 > MAX_FILES:
        raise ValueError("Selected ancillary file declarations are malformed")
    total = 0
    for name, member in files.items():
        _member(name)
        if (
            name == "manifest.json"
            or not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member.get("bytes")) is not int
            or not 0 <= member["bytes"] <= MAX_BYTES
            or not _digest(member.get("sha256"))
        ):
            raise ValueError("Selected ancillary member declaration is malformed")
        total += member["bytes"]
    if (
        type(document.get("source_bytes")) is not int
        or document["source_bytes"] != total
        or total + len(raw) > MAX_BYTES
    ):
        raise ValueError("Selected ancillary declared byte budget differs")


def observation_identity(value: Any, population: str) -> tuple[str, int]:
    match = _ID.fullmatch(value) if isinstance(value, str) else None
    if match is None or match[2] != population:
        raise ValueError("Selection requires an exact immutable observation identity")
    return match[1], int(match[3])


@dataclass
class SelectedMetadata:
    """Selected metadata integrity, never a full federation or capsule replay."""

    root: Path
    manifest: dict[str, Any]
    index: dict[str, Any]
    capsule_sources: Mapping[str, Path]
    context_pin: str
    native_pin: str
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS
    captures: dict[str, dict[str, Any]] = field(default_factory=dict)
    rows: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    evidence_sources: Mapping[str, Path] | None = None

    def member(
        self,
        root: Path,
        document: dict[str, Any],
        name: str,
        *,
        bound: int = MAX_METADATA,
    ) -> bytes:
        _member(name)
        member = document["files"].get(name)
        if not isinstance(member, dict):
            raise ValueError("Selected ancillary member is undeclared")
        return pinned(root / name, member["sha256"], member["bytes"], bound=bound)

    def row(self, population: str, group: str, key: str) -> dict[str, Any]:
        cache = (population, key)
        if cache in self.rows:
            return self.rows[cache]
        field_name = {
            "slots": "slot_key",
            "observations": "observation_id",
            "linked_occurrences": "occurrence_id",
        }[population]
        parts = [
            part
            for part in self.index["parts"]
            if part["population"] == population
            and part["group"] == group
            and part["first_key"] <= key <= part["last_key"]
        ]
        if len(parts) != 1:
            raise ValueError("Selected federation index key is absent or ambiguous")
        part = parts[0]
        document = _object(self.member(self.root, self.manifest, part["path"]))
        rows = document.get("rows")
        if (
            set(document) != {"schema_version", "population", "rows"}
            or document["schema_version"] != INDEX_SCHEMA
            or document["population"] != population
            or not isinstance(rows, list)
            or not rows
            or len(rows) != part["row_count"]
            or any(
                not isinstance(row, dict) or not isinstance(row.get(field_name), str)
                for row in rows
            )
        ):
            raise ValueError("Selected federation index population differs")
        keys = [row[field_name] for row in rows]
        if (
            keys != sorted(set(keys))
            or keys[0] != part["first_key"]
            or keys[-1] != part["last_key"]
        ):
            raise ValueError("Selected federation index range differs")
        matches = [row for row in rows if row[field_name] == key]
        if len(matches) != 1:
            raise ValueError("Selected federation index correspondence differs")
        selected: dict[str, Any] = matches[0]
        self.rows[cache] = selected
        return selected

    def response_bound(
        self, capture: dict[str, Any], selected: dict[str, Any], receipt: dict[str, Any]
    ) -> int:
        """Budget this original capture prefix, not aggregate SDK I/O or later history."""
        return capture_response_bound(capture, selected, receipt, self.limits)

    def slot(self, observation: dict[str, Any], parent: dict[str, Any]) -> None:
        """Check selected correspondence without claiming other epoch statuses were replayed."""
        owner, facet = observation["root_identity"], observation["facet"]
        dataset = owner["dataset_id"]
        key = f"dataset-{dataset}-facet-{facet}-current"
        slot = self.row("slots", f"native-datasets-{dataset // 1000}", key)
        identities, counts = (
            slot.get("observation_ids"),
            slot.get("source_terminal_counts"),
        )
        if (
            set(slot)
            != {
                "slot_key",
                "root_identity",
                "facet",
                "content_version",
                "api_version",
                "current_declared_role",
                "current_use_role",
                "current_use_scope_verification",
                "coverage_status",
                "observation_ids",
                "selected_observation_id",
                "source_terminal_counts",
                "scientific_admission",
            }
            or not isinstance(identities, list)
            or any(not isinstance(value, str) for value in identities)
            or len(set(identities)) != len(identities)
            or observation["observation_id"] not in identities
            or not isinstance(counts, dict)
            or any(type(count) is not int or count < 1 for count in counts.values())
            or sum(counts.values()) != len(identities)
            or observation["terminal_status"] not in counts
            or slot.get("facet") != facet
            or slot.get("content_version") != "current"
            or slot.get("api_version") != "v2.0"
            or slot.get("current_declared_role") != parent["declared_root_role"]
            or slot.get("current_use_role") != parent["effective_scope_role"]
            or slot.get("current_use_scope_verification")
            != "authenticated_current_context_only"
            or slot.get("selected_observation_id") is not None
            or slot.get("scientific_admission") != "not_asserted"
            or slot.get("coverage_status")
            not in {"complete_source_entity", "recorded_without_complete_source_entity"}
            or observation["terminal_status"] == "received_complete_unqualified_facet"
            and slot["coverage_status"] != "complete_source_entity"
            or not _same(
                slot.get("root_identity"),
                {
                    key: owner[key]
                    for key in (
                        "dataset_id",
                        "site_id",
                        "collection_unit_id",
                        "dataset_type",
                        "database",
                    )
                },
            )
        ):
            raise ValueError("Selected facet slot correspondence differs")
        for value in identities:
            observation_identity(value, "facets")

    def capture(self, digest: str, kind: str) -> dict[str, Any]:
        if digest in self.captures:
            result = self.captures[digest]
            if result["descriptor"]["kind"] != kind:
                raise ValueError("Selected capture kind differs")
            return result
        owners = [
            pin
            for pin, captures in self.manifest["capsule_captures"].items()
            if digest in captures
        ]
        if len(owners) != 1 or owners[0] not in self.capsule_sources:
            raise ValueError("Selected capture owner resolver is absent or ambiguous")
        owner = owners[0]
        root = _safe_root(self.capsule_sources[owner])
        raw = pinned(root / "manifest.json", owner)
        capsule = _object(raw)
        members(capsule, raw)
        if (
            set(capsule)
            != CAPSULE_FIELDS
            | (
                {"linked_evidence"}
                if capsule.get("schema_version") == SCOPED_CAPSULE_SCHEMA
                else set()
            )
            or not isinstance(capsule.get("schema_version"), str)
            or capsule["schema_version"] not in {CAPSULE_SCHEMA, SCOPED_CAPSULE_SCHEMA}
            or capsule["context_manifest_sha256"] != self.context_pin
            or capsule["native_archive_manifest_sha256"] != self.native_pin
            or capsule["scientific_admission"] != "not_asserted"
            or type(capsule["native_body_copies"]) is not int
            or capsule["native_body_copies"] != 0
            or capsule["historical_snapshot_replaced"] is not False
            or not isinstance(capsule["captures"], dict)
            or sorted(capsule["captures"]) != self.manifest["capsule_captures"][owner]
        ):
            raise ValueError("Selected capsule identity or claims differ")
        if capsule["schema_version"] == SCOPED_CAPSULE_SCHEMA:
            _evidence_descriptors(capsule)
        descriptor = capsule["captures"][digest]
        if (
            not isinstance(descriptor, dict)
            or set(descriptor) != {"kind", "native_schema_version", "files"}
            or descriptor["kind"] != kind
            or not isinstance(descriptor["files"], dict)
        ):
            raise ValueError("Selected capture descriptor differs")
        for name, member in descriptor["files"].items():
            if _member(name) != Path(name).name or not _same(
                capsule["files"].get(f"captures/{digest}/{name}"), member
            ):
                raise ValueError("Selected capture member declarations differ")
        for name in ("capture-manifest.json", "request-plan.json"):
            self.member(root, capsule, f"captures/{digest}/{name}")
        directory = root / "captures" / digest
        controlled = (facet_control if kind == "facet" else linked_control)(
            directory, digest
        )
        document = controlled[0]
        control = _object(
            self.member(root, capsule, f"captures/{digest}/request-plan.json")
        )
        if (
            document["schema_version"] != descriptor["native_schema_version"]
            or descriptor["files"]["capture-manifest.json"]["sha256"] != digest
            or descriptor["files"]["request-plan.json"]["sha256"]
            != document["plan_sha256"]
        ):
            raise ValueError("Selected capture source identity differs")
        verify_metadata_population(descriptor, document, control)
        if document["schema_version"] == SCOPED_LINKED_SCHEMA:
            reference = control.get("source_evidence")
            if (
                not isinstance(reference, dict)
                or set(reference) != {"schema_version", "manifest_sha256"}
                or reference["schema_version"] != EVIDENCE_SCHEMA
                or not _digest(reference["manifest_sha256"])
            ):
                raise ValueError("Selected scoped evidence reference differs")
            state = reference["manifest_sha256"]
            expected = {"schema_version": EVIDENCE_SCHEMA}
            if (
                not _same(document.get("source_evidence"), reference)
                or not _same(capsule.get("linked_evidence", {}).get(state), expected)
                or not _same(
                    self.manifest.get("linked_evidence", {}).get(state), expected
                )
            ):
                raise ValueError("Selected scoped evidence owner binding differs")
        result = {
            "root": root,
            "directory": directory,
            "capsule": capsule,
            "capsule_pin": owner,
            "descriptor": descriptor,
            "document": document,
            "control": control,
            "plan": controlled[1] if kind == "facet" else controlled[2],
            "limits": controlled[2] if kind == "facet" else controlled[3],
        }
        self.captures[digest] = result
        return result

    def source_member(
        self, capture: dict[str, Any], name: str, *, bound: int = MAX_METADATA
    ) -> bytes:
        digest = capture["descriptor"]["files"]["capture-manifest.json"]["sha256"]
        return self.member(
            capture["root"],
            capture["capsule"],
            f"captures/{digest}/{name}",
            bound=bound,
        )


def selected_metadata(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    evidence_sources: Mapping[str, Path] | None = None,
) -> SelectedMetadata:
    _validate_limits(limits)
    root = _safe_root(directory)
    raw = pinned(root / "manifest.json", expected_manifest_sha256)
    manifest = _object(raw)
    members(manifest, raw)
    if (
        set(manifest)
        != _FIELDS
        | (
            {"linked_evidence"}
            if manifest.get("schema_version") == SCOPED_SCHEMA
            else set()
        )
        or not isinstance(manifest.get("schema_version"), str)
        or manifest["schema_version"] not in {SCHEMA, SCOPED_SCHEMA}
        or manifest["context_manifest_sha256"] != expected_context_sha256
        or manifest["native_archive_manifest_sha256"] != expected_native_archive_sha256
        or manifest["declared_facets"] != list(FACETS)
        or manifest["integrity_scope"] != "current_context_and_capsule_metadata"
        or manifest["entity_body_hashes_verified"] is not False
        or manifest["source_assessments_replayed"] is not False
        or manifest["scientific_admission"] != "not_asserted"
        or type(manifest["payload_copies"]) is not int
        or manifest["payload_copies"] != 0
        or manifest["original_preget_scope_reconstructed"] is not False
        or manifest["related_resource_graph_complete"] is not False
        or manifest["related_resource_scope"]
        != "captured_occurrences_and_current_native_parent_obligations"
    ):
        raise ValueError("Selected federation anchors or integrity claims differ")
    if manifest["schema_version"] == SCOPED_SCHEMA:
        _evidence_descriptors(manifest)
    owners = manifest["capsule_captures"]
    if (
        not isinstance(owners, dict)
        or sorted(owners) != manifest["capsule_manifest_sha256s"]
        or not isinstance(capsule_sources, Mapping)
    ):
        raise ValueError("Selected federation capture owners differ")
    seen = set()
    for owner, captures in owners.items():
        if (
            not _digest(owner)
            or not isinstance(captures, list)
            or not captures
            or captures != sorted(set(captures))
            or any(not _digest(capture) or capture in seen for capture in captures)
        ):
            raise ValueError(
                "Selected federation capture ownership is duplicated or malformed"
            )
        seen.update(captures)
    result = SelectedMetadata(
        root,
        manifest,
        {},
        capsule_sources,
        expected_context_sha256,
        expected_native_archive_sha256,
        limits=limits,
        evidence_sources=evidence_sources,
    )
    index = _object(result.member(root, manifest, "index.json"))
    if (
        set(index) != {"schema_version", "summary", "parts"}
        or index["schema_version"] != INDEX_SCHEMA
        or not _same(index["summary"], manifest["summary"])
        or not isinstance(index["parts"], list)
    ):
        raise ValueError("Selected federation index directory differs")
    paths = {"index.json", "scope/current-parent-proof.json"}
    for part in index["parts"]:
        if (
            not isinstance(part, dict)
            or set(part)
            != {
                "population",
                "group",
                "first_key",
                "last_key",
                "path",
                "sha256",
                "bytes",
                "row_count",
            }
            or part["population"] not in {"slots", "observations", "linked_occurrences"}
            or any(
                not isinstance(part[key], str)
                for key in ("group", "first_key", "last_key", "path")
            )
            or part["first_key"] > part["last_key"]
            or type(part["row_count"]) is not int
            or part["row_count"] < 1
            or part["path"] in paths
            or not _same(
                {key: part[key] for key in ("sha256", "bytes")},
                manifest["files"].get(part["path"]),
            )
        ):
            raise ValueError("Selected federation part declaration differs")
        paths.add(part["path"])
    if paths != set(manifest["files"]):
        raise ValueError("Selected federation member correspondence differs")
    result.index = index
    return result
