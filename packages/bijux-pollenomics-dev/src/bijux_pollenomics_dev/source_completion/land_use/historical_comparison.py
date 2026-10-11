"""Reproduce the retained Swedish land-use comparison from a pinned Git baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from bijux_pollenomics_dev.source_completion.sweden_land_use_replay import (
    OUTPUT_FILES,
    PRODUCT,
    SOURCE_FILES,
    compare_historical,
)

PACKET = Path(
    "data/landclim/retained-country-baselines/sweden-land-use/historical-baseline.json"
)
STAGES = Path("artifacts/jobs/sweden-land-use-historical-source-stages")
SOURCE_PATHS = (
    "data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno",
    "data/aadr/v66/ho/v66.HO.aadr.PUB.anno",
    "data/aadr/v66/release_manifest.json",
    "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
    "data/sead/normalized/nordic_temporal_evidence.geojson",
    "data/svar/review/lake_candidate_registry_review.json",
    "data/svar/review/sweden_lake_candidate_registry.geojson",
)
POLICY_ROOT = Path(
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/land_use"
)
POLICY_NAMES = (
    "__init__.py",
    "context.py",
    "inputs.py",
    "interpretation.py",
    "models.py",
    "outputs.py",
    "quality.py",
    "spatial.py",
    "synthesis.py",
    "targets.py",
    "temporal.py",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=30,
    ).stdout


def _regular(repository: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("historical source path must be repository-relative")
    path = repository / relative
    if (
        path.is_symlink()
        or not path.is_file()
        or any(
            (repository.joinpath(*relative.parts[:index])).is_symlink()
            for index in range(1, len(relative.parts))
        )
    ):
        raise ValueError(f"historical source file must be regular: {relative}")
    if not path.resolve(strict=True).is_relative_to(repository.resolve(strict=True)):
        raise ValueError("historical source file escapes repository")
    return path


def publish(repository: Path, output: Path) -> dict[str, object]:
    """Compare fixed prior Git bytes with the current tracked Swedish product."""
    repository = repository.resolve(strict=True)
    output = output.absolute()
    artifact_root = repository / "artifacts"
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(artifact_root)
    ):
        raise ValueError("historical comparison output must be absent under artifacts")
    if not output.parent.is_dir() or not output.parent.resolve().is_relative_to(
        artifact_root
    ):
        raise ValueError("historical comparison output parent must be confined")
    if any(
        parent.is_symlink()
        for parent in output.parents
        if parent.is_relative_to(artifact_root)
    ):
        raise ValueError("historical comparison output parent must be real")
    if _git(repository, "status", "--porcelain=v1", "--untracked-files=no"):
        raise ValueError("historical comparison requires clean tracked candidate bytes")
    if tuple(sorted(path.as_posix() for path in SOURCE_FILES)) != SOURCE_PATHS:
        raise ValueError("historical comparison direct source membership differs")
    policy_root = repository / POLICY_ROOT
    if (
        not policy_root.is_dir()
        or policy_root.is_symlink()
        or tuple(path.name for path in sorted(policy_root.glob("*.py"))) != POLICY_NAMES
    ):
        raise ValueError("historical comparison policy membership differs")
    for name in POLICY_NAMES:
        _regular(repository, POLICY_ROOT / name)
    packet = json.loads(_regular(repository, PACKET).read_bytes())
    baseline = packet["baseline_revision"]
    paths = tuple((PRODUCT / name).as_posix() for name in OUTPUT_FILES)
    if (
        packet["schema_version"] != "sweden-land-use-prior-product.v1"
        or not isinstance(baseline, str)
        or re.fullmatch(r"[0-9a-f]{40}", baseline) is None
        or set(packet["files"]) != set(paths)
        or _git(repository, "rev-parse", "--verify", f"{baseline}^{{commit}}")
        .decode()
        .strip()
        != baseline
        or _git(repository, "rev-parse", f"{baseline}^{{tree}}").decode().strip()
        != packet["baseline_tree"]
    ):
        raise ValueError("historical source packet identity differs")
    for relative in paths:
        old = _git(repository, "show", f"{baseline}:{relative}")
        row = packet["files"][relative]
        if (
            set(row) != {"sha256", "git_blob_oid", "bytes"}
            or _sha(old) != row["sha256"]
            or len(old) != row["bytes"]
            or _git(repository, "rev-parse", f"{baseline}:{relative}").decode().strip()
            != row["git_blob_oid"]
        ):
            raise ValueError(f"historical product Git blob differs: {relative}")
        current = _regular(repository, Path(relative)).read_bytes()
        if current != _git(repository, "show", f"HEAD:{relative}"):
            raise ValueError(f"current governed product differs from HEAD: {relative}")
    stages = repository / STAGES
    if (stages.exists() or stages.is_symlink()) and (
        not stages.is_dir()
        or stages.is_symlink()
        or not stages.resolve().is_relative_to(artifact_root)
    ):
        raise ValueError("historical comparison stages must be confined")
    if any(
        parent.is_symlink()
        for parent in stages.parents
        if parent.is_relative_to(artifact_root)
    ):
        raise ValueError("historical comparison stages must be real")
    # Distinct destinations share this ancestor; each hashed leaf stays exclusive.
    stages.mkdir(parents=True, exist_ok=True)
    if (
        not stages.is_dir()
        or stages.is_symlink()
        or not stages.resolve().is_relative_to(artifact_root)
    ):
        raise ValueError("historical comparison stages must remain confined")
    stage = stages / _sha(output.relative_to(artifact_root).as_posix().encode())
    if stage.exists() or stage.is_symlink():
        raise ValueError("historical comparison stage already exists")
    stage.mkdir()
    report = compare_historical(repository, baseline, stage)
    if report["baseline_revision"] != baseline:
        raise ValueError("historical comparison selected a different baseline")
    staged = stage / "historical-comparison.json"
    destination_part = output.with_name(output.name + ".part")
    if destination_part.exists() or destination_part.is_symlink():
        raise ValueError("historical comparison partial output already exists")
    stream = destination_part.open("xb")
    try:
        with stream:
            stream.write(staged.read_bytes())
        os.link(destination_part, output)
    finally:
        destination_part.unlink(missing_ok=True)
    return report


def main() -> None:
    """Run the fixed historical country comparison into one absent artifact file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = publish(arguments.repository, arguments.output)
    print(
        json.dumps(
            {
                "baseline_revision": result["baseline_revision"],
                "change_counts": result["change_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
