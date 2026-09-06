"""Journaled installation and verified rollback for SEAD surfaces."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict

from .contract import (
    RepositorySurfaceCandidate,
    file_sha256,
    surface_baseline,
)
from .validation import validate_repository_surface_candidate


def publish_repository_surface_candidate(
    candidate: RepositorySurfaceCandidate,
) -> str:
    """Publish all candidate paths with a journaled, verified rollback boundary."""
    candidate_hashes = validate_repository_surface_candidate(candidate)
    require_unchanged_baseline(candidate)
    if all(
        baseline.sha256 == candidate_hashes[baseline.relative_path]
        for baseline in candidate.baseline
    ):
        complete_transaction(candidate, state="unchanged", installed=[])
        return "unchanged"
    installed: list[str] = []
    try:
        for baseline in candidate.baseline:
            relative_path = baseline.relative_path
            target = candidate.data_root / relative_path
            source = candidate.candidate_data_root / relative_path
            recovery = candidate.recovery_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            recovery.parent.mkdir(parents=True, exist_ok=True)
            installed.append(str(relative_path))
            write_transaction_journal(
                candidate, state="publishing", installed=installed
            )
            if baseline.existed:
                os.replace(target, recovery)
            os.replace(source, target)
        for relative_path, expected_hash in candidate_hashes.items():
            if file_sha256(candidate.data_root / relative_path) != expected_hash:
                raise OSError(f"SEAD published surface hash differs: {relative_path}")
    except BaseException as error:
        rollback_transaction(candidate, installed=installed, error=error)
        raise
    state = (
        "replaced" if any(item.existed for item in candidate.baseline) else "created"
    )
    complete_transaction(candidate, state=state, installed=installed)
    return state


def abort_repository_surface_transaction(
    candidate: RepositorySurfaceCandidate,
    error: BaseException,
) -> None:
    """Retain a failed candidate and release its cooperative lock."""
    write_transaction_journal(
        candidate, state="generation_failed", installed=[], error=error
    )
    candidate.lock_path.unlink(missing_ok=True)


def rollback_transaction(
    candidate: RepositorySurfaceCandidate,
    *,
    installed: list[str],
    error: BaseException,
) -> None:
    for baseline in reversed(candidate.baseline):
        relative_path = baseline.relative_path
        target = candidate.data_root / relative_path
        source = candidate.candidate_data_root / relative_path
        recovery = candidate.recovery_root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        if baseline.existed and recovery.exists():
            if target.exists():
                os.replace(target, source)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(recovery, target)
        elif not baseline.existed and target.exists():
            os.replace(target, source)
    require_unchanged_baseline(candidate)
    write_transaction_journal(
        candidate, state="rolled_back", installed=installed, error=error
    )
    candidate.lock_path.unlink(missing_ok=True)


def complete_transaction(
    candidate: RepositorySurfaceCandidate,
    *,
    state: str,
    installed: list[str],
) -> None:
    write_transaction_journal(candidate, state=state, installed=installed)
    try:
        shutil.rmtree(candidate.transaction_root / "candidate", ignore_errors=False)
        shutil.rmtree(candidate.transaction_root / "recovery", ignore_errors=False)
    except OSError as error:
        write_transaction_journal(
            candidate,
            state=f"{state}_cleanup_pending",
            installed=installed,
            error=error,
        )
    finally:
        candidate.lock_path.unlink(missing_ok=True)


def require_unchanged_baseline(candidate: RepositorySurfaceCandidate) -> None:
    current = tuple(
        surface_baseline(candidate.data_root, item.relative_path)
        for item in candidate.baseline
    )
    if current != candidate.baseline:
        raise RuntimeError("SEAD repository-surface baseline changed during generation")


def write_transaction_journal(
    candidate: RepositorySurfaceCandidate,
    *,
    state: str,
    installed: list[str],
    error: BaseException | None = None,
) -> None:
    payload = {
        "schema_version": "sead-repository-surface-transaction.v1",
        "state": state,
        "surface_count": len(candidate.baseline),
        "installed": installed,
        "baseline": [
            {**asdict(item), "relative_path": str(item.relative_path)}
            for item in candidate.baseline
        ],
        "error": f"{type(error).__name__}: {error}" if error is not None else "",
    }
    path = candidate.transaction_root / "journal.json"
    staging = path.with_suffix(".json.staging")
    with staging.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(staging, path)
