"""Publish source chronology support without changing historical study decisions."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.models import (
    canonical_bytes,
    producer_identity,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    NeotomaEvidence,
    json_object,
    read_neotoma_evidence,
)
from bijux_pollenomics.collection.sources.neotoma.chronology.quality import (
    assess_neotoma_chronology_quality,
)
from bijux_pollenomics_dev.ci.report_rebuild import artifact_paths

RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
NORMALIZED = Path("data/neotoma/relational")
_SURFACES = (
    "samples",
    "age_claims",
    "chronologies",
    "chronology_controls",
    "conflicts",
)


def _implementation_identity() -> dict[str, Any]:
    return {
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "artifact_guard_sha256": hashlib.sha256(
            Path(artifact_paths.__file__).read_bytes()
        ).hexdigest(),
        "host": producer_identity(),
    }


def _build_report(repository: Path) -> tuple[dict[str, Any], NeotomaEvidence]:
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("real absolute repository root required")
    implementation = _implementation_identity()
    evidence = read_neotoma_evidence(repository / RAW, repository / NORMALIZED)
    manifest = evidence.manifest()
    metadata = {
        surface: [row.payload() for row in evidence.rows(surface)]
        for surface in _SURFACES
    }
    quality = assess_neotoma_chronology_quality(**metadata)
    report = {
        "schema_version": "neotoma-source-chronology-quality-report.v1",
        "scope": "all_retained_source_metadata_without_country_or_time_filter",
        "source_identity": {
            key: manifest[key]
            for key in (
                "source_family",
                "source_snapshot_id",
                "build_id",
                "materialization_sha256",
            )
        }
        | {"manifest_sha256": dict(evidence.normalized_files)["manifest.json"]},
        "source_authorities": {
            "raw": RAW.as_posix(),
            "normalized": NORMALIZED.as_posix(),
        },
        "source_input_records": evidence.input_records(),
        "implementation_identity": implementation,
        "source_profile_eligibility_changed": False,
        "source_chronology_quality": quality,
        "interpretation": (
            "Descriptive source support only. Every retained sample and age claim "
            "is accounted, including unavailable and refused context. No country, "
            "time-window or source-profile exclusion is applied. This report "
            "does not select a chronology, alter study cohorts, fit a model, "
            "recalibrate source dates or establish a physical core base, hiatus, "
            "chronological precision or ecological accuracy."
        ),
    }
    canonical_bytes(report)
    evidence.assert_unchanged()
    if _implementation_identity() != implementation:
        raise ValueError("chronology quality implementation changed during assessment")
    return report, evidence


def build_report(repository: Path) -> dict[str, Any]:
    """Bind every source support diagnostic to validated retained source identities."""
    report, _ = _build_report(repository)
    return report


def _regular_identity(path: Path) -> tuple[int, int] | None:
    try:
        identity = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(identity.st_mode):
        return None
    return identity.st_dev, identity.st_ino


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Verify published bytes; retain refused publication files for diagnosis.

    Success attests the destination inode and bytes at readback. It cannot make
    files immutable against subsequent writes by another filesystem user.
    """
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("real absolute repository root required")
    destination = artifact_paths.require_absent_artifact_output(repository, output)
    stage = artifact_paths.require_absent_artifact_output(
        repository, destination.with_name(destination.name + ".stage")
    )
    report, evidence = _build_report(repository)
    content = canonical_bytes(report)
    with stage.open("xb") as stream:
        created = os.fstat(stream.fileno())
        identity = created.st_dev, created.st_ino
        verified = False
        try:
            stream.write(content)
            stream.flush()
            readback = stage.read_bytes()
            if (
                _regular_identity(stage) != identity
                or readback != content
                or canonical_bytes(json_object(readback)) != content
            ):
                raise ValueError("chronology quality staged report readback differs")
            evidence.assert_unchanged()
            if _implementation_identity() != report["implementation_identity"]:
                raise ValueError(
                    "chronology quality implementation changed before publication"
                )
            artifact_paths.require_absent_artifact_output(repository, destination)
            os.link(stage, destination)
            with destination.open("rb") as published:
                published_identity = os.fstat(published.fileno())
                readback = published.read()
            if (
                (published_identity.st_dev, published_identity.st_ino) != identity
                or _regular_identity(destination) != identity
                or readback != content
            ):
                raise ValueError("chronology quality published report readback differs")
            verified = True
        finally:
            # The open descriptor keeps the created inode alive during cleanup.
            # Refusals never unlink paths; a replacement may belong to its writer.
            if verified and _regular_identity(stage) == identity:
                stage.unlink()
    return report


def main(argv: list[str] | None = None) -> int:
    """Write a reproducible current-source chronology report to an absent artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
