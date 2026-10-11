"""Route retained Nordic pollen scores through their original source CLIs."""

from __future__ import annotations

import gzip
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
PREPARED_ROOT = Path("docs/report/regions/nordic")
ROUTES = {
    ("nordic_author_target_pollen", "author-target-pollen"): ("DK", "FI", "NO"),
    ("swedish_author_target_pollen", "swedish-author-target-pollen"): ("SE",),
    ("swedish_lake_transfer", "swedish-lake-transfer"): ("SE",),
    ("swedish_neotoma_holdout", "swedish-neotoma-holdout"): ("SE",),
}
FROZEN = frozenset({"swedish-lake-transfer", "swedish-neotoma-holdout"})
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("retained score input is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained score input uses a symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("retained score input is not a real regular file")
    return path


def _directory(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("retained score directory is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained score directory uses a symlink")
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("retained score directory is not real")
    return path


def _exact_files(directory: Path, expected: set[str], repository: Path) -> None:
    _directory(directory, repository)
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError("retained score source-file population changed")
    for name in expected:
        _regular(directory / name, repository)


def _json(path: Path, repository: Path) -> dict[str, Any]:
    value = json.loads(_regular(path, repository).read_bytes())
    if not isinstance(value, dict):
        raise ValueError("retained score JSON is not an object")
    return value


def _prediction(path: Path, repository: Path) -> dict[str, Any]:
    value = json.loads(gzip.decompress(_regular(path, repository).read_bytes()))
    if not isinstance(value, dict):
        raise ValueError("retained prediction is not an object")
    return value


def score_to_artifacts(
    repository: Path, output: Path, source_relative: Path, prepared_relative: Path
) -> None:
    """Use one fixed source/prepared/prediction route and an absent artifact output."""
    if repository.is_symlink() or repository.resolve(strict=True) != repository:
        raise ValueError("repository must be a real absolute path")
    if (
        source_relative.is_absolute()
        or source_relative.parent != SOURCE_ROOT
        or prepared_relative.is_absolute()
        or prepared_relative.parent != PREPARED_ROOT
    ):
        raise ValueError("retained score source or cohort route differs")
    countries = ROUTES.get((source_relative.stem, prepared_relative.name))
    if countries is None:
        raise ValueError("retained score source and cohort do not match")
    source = _regular(repository / source_relative, repository)
    prepared = _directory(repository / prepared_relative, repository)
    artifacts = _directory(repository / "artifacts", repository)
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("retained score output must be an absolute real path")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained score output ancestor uses a symlink")
    else:
        raise ValueError("retained score output is outside repository")
    destination = output.resolve()
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or output.exists()
    ):
        raise ValueError("absent repository artifact destination required")

    manifest_path = prepared / "input-manifest.json"
    manifest = _json(manifest_path, repository)
    axis = manifest.get("axis")
    produced = manifest.get("produced_file_sha256")
    if (
        manifest.get("target_outcomes_in_prediction_inputs") is not False
        or not isinstance(axis, list)
        or len(axis) != 31
        or len(set(axis)) != 31
        or not isinstance(produced, dict)
    ):
        raise ValueError("retained score manifest axis or outcome seal differs")
    _directory(prepared / "inputs", repository)
    _exact_files(
        prepared / "predictions",
        {f"predictions-{country}.json.gz" for country in countries},
        repository,
    )
    _exact_files(
        prepared / "sealed-outcomes",
        {f"outcomes-{country}.json.gz" for country in countries},
        repository,
    )
    for country in countries:
        metadata = prepared / "inputs" / f"metadata-{country}.json.gz"
        outcome = prepared / "sealed-outcomes" / f"outcomes-{country}.json.gz"
        prediction = prepared / "predictions" / f"predictions-{country}.json.gz"
        for path in (metadata, outcome):
            relative = path.relative_to(prepared).as_posix()
            if _sha(_regular(path, repository)) != produced.get(relative):
                raise ValueError("retained score metadata or sealed outcome differs")
        payload = _prediction(prediction, repository)
        if (
            payload.get("country") != country
            or payload.get("axis") != axis
            or not isinstance(payload.get("predictions"), list)
            or not isinstance(payload.get("refusals"), list)
            or any(
                row.get("country") != country
                or row.get("target_pollen_counts_read") is not False
                for row in payload["predictions"]
            )
        ):
            raise ValueError("retained prediction identity or target seal differs")
        if prepared_relative.name in FROZEN:
            freeze = _json(prepared / "prediction-freeze.json", repository)
            protocol_path = prepared / "protocol.json"
            protocol = _json(protocol_path, repository)
            if (
                freeze.get("prediction_file")
                != prediction.relative_to(prepared).as_posix()
                or freeze.get("prediction_sha256") != _sha(prediction)
                or freeze.get("prepared_input_manifest_sha256") != _sha(manifest_path)
                or freeze.get("protocol_sha256") != _sha(protocol_path)
                or manifest.get("protocol_sha256") != _sha(protocol_path)
                or freeze.get("metadata_sha256", _sha(metadata)) != _sha(metadata)
                or freeze.get("training_sha256")
                != produced.get(f"inputs/training-{country}.json.gz")
                or freeze.get("target_pollen_counts_read_by_predictor") is not False
                or tuple(protocol.get("fixed_methods", ())) != METHODS
            ):
                raise ValueError("retained prediction freeze or protocol differs")

    module = ".".join(
        source_relative.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("retained score source module origin differs")
    original_argv = sys.argv
    try:
        sys.argv = [
            str(source),
            "score",
            "--prepared",
            str(prepared),
            "--predictions",
            str(prepared / "predictions"),
            "--output",
            str(destination),
        ]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original_argv
