"""Bind reviewed checked-in report documentation and code to the Git candidate."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import subprocess

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    ReproducibleReportError,
    repository_identity,
)

from .contracts import (
    JsonObject,
    ReportRebuildError,
    canonical_json_sha256,
    sha256_bytes,
)
from .evidence import inventory_json
from .ownership import (
    DEFAULT_INVENTORY,
    ReportOwnershipError,
    _load_inventory,
    _regular_confined_file,
    check_report_ownership,
)

# This independent admission set is reviewed separately from mutable role labels.
# Updating a maintained report path requires an explicit transport-contract change.
MAINTAINED_ROLE_PATHS = {
    "maintained_code": (
        62,
        "fe00aed84742364e74dfa0bc51425268e0e2ec657a891410530eaaebd19b8629",
    ),
    "maintained_editorial": (
        172,
        "c2a7b34cac08b8c8bbfb8819117c101c774c7f799b09e908f94fa87c72933e9e",
    ),
}
SOURCE_FORMATS = {
    "maintained_code": frozenset({".py", ".R"}),
    "maintained_editorial": frozenset({".md"}),
}


def _head_blob(repository: Path, path: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "show", f"HEAD:{path}"],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReportRebuildError(
            f"maintained source has no committed blob: {path}"
        ) from error
    return result.stdout


def validated_maintained_report_sources(
    repository: Path,
    tracked: tuple[InventoryEntry, ...],
    *,
    expected_repository: JsonObject,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only reviewed source formats and bytes from this clean Git commit."""
    repository = repository.resolve()
    try:
        ownership = check_report_ownership(repository)
        inventory = _load_inventory(repository, DEFAULT_INVENTORY)
        inventory_path = _regular_confined_file(
            repository, DEFAULT_INVENTORY.as_posix(), "ownership inventory"
        )
        inventory_bytes = inventory_path.read_bytes()
        if inventory_bytes != _head_blob(repository, DEFAULT_INVENTORY.as_posix()):
            raise ReportRebuildError("ownership inventory differs from Git candidate")
        if repository_identity(repository, required=True) != expected_repository:
            raise ReportRebuildError("maintained source Git candidate changed")
    except (ReportOwnershipError, ReproducibleReportError) as error:
        raise ReportRebuildError(
            "maintained source ownership or Git identity failed"
        ) from error

    role_paths: dict[str, list[str]] = {role: [] for role in MAINTAINED_ROLE_PATHS}
    role_owners: dict[str, dict[str, list[str]]] = {
        role: {} for role in MAINTAINED_ROLE_PATHS
    }
    for raw in inventory["owners"]:
        owner = raw if isinstance(raw, dict) else {}
        role = owner.get("role")
        if role not in MAINTAINED_ROLE_PATHS:
            continue
        paths = owner["paths"]
        if not isinstance(paths, list) or not all(
            isinstance(path, str) for path in paths
        ):
            raise ReportRebuildError("maintained source owner paths are invalid")
        role_paths[role].extend(paths)
        role_owners[role][owner["owner_id"]] = paths

    for role, (expected_count, expected_digest) in MAINTAINED_ROLE_PATHS.items():
        paths = sorted(role_paths[role])
        if (
            len(paths) != expected_count
            or canonical_json_sha256(paths) != expected_digest
            or ownership.role_counts.get(role) != expected_count
        ):
            raise ReportRebuildError(f"reviewed {role} path set changed")
        if any(Path(path).suffix not in SOURCE_FORMATS[role] for path in paths):
            raise ReportRebuildError(f"unsupported {role} source format")

    tracked_by_path = {f"docs/report/{entry.path}": entry for entry in tracked}
    selected: list[InventoryEntry] = []
    for role in MAINTAINED_ROLE_PATHS:
        for path in sorted(role_paths[role]):
            try:
                source = _regular_confined_file(repository, path, "maintained source")
                payload = source.read_bytes()
                text = payload.decode("utf-8")
                if "\x00" in text:
                    raise ReportRebuildError(f"maintained source contains NUL: {path}")
                if source.suffix == ".py":
                    ast.parse(text, filename=path)
            except (OSError, UnicodeError, SyntaxError, ReportOwnershipError) as error:
                raise ReportRebuildError(
                    f"maintained source format invalid: {path}"
                ) from error
            if payload != _head_blob(repository, path):
                raise ReportRebuildError(
                    f"maintained source differs from Git candidate: {path}"
                )
            entry = tracked_by_path.get(path)
            if (
                entry is None
                or entry.kind != "file"
                or entry.sha256 != sha256_bytes(payload)
                or entry.size != len(payload)
            ):
                raise ReportRebuildError(f"maintained source inventory differs: {path}")
            selected.append(entry)
    try:
        if repository_identity(repository, required=True) != expected_repository:
            raise ReportRebuildError("maintained source Git candidate changed")
    except ReproducibleReportError as error:
        raise ReportRebuildError("maintained source Git candidate changed") from error
    if len(selected) != sum(count for count, _ in MAINTAINED_ROLE_PATHS.values()):
        raise ReportRebuildError("maintained source coverage is incomplete")
    evidence: JsonObject = {
        "schema_version": "maintained-report-source-evidence.v1",
        "repository": expected_repository,
        "ownership_inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "roles": {
            role: {
                "path_count": len(role_paths[role]),
                "paths_sha256": canonical_json_sha256(sorted(role_paths[role])),
                "owners": role_owners[role],
            }
            for role in MAINTAINED_ROLE_PATHS
        },
        "inventory": inventory_json(sorted(selected, key=lambda entry: entry.path)),
    }
    return tuple(sorted(selected, key=lambda entry: entry.path)), evidence
