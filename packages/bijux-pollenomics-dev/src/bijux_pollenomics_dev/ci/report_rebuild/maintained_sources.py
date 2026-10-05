"""Bind reviewed checked-in report documentation and code to the Git candidate."""

from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

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
from .scientific_captures.nordic_static_basin import (
    validated_nordic_static_basin_captures,
)
from .scientific_captures.swedish_parameter_transfer import (
    validated_swedish_parameter_transfer_captures,
)
from .scientific_captures.swedish_source_chronology import (
    validated_swedish_source_chronology_captures,
)
from .scientific_captures.swedish_static_basin import (
    validated_swedish_static_basin_captures,
)
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
        63,
        "0180b0dc0e74063546778f1d63acdfcccf13f476ac9c5f0048ccaeb19df6c56d",
    ),
    "maintained_editorial": (
        189,
        "c9e36f0a8262ddc7fbc883eb6ca42726b07ec284ba52be7540da7abf6f035c8b",
    ),
    "maintained_configuration": (
        14,
        "a81101b6cffc4ddc16e6691dc8a0eab0364b40e3787a316b4e7757d633298774",
    ),
}
SOURCE_FORMATS = {
    "maintained_code": frozenset({".py", ".R"}),
    "maintained_editorial": frozenset({".md"}),
    "maintained_configuration": frozenset({".json"}),
}


def _configuration_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportRebuildError(f"duplicate maintained configuration key: {key}")
        result[key] = value
    return result


def _finite_json(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite_json(child) for child in value.values())
    if isinstance(value, list):
        return all(_finite_json(child) for child in value)
    return True


def _configuration_constant(value: str) -> None:
    raise ReportRebuildError(f"nonfinite maintained configuration value: {value}")


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
                if role == "maintained_configuration":
                    configuration = json.loads(
                        text,
                        object_pairs_hook=_configuration_object,
                        parse_constant=_configuration_constant,
                    )
                    if not isinstance(configuration, dict) or not _finite_json(
                        configuration
                    ):
                        raise ReportRebuildError(
                            f"maintained configuration must be a finite object: {path}"
                        )
            except (
                OSError,
                SyntaxError,
                ValueError,
                RecursionError,
            ) as error:
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
    capture_entries, capture_evidence = validated_swedish_static_basin_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    parameter_entries, parameter_evidence = (
        validated_swedish_parameter_transfer_captures(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    chronology_entries, chronology_evidence = (
        validated_swedish_source_chronology_captures(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    nordic_entries, nordic_evidence = validated_nordic_static_basin_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    all_capture_entries = (
        capture_entries + parameter_entries + chronology_entries + nordic_entries
    )
    for entry in all_capture_entries:
        name = "docs/report/" + entry.path
        capture = _regular_confined_file(repository, name, "scientific capture")
        if capture.read_bytes() != _head_blob(repository, name):
            raise ReportRebuildError("scientific capture differs from Git candidate")
    selected.extend(all_capture_entries)
    try:
        if repository_identity(repository, required=True) != expected_repository:
            raise ReportRebuildError("maintained source Git candidate changed")
    except ReproducibleReportError as error:
        raise ReportRebuildError("maintained source Git candidate changed") from error
    if len(selected) != sum(count for count, _ in MAINTAINED_ROLE_PATHS.values()) + len(
        all_capture_entries
    ):
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
    if capture_entries:
        evidence["retained_scientific_captures"] = capture_evidence
    if parameter_entries:
        evidence["retained_parameter_transfer_captures"] = parameter_evidence
    if chronology_entries:
        evidence["retained_source_chronology_captures"] = chronology_evidence
    if nordic_entries:
        evidence["retained_nordic_static_basin_captures"] = nordic_evidence
    return tuple(sorted(selected, key=lambda entry: entry.path)), evidence
