"""Rebuild the retained English buffered-pollen results from a qualified snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SOURCE_MANIFEST_SHA256 = (
    "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
)
FAMILY = Path("docs/report/pollen-reconstruction/author-buffered-pollen")
REPLAY_SHA256 = "f5d3461cb17ed39db6f4465b4219bc2a8954224b95796c682bcebda739b89634"
MANIFEST_SHA256 = "6ea5f219f9bc1d3878ef50ff831d3eb95f7d4d6293dd61ce34e6e5c442412026"
RUN = Path("docs/report/publication-replay/landclim-method-profile/reference")
RUN_INPUTS = (
    RUN / "report.json",
    RUN / "512/run-manifest.json",
    RUN / "562/run-manifest.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    repository: Path,
    source_root: Path,
    source_descriptor: Path,
    output: Path,
) -> None:
    """Run the original 51-output replay and retain its intermediate baseline."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if (
        destination.parent.name != "producer-output"
        or destination.name != "source-products"
    ):
        raise ValueError(
            "buffered-pollen output must use the configured owner directory"
        )
    if source_descriptor != DESCRIPTOR:
        raise ValueError("buffered-pollen source descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or _sha256(_regular_path(qualified.directory / "snapshot-manifest.json"))
        != SOURCE_MANIFEST_SHA256
    ):
        raise ValueError("buffered-pollen source identity differs")
    replay = _regular_path(repository / FAMILY / "replay.py")
    manifest = _regular_path(repository / FAMILY / "manifest.json")
    if _sha256(replay) != REPLAY_SHA256 or _sha256(manifest) != MANIFEST_SHA256:
        raise ValueError("buffered-pollen replay or manifest identity differs")
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    if (
        manifest_payload.get("private_source_manifest_sha256") != SOURCE_MANIFEST_SHA256
        or manifest_payload.get("producer_sha256", {}).get(
            replay.relative_to(repository).as_posix()
        )
        != REPLAY_SHA256
    ):
        raise ValueError("buffered-pollen manifest source pins differ")
    inputs = dict(qualified.inputs)
    inputs[(FAMILY / "manifest.json").as_posix()] = manifest
    inputs[(FAMILY / "replay.py").as_posix()] = replay
    for relative in RUN_INPUTS:
        inputs[relative.as_posix()] = _regular_path(repository / relative)
    before = producer_input_identity(inputs, repository)
    work = destination.parent / f"{destination.name}-work"
    retained_work = destination.parent.parent / "retained-work"
    if (
        work.exists()
        or work.is_symlink()
        or retained_work.exists()
        or retained_work.is_symlink()
    ):
        raise ValueError("buffered-pollen intermediate destination already exists")
    subprocess.run(
        [
            sys.executable,
            str(replay),
            "--source-root",
            str(qualified.directory),
            "--output",
            str(destination),
        ],
        cwd=repository,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
    )
    if producer_input_identity(inputs, repository) != before:
        raise ValueError("buffered-pollen source changed during replay")
    if not _regular_path(work / "local-site-mean/scores.csv").is_file():
        raise ValueError("buffered-pollen intermediate baseline is missing")
    for member in work.rglob("*"):
        if member.is_symlink() or not (member.is_file() or member.is_dir()):
            raise ValueError("buffered-pollen intermediate contains a non-real path")
    work.rename(retained_work)


def main() -> None:
    """Run a configured author-snapshot replay into a new artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.source_root, args.source_descriptor, args.output)


if __name__ == "__main__":
    main()
