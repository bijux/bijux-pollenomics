"""One bounded portable occurrence publication for complete native source scopes."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import (
    OwnedTreeWriter,
    validate_regular_namespace,
)
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
)

from ...client import positive_native_id
from ...publication.ownership import publish_owned_source_tree
from ..facets.links import discover_neotoma_facet_links
from ..facets.models import NeotomaFacetScopeInputs
from ..receipts import _object, _read, _safe_root, _write_json
from ..resources.models import EXPOSURE_ROLES
from ..resources.replay import _same_json
from .authority import (
    _RANK,
    _digest,
    authenticate_linked_source_scope,
    source_bindings,
    source_pins,
    validate_linked_authority,
)
from .models import EVIDENCE_SCHEMA, LINKED_KINDS, NeotomaLinkedEvidence

PART_TARGET_BYTES = 2 * 1024 * 1024
PART_HARD_BYTES = 3 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_EVIDENCE_BYTES = 256 * 1024 * 1024
MAX_PARTS = 256
MAX_OCCURRENCES = 250000
MAX_TARGETS = 10000
_INDEX_FIELDS = {
    "schema_version",
    "status",
    "authority",
    "source_input_pins",
    "parts",
    "targets",
    "occurrence_count",
    "scientific_admission",
}
_TARGET_FIELDS = {
    "kind",
    "native_id",
    "exposure_role",
    "occurrence_count",
    "has_direct_proof",
    "proof_ranges",
    "metadata_dependencies",
}


def _encoded(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def _count(value: Any, *, zero: bool = False) -> int:
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError("Linked evidence count or range is invalid")
    return value


def _index(directory: Path, expected: str) -> dict[str, Any]:
    raw = _read(directory / "evidence-manifest.json", MAX_MANIFEST_BYTES)
    if sha256(raw).hexdigest() != _digest(expected):
        raise ValueError("Linked evidence manifest identity differs")
    value = _object(raw)
    if (
        set(value) != _INDEX_FIELDS
        or value["schema_version"] != EVIDENCE_SCHEMA
        or value["status"] != "closed"
        or value["scientific_admission"] != "not_asserted"
        or not isinstance(value["authority"], dict)
        or not isinstance(value["source_input_pins"], dict)
        or not isinstance(value["parts"], list)
        or len(value["parts"]) > MAX_PARTS
        or not isinstance(value["targets"], dict)
        or len(value["targets"]) > MAX_TARGETS
    ):
        raise ValueError("Linked evidence manifest fields differ")
    validate_linked_authority(value["authority"])
    parts = {}
    total_bytes = len(raw)
    rows = 0
    for part in value["parts"]:
        if not isinstance(part, dict) or set(part) != {"sha256", "bytes", "rows"}:
            raise ValueError("Linked evidence part descriptor differs")
        digest = _digest(part["sha256"])
        size = _count(part["bytes"])
        count = _count(part["rows"])
        if digest in parts or size > PART_HARD_BYTES:
            raise ValueError("Linked evidence part population or byte bound differs")
        total_bytes += size
        rows += count
        parts[digest] = part
    if (
        total_bytes > MAX_EVIDENCE_BYTES
        or rows > MAX_OCCURRENCES
        or rows != _count(value["occurrence_count"], zero=True)
    ):
        raise ValueError("Linked evidence finite publication budget differs")
    ranges: dict[str, list[tuple[int, int]]] = {digest: [] for digest in parts}
    target_rows = 0
    for key, target in value["targets"].items():
        if (
            not isinstance(target, dict)
            or set(target) != _TARGET_FIELDS
            or target["kind"] not in LINKED_KINDS
            or key != f"{target['kind']}-{positive_native_id(target['native_id'])}"
            or not isinstance(target["exposure_role"], str)
            or target["exposure_role"] not in EXPOSURE_ROLES
            or type(target["has_direct_proof"]) is not bool
            or not isinstance(target["metadata_dependencies"], list)
            or not isinstance(target["proof_ranges"], list)
        ):
            raise ValueError("Linked evidence target identity or role differs")
        dependency = (
            value["authority"]["protected_contacts"].get(str(target["native_id"]))
            if target["kind"] == "contact"
            else None
        )
        expected_dependencies = dependency["metadata_witnesses"] if dependency else []
        if (
            not _same_json(target["metadata_dependencies"], expected_dependencies)
            or dependency
            and _RANK[target["exposure_role"]] < _RANK[dependency["exposure_role"]]
        ):
            raise ValueError("Linked evidence restrictive metadata dependency differs")
        count = 0
        previous_range = (-1, -1)
        part_order = {digest: offset for offset, digest in enumerate(parts)}
        for ref in target["proof_ranges"]:
            if not isinstance(ref, dict) or set(ref) != {
                "part_sha256",
                "start",
                "count",
            }:
                raise ValueError("Linked evidence proof range fields differ")
            digest = _digest(ref["part_sha256"])
            start, length = _count(ref["start"], zero=True), _count(ref["count"])
            if digest not in parts or start + length > parts[digest]["rows"]:
                raise ValueError("Linked evidence proof range exceeds its part")
            position = (part_order[digest], start)
            if position <= previous_range:
                raise ValueError("Linked evidence proof range order differs")
            previous_range = position
            ranges[digest].append((start, length))
            count += length
        if count != _count(target["occurrence_count"]):
            raise ValueError("Linked evidence target proof count differs")
        target_rows += count
    for digest, entries in ranges.items():
        cursor = 0
        for start, length in sorted(entries):
            if start != cursor:
                raise ValueError("Linked evidence proof ranges overlap or omit rows")
            cursor += length
        if cursor != parts[digest]["rows"]:
            raise ValueError("Linked evidence part rows are not fully indexed")
    if target_rows != rows:
        raise ValueError("Linked evidence target population differs")
    return value


def _namespace(root: Path, index: dict[str, Any]) -> None:
    expected = {"evidence-manifest.json"}
    expected.update("proofs/" + row["sha256"] + ".json" for row in index["parts"])
    validate_regular_namespace(
        root, expected, max_files=MAX_PARTS + 1, max_bytes=MAX_EVIDENCE_BYTES
    )


def _part(root: Path, descriptor: dict[str, Any]) -> list[dict[str, Any]]:
    path = _safe_root(root / "proofs" / (descriptor["sha256"] + ".json"))
    raw = _read(path, descriptor["bytes"])
    if (
        len(raw) != descriptor["bytes"]
        or sha256(raw).hexdigest() != descriptor["sha256"]
    ):
        raise ValueError("Linked evidence proof part identity differs")
    value = _object(raw)
    if (
        set(value) != {"schema_version", "proofs"}
        or value["schema_version"] != EVIDENCE_SCHEMA
        or not isinstance(value["proofs"], list)
        or len(value["proofs"]) != descriptor["rows"]
        or any(not isinstance(row, dict) for row in value["proofs"])
    ):
        raise ValueError("Linked evidence proof part population differs")
    return value["proofs"]


def load_neotoma_linked_evidence(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    expected_roster_sha256: str,
    scope: NeotomaFacetScopeInputs,
    source_facets: Mapping[str, Path],
    legacy_rosters: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Guard all original bytes and namespaces, without repeating semantic discovery."""
    root = _safe_root(directory)
    index = _index(root, expected_manifest_sha256)
    if index["authority"]["roster_sha256"] != expected_roster_sha256:
        raise ValueError("Linked evidence frozen roster identity differs")
    inputs: dict[str, Any] = {
        "expected_roster_sha256": expected_roster_sha256,
        "scope": scope,
        "source_facets": source_facets,
        "legacy_rosters": legacy_rosters,
    }
    if not _same_json(
        source_pins(source_bindings(**inputs)), index["source_input_pins"]
    ):
        raise ValueError("Linked evidence source pins or namespace differ")
    _namespace(root, index)
    for descriptor in index["parts"]:
        _part(root, descriptor)
    _namespace(root, index)
    if not _same_json(
        source_pins(source_bindings(**inputs)), index["source_input_pins"]
    ):
        raise ValueError("Linked evidence source pins changed during readback")
    return index


def _proof_owner(
    proof: dict[str, Any], index: dict[str, Any], kind: str, native_id: int
) -> None:
    if (
        proof.get("target_kind") != kind
        or type(proof.get("native_id")) is not int
        or proof["native_id"] != native_id
    ):
        raise ValueError("Linked selected proof native target differs")
    if (
        proof.get("source_capture_manifest_sha256")
        not in index["authority"]["source_captures"]
    ):
        raise ValueError("Linked selected proof source scope differs")
    dataset = positive_native_id(proof.get("root_dataset_id"))
    if not _same_json(
        proof.get("root_identity"),
        index["authority"]["root_identities"].get(str(dataset)),
    ):
        raise ValueError("Linked selected proof native root differs")


def read_neotoma_linked_evidence_metadata(
    directory: Path, *, expected_manifest_sha256: str
) -> dict[str, Any]:
    """Authenticate the anchored metadata header, without source or proof-body claims."""
    return _index(_safe_root(directory), expected_manifest_sha256)


def _occurrences(
    root: Path, index: dict[str, Any], keys: set[str]
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    ranges: dict[str, list[tuple[int, int, str]]] = {}
    for key in sorted(keys):
        for ref in index["targets"][key]["proof_ranges"]:
            ranges.setdefault(ref["part_sha256"], []).append(
                (ref["start"], ref["count"], key)
            )
    for descriptor in index["parts"]:
        digest = descriptor["sha256"]
        if digest not in ranges:
            continue
        rows = _part(root, descriptor)
        for start, count, key in sorted(ranges[digest]):
            target = index["targets"][key]
            for offset in range(start, start + count):
                proof = rows[offset]
                _proof_owner(proof, index, target["kind"], target["native_id"])
                yield proof, {"part_sha256": digest, "row_offset": offset}


def iter_neotoma_linked_evidence_occurrences(
    directory: Path, *, expected_manifest_sha256: str
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield all dated proofs from each same authenticated part buffer once."""
    root = _safe_root(directory)
    index = _index(root, expected_manifest_sha256)
    for proof, locator in _occurrences(root, index, set(index["targets"])):
        yield proof, {"evidence_manifest_sha256": expected_manifest_sha256, **locator}


def read_neotoma_linked_evidence_target(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    kind: str,
    native_id: int,
) -> dict[str, Any]:
    """Read dated proof metadata only; this never authorizes a source entity GET.

    Capture callers must also authenticate the complete source bindings. Selected
    consumers must independently apply their current context and exposure duties.
    """
    if kind not in LINKED_KINDS:
        raise ValueError("Linked evidence target kind is invalid")
    key = f"{kind}-{positive_native_id(native_id)}"
    root = _safe_root(directory)
    index = _index(root, expected_manifest_sha256)
    if key not in index["targets"]:
        raise ValueError("Linked target has no authenticated source proof")
    target = index["targets"][key]
    proofs, locators = [], []
    for proof, locator in _occurrences(root, index, {key}):
        proofs.append(proof)
        locators.append(
            {"evidence_manifest_sha256": expected_manifest_sha256, **locator}
        )
    return {
        "target": target,
        "source_proofs": tuple(proofs),
        "proof_locators": tuple(locators),
        "scientific_admission": "not_asserted",
        "source_epoch": EVIDENCE_SCHEMA,
    }


def publish_neotoma_linked_evidence(
    directory: Path,
    *,
    expected_roster_sha256: str,
    scope: NeotomaFacetScopeInputs,
    source_facets: Mapping[str, Path],
    legacy_rosters: Mapping[str, Path] | None = None,
) -> NeotomaLinkedEvidence:
    """Recompute the complete finite native graph once, then publish absent output."""
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Linked evidence output exists: {final}")
    inputs: dict[str, Any] = {
        "expected_roster_sha256": expected_roster_sha256,
        "scope": scope,
        "source_facets": source_facets,
        "legacy_rosters": legacy_rosters,
    }
    authority = authenticate_linked_source_scope(**inputs)
    before = source_pins(source_bindings(**inputs))
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(
        staging, max_bytes=MAX_EVIDENCE_BYTES + 65536, max_files=MAX_PARTS + 2
    ) as writer:
        try:
            targets: dict[str, Any] = {}
            parts: list[dict[str, Any]] = []
            pending: list[dict[str, Any]] = []
            pending_size = 0
            occurrences: set[str] = set()
            total = 0

            def flush() -> None:
                nonlocal pending, pending_size, total
                if not pending:
                    return
                raw = _encoded({"schema_version": EVIDENCE_SCHEMA, "proofs": pending})
                if (
                    len(raw) > PART_HARD_BYTES
                    or len(parts) >= MAX_PARTS
                    or total + len(raw) > MAX_EVIDENCE_BYTES
                ):
                    raise ValueError("Linked evidence finite part byte budget exceeded")
                digest = sha256(raw).hexdigest()
                writer.write_bytes("proofs/" + digest + ".json", raw)
                number = len(parts)
                for offset, proof in enumerate(pending):
                    key = f"{proof['target_kind']}-{proof['native_id']}"
                    ranges = targets[key]["proof_ranges"]
                    if (
                        ranges
                        and ranges[-1]["part_number"] == number
                        and ranges[-1]["start"] + ranges[-1]["count"] == offset
                    ):
                        ranges[-1]["count"] += 1
                    else:
                        ranges.append(
                            {"part_number": number, "start": offset, "count": 1}
                        )
                parts.append(
                    {"sha256": digest, "bytes": len(raw), "rows": len(pending)}
                )
                total += len(raw)
                pending, pending_size = [], 0

            for digest, capture in sorted(source_facets.items()):
                linked = discover_neotoma_facet_links(
                    capture,
                    expected_manifest_sha256=digest,
                    include_higher_taxa=True,
                    scope_inputs={expected_roster_sha256: scope},
                )
                if any(
                    row["reason"]
                    not in {
                        "source_null_native_id",
                        "not_attempted_exposure_role",
                        "not_attempted_parent_scope",
                    }
                    for row in linked["unavailable"]
                ):
                    raise ValueError(
                        "Complete linked source proof requires source-format review"
                    )
                for proof in sorted(
                    linked["links"],
                    key=lambda row: (row["target_kind"], row["native_id"]),
                ):
                    fingerprint = sha256(_encoded(proof)).hexdigest()
                    if (
                        fingerprint in occurrences
                        or len(occurrences) >= MAX_OCCURRENCES
                    ):
                        raise ValueError(
                            "Linked occurrence is duplicated or exceeds finite population"
                        )
                    occurrences.add(fingerprint)
                    native_id = positive_native_id(proof["native_id"])
                    kind = proof["target_kind"]
                    if kind not in LINKED_KINDS:
                        raise ValueError("Unknown native linked target kind")
                    key = f"{kind}-{native_id}"
                    target = targets.setdefault(
                        key,
                        {
                            "kind": kind,
                            "native_id": native_id,
                            "exposure_role": proof["inherited_exposure_role"],
                            "occurrence_count": 0,
                            "has_direct_proof": False,
                            "proof_ranges": [],
                            "metadata_dependencies": [],
                        },
                    )
                    target["exposure_role"] = max(
                        (target["exposure_role"], proof["inherited_exposure_role"]),
                        key=_RANK.__getitem__,
                    )
                    target["occurrence_count"] += 1
                    target["has_direct_proof"] |= (
                        proof["relation"] != "source_reported_higher_taxon"
                    )
                    size = len(_encoded(proof))
                    if pending and pending_size + size > PART_TARGET_BYTES:
                        flush()
                    pending.append(proof)
                    pending_size += size
            flush()
            if len(targets) > MAX_TARGETS:
                raise ValueError("Linked target population exceeds its finite bound")
            for target in targets.values():
                dependency = (
                    authority["protected_contacts"].get(str(target["native_id"]))
                    if target["kind"] == "contact"
                    else None
                )
                if dependency is not None:
                    target["metadata_dependencies"] = dependency["metadata_witnesses"]
                    target["exposure_role"] = max(
                        (target["exposure_role"], dependency["exposure_role"]),
                        key=_RANK.__getitem__,
                    )
                for ref in target["proof_ranges"]:
                    ref["part_sha256"] = parts[ref.pop("part_number")]["sha256"]
            index = {
                "schema_version": EVIDENCE_SCHEMA,
                "status": "closed",
                "authority": authority,
                "source_input_pins": before,
                "parts": parts,
                "targets": dict(sorted(targets.items())),
                "occurrence_count": len(occurrences),
                "scientific_admission": "not_asserted",
            }
            raw = _encoded(index)
            if len(raw) > MAX_MANIFEST_BYTES or total + len(raw) > MAX_EVIDENCE_BYTES:
                raise ValueError("Linked evidence manifest exceeds finite byte budget")
            writer.write_bytes("evidence-manifest.json", raw)
            manifest_sha = sha256(raw).hexdigest()
            publish_owned_source_tree(
                writer,
                staging=staging,
                final=final,
                validate=lambda location: load_neotoma_linked_evidence(
                    location, expected_manifest_sha256=manifest_sha, **inputs
                ),
            )
            return NeotomaLinkedEvidence(final, manifest_sha)
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {"status": "refused_linked_evidence", "reason": str(error)},
                    writer=writer,
                )
            raise
