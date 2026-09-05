from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import os
from pathlib import Path

from .model import ACQUISITION_MANIFEST_SCHEMA_VERSION, SeadTableAcquisition
from .serialization import canonical_bytes, payload_bytes
from .validation import safe_output_root, validate_table_name


def materialize_sead_acquisition(
    output_root: Path,
    *,
    acquisitions: Sequence[SeadTableAcquisition],
    required_tables: Sequence[str],
    country_reconciliation: Mapping[str, object],
    join_reconciliations: Sequence[Mapping[str, object]],
) -> Path:
    """Atomically persist payloads, receipts, reconciliations, and a digest manifest."""
    root = safe_output_root(output_root)
    by_table = _validated_acquisitions(acquisitions, required_tables)
    missing, incomplete, failed_joins, country_status, status = _release_status(
        by_table,
        required_tables=required_tables,
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )
    files = _acquisition_files(
        by_table,
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )
    manifest = {
        "schema_version": ACQUISITION_MANIFEST_SCHEMA_VERSION,
        "status": status,
        "required_tables": sorted(set(required_tables)),
        "missing_required_tables": missing,
        "incomplete_required_tables": incomplete,
        "failed_join_edges": failed_joins,
        "country_reconciliation_status": country_status,
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_count": len(content),
            }
            for path, content in sorted(files.items())
        ],
    }
    files["manifest.json"] = canonical_bytes(manifest)
    publish_directory(root, files)
    return root / "manifest.json"


def _validated_acquisitions(
    acquisitions: Sequence[SeadTableAcquisition], required_tables: Sequence[str]
) -> dict[str, SeadTableAcquisition]:
    for item in acquisitions:
        validate_table_name(item.table)
    for table in required_tables:
        validate_table_name(table)
    by_table = {item.table: item for item in acquisitions}
    if len(by_table) != len(acquisitions):
        raise ValueError("Duplicate SEAD table acquisition")
    return by_table


def _release_status(
    by_table: Mapping[str, SeadTableAcquisition],
    *,
    required_tables: Sequence[str],
    country_reconciliation: Mapping[str, object],
    join_reconciliations: Sequence[Mapping[str, object]],
) -> tuple[list[str], list[str], list[str], str, str]:
    missing = sorted(set(required_tables) - set(by_table))
    incomplete = sorted(
        table
        for table in required_tables
        if table in by_table and by_table[table].receipt.get("status") != "complete"
    )
    failed_joins = sorted(
        str(item.get("edge", "unknown"))
        for item in join_reconciliations
        if item.get("status") != "complete"
    )
    country_status = (
        "complete" if country_reconciliation.get("reconciles") is True else "failed"
    )
    status = (
        "complete"
        if not missing
        and not incomplete
        and not failed_joins
        and country_status == "complete"
        else "failed"
    )
    return missing, incomplete, failed_joins, country_status, status


def _acquisition_files(
    by_table: Mapping[str, SeadTableAcquisition],
    *,
    country_reconciliation: Mapping[str, object],
    join_reconciliations: Sequence[Mapping[str, object]],
) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for table, acquisition in sorted(by_table.items()):
        payload = payload_bytes(table, acquisition.rows)
        if acquisition.receipt.get("table") != table:
            raise ValueError(f"SEAD receipt table mismatch: {table}")
        if acquisition.receipt.get("row_count") != len(acquisition.rows):
            raise ValueError(f"SEAD receipt row count mismatch: {table}")
        if (
            acquisition.receipt.get("content_sha256")
            != hashlib.sha256(payload).hexdigest()
        ):
            raise ValueError(f"SEAD receipt content checksum mismatch: {table}")
        files[f"payloads/{table}.json"] = payload
        files[f"receipts/{table}.json"] = canonical_bytes(acquisition.receipt)
    files["reconciliation/countries.json"] = canonical_bytes(country_reconciliation)
    files["reconciliation/joins.json"] = canonical_bytes(
        {
            "schema_version": "sead-join-reconciliations.v1",
            "edges": list(join_reconciliations),
        }
    )
    return files


def publish_directory(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        _accept_existing_directory(root, files)
        return
    staging = root.with_name(f".{root.name}.staging-{os.getpid()}")
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"SEAD acquisition staging collision: {staging}")
    staging.mkdir()
    try:
        for relative_path, content in files.items():
            destination = staging / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        os.replace(staging, root)
    except Exception:
        _remove_staging_directory(staging)
        raise


def _accept_existing_directory(root: Path, files: Mapping[str, bytes]) -> None:
    if not root.is_dir() or root.is_symlink():
        raise FileExistsError(f"Unsafe existing SEAD acquisition output: {root}")
    existing = {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    if existing != dict(files):
        raise FileExistsError(f"Non-identical SEAD acquisition output exists: {root}")


def _remove_staging_directory(staging: Path) -> None:
    if not staging.exists():
        return
    for path in sorted(staging.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    staging.rmdir()
