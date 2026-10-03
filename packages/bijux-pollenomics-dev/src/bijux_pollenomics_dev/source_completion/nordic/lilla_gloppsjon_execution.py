"""Route retained Lilla Gloppsjön stages to exact artifact-only destinations."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import stat
import sys
from typing import Any

SOURCE_ROOT = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion"
)
STUDY = Path("docs/report/regions/nordic/lilla-gloppsjon-direct-pollen")
PREDICT_SOURCE = SOURCE_ROOT / "lilla_gloppsjon_direct_pollen.py"
SCORE_SOURCE = SOURCE_ROOT / "lilla_gloppsjon_direct_pollen_scoring.py"
INTERVAL_SOURCE = STUDY / "interval-support/replay.py"
FROZEN_FILES = {"freeze.json", "predictions.json"}
SCORED_FILES = {"coverage.csv", "report.json", "sample-counts.csv", "scores.csv"}
INTERVAL_FILES = {"coverage.csv", "report.json", "samples.csv", "scores.csv"}
SITE = "neotoma:site:3234"
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Lilla source path is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Lilla source path uses symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Lilla source path is not a real regular file")
    return path


def _real_dir(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Lilla directory is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Lilla directory uses symlink")
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Lilla directory is not real")
    return path


def _destination(repository: Path, output: Path) -> None:
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve() != repository
    ):
        raise ValueError("repository must be a real absolute path")
    artifacts = _real_dir(repository / "artifacts", repository)
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("Lilla output must be a real absolute path")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Lilla output ancestor uses symlink")
    else:
        raise ValueError("Lilla output is outside repository")
    if (
        output.exists()
        or output.resolve() == artifacts
        or not output.resolve().is_relative_to(artifacts)
    ):
        raise ValueError("absent repository artifact destination required")


def _module(repository: Path, source_relative: Path) -> str:
    source = _real_file(repository / source_relative, repository)
    module = ".".join(
        source_relative.relative_to(SOURCE_ROOT.parent.parent).with_suffix("").parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("Lilla producer module origin differs")
    return module


def _invoke(module: str, source: Path, args: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *args]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def _files(repository: Path, output: Path, expected: set[str]) -> None:
    _real_dir(output, repository)
    if {path.name for path in output.iterdir()} != expected:
        raise ValueError("Lilla stage output population differs")
    for name in expected:
        _real_file(output / name, repository)


def _json(path: Path, repository: Path) -> dict[str, Any]:
    value = json.loads(_real_file(path, repository).read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Lilla stage JSON must be an object")
    return value


def _prediction_grid(repository: Path, prediction_path: Path) -> None:
    """Require one target-free prediction for each declared bin and method."""
    protocol = _json(repository / STUDY / "protocol.json", repository)
    if (
        protocol.get("candidate_bin_ids") != list(range(23))
        or tuple(protocol.get("methods", ())) != METHODS
    ):
        raise ValueError("Lilla prediction protocol grid differs")
    payload = _json(prediction_path, repository)
    rows = payload.get("predictions")
    if not isinstance(rows, list) or len(rows) != 69 or payload.get("refusals") != []:
        raise ValueError("Lilla prediction row population differs")
    pairs: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Lilla prediction row must be an object")
        bin_id = row.get("bin_id")
        method = row.get("method")
        training = row.get("training_site_ids")
        if (
            type(bin_id) is not int
            or not isinstance(method, str)
            or row.get("site_id") != SITE
            or not isinstance(training, list)
            or any(not isinstance(site, str) for site in training)
            or SITE in training
        ):
            raise ValueError("Lilla prediction source identity differs")
        pairs.append((bin_id, method))
    expected = {(bin_id, method) for bin_id in range(23) for method in METHODS}
    if len(set(pairs)) != len(pairs) or set(pairs) != expected:
        raise ValueError("Lilla prediction bin-method grid differs")


def _retained_freeze(repository: Path) -> tuple[Path, str]:
    frozen = _real_dir(repository / STUDY / "frozen", repository)
    _files(repository, frozen, FROZEN_FILES)
    freeze = _json(frozen / "freeze.json", repository)
    predictions = _json(frozen / "predictions.json", repository)
    if (
        freeze.get("schema_version") != "lilla-gloppsjon-direct-pollen-freeze.v1"
        or freeze.get("target_site_id") != SITE
        or freeze.get("target_observations_used_for_prediction") is not False
        or freeze.get("prediction_rows") != 69
        or freeze.get("predicted_bins") != 23
        or freeze.get("refused_bins") != 0
        or freeze.get("predictions_sha256") != _sha(frozen / "predictions.json")
        or len(predictions.get("predictions", [])) != 69
        or predictions.get("refusals") != []
    ):
        raise ValueError("retained Lilla prediction freeze differs")
    _prediction_grid(repository, frozen / "predictions.json")
    return frozen, _sha(frozen / "freeze.json")


def predict_to_artifacts(repository: Path, output: Path) -> None:
    """Run only the original prediction stage with retained prepared inputs."""
    _destination(repository, output)
    prepared = _real_dir(repository / STUDY / "inputs", repository)
    _files(repository, prepared, {"input-manifest.json", "metadata.json"})
    protocol = _real_file(repository / STUDY / "protocol.json", repository)
    manifest = _json(prepared / "input-manifest.json", repository)
    if (
        manifest.get("protocol_sha256") != _sha(protocol)
        or manifest.get("metadata_sha256") != _sha(prepared / "metadata.json")
        or manifest.get("target_observations_used_for_prediction") is not False
    ):
        raise ValueError("retained Lilla prepared input differs")
    module = _module(repository, PREDICT_SOURCE)
    _invoke(
        module,
        repository / PREDICT_SOURCE,
        [
            "predict",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--output",
            str(output),
        ],
    )
    _files(repository, output, FROZEN_FILES)
    freeze = _json(output / "freeze.json", repository)
    if (
        freeze.get("schema_version") != "lilla-gloppsjon-direct-pollen-freeze.v1"
        or freeze.get("target_observations_used_for_prediction") is not False
        or freeze.get("target_site_id") != SITE
        or freeze.get("prediction_rows") != 69
        or freeze.get("predicted_bins") != 23
        or freeze.get("refused_bins") != 0
        or freeze.get("predictions_sha256") != _sha(output / "predictions.json")
    ):
        raise ValueError("Lilla prediction stage differs")
    _prediction_grid(repository, output / "predictions.json")


def score_to_artifacts(repository: Path, output: Path) -> None:
    """Score against the unchanged historical freeze and sealed target counts."""
    _destination(repository, output)
    prepared = _real_dir(repository / STUDY / "inputs", repository)
    _files(repository, prepared, {"input-manifest.json", "metadata.json"})
    frozen, freeze_sha = _retained_freeze(repository)
    module = _module(repository, SCORE_SOURCE)
    _invoke(
        module,
        repository / SCORE_SOURCE,
        [
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            freeze_sha,
            "--output",
            str(output),
        ],
    )
    _files(repository, output, SCORED_FILES)
    report = _json(output / "report.json", repository)
    if (
        report.get("candidate_bins") != 23
        or report.get("predicted_bins") != 23
        or report.get("scored_common_bins") != 23
        or report.get("refused_or_failed_bins") != 0
        or report.get("prediction_freeze_sha256") != freeze_sha
    ):
        raise ValueError("Lilla score denominator differs")


def interval_to_artifacts(repository: Path, output: Path) -> None:
    """Replay only original contained-age-support from retained source products."""
    _destination(repository, output)
    source = _real_file(repository / INTERVAL_SOURCE, repository)
    _retained_freeze(repository)
    scored = _real_dir(repository / STUDY / "scored", repository)
    _files(repository, scored, SCORED_FILES)
    original = sys.argv
    try:
        sys.argv = [
            str(source),
            "--repository",
            str(repository),
            "--output",
            str(output),
        ]
        runpy.run_path(str(source), run_name="__main__")
    finally:
        sys.argv = original
    _files(repository, output, INTERVAL_FILES)
    report = _json(output / "report.json", repository)
    if (
        report.get("candidate_bins") != 23
        or report.get("scored_common_bins") != 20
        or report.get("refused_or_failed_bins") != 3
        or report.get("prediction_freeze_sha256")
        != _sha(repository / STUDY / "frozen/freeze.json")
        or report.get("sample_statuses")
        != {"age_refused": 2, "contained": 42, "crosses_boundary": 42}
    ):
        raise ValueError("Lilla contained-age denominator differs")
