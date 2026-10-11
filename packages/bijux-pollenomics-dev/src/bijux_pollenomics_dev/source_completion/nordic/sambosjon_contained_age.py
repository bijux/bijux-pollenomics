"""Route retained Sämbosjön contained-age support through its original CLI."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import stat
import sys
from typing import Any

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/sambosjon.py"
)
STUDY = Path("docs/report/regions/nordic/sambosjon-direct-pollen")
OUTPUTS = {"coverage.csv", "report.json", "samples.csv", "scores.csv"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Sämbosjön input is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Sämbosjön input uses symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Sämbosjön input is not a real regular file")
    return path


def _destination(repository: Path, output: Path) -> None:
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve() != repository
    ):
        raise ValueError("repository must be a real absolute path")
    artifacts = repository / "artifacts"
    if artifacts.is_symlink() or not stat.S_ISDIR(artifacts.lstat().st_mode):
        raise ValueError("repository artifacts directory is not real")
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("Sämbosjön output must be real and absolute")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Sämbosjön output ancestor uses symlink")
    else:
        raise ValueError("Sämbosjön output is outside repository")
    if (
        output.exists()
        or output.resolve() == artifacts
        or not output.resolve().is_relative_to(artifacts)
    ):
        raise ValueError("absent artifact output required")


def run(repository: Path, output: Path) -> None:
    """Call only the source-bound, no-refit contained-age replay."""
    _destination(repository, output)
    source = _real_file(repository / SOURCE, repository)
    module = ".".join(
        SOURCE.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("Sämbosjön source module origin differs")
    for relative in (
        "protocol.json",
        "inputs/input-manifest.json",
        "inputs/metadata.json",
        "inputs/training.json.gz",
        "frozen/freeze.json",
        "frozen/predictions.json",
        "coverage.csv",
        "report.json",
        "scores.csv",
        "age-bounds/report.json",
        "age-bounds/samples.csv",
    ):
        _real_file(repository / STUDY / relative, repository)
    original = sys.argv
    try:
        sys.argv = [
            str(source),
            "--repository",
            str(repository),
            "--output",
            str(output),
        ]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original
    if {path.name for path in output.iterdir()} != OUTPUTS:
        raise ValueError("Sämbosjön contained-age output population differs")
    for name in OUTPUTS:
        _real_file(output / name, repository)
    report: dict[str, Any] = json.loads((output / "report.json").read_bytes())
    if (
        report.get("schema_version") != "sambosjon-interval-support.v1"
        or report.get("sample_statuses") != {"contained": 53, "crosses_boundary": 58}
        or report.get("candidate_bins") != 22
        or report.get("scored_common_bins") != 21
        or report.get("refused_or_failed_bins") != 1
        or report.get("attempted_method_bin_scores") != 66
        or report.get("input_sha256", {}).get("frozen/freeze.json")
        != _sha(repository / STUDY / "frozen/freeze.json")
    ):
        raise ValueError("Sämbosjön contained-age denominator differs")


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and route retained Sämbosjön contained-age support through its original CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
