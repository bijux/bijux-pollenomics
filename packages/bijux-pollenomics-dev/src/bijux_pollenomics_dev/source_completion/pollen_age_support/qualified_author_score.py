"""Score an existing age-supported freeze against qualified author pollen bytes."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import os
from pathlib import Path
import runpy
import shutil
import tempfile

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
SOURCE_ID = "landclim/author-reference"
LOOKUP = "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"
FROZEN = ("predictions.json", "protocol.json", "sample-support.csv")
SCORED = ("report.json", "scores.csv")


def _sha(path: Path) -> str:
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
    *,
    replay: Path,
    replay_sha256: str,
    frozen: Path,
) -> None:
    """Call only the original scorer and expose its two owned result files."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("author age score descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or qualified.inputs.get(f"external/{SOURCE_ID}/{LOOKUP}")
        != qualified.directory / LOOKUP
    ):
        raise ValueError("author age score source coverage differs")
    source = _regular_path(repository / replay)
    if _sha(source) != replay_sha256:
        raise ValueError("author age score source implementation differs")
    frozen_paths = {name: _regular_path(repository / frozen / name) for name in FROZEN}
    frozen_hashes = {name: _sha(path) for name, path in frozen_paths.items()}
    before = producer_input_identity(qualified.inputs, repository)
    namespace = runpy.run_path(str(source), run_name="bijux_qualified_author_age_score")
    score = namespace.get("score")
    if (
        not callable(score)
        or getattr(getattr(score, "__code__", None), "co_filename", None) != str(source)
        or namespace.get("LOOKUP") != Path(LOOKUP)
    ):
        raise ValueError("author age score function or lookup differs")
    scorer: Callable[[Path, Path, Path], None] = score
    with tempfile.TemporaryDirectory(
        prefix=".qualified-author-age-", dir=destination.parent
    ) as staging:
        prepared = Path(staging) / "prepared"
        prepared.mkdir()
        for name, path in frozen_paths.items():
            shutil.copyfile(path, prepared / name)
        scorer(repository, prepared, qualified.directory)
        if {path.name for path in prepared.iterdir()} != {*FROZEN, *SCORED}:
            raise ValueError("author age score stage file population differs")
        for name in (*FROZEN, *SCORED):
            _regular_path(prepared / name)
        if any(_sha(prepared / name) != frozen_hashes[name] for name in FROZEN):
            raise ValueError("frozen author age predictions changed during scoring")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or after.inputs != qualified.inputs
            or producer_input_identity(after.inputs, repository) != before
            or _sha(source) != replay_sha256
            or any(
                _sha(path) != frozen_hashes[name] for name, path in frozen_paths.items()
            )
        ):
            raise ValueError("author age score inputs changed during scoring")
        for name in FROZEN:
            (prepared / name).unlink()
        require_absent_artifact_output(repository, destination)
        os.replace(prepared, destination)
