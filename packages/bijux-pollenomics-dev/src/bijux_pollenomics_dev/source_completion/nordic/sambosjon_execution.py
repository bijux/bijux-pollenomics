"""Run fixed Sämbosjön source stages into confined, retained artifact trees."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import stat
import sys
from typing import Any

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sambosjon_direct_pollen.py"
)
PREPARED = Path("docs/report/regions/nordic/sambosjon-direct-pollen/inputs")
PROTOCOL = Path("docs/report/regions/nordic/sambosjon-direct-pollen/protocol.json")
SITE = "neotoma:site:3398"
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Sämbosjön source file is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Sämbosjön source file uses a symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Sämbosjön source file is not real")
    return path


def _real_dir(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Sämbosjön source directory is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Sämbosjön source directory uses a symlink")
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Sämbosjön source directory is not real")
    return path


def _destination(repository: Path, output: Path) -> tuple[Path, Path]:
    if repository.is_symlink() or repository.resolve(strict=True) != repository:
        raise ValueError("repository must be a real absolute path")
    artifacts = _real_dir(repository / "artifacts", repository)
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("Sämbosjön output must be an absolute real path")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Sämbosjön output ancestor uses a symlink")
    else:
        raise ValueError("Sämbosjön output is outside repository")
    destination = output.resolve()
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or output.exists()
    ):
        raise ValueError("absent repository artifact destination required")
    return artifacts, destination


def _source(repository: Path) -> str:
    path = _real_file(repository / SOURCE, repository)
    module = ".".join(
        SOURCE.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != path:
        raise ValueError("Sämbosjön producer module origin differs")
    return module


def _invoke(module: str, source: Path, arguments: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *arguments]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def prepare_to_artifacts(repository: Path, output: Path) -> None:
    """Run only the original preparation CLI at its absent artifact output."""
    _destination(repository, output)
    _real_file(repository / PROTOCOL, repository)
    module = _source(repository)
    _invoke(
        module,
        repository / SOURCE,
        ["prepare", "--repository", str(repository), "--output", str(output)],
    )


def _prepared(
    repository: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any], tuple[int, ...]]:
    prepared = _real_dir(repository / PREPARED, repository)
    expected = {"input-manifest.json", "metadata.json", "training.json.gz"}
    if {path.name for path in prepared.iterdir()} != expected:
        raise ValueError("Sämbosjön retained prepared population differs")
    files = {name: _real_file(prepared / name, repository) for name in expected}
    manifest = json.loads(files["input-manifest.json"].read_bytes())
    metadata = json.loads(files["metadata.json"].read_bytes())
    protocol_path = _real_file(repository / PROTOCOL, repository)
    if (
        manifest.get("protocol_sha256") != _sha(protocol_path)
        or manifest.get("training_sha256") != _sha(files["training.json.gz"])
        or manifest.get("metadata_sha256") != _sha(files["metadata.json"])
        or manifest.get("target_observation_profile_in_prepared_inputs") is not False
        or manifest.get("training_physical_sites") != 84
        or manifest.get("target_samples") != 111
        or manifest.get("target_candidate_bins") != 22
        or len(metadata.get("sites", [])) != 1
        or metadata["sites"][0].get("site_id") != SITE
        or len(metadata["sites"][0].get("candidate_bin_ids", [])) != 22
    ):
        raise ValueError("Sämbosjön prepared input identity differs")
    raw_bins = metadata["sites"][0]["candidate_bin_ids"]
    if (
        not isinstance(raw_bins, list)
        or any(
            not isinstance(value, str)
            or not value.isascii()
            or not value.isdecimal()
            or str(int(value)) != value
            for value in raw_bins
        )
        or len(set(raw_bins)) != len(raw_bins)
    ):
        raise ValueError("Sämbosjön candidate bin identities differ")
    candidate_bins = tuple(int(value) for value in raw_bins)
    protocol = json.loads(protocol_path.read_bytes())
    if (
        protocol.get("target_site_id") != SITE
        or tuple(protocol.get("methods", ())) != METHODS
        or protocol.get("pre_score_predictions_sha256") is None
    ):
        raise ValueError("Sämbosjön prediction protocol differs")
    return prepared, manifest, protocol, candidate_bins


def _complete_stage(
    stage: Path,
    repository: Path,
    manifest: dict[str, Any],
    protocol: dict[str, Any],
    candidate_bins: tuple[int, ...],
) -> dict[str, str]:
    _real_dir(stage, repository)
    if {path.name for path in stage.iterdir()} != {"predictions.json", "freeze.json"}:
        raise ValueError("Sämbosjön prediction stage population differs")
    prediction_path = _real_file(stage / "predictions.json", repository)
    freeze_path = _real_file(stage / "freeze.json", repository)
    prediction_sha = _sha(prediction_path)
    if prediction_sha != protocol["pre_score_predictions_sha256"]:
        raise ValueError("Sämbosjön fixed prediction oracle differs")
    frozen = json.loads(freeze_path.read_bytes())
    predictions = json.loads(prediction_path.read_bytes())
    rows = predictions.get("predictions")
    refusals = predictions.get("refusals")
    timestamp = datetime.fromisoformat(frozen["created_at_utc"])
    expected_pairs = {
        (bin_id, method) for bin_id in candidate_bins for method in METHODS
    }
    if (
        isinstance(rows, list)
        and len(rows) == 66
        and all(isinstance(row, dict) for row in rows)
    ):
        actual_pairs = [(row.get("bin_id"), row.get("method")) for row in rows]
        if (
            any(
                type(bin_id) is not int or not isinstance(method, str)
                for bin_id, method in actual_pairs
            )
            or len(set(actual_pairs)) != len(actual_pairs)
            or set(actual_pairs) != expected_pairs
        ):
            raise ValueError("Sämbosjön prediction bin-method grid differs")
    if (
        timestamp.tzinfo is None
        or frozen.get("schema_version") != "sambosjon-direct-pollen-freeze.v1"
        or frozen.get("protocol_sha256") != _sha(repository / PROTOCOL)
        or frozen.get("input_manifest_sha256")
        != _sha(repository / PREPARED / "input-manifest.json")
        or frozen.get("training_sha256") != manifest["training_sha256"]
        or frozen.get("metadata_sha256") != manifest["metadata_sha256"]
        or frozen.get("predictions_sha256") != prediction_sha
        or frozen.get("target_observations_used_for_prediction") is not False
        or frozen.get("target_site_id") != SITE
        or frozen.get("prediction_rows") != 66
        or frozen.get("refused_bins") != 0
        or not isinstance(rows, list)
        or len(rows) != 66
        or refusals != []
        or Counter(row["method"] for row in rows) != dict.fromkeys(METHODS, 22)
        or any(
            row.get("site_id") != SITE or SITE in row.get("training_site_ids", ())
            for row in rows
        )
    ):
        raise ValueError("Sämbosjön complete prediction freeze differs")
    return {"predictions.json": prediction_sha, "freeze.json": _sha(freeze_path)}


def predict_to_artifacts(repository: Path, output: Path) -> dict[str, Any]:
    """Retain the full live freeze stage; expose only its exact prediction bytes."""
    artifacts, destination = _destination(repository, output)
    prepared, manifest, protocol, candidate_bins = _prepared(repository)
    module = _source(repository)
    stage_id = hashlib.sha256(
        destination.relative_to(artifacts).as_posix().encode("utf-8")
    ).hexdigest()
    stage_root = artifacts / "jobs/retained-pollen-freezes/sambosjon" / stage_id
    if (
        stage_root.exists()
        or stage_root.is_symlink()
        or stage_root.resolve() != stage_root
    ):
        raise ValueError("Sämbosjön complete stage must be absent and real")
    stage_root.mkdir(parents=True, exist_ok=False)
    stage = stage_root / "complete-stage"
    _invoke(
        module,
        repository / SOURCE,
        [
            "predict",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--output",
            str(stage),
        ],
    )
    stage_hashes = _complete_stage(
        stage, repository, manifest, protocol, candidate_bins
    )
    destination.mkdir(parents=True, exist_ok=False)
    copied = destination / "predictions.json"
    shutil.copyfile(stage / "predictions.json", copied)
    if _sha(copied) != stage_hashes["predictions.json"]:
        raise ValueError("Sämbosjön exposed prediction bytes differ from stage")
    receipt: dict[str, Any] = {
        "schema_version": "sambosjon-retained-prediction-stage.v1",
        "complete_stage_path": stage.relative_to(repository).as_posix(),
        "complete_stage_sha256": stage_hashes,
        "owned_prediction_sha256": _sha(copied),
        "historical_freeze_overwritten": False,
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt
