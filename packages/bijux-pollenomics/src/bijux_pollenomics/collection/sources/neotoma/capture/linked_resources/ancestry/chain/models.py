"""Independent portable source epochs and finite immutable-baseline chain limits."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ....receipts import _object
from ..models import NeotomaTaxonAncestrySources

SCHEMA = "neotoma-taxon-ancestry-chain.v1"
CAPTURE_SCHEMA = "neotoma-taxonomy-ancestry-http-capture.v1"
COLLECTIONS = ("edges", "taxa", "publications", "frontier", "cycle_components")
MAX_ENTITY_BYTES = 2 * 1024 * 1024
MAX_CAPTURE_BYTES = 64 * 1024 * 1024
MAX_SOURCE_BYTES = 768 * 1024 * 1024
MAX_FILES = 40960


@dataclass(frozen=True)
class NeotomaTaxonAncestryChainLimits:
    """Bound expansion from the original seeds, never from a newly fetched parent."""

    max_additional_parent_hops: int = 32
    max_new_taxa: int = 10000
    max_new_requests: int = 10000
    max_literal_edges: int = 100000

    def validate(self) -> None:
        """Reject booleans, unknown-sized populations and cap increases."""
        for name, maximum in (
            ("max_additional_parent_hops", 32),
            ("max_new_taxa", 10000),
            ("max_new_requests", 10000),
            ("max_literal_edges", 100000),
        ):
            value = getattr(self, name)
            if (
                type(value) is not int
                or not 0 <= value <= maximum
                or (name != "max_additional_parent_hops" and value == 0)
            ):
                raise ValueError("Ancestry chain requires native finite bounds")


@dataclass(frozen=True)
class NeotomaTaxonAncestryChainSources:
    """Resolve literal independently pinned source identities without path discovery."""

    recorded_baseline_sources: NeotomaTaxonAncestrySources
    baseline_projection_directory: Path
    expected_baseline_projection_sha256: str
    chain_sources: Mapping[str, Path]
    ancestry_capture_sources: Mapping[str, Path]
    current_context_directory: Path
    expected_current_context_sha256: str
    current_native_archive_directory: Path
    expected_current_native_archive_sha256: str
    context_sources: Mapping[str, Path] = field(default_factory=dict)
    native_archive_sources: Mapping[str, Path] = field(default_factory=dict)


DEFAULT_LIMITS = NeotomaTaxonAncestryChainLimits()


def capture_control(
    manifest_raw: bytes,
    plan_raw: bytes,
    pin: str,
    parent: str | None,
    baseline_pin: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Decode only the strict closed wire owned jointly with the future producer."""
    manifest = _object(manifest_raw)
    if (
        sha256(manifest_raw).hexdigest() != pin
        or set(manifest)
        != {
            "schema_version",
            "status",
            "plan_sha256",
            "resources",
            "request_count",
            "response_bytes",
            "scientific_admission",
        }
        or manifest["schema_version"] != CAPTURE_SCHEMA
        or manifest["status"] != "closed"
        or manifest["scientific_admission"] != "not_asserted"
    ):
        raise ValueError("Ancestry capture wire is unknown, incomplete or unanchored")
    plan = _object(plan_raw)
    if (
        sha256(plan_raw).hexdigest() != manifest["plan_sha256"]
        or set(plan)
        != {
            "schema_version",
            "source_ancestry",
            "current_context_manifest_sha256",
            "current_native_archive_manifest_sha256",
            "frontier_target_keys",
            "limits",
        }
        or plan["schema_version"] != CAPTURE_SCHEMA
    ):
        raise ValueError("Ancestry capture plan differs")
    from ..models import SCHEMA as BASELINE_SCHEMA

    if not isinstance(plan["limits"], dict) or any(
        type(value) is not int for value in plan["limits"].values()
    ):
        raise ValueError("Ancestry capture limits require native integers")
    if plan["source_ancestry"] != {
        "schema_version": SCHEMA if parent else BASELINE_SCHEMA,
        "manifest_sha256": parent or baseline_pin,
    } or plan["limits"] != {
        "max_response_bytes": MAX_ENTITY_BYTES,
        "max_attempts": 1,
    }:
        raise ValueError("Ancestry capture parent closure or finite limits differ")
    return manifest, plan


def capture_target(key: str, entry: Any, frontier: dict[str, Any]) -> dict[str, Any]:
    """Reject foreign identities, omitted roots and depth rebasing before source IO."""
    if (
        key not in frontier
        or not isinstance(entry, dict)
        or set(entry)
        != {
            "target_key",
            "kind",
            "native_id",
            "root_dataset_ids",
            "recorded_role",
            "recorded_hop",
            "witness_edge_id",
            "terminal_status",
            "attempts",
        }
    ):
        raise ValueError("Ancestry target is absent from the complete parent frontier")
    node = frontier[key]
    if (
        entry["target_key"] != key
        or entry["kind"] != node["target_kind"]
        or type(entry["native_id"]) is not int
        or entry["native_id"] != node["native_id"]
        or entry["root_dataset_ids"] != node["current_root_dataset_ids"]
        or entry["recorded_role"] != node["current_use_role"]
        or type(entry["recorded_hop"])
        is not type(node.get("additional_parent_hops_from_seed"))
        or entry["recorded_hop"] != node.get("additional_parent_hops_from_seed")
        or any(type(root) is not int for root in entry["root_dataset_ids"])
    ):
        raise ValueError(
            "Ancestry target native identity, frozen depth or complete root duties differ"
        )
    return dict(node)


