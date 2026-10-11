"""Route two retained Swedish age/support studies through their original stages."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import stat
import sys
from typing import Any

SOURCE_ROOT = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion"
)
REPORT_ROOT = Path("docs/report/regions/nordic")
PARENT = REPORT_ROOT / "swedish-training-scope/prepared"
OUTCOME = (
    REPORT_ROOT / "swedish-author-target-pollen/sealed-outcomes/outcomes-SE.json.gz"
)
SITES = ("13338", "28869", "28872")
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
ROUTES = {
    ("swedish_chronology_block", "swedish-chronology-block"): {
        "freeze_schema": "swedish-chronology-block-freeze.v1",
        "preparation_schema": "swedish-chronology-block-preparation.v1",
        "prediction_schema": "swedish-chronology-block-predictions.v1",
        "score_rows": 162,
        "paired_score_rows": 162,
        "prediction_rows": 162,
        "refusals": 0,
    },
    ("swedish_support_sensitivity", "swedish-support-sensitivity"): {
        "freeze_schema": "swedish-support-sensitivity-freeze.v1",
        "preparation_schema": "swedish-support-sensitivity-preparation.v1",
        "prediction_schema": "swedish-support-sensitivity-predictions.v1",
        "score_rows": 1419,
        "paired_score_rows": 1257,
        "prediction_rows": 1419,
        "refusals": 13,
    },
}
SCORED_FILES = frozenset(
    {"coverage.csv", "paired-scores.csv", "report.json", "scores.csv"}
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("retained Swedish study source is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained Swedish study source uses a symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("retained Swedish study source is not a real regular file")
    return path


def _real_dir(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("retained Swedish study directory is outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("retained Swedish study directory uses a symlink")
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("retained Swedish study directory is not real")
    return path


def _exact_files(directory: Path, names: set[str], repository: Path) -> None:
    _real_dir(directory, repository)
    if {path.name for path in directory.iterdir()} != names:
        raise ValueError("retained Swedish study file population differs")
    for name in names:
        _real_file(directory / name, repository)


def _json(path: Path, repository: Path) -> dict[str, Any]:
    value = json.loads(_real_file(path, repository).read_bytes())
    if not isinstance(value, dict):
        raise ValueError("retained Swedish study JSON must be an object")
    return value


def _destination(repository: Path, output: Path) -> tuple[Path, Path]:
    if repository.is_symlink() or repository.resolve(strict=True) != repository:
        raise ValueError("repository must be a real absolute path")
    artifacts = _real_dir(repository / "artifacts", repository)
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("study output must be an absolute real path")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("study output ancestor uses a symlink")
    else:
        raise ValueError("study output is outside repository")
    destination = output.resolve()
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or output.exists()
    ):
        raise ValueError("absent repository artifact destination required")
    return artifacts, destination


def _source(repository: Path, source_relative: Path) -> str:
    source = _real_file(repository / source_relative, repository)
    module = ".".join(
        source_relative.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("retained Swedish study producer module origin differs")
    return module


def _invoke(module: str, source: Path, args: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *args]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def _parent_folds(repository: Path) -> list[dict[str, Any]]:
    parent = _real_dir(repository / PARENT, repository)
    receipt = _json(parent / "prepare.json", repository)
    folds = [row for row in receipt["folds"] if row["scope"] == "four_country"]
    if sorted(row["site_id"] for row in folds) != list(SITES):
        raise ValueError("retained Swedish study site set differs")
    for site_id in SITES:
        folder = _real_dir(parent / "four_country" / site_id, repository)
        _exact_files(
            folder / "inputs",
            {"metadata-SE.json.gz", "training-SE.json.gz"},
            repository,
        )
        manifest = _json(folder / "input-manifest.json", repository)
        produced = manifest.get("produced_file_sha256")
        if not isinstance(produced, dict) or set(produced) != {
            "inputs/metadata-SE.json.gz",
            "inputs/training-SE.json.gz",
        }:
            raise ValueError("retained Swedish fold input population changed")
        for relative, expected in produced.items():
            if _sha(_real_file(folder / relative, repository)) != expected:
                raise ValueError("retained Swedish fold input changed")
        fold = next(row for row in folds if row["site_id"] == site_id)
        if (
            _sha(folder / "input-manifest.json") != fold["input_manifest_sha256"]
            or manifest.get("target_outcomes_in_prediction_inputs") is not False
        ):
            raise ValueError("retained Swedish fold manifest changed")
    return folds


def _prepared(
    repository: Path, stage: Path, route: dict[str, Any], source_name: str
) -> dict[str, Any]:
    _exact_files(stage, {"prepare.json"}, repository)
    receipt = _json(stage / "prepare.json", repository)
    parent_path = repository / PARENT / "prepare.json"
    if (
        receipt.get("schema_version") != route["preparation_schema"]
        or receipt.get("source_prepare_sha256") != _sha(parent_path)
        or receipt.get("folds") != _parent_folds(repository)
        or receipt.get("age_bin_width_bp") != 500
        or receipt.get("sealed_outcome_sha256")
        != _json(parent_path, repository)["sealed_outcome_sha256"]
    ):
        raise ValueError("retained Swedish study preparation differs")
    if source_name == "swedish_chronology_block":
        baseline = _real_file(
            repository / REPORT_ROOT / "swedish-support-sensitivity/scores.csv",
            repository,
        )
        if (
            receipt.get("older_source_bin_offset") != 2
            or receipt.get("excluded_source_bin_offsets") != [-1, 0, 1]
            or receipt.get("methods") != list(METHODS)
            or receipt.get("baseline_scores_sha256") != _sha(baseline)
        ):
            raise ValueError("retained chronology-block separation differs")
    elif receipt.get("shift_bins") != [-1, 0, 1] or receipt.get("support_policies") != [
        "all",
        "nearest_five",
        "beyond_100_km",
    ]:
        raise ValueError("retained support-sensitivity design differs")
    return receipt


def _frozen(
    repository: Path,
    prepared: Path,
    frozen: Path,
    route: dict[str, Any],
    source_name: str,
) -> dict[str, str]:
    names = {"freeze.json", *(f"predictions-{site_id}.json.gz" for site_id in SITES)}
    _exact_files(frozen, names, repository)
    freeze = _json(frozen / "freeze.json", repository)
    if (
        freeze.get("schema_version") != route["freeze_schema"]
        or freeze.get("prepare_sha256") != _sha(prepared / "prepare.json")
        or [row.get("site_id") for row in freeze.get("products", [])] != list(SITES)
    ):
        raise ValueError("retained Swedish prediction freeze differs")
    hashes = {"freeze.json": _sha(frozen / "freeze.json")}
    prediction_rows = 0
    refusals = 0
    for product in freeze["products"]:
        site_id = product["site_id"]
        path = frozen / f"predictions-{site_id}.json.gz"
        if _sha(path) != product["prediction_sha256"]:
            raise ValueError("retained Swedish frozen product hash differs")
        payload = json.loads(gzip.decompress(path.read_bytes()))
        rows = payload.get("predictions")
        refusal_rows = payload.get("refusals")
        if (
            payload.get("schema_version") != route["prediction_schema"]
            or payload.get("site_id") != site_id
            or not isinstance(rows, list)
            or not isinstance(refusal_rows, list)
            or any(
                row.get("site_id") != site_id
                or row.get("target_pollen_counts_read") is not False
                or site_id in row.get("training_site_ids", ())
                for row in rows
            )
        ):
            raise ValueError("retained Swedish prediction target lineage differs")
        if source_name == "swedish_chronology_block":
            if any(
                row.get("source_bin_id") != row.get("target_bin_id", -99) + 2
                or row.get("excluded_source_bin_ids")
                != [row.get("target_bin_id", -99) + offset for offset in (-1, 0, 1)]
                for row in (*rows, *refusal_rows)
            ):
                raise ValueError("retained chronology-block source bin differs")
        elif any(
            row.get("shift_bins") not in (-1, 0, 1)
            or row.get("support_policy") not in ("all", "nearest_five", "beyond_100_km")
            or row.get("source_bin_id")
            != row.get("target_bin_id", -99) + row.get("shift_bins", -99)
            for row in (*rows, *refusal_rows)
        ):
            raise ValueError("retained Swedish support scenario differs")
        prediction_rows += len(rows)
        refusals += len(refusal_rows)
        hashes[path.name] = _sha(path)
    if prediction_rows != route["prediction_rows"] or refusals != route["refusals"]:
        raise ValueError("retained Swedish prediction/refusal denominator differs")
    return hashes


def _scored(
    repository: Path, stage: Path, route: dict[str, Any], source_name: str
) -> dict[str, str]:
    _exact_files(stage, set(SCORED_FILES), repository)
    report = _json(stage / "report.json", repository)
    if (
        report.get("score_rows") != route["score_rows"]
        or report.get("paired_score_rows") != route["paired_score_rows"]
        or (
            source_name == "swedish_chronology_block"
            and (
                report.get("attempted_bins"),
                report.get("scored_bins"),
                report.get("refused_bins"),
            )
            != (54, 54, 0)
        )
        or (
            source_name == "swedish_support_sensitivity"
            and (
                report.get("attempted_site_policy_bins"),
                report.get("predicted_site_policy_bins"),
                report.get("refused_site_policy_bins"),
            )
            != (486, 473, 13)
        )
    ):
        raise ValueError("retained Swedish score denominator differs")
    return {name: _sha(stage / name) for name in sorted(SCORED_FILES)}


def run_study(
    repository: Path, output: Path, source_relative: Path, report_relative: Path
) -> dict[str, Any]:
    """Retain all original stage products and expose their exact owned bytes."""
    artifacts, destination = _destination(repository, output)
    if (
        source_relative.is_absolute()
        or source_relative.parent != SOURCE_ROOT
        or report_relative.is_absolute()
        or report_relative.parent != REPORT_ROOT
    ):
        raise ValueError("retained Swedish study route differs")
    route = ROUTES.get((source_relative.stem, report_relative.name))
    if route is None:
        raise ValueError("retained Swedish source and report route do not match")
    _real_dir(repository / report_relative, repository)
    _parent_folds(repository)
    module = _source(repository, source_relative)
    stage_id = hashlib.sha256(
        destination.relative_to(artifacts).as_posix().encode("utf-8")
    ).hexdigest()
    stage_root = (
        artifacts
        / "jobs/retained-pollen-studies/swedish-age-support"
        / report_relative.name
        / stage_id
    )
    if (
        stage_root.exists()
        or stage_root.is_symlink()
        or stage_root.resolve() != stage_root
    ):
        raise ValueError("retained Swedish study stage must be absent and real")
    stage_root.mkdir(parents=True, exist_ok=False)
    prepared = stage_root / "prepared"
    frozen = stage_root / "frozen"
    scored = stage_root / "scored"
    source = repository / source_relative
    _invoke(
        module,
        source,
        ["prepare", "--repository", str(repository), "--output", str(prepared)],
    )
    _prepared(repository, prepared, route, source_relative.stem)
    _invoke(
        module,
        source,
        [
            "predict",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--output",
            str(frozen),
        ],
    )
    frozen_hashes = _frozen(repository, prepared, frozen, route, source_relative.stem)
    _invoke(
        module,
        source,
        [
            "score",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            frozen_hashes["freeze.json"],
            "--output",
            str(scored),
        ],
    )
    scored_hashes = _scored(repository, scored, route, source_relative.stem)
    stage_files = {
        "prepared/prepare.json": _sha(prepared / "prepare.json"),
        **{f"frozen/{name}": digest for name, digest in frozen_hashes.items()},
        **scored_hashes,
    }
    if len(stage_files) != 9:
        raise ValueError("retained Swedish complete stage file count differs")
    destination.mkdir(parents=True, exist_ok=False)
    for relative, digest in sorted(stage_files.items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source_file = (
            prepared / "prepare.json"
            if relative == "prepared/prepare.json"
            else frozen / relative.removeprefix("frozen/")
            if relative.startswith("frozen/")
            else scored / relative
        )
        shutil.copyfile(source_file, target)
        if _sha(target) != digest:
            raise ValueError("retained Swedish owned output differs from stage")
    receipt: dict[str, Any] = {
        "schema_version": "retained-swedish-age-support-study-stage.v1",
        "complete_stage_path": stage_root.relative_to(repository).as_posix(),
        "complete_stage_sha256": stage_files,
        "source_module": module,
        "source_stages": ["prepare", "predict", "score"],
        "interpretation": "previously exposed observed-pollen development only",
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt
