"""Stage compact external-source receipts and publish with atomic no-replace ownership."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import tempfile
import zipfile

from .....core.owned_tree import publish_new_output_tree
from ...quarantine import IntakeRefusal
from .contracts import (
    POSTURE,
    REVIEW_REQUIRED,
    SCHEMA,
    LocalHydeInventory,
    LocalInventoryLimits,
    checked_path,
    encode,
    implementation_identity,
    sha256,
)
from .inventory import collect_sources, source_snapshot, summary, unchanged


def prepare_local_hyde_inventory(
    source_root: Path,
    destination: Path,
    *,
    limits: LocalInventoryLimits | None = None,
) -> LocalHydeInventory:
    """Hash external native files, retain compact custody, and refuse scientific admission."""
    limits = LocalInventoryLimits() if limits is None else limits
    if not isinstance(limits, LocalInventoryLimits):
        raise IntakeRefusal("hyde_custody_limit_invalid", "typed limits required")
    source = checked_path(source_root)
    target = checked_path(destination)
    producer = implementation_identity()
    if source.is_symlink() or not source.is_dir():
        raise IntakeRefusal("hyde_source_root_invalid", str(source))
    if target.is_symlink() or target.exists():
        raise IntakeRefusal("hyde_custody_destination_exists", str(target))
    if target.resolve().is_relative_to(source.resolve()):
        raise IntakeRefusal("hyde_custody_destination_inside_source", str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.pending-", dir=target.parent))
    try:
        snapshot = source_snapshot(source, limits)
        members = collect_sources(source, snapshot, limits)
        files = members["files.json"]
        archives = members["archives.json"]
        assert isinstance(files, list) and isinstance(archives, list)
        inventory = {}
        total = 0
        for name, value in members.items():
            content = encode(value)
            total += len(content)
            if total > limits.maximum_retained_bytes:
                raise IntakeRefusal("hyde_custody_output_limit", str(total))
            (stage / name).write_bytes(content)
            inventory[name] = {"bytes": len(content), "sha256": sha256(content)}
        manifest = {
            "schema_version": SCHEMA,
            "producer": {
                "profile": "hyde-custody-python-source-v1",
                "files": producer,
                "files_sha256": sha256(encode(producer)),
                "attestation": "source_bytes_not_loaded_runtime",
            },
            **POSTURE,
            "review_required": list(REVIEW_REQUIRED),
            "files": inventory,
            "counts": summary(files, archives),
            "limits": asdict(limits),
            "dataset_inventory_sha256": sha256(
                encode([row for row in files if row["classification"] == "dataset"])
            ),
        }
        content = encode(manifest)
        (stage / "manifest.json").write_bytes(content)
        from .reading import read_local_hyde_inventory

        read_local_hyde_inventory(stage, expected_manifest_sha256=sha256(content))
        unchanged(source, snapshot, limits)
        checked_path(target)
        if implementation_identity() != producer:
            raise IntakeRefusal(
                "hyde_custody_producer_changed",
                "Producer source bytes changed during preparation",
            )
        publish_new_output_tree(final_output_root=target, staging_output_root=stage)
        return read_local_hyde_inventory(
            target, expected_manifest_sha256=sha256(content)
        )
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal(
            "hyde_local_preparation_failed",
            f"{type(exc).__name__}: {exc}; stage={stage}",
        ) from exc