def capture_members(entry: dict[str, Any]) -> set[str]:
    """Bind finite literal receipt/body names to the official native request."""
    from .....resource_catalogue.archive.files import _digest
    from ...protocol import request_for

    key, attempts = entry["target_key"], entry["attempts"]
    expected: set[str] = set()
    for attempt in attempts:
        request = request_for(
            {
                "target_key": key,
                "kind": entry["kind"],
                "native_id": entry["native_id"],
            },
            1,
        )
        if (
            not isinstance(attempt, dict)
            or set(attempt)
            not in (
                {"request_name", "receipt_file", "receipt_sha256"},
                {"request_name", "receipt_file", "receipt_sha256", "body_file"},
            )
            or attempt["request_name"] != request.name
            or attempt["receipt_file"] != f"{request.name}.receipt.json"
            or not _digest(attempt["receipt_sha256"])
            or (
                "body_file" in attempt
                and attempt["body_file"] != f"{request.name}.body"
            )
        ):
            raise ValueError("Ancestry source receipt/body locator differs")
        expected.add(attempt["receipt_file"])
        if "body_file" in attempt:
            expected.add(attempt["body_file"])
    return expected


def validate_capture_pins(pins: tuple[str, ...], maximum: int) -> None:
    """Reject duplicate or non-native capture references before resolving sources."""
    from .....resource_catalogue.archive.files import _digest

    if (
        not isinstance(pins, tuple)
        or len(pins) > maximum
        or any(not _digest(pin) for pin in pins)
        or len(set(pins)) != len(pins)
    ):
        raise ValueError("Ancestry capture reference population is malformed")


def strongest_roles(*populations: dict[int, str]) -> dict[int, str]:
    """Keep every known historical or current restriction without changing owners."""
    from ...protocol import _RANK

    result: dict[int, str] = {}
    for population in populations:
        for identity, role in population.items():
            result[identity] = max(
                (result.get(identity, role), role), key=_RANK.__getitem__
            )
    return result


def reconcile_roots(
    recorded: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    """Match every frozen native owner while allowing stronger independent duties."""
    fields = ("dataset_id", "site_id", "collection_unit_id", "dataset_type", "database")
    if set(recorded) != {str(identity) for identity in current["roots"]} or any(
        any(owner[field] != current["roots"][int(key)][field] for field in fields)
        for key, owner in recorded.items()
    ):
        raise ValueError("Ancestry complete current root owner population differs")
    return {
        **current,
        "roles": strongest_roles(
            current["roles"],
            {int(key): row["exposure_role"] for key, row in recorded.items()},
        ),
    }


def validate_sources(sources: NeotomaTaxonAncestryChainSources) -> None:
    """Reject malformed independent bindings before opening any source namespace."""
    from .....resource_catalogue.archive.files import _digest

    if not isinstance(sources, NeotomaTaxonAncestryChainSources):
        raise ValueError("Ancestry chain requires explicit source bindings")
    for mapping in (
        sources.chain_sources,
        sources.ancestry_capture_sources,
        sources.context_sources,
        sources.native_archive_sources,
    ):
        if (
            not isinstance(mapping, Mapping)
            or len(mapping) > 10000
            or any(not _digest(key) for key in mapping)
        ):
            raise ValueError("Ancestry chain source resolver is malformed")
    if not isinstance(sources.recorded_baseline_sources, NeotomaTaxonAncestrySources):
        raise ValueError("Ancestry recorded baseline source bindings differ")


def baseline_limits(recorded: dict[str, Any]) -> NeotomaTaxonAncestryChainLimits:
    """Compare a delta against recorded baseline bounds, not newly requested bounds."""
    return NeotomaTaxonAncestryChainLimits(
        **{
            name: recorded[name]
            for name in (
                "max_additional_parent_hops",
                "max_new_taxa",
                "max_literal_edges",
            )
        }
    )


def entity_role(
    target: dict[str, Any],
    roots: set[int],
    roles: dict[int, str],
    epochs: Iterable[dict[str, Any]],
) -> str:
    """Retain independent PI restrictions from every authenticated source epoch."""
    from ...protocol import _RANK

    inherited = [roles[identity] for identity in roots]
    if target["kind"] == "contact":
        for epoch in epochs:
            protected = epoch["protected"].get(str(target["native_id"]))
            if protected is not None:
                inherited.append(protected["exposure_role"])
    return max(inherited, key=_RANK.__getitem__)


def capture_population(
    manifest: dict[str, Any], plan: dict[str, Any]
) -> tuple[list[Any], list[str]]:
    """Require every ordered target slot before graph/source access begins."""
    entries, keys = manifest["resources"], plan["frontier_target_keys"]
    if (
        not isinstance(keys, list)
        or not keys
        or any(not isinstance(key, str) for key in keys)
        or len(set(keys)) != len(keys)
        or not isinstance(entries, list)
        or len(entries) != len(keys)
    ):
        raise ValueError("Ancestry complete capture target population differs")
    return entries, keys


@dataclass
class AncestrySourceBudget:
    """Count unique physical input members across overlapping explicit resolvers."""

    max_files: int = MAX_FILES
    members: dict[tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Keep the operational closure file bound finite and native-valued."""
        if type(self.max_files) is not int or not 1 <= self.max_files <= MAX_FILES:
            raise ValueError(
                "Ancestry source file bound must be a positive native integer"
            )

    def include(self, files: Mapping[str, tuple[int, ...]]) -> None:
        """Refuse a complete source closure beyond its file or unique-byte bound."""
        for device, inode, _kind, _links, size, _mtime, _ctime in files.values():
            self.members[device, inode] = size
        if (
            len(self.members) > self.max_files
            or sum(self.members.values()) > MAX_SOURCE_BYTES
        ):
            raise ValueError("Ancestry complete source closure exceeds finite budget")
