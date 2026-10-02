"""Invoke a retained-input prediction stage at an absent repository artifact directory."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import runpy
import sys

SOURCE_ROOT = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion"
)
PREPARED_ROOT = Path("docs/report/regions/nordic")
INPUT_FILES = (
    Path("input-manifest.json"),
    Path("inputs/metadata-SE.json.gz"),
    Path("inputs/training-SE.json.gz"),
)


def predict_to_artifacts(
    repository: Path, output: Path, source_relative: Path, prepared_relative: Path
) -> None:
    """Run only the existing predict CLI with exact source and input boundaries."""
    repository = repository.resolve(strict=True)
    source = repository / source_relative
    artifacts = repository / "artifacts"
    if (
        source_relative.is_absolute()
        or ".." in source_relative.parts
        or source_relative.parent != SOURCE_ROOT
        or source.suffix != ".py"
        or not source.is_file()
        or source.is_symlink()
        or source.resolve() != source
    ):
        raise ValueError("retained prediction source is not a real source module")
    module = ".".join(
        source_relative.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    if (
        artifacts.is_symlink()
        or not artifacts.is_dir()
        or artifacts.resolve() != artifacts
    ):
        raise ValueError("repository artifact root is not a real directory")
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("retained prediction output must be an absolute real path")
    destination = output.resolve()
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained prediction output ancestor may not be a symlink")
    else:
        raise ValueError("retained prediction output lies outside repository")
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("absent repository artifact directory required")
    prepared = repository / prepared_relative
    if (
        prepared_relative.is_absolute()
        or ".." in prepared_relative.parts
        or prepared_relative.parent != PREPARED_ROOT
        or not prepared.is_dir()
        or prepared.is_symlink()
        or prepared.resolve() != prepared
        or any(
            not (prepared / relative).is_file()
            or (prepared / relative).is_symlink()
            or (prepared / relative).resolve() != prepared / relative
            for relative in INPUT_FILES
        )
    ):
        raise ValueError("retained prediction prepared inputs are invalid")
    manifest = json.loads((prepared / "input-manifest.json").read_bytes())
    if (
        not isinstance(manifest, dict)
        or manifest.get("target_outcomes_in_prediction_inputs") is not False
        or len(manifest.get("axis", [])) != 31
    ):
        raise ValueError("retained prediction manifest does not seal target outcomes")
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("retained prediction module origin differs")
    original = sys.argv
    try:
        sys.argv = [
            str(source),
            "predict",
            "--prepared",
            str(prepared),
            "--output",
            str(destination),
        ]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original
