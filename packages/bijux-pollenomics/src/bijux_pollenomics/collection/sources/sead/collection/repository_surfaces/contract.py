"""Owned-path and baseline contract for SEAD repository surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile

SEAD_REPOSITORY_SURFACE_PATHS = tuple(
    Path(value)
    for value in (
        "sead/derived/sweden_archaeology_site_discovery.csv",
        "sead/derived/sweden_archaeology_site_discovery.geojson",
        "sead/derived/sweden_archaeology_site_discovery.json",
        "sead/derived/sweden_archaeology_site_discovery.md",
        "sead/normalized/chronology_claims.json",
        "sead/normalized/nordic_environmental_sites.csv",
        "sead/normalized/nordic_environmental_sites.geojson",
        "sead/normalized/nordic_temporal_evidence.csv",
        "sead/normalized/nordic_temporal_evidence.geojson",
        "sead/review/access_model.csv",
        "sead/review/access_model.json",
        "sead/review/access_model.md",
        "sead/review/evidence_legibility_review.csv",
        "sead/review/evidence_legibility_review.json",
        "sead/review/evidence_legibility_review.md",
        "sead/review/recovery_requirements.csv",
        "sead/review/recovery_requirements.json",
        "sead/review/recovery_requirements.md",
        "sead/review/scientific_classification_candidates.csv",
        "sead/review/scientific_classification_review.json",
        "sead/review/scientific_classification_review.md",
        "sead/review/temporal_review.csv",
        "sead/review/temporal_review.json",
        "sead/review/temporal_review.md",
    )
)


@dataclass(frozen=True)
class RepositorySurfaceBaseline:
    relative_path: Path
    existed: bool
    sha256: str | None
    byte_count: int | None


@dataclass(frozen=True)
class RepositorySurfaceCandidate:
    data_root: Path
    transaction_root: Path
    candidate_data_root: Path
    recovery_root: Path
    lock_path: Path
    baseline: tuple[RepositorySurfaceBaseline, ...]


def prepare_repository_surface_transaction(
    data_root: Path,
    *,
    artifacts_root: Path,
) -> RepositorySurfaceCandidate:
    """Lock the surface set and capture its exact pre-generation identity."""
    from .transaction import write_transaction_journal

    data_root = Path(data_root).resolve()
    artifacts_root = Path(artifacts_root).resolve()
    artifacts_root.mkdir(parents=True, exist_ok=True)
    if data_root.stat().st_dev != artifacts_root.stat().st_dev:
        raise ValueError("SEAD transaction artifacts and data must share a filesystem")
    lock_path = artifacts_root / ".repository-surfaces.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise RuntimeError(
            "another SEAD repository-surface transaction is active"
        ) from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"pid={os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())
        baseline = tuple(
            surface_baseline(data_root, relative_path)
            for relative_path in SEAD_REPOSITORY_SURFACE_PATHS
        )
        existing_count = sum(item.existed for item in baseline)
        if existing_count not in {0, len(SEAD_REPOSITORY_SURFACE_PATHS)}:
            raise ValueError("SEAD repository-surface baseline is partial")
        transaction_root = Path(
            tempfile.mkdtemp(prefix="transaction-", dir=artifacts_root)
        )
        candidate_data_root = transaction_root / "candidate" / "data"
        recovery_root = transaction_root / "recovery" / "data"
        candidate_data_root.mkdir(parents=True)
        recovery_root.mkdir(parents=True)
        transaction = RepositorySurfaceCandidate(
            data_root=data_root,
            transaction_root=transaction_root,
            candidate_data_root=candidate_data_root,
            recovery_root=recovery_root,
            lock_path=lock_path,
            baseline=baseline,
        )
        write_transaction_journal(transaction, state="prepared", installed=[])
        return transaction
    except BaseException:
        lock_path.unlink(missing_ok=True)
        raise


def surface_baseline(data_root: Path, relative_path: Path) -> RepositorySurfaceBaseline:
    path = data_root / relative_path
    if path.is_symlink():
        raise ValueError(f"SEAD repository surface is a symlink: {relative_path}")
    if not path.exists():
        return RepositorySurfaceBaseline(relative_path, False, None, None)
    if not path.is_file():
        raise ValueError(f"SEAD repository surface is not a file: {relative_path}")
    return RepositorySurfaceBaseline(
        relative_path=relative_path,
        existed=True,
        sha256=file_sha256(path),
        byte_count=path.stat().st_size,
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
