"""Validate partial current count evidence without discharging original mass custody."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....retained_source import validate_capsule, validated_descriptor
from .transport import json_object, normalized, validate_packet

WITNESS = "reports/science/source-cohorts/neotoma-selected-counts.json"
CAPTURE = "data/source-custody/neotoma/selected-counts/capture.json"
ORIGINAL_COUNT_CRITERION = "Reconcile the selected sample rows with the original mass audit identity and normalized source locators before source-certificate ownership. This input feeds the core report and cannot be reconstructed from that report."
CAPTURE_SHA256 = "22f2c291682ce9b7f7d502f6ce8e98b06e79d62e8627e545faf38c21fafd3a75"
OWNERS = {
    "source-relations/neotoma/abbo-core-identity/count-mass-crosscheck": "docs/report/source-relations/neotoma/abbo-core-identity/count-mass-crosscheck.json",
    "source-relations/neotoma/swedish-lake-core-identity/count-mass-crosscheck": "docs/report/source-relations/neotoma/swedish-lake-core-identity/count-mass-crosscheck.json",
}


def require(value: object, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ReportRebuildError("Selected Neotoma count custody: " + reason)


def owner_paths(owner: JsonObject) -> list[str]:
    """Require an explicit, non-overlapping set of declared owner outputs."""
    paths = owner.get("paths")
    require(
        isinstance(paths, list) and all(isinstance(path, str) for path in paths),
        "Typed ownership paths required",
    )
    return cast(list[str], paths)


def ownership(owners: list[JsonObject]) -> None:
    """Require only the exact count owners and reject any overlapping sibling."""
    for name, publication in OWNERS.items():
        selected = [row for row in owners if row.get("owner_id") == name]
        require(len(selected) == 1, "Unique selected count owner required")
        row = selected[0]
        require(
            row["role"] == "unresolved"
            and row["verification"] == ORIGINAL_COUNT_CRITERION
            and row["paths"] == [publication]
            and row["producer_paths"] == []
            and row["producer_inputs"] == [],
            "Exact current count owner contract required",
        )
        require(
            all(
                other is row or publication not in owner_paths(other)
                for other in owners
            ),
            "Another owner overlaps the selected count path",
        )


def physical(repository: Path, name: str) -> Path:
    """Resolve an ordinary retained-input file without following aliases."""
    path = repository / name
    require(
        path.is_file()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular retained member required",
    )
    return path


def exact_tree(root: Path, names: set[str]) -> None:
    """Require an exact, alias-free physical member inventory."""
    require(
        root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical capture root required",
    )
    files: set[str] = set()
    directories: set[str] = set()
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Retained alias or special entry",
        )
        (files if path.is_file() else directories).add(
            path.relative_to(root).as_posix()
        )
    require(
        files == names | {"capture.json"} and directories == {"payloads"},
        "Exact retained namespace required",
    )


def _validated(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> JsonObject:
    present = (repository / CAPTURE).exists() or (repository / CAPTURE).is_symlink()
    witness = repository / WITNESS
    require(
        not any(node.is_symlink() for node in (witness, *witness.parents)),
        "Current count witness ancestry alias",
    )
    witness_present = witness.exists() or witness.is_symlink()
    if witness_present:
        physical(repository, WITNESS)
        require(present, "Published current count evidence requires its exact capture")
    selected = [r for r in owners if r.get("owner_id") in OWNERS]
    if not selected and not present:
        return {}
    ownership(owners)
    if not present:
        return {}
    raw = physical(repository, CAPTURE).read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == CAPTURE_SHA256,
        "Exact actual metadata capture required",
    )
    packet = json_object(raw)
    resolver = validated_descriptor(
        repository, Path(CAPTURE).parent.as_posix(), packet["members"]
    )

    def payload(name: str) -> bytes:
        return resolver.read_source(name)

    evidence = validate_packet(packet, payload)
    bindings = {row["original"]["path"]: row for row in packet["public_bindings"]}
    plan_row = packet["native_references"]["plan"]
    plan = json_object(payload(bindings[plan_row["path"]]["member"]))
    original_root = Path(plan["repository"])
    for publication in OWNERS.values():
        original = str(original_root / publication)
        require(original in bindings, "Original current count role absent")
        binding = bindings[original]
        expected = normalized(binding["original"])
        current = physical(repository, publication).read_bytes()
        require(
            current == payload(binding["member"])
            and len(current) == expected["bytes"]
            and hashlib.sha256(current).hexdigest() == expected["sha256"],
            "Current count receipt changed",
        )
        require(
            publication in tracked_by_path, "Current selected count must be governed"
        )
        entry = tracked_by_path[publication]
        require(
            entry.path == publication.removeprefix("docs/report/")
            and entry.kind == "file"
            and entry.size == len(current)
            and entry.sha256 == expected["sha256"],
            "Tracked current count inventory differs",
        )
    validate_capsule(repository, Path(CAPTURE).parent.as_posix(), packet["members"])
    return {
        "schema_version": "neotoma-selected-count-current-partial-evidence.v1",
        "capture": {"path": CAPTURE, "sha256": CAPTURE_SHA256},
        "current_source_evidence": evidence,
        "current_count_evidence_paths": list(OWNERS.values()),
        "selected_retained_entries": 0,
        "current_count_receipts_checked": 2,
        "count_owners_remain_unresolved": True,
        "original_count_acceptance_criterion_discharged": False,
        "historical_manifest_owners_selected": False,
        "original_mass_or_manifest_construction_recovered": False,
        "physical_core_chronology_denominator_rights_human_or_LRA_admitted": False,
    }


def validated_neotoma_selected_count_evidence(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> JsonObject:
    """Authenticate portable actual evidence without invoking data consumers."""
    try:
        return _validated(repository, tracked_by_path, owners)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ReportRebuildError(
            "Selected Neotoma count evidence is malformed"
        ) from error
