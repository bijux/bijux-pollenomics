"""Check the fixed five-stage Nordic route with fake source writers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.nordic import nordic_direct_study as study


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def fixture_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    (repository / study.RAW).mkdir(parents=True)
    (repository / study.RELATIONAL).mkdir(parents=True)
    source = repository / study.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fake original source\n")
    return repository


def fake_source(
    argv: list[str], *, wrong_country: bool = False, extra: bool = False
) -> None:
    command = argv[1]
    if command == "prepare":
        workdir = Path(argv[argv.index("--workdir") + 1])
        workdir.mkdir(parents=True, exist_ok=False)
        inputs = workdir / "inputs"
        inputs.mkdir()
        for country in study.COUNTRIES:
            for kind in ("metadata", "training"):
                write_json(inputs / f"{kind}-{country}.json", {})
        write_json(workdir / "target-metadata.json", {})
        write_json(
            workdir / "input-manifest.json",
            {
                "runner_sha256": sha(Path(argv[0])),
                "target_outcomes_in_prediction_inputs": False,
                "country_candidate_samples": {"DK": 91, "FI": 1797, "NO": 3544},
                "age_bin_width_bp": 500,
            },
        )
    elif command == "predict":
        country = argv[argv.index("--country") + 1]
        workdir = Path(argv[argv.index("--workdir") + 1])
        rows = [
            {
                "country": "FI" if wrong_country else country,
                "target_pollen_counts_read": False,
            }
            for _ in range(study.EXPECTED_PREDICTIONS[country])
        ]
        write_json(
            workdir / f"predictions-{country}.json",
            {
                "schema_version": "nordic-direct-pollen-country-held-out.v1",
                "country": country,
                "predictions": rows,
            },
        )
    elif command == "score":
        workdir = Path(argv[argv.index("--workdir") + 1])
        output = Path(argv[argv.index("--publish-dir") + 1])
        output.mkdir(parents=True, exist_ok=False)
        for name in study.SCORE_FILES:
            (workdir / name).write_bytes(b"synthetic score fixture\n")
            (output / name).write_bytes((workdir / name).read_bytes())
        for country in study.COUNTRIES:
            (output / f"predictions-{country}.json").write_bytes(
                (workdir / f"predictions-{country}.json").read_bytes()
            )
        (output / "RESULTS.md").write_text("# Fixture\n")
        if extra:
            (output / "unexpected.txt").write_text("extra")
        write_json(
            output / "manifest.json",
            {
                "schema_version": "nordic-direct-pollen-results.v1",
                "prediction_counts": study.EXPECTED_PREDICTIONS,
                "scored_rows": 6172,
                "input_identity": json.loads(
                    (workdir / "input-manifest.json").read_bytes()
                ),
                "prediction_sha256": {
                    country: sha(output / f"predictions-{country}.json")
                    for country in study.COUNTRIES
                },
                "scores_sha256": sha(output / "scores.csv"),
                "site_scores_sha256": sha(output / "site-scores.csv"),
                "coverage_sha256": sha(output / "coverage.csv"),
                "training_sources_sha256": sha(output / "training-sources.csv"),
                "prediction_table_sha256": sha(output / "predictions.csv"),
                "cohort_sha256": sha(output / "cohort.csv"),
                "results_sha256": sha(output / "RESULTS.md"),
            },
        )
    else:
        pytest.fail("unexpected original source command")


def test_fixed_stage_order_and_complete_retained_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / study.SOURCE)),
    )
    seen: list[str] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert module == "bijux_pollenomics_dev.source_completion.nordic_direct_pollen"
        assert run_name == "__main__"
        seen.append(sys.argv[1])
        fake_source(sys.argv)

    monkeypatch.setattr(runpy, "run_module", fake_run)
    original = sys.argv
    output = repository / "artifacts/source-products"
    assert study.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is original
    assert seen == ["prepare", "predict", "predict", "predict", "score"]
    assert {path.name for path in output.iterdir()} == study.PUBLISHED
    roots = list(
        (
            repository / "artifacts/jobs/retained-pollen-studies/nordic-direct-pollen"
        ).iterdir()
    )
    assert len(roots) == 1
    workdir = roots[0] / "workdir"
    assert (workdir / "inputs").is_dir()
    assert {path.name for path in workdir.iterdir()} == {
        "inputs",
        "input-manifest.json",
        "target-metadata.json",
        "predictions-DK.json",
        "predictions-FI.json",
        "predictions-NO.json",
        *study.SCORE_FILES,
    }


def test_foreign_origin_and_symlinked_source_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    output = repository / "artifacts/source-products"
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin="/foreign/source.py"),
    )
    with pytest.raises(ValueError, match="origin"):
        study.main(["--repository", str(repository), "--output", str(output)])
    source = repository / study.SOURCE
    source.unlink()
    source.symlink_to(repository / study.RELATIONAL)
    with pytest.raises(ValueError, match="symlink"):
        study.main(["--repository", str(repository), "--output", str(output)])


@pytest.mark.parametrize("relative", ("outside", "artifacts/existing"))
def test_output_confinement_and_absence(tmp_path: Path, relative: str) -> None:
    repository = fixture_repository(tmp_path)
    output = (
        repository.parent / "outside"
        if relative == "outside"
        else repository / relative
    )
    if relative != "outside":
        output.mkdir()
    with pytest.raises(ValueError, match="outside repository|absent artifact"):
        study.main(["--repository", str(repository), "--output", str(output)])


@pytest.mark.parametrize("defect", ("crossed_country", "extra_output"))
def test_country_or_output_drift_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / study.SOURCE)),
    )

    def fake_run(module: str, *, run_name: str) -> None:
        fake_source(
            sys.argv,
            wrong_country=defect == "crossed_country" and sys.argv[1] == "predict",
            extra=defect == "extra_output" and sys.argv[1] == "score",
        )

    monkeypatch.setattr(runpy, "run_module", fake_run)
    original = sys.argv
    with pytest.raises(
        ValueError, match="prediction identity differs|file population differs"
    ):
        study.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(repository / "artifacts/source-products"),
            ]
        )
    assert sys.argv is original


def test_retained_prediction_origin_and_current_source_qualification() -> None:
    """Keep historical prediction origin separate from current source qualification."""
    repository = Path(__file__).resolve().parents[5]
    root = repository / "docs/report/regions/nordic/direct-pollen"
    report = json.loads((root / "manifest.json").read_bytes())
    correspondence = json.loads((root / "source-correspondence.json").read_bytes())
    assert (
        correspondence["schema_version"] == "nordic-retained-producer-correspondence.v1"
    )
    assert correspondence["status"] == (
        "qualified_source_preparation_and_retained_prediction_rescoring"
    )
    historical = correspondence["historical_prediction_producer"]
    current = correspondence["qualified_current_preparation_and_scoring_producer"]
    assert historical["path"] == current["path"] == study.SOURCE.as_posix()
    assert report["input_identity"]["runner_sha256"] == historical["sha256"]
    assert current["sha256"] == sha(repository / study.SOURCE)
    assert historical["sha256"] != current["sha256"]
    assert correspondence["new_prediction_or_fit_calls"] == 0
    assert correspondence["actual_stages"] == [
        "historical_prepare",
        "current_prepare",
        "current_score_with_unchanged_retained_predictions",
    ]
    assert (
        correspondence["preparation"][
            "historical_input_identity_equals_retained_publication"
        ]
        is True
    )
    assert (
        correspondence["preparation"]["byte_identical_training_and_metadata_products"]
        == 7
    )
    assert correspondence["execution"]["native_exit_code"] == 0
    retained = correspondence["retained_publication"]
    assert retained["manifest_sha256"] == sha(root / "manifest.json")
    assert retained["prediction_counts"] == report["prediction_counts"]
    assert retained["prediction_sha256"] == report["prediction_sha256"]
    assert retained["scored_rows"] == report["scored_rows"] == 6172
    for country, expected in report["prediction_sha256"].items():
        assert sha(root / f"predictions-{country}.json") == expected
    for name, expected in retained["matched_product_sha256"].items():
        raw = (root / name).read_bytes()
        if name == "RESULTS.md":
            from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
                load_routes,
                verified_authored_reader,
            )

            relative = (root / name).relative_to(repository).as_posix()
            raw = verified_authored_reader(raw, load_routes()[relative])
        assert hashlib.sha256(raw).hexdigest() == expected
