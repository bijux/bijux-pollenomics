"""Run the original Nordic held-out pollen stages in one retained artifact tree."""

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
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/nordic_direct_pollen.py"
)
COUNTRIES = ("DK", "FI", "NO")
EXPECTED_PREDICTIONS = {"DK": 96, "FI": 1740, "NO": 4336}
PUBLISHED = {
    "RESULTS.md",
    "cohort.csv",
    "coverage.csv",
    "manifest.json",
    "predictions-DK.json",
    "predictions-FI.json",
    "predictions-NO.json",
    "predictions.csv",
    "scores.csv",
    "site-scores.csv",
    "training-sources.csv",
}
SCORE_FILES = {
    "cohort.csv",
    "coverage.csv",
    "predictions.csv",
    "scores.csv",
    "site-scores.csv",
    "training-sources.csv",
}
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
RELATIONAL = Path("data/neotoma/relational")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Nordic source path is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Nordic source path uses symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Nordic source path is not a real regular file")
    return path


def _real_dir(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("Nordic directory is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Nordic directory uses symlink")
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("Nordic directory is not real")
    return path


def _destination(repository: Path, output: Path) -> Path:
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve() != repository
    ):
        raise ValueError("repository must be a real absolute path")
    artifacts = _real_dir(repository / "artifacts", repository)
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("Nordic output must be real and absolute")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Nordic output ancestor uses symlink")
    else:
        raise ValueError("Nordic output is outside repository")
    if (
        output.exists()
        or output.resolve() == artifacts
        or not output.resolve().is_relative_to(artifacts)
    ):
        raise ValueError("absent artifact output required")
    return artifacts


def _json(path: Path, repository: Path) -> dict[str, Any]:
    value = json.loads(_real_file(path, repository).read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Nordic stage JSON is not an object")
    return value


def _exact_files(path: Path, names: set[str], repository: Path) -> None:
    _real_dir(path, repository)
    if {item.name for item in path.iterdir()} != names:
        raise ValueError("Nordic stage file population differs")
    for name in names:
        _real_file(path / name, repository)


def _source(repository: Path) -> str:
    path = _real_file(repository / SOURCE, repository)
    module = ".".join(
        SOURCE.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != path:
        raise ValueError("Nordic source module origin differs")
    return module


def _invoke(module: str, source: Path, args: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *args]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def _prepared(workdir: Path, repository: Path) -> None:
    _real_dir(workdir, repository)
    inputs = workdir / "inputs"
    _exact_files(
        inputs,
        {
            f"{kind}-{country}.json"
            for kind in ("training", "metadata")
            for country in COUNTRIES
        },
        repository,
    )
    manifest = _json(workdir / "input-manifest.json", repository)
    _real_file(workdir / "target-metadata.json", repository)
    if (
        manifest.get("runner_sha256") != _sha(repository / SOURCE)
        or manifest.get("target_outcomes_in_prediction_inputs") is not False
        or manifest.get("country_candidate_samples")
        != {"DK": 91, "FI": 1797, "NO": 3544}
        or manifest.get("age_bin_width_bp") != 500
    ):
        raise ValueError("Nordic prepared country/input identity differs")


def _predicted(workdir: Path, country: str, repository: Path) -> None:
    payload = _json(workdir / f"predictions-{country}.json", repository)
    rows = payload.get("predictions")
    if (
        payload.get("schema_version") != "nordic-direct-pollen-country-held-out.v1"
        or payload.get("country") != country
        or not isinstance(rows, list)
        or len(rows) != EXPECTED_PREDICTIONS[country]
        or any(
            row.get("country") != country
            or row.get("target_pollen_counts_read") is not False
            for row in rows
        )
    ):
        raise ValueError("Nordic held-out prediction identity differs")


def _published(output: Path, workdir: Path, repository: Path) -> dict[str, str]:
    _exact_files(output, PUBLISHED, repository)
    _exact_files(
        workdir / "inputs",
        {
            f"{kind}-{country}.json"
            for kind in ("training", "metadata")
            for country in COUNTRIES
        },
        repository,
    )
    for country in COUNTRIES:
        _predicted(workdir, country, repository)
    manifest = _json(output / "manifest.json", repository)
    if (
        manifest.get("schema_version") != "nordic-direct-pollen-results.v1"
        or manifest.get("prediction_counts") != EXPECTED_PREDICTIONS
        or manifest.get("scored_rows") != 6172
        or manifest.get("input_identity")
        != _json(workdir / "input-manifest.json", repository)
    ):
        raise ValueError("Nordic result manifest identity differs")
    hashes = {name: _sha(output / name) for name in PUBLISHED}
    mappings = {
        "scores_sha256": "scores.csv",
        "site_scores_sha256": "site-scores.csv",
        "coverage_sha256": "coverage.csv",
        "training_sources_sha256": "training-sources.csv",
        "prediction_table_sha256": "predictions.csv",
        "cohort_sha256": "cohort.csv",
        "results_sha256": "RESULTS.md",
    }
    if any(manifest.get(key) != hashes[name] for key, name in mappings.items()):
        raise ValueError("Nordic publication product hash differs")
    if manifest.get("prediction_sha256") != {
        country: hashes[f"predictions-{country}.json"] for country in COUNTRIES
    }:
        raise ValueError("Nordic country prediction hash differs")
    for name in SCORE_FILES:
        if hashes[name] != _sha(workdir / name):
            raise ValueError("Nordic published score copy differs from stage")
    return dict(sorted(hashes.items()))


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Retain the complete original preparation/prediction/scoring stages."""
    artifacts = _destination(repository, output)
    module = _source(repository)
    _real_dir(repository / RAW, repository)
    _real_dir(repository / RELATIONAL, repository)
    stage_id = hashlib.sha256(
        output.relative_to(artifacts).as_posix().encode()
    ).hexdigest()
    stage_root = (
        artifacts / "jobs/retained-pollen-studies/nordic-direct-pollen" / stage_id
    )
    if (
        stage_root.exists()
        or stage_root.is_symlink()
        or stage_root.resolve() != stage_root
    ):
        raise ValueError("Nordic complete stage must be absent and real")
    stage_root.mkdir(parents=True, exist_ok=False)
    workdir = stage_root / "workdir"
    source = repository / SOURCE
    _invoke(
        module,
        source,
        [
            "prepare",
            "--relational-root",
            str(repository / RELATIONAL),
            "--raw-root",
            str(repository / RAW),
            "--workdir",
            str(workdir),
        ],
    )
    _prepared(workdir, repository)
    for country in COUNTRIES:
        _invoke(
            module, source, ["predict", "--country", country, "--workdir", str(workdir)]
        )
        _predicted(workdir, country, repository)
    _invoke(
        module,
        source,
        [
            "score",
            "--relational-root",
            str(repository / RELATIONAL),
            "--workdir",
            str(workdir),
            "--publish-dir",
            str(output),
        ],
    )
    stage_expected = {
        "inputs",
        "input-manifest.json",
        "target-metadata.json",
        *(f"predictions-{country}.json" for country in COUNTRIES),
        *SCORE_FILES,
    }
    if {path.name for path in workdir.iterdir()} != stage_expected:
        raise ValueError("Nordic complete workdir population differs")
    hashes = _published(output, workdir, repository)
    receipt: dict[str, Any] = {
        "schema_version": "nordic-direct-retained-stage.v1",
        "complete_stage_path": stage_root.relative_to(repository).as_posix(),
        "published_sha256": hashes,
        "source_stages": ["prepare", "predict-DK", "predict-FI", "predict-NO", "score"],
        "interpretation": "previously exposed observed-pollen development only",
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and run the original Nordic held-out pollen stages in one retained artifact tree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
