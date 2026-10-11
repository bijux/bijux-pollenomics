"""Test fixed Swedish study stage routing without running the real studies."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    study_execution as execution,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    swedish_chronology_study as chronology,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    swedish_support_study as support,
)

ROUTES = (chronology, support)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def fixture_repository(tmp_path: Path, route: ModuleType) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = repository / route.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fixture source; never executed\n")
    (repository / route.REPORT).mkdir(parents=True)
    parent = repository / execution.PARENT
    folds: list[dict[str, str]] = []
    for site_id in execution.SITES:
        folder = parent / "four_country" / site_id
        inputs = folder / "inputs"
        inputs.mkdir(parents=True)
        metadata = inputs / "metadata-SE.json.gz"
        training = inputs / "training-SE.json.gz"
        metadata.write_bytes(b"metadata")
        training.write_bytes(b"training")
        manifest = folder / "input-manifest.json"
        write_json(
            manifest,
            {
                "target_outcomes_in_prediction_inputs": False,
                "produced_file_sha256": {
                    "inputs/metadata-SE.json.gz": sha(metadata),
                    "inputs/training-SE.json.gz": sha(training),
                },
            },
        )
        folds.append(
            {
                "site_id": site_id,
                "scope": "four_country",
                "input_manifest_sha256": sha(manifest),
            }
        )
    outcome = repository / execution.OUTCOME
    outcome.parent.mkdir(parents=True)
    outcome.write_bytes(b"sealed outcomes")
    write_json(
        parent / "prepare.json",
        {"folds": folds, "sealed_outcome_sha256": sha(outcome)},
    )
    baseline = (
        repository / execution.REPORT_ROOT / "swedish-support-sensitivity/scores.csv"
    )
    baseline.parent.mkdir(parents=True, exist_ok=True)
    baseline.write_bytes(b"retained baseline scores")
    return repository


def fake_stage(repository: Path, route: ModuleType, argv: list[str]) -> None:
    source_name = route.SOURCE.stem
    spec = execution.ROUTES[(source_name, route.REPORT.name)]
    stage = argv[1]
    output = Path(argv[-1])
    output.mkdir(parents=True, exist_ok=False)
    parent = repository / execution.PARENT
    folds = json.loads((parent / "prepare.json").read_bytes())["folds"]
    if stage == "prepare":
        receipt: dict[str, Any] = {
            "schema_version": spec["preparation_schema"],
            "source_prepare_sha256": sha(parent / "prepare.json"),
            "sealed_outcome_sha256": sha(repository / execution.OUTCOME),
            "folds": folds,
            "age_bin_width_bp": 500,
        }
        if route is chronology:
            receipt.update(
                older_source_bin_offset=2,
                excluded_source_bin_offsets=[-1, 0, 1],
                methods=list(execution.METHODS),
                baseline_scores_sha256=sha(
                    repository
                    / execution.REPORT_ROOT
                    / "swedish-support-sensitivity/scores.csv"
                ),
            )
        else:
            receipt.update(
                shift_bins=[-1, 0, 1],
                support_policies=["all", "nearest_five", "beyond_100_km"],
            )
        write_json(output / "prepare.json", receipt)
    elif stage == "predict":
        products: list[dict[str, str]] = []
        prediction_total = spec["prediction_rows"]
        refusal_total = spec["refusals"]
        assert isinstance(prediction_total, int)
        assert isinstance(refusal_total, int)
        remaining_predictions = prediction_total
        remaining_refusals = refusal_total
        for index, site_id in enumerate(execution.SITES):
            count = (
                remaining_predictions
                if index == 2
                else remaining_predictions // (3 - index)
            )
            remaining_predictions -= count
            refused = remaining_refusals if index == 2 else 0
            remaining_refusals -= refused
            rows: list[dict[str, Any]] = []
            refusal_rows: list[dict[str, Any]] = []
            for number in range(count):
                target_bin = number // 3
                item: dict[str, Any] = {
                    "site_id": site_id,
                    "target_bin_id": target_bin,
                    "training_site_ids": ["other"],
                    "target_pollen_counts_read": False,
                }
                if route is chronology:
                    item.update(
                        source_bin_id=target_bin + 2,
                        excluded_source_bin_ids=[
                            target_bin - 1,
                            target_bin,
                            target_bin + 1,
                        ],
                    )
                else:
                    item.update(
                        source_bin_id=target_bin,
                        shift_bins=0,
                        support_policy="all",
                    )
                rows.append(item)
            for number in range(refused):
                item = {"site_id": site_id, "target_bin_id": 1000 + number}
                if route is chronology:
                    item.update(
                        source_bin_id=1002 + number,
                        excluded_source_bin_ids=[
                            999 + number,
                            1000 + number,
                            1001 + number,
                        ],
                    )
                else:
                    item.update(
                        source_bin_id=1000 + number,
                        shift_bins=0,
                        support_policy="all",
                    )
                refusal_rows.append(item)
            prediction = output / f"predictions-{site_id}.json.gz"
            prediction.write_bytes(
                gzip.compress(
                    json.dumps(
                        {
                            "schema_version": spec["prediction_schema"],
                            "site_id": site_id,
                            "predictions": rows,
                            "refusals": refusal_rows,
                        }
                    ).encode(),
                    mtime=0,
                )
            )
            products.append({"site_id": site_id, "prediction_sha256": sha(prediction)})
        write_json(
            output / "freeze.json",
            {
                "schema_version": spec["freeze_schema"],
                "prepare_sha256": sha(
                    Path(argv[argv.index("--prepared") + 1]) / "prepare.json"
                ),
                "products": products,
            },
        )
    elif stage == "score":
        assert argv[argv.index("--freeze-sha256") + 1] == sha(
            Path(argv[argv.index("--frozen") + 1]) / "freeze.json"
        )
        for name in ("coverage.csv", "paired-scores.csv", "scores.csv"):
            (output / name).write_bytes(b"fixture score output\n")
        report: dict[str, Any] = {
            "score_rows": spec["score_rows"],
            "paired_score_rows": spec["paired_score_rows"],
        }
        if route is chronology:
            report.update(attempted_bins=54, scored_bins=54, refused_bins=0)
        else:
            report.update(
                attempted_site_policy_bins=486,
                predicted_site_policy_bins=473,
                refused_site_policy_bins=13,
            )
        write_json(output / "report.json", report)
    else:
        pytest.fail("unexpected source stage")


@pytest.mark.parametrize("route", ROUTES)
def test_original_three_stages_and_exact_nine_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    repository = fixture_repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / route.SOURCE)),
    )
    seen: list[str] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        seen.append(sys.argv[1])
        fake_stage(repository, route, sys.argv)

    monkeypatch.setattr(runpy, "run_module", fake_run)
    old_argv = sys.argv
    output = repository / "artifacts/source-products"
    assert route.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is old_argv
    assert seen == ["prepare", "predict", "score"]
    owned = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    )
    assert owned == sorted(
        (
            "prepared/prepare.json",
            "frozen/freeze.json",
            *(f"frozen/predictions-{site}.json.gz" for site in execution.SITES),
            "coverage.csv",
            "paired-scores.csv",
            "report.json",
            "scores.csv",
        )
    )
    stage = next(
        (
            repository
            / "artifacts/jobs/retained-pollen-studies/swedish-age-support"
            / route.REPORT.name
        ).iterdir()
    )
    for relative in owned:
        source = (
            stage / relative
            if relative.startswith(("prepared/", "frozen/"))
            else stage / "scored" / relative
        )
        assert sha(source) == sha(output / relative)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "mode", ("outside", "existing", "relative", "symlink", "crossed", "origin")
)
def test_refuses_unsafe_or_crossed_route_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType, mode: str
) -> None:
    repository = fixture_repository(tmp_path, route)
    output = repository / "artifacts/source-products"
    source = route.SOURCE
    report = route.REPORT
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "existing":
        output.mkdir()
    elif mode == "relative":
        output = Path("artifacts/source-products")
    elif mode == "symlink":
        output.symlink_to(tmp_path, target_is_directory=True)
    elif mode == "crossed":
        report = support.REPORT if route is chronology else chronology.REPORT
    elif mode == "origin":
        monkeypatch.setattr(
            importlib.util,
            "find_spec",
            lambda module: SimpleNamespace(origin=str(repository / "foreign.py")),
        )
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        execution.run_study(repository, output, source, report)


@pytest.mark.parametrize("route", ROUTES)
def test_refuses_changed_parent_fold_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    repository = fixture_repository(tmp_path, route)
    manifest = repository / execution.PARENT / "four_country/13338/input-manifest.json"
    manifest.write_text("{}")
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        route.run(repository, repository / "artifacts/source-products")


@pytest.mark.parametrize("route", ROUTES)
def test_source_refusal_restores_argv_and_retains_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    repository = fixture_repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / route.SOURCE)),
    )
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("source refusal")),
    )
    old_argv = sys.argv
    output = repository / "artifacts/source-products"
    with pytest.raises(RuntimeError, match="source refusal"):
        route.run(repository, output)
    assert sys.argv is old_argv and not output.exists()
    stage_root = (
        repository
        / "artifacts/jobs/retained-pollen-studies/swedish-age-support"
        / route.REPORT.name
    )
    assert len(list(stage_root.iterdir())) == 1
