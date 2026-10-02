"""Check fixed scoring routes with fixture source CLIs; no score is computed."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    nordic_heldout_scores,
    swedish_author_scores,
    swedish_core_scores,
    swedish_lake_scores,
)
from bijux_pollenomics_dev.source_completion.nordic.score_execution import (
    score_to_artifacts,
)

ROUTES = (
    nordic_heldout_scores,
    swedish_author_scores,
    swedish_lake_scores,
    swedish_core_scores,
)


def _write_json(path: Path, value: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_gzip(path: Path, value: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(value).encode(), mtime=0))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_repository(tmp_path: Path, route: ModuleType) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = repository / route.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fake source; never executed\n", encoding="utf-8")
    prepared = repository / route.PREPARED
    countries = ("DK", "FI", "NO") if route is nordic_heldout_scores else ("SE",)
    axis = [f"taxon-{index}" for index in range(31)]
    produced: dict[str, str] = {}
    predictions: dict[str, str] = {}
    for country in countries:
        profiles: tuple[tuple[str, dict[str, object]], ...] = (
            ("inputs/metadata", {"country": country, "sites": []}),
            ("inputs/training", {"country": country}),
            ("sealed-outcomes/outcomes", {"country": country}),
        )
        for prefix, body in profiles:
            relative = f"{prefix}-{country}.json.gz"
            produced[relative] = _write_gzip(prepared / relative, body)
        relative = f"predictions/predictions-{country}.json.gz"
        predictions[country] = _write_gzip(
            prepared / relative,
            {
                "country": country,
                "axis": axis,
                "predictions": [
                    {"country": country, "target_pollen_counts_read": False}
                ],
                "refusals": [],
            },
        )
    manifest: dict[str, object] = {
        "axis": axis,
        "produced_file_sha256": produced,
        "target_outcomes_in_prediction_inputs": False,
    }
    if route in (swedish_lake_scores, swedish_core_scores):
        protocol_sha = _write_json(
            prepared / "protocol.json",
            {
                "fixed_methods": [
                    "training_mean",
                    "nearest_site",
                    "inverse_distance_squared",
                ]
            },
        )
        manifest["protocol_sha256"] = protocol_sha
    manifest_sha = _write_json(prepared / "input-manifest.json", manifest)
    if route in (swedish_lake_scores, swedish_core_scores):
        _write_json(
            prepared / "prediction-freeze.json",
            {
                "prediction_file": "predictions/predictions-SE.json.gz",
                "prediction_sha256": predictions["SE"],
                "prepared_input_manifest_sha256": manifest_sha,
                "protocol_sha256": manifest["protocol_sha256"],
                "training_sha256": produced["inputs/training-SE.json.gz"],
                "metadata_sha256": produced["inputs/metadata-SE.json.gz"],
                "target_pollen_counts_read_by_predictor": False,
            },
        )
    return repository


def _fake_source(
    monkeypatch: pytest.MonkeyPatch,
    repository: Path,
    route: ModuleType,
    calls: list[str],
) -> None:
    source = repository / route.SOURCE
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(source)),
    )

    def fake_run(module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        assert sys.argv == [
            str(source),
            "score",
            "--prepared",
            str(repository / route.PREPARED),
            "--predictions",
            str(repository / route.PREPARED / "predictions"),
            "--output",
            str(repository / "artifacts/source-products"),
        ]
        calls.append(module)
        destination = Path(sys.argv[-1])
        destination.mkdir()
        for name in (
            "coverage.csv",
            "report.json",
            "scores.csv",
            "site-scores.csv",
            "taxon-diagnostics.csv",
        ):
            (destination / name).write_bytes(b"fixture score output\n")

    monkeypatch.setattr(runpy, "run_module", fake_run)


@pytest.mark.parametrize("route", ROUTES)
def test_only_score_stage_and_fixed_source_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    repository = fixture_repository(tmp_path, route)
    calls: list[str] = []
    _fake_source(monkeypatch, repository, route, calls)
    old = sys.argv
    assert (
        route.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(repository / "artifacts/source-products"),
            ]
        )
        == 0
    )
    assert sys.argv is old
    assert calls == [
        str(route.SOURCE)
        .removeprefix("packages/bijux-pollenomics-dev/src/")
        .removesuffix(".py")
        .replace("/", ".")
    ]
    assert len(list((repository / "artifacts/source-products").iterdir())) == 5


def test_refuses_crossed_source_and_cohort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = swedish_author_scores
    repository = fixture_repository(tmp_path, route)
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError, match="do not match"):
        score_to_artifacts(
            repository,
            repository / "artifacts/source-products",
            swedish_lake_scores.SOURCE,
            route.PREPARED,
        )


@pytest.mark.parametrize(
    "mode",
    (
        "extra_prediction",
        "wrong_country",
        "changed_metadata",
        "changed_outcome",
        "target_read",
        "freeze_mismatch",
        "protocol_mismatch",
    ),
)
def test_refuses_crossed_or_unfrozen_inputs_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    route = swedish_lake_scores
    repository = fixture_repository(tmp_path, route)
    prepared = repository / route.PREPARED
    prediction = prepared / "predictions/predictions-SE.json.gz"
    if mode == "extra_prediction":
        (prediction.parent / "predictions-NO.json.gz").write_bytes(b"foreign")
    elif mode in ("wrong_country", "target_read"):
        payload = json.loads(gzip.decompress(prediction.read_bytes()))
        if mode == "wrong_country":
            payload["country"] = "NO"
        else:
            payload["predictions"][0]["target_pollen_counts_read"] = True
        _write_gzip(prediction, payload)
    elif mode == "changed_metadata":
        (prepared / "inputs/metadata-SE.json.gz").write_bytes(b"changed")
    elif mode == "changed_outcome":
        (prepared / "sealed-outcomes/outcomes-SE.json.gz").write_bytes(b"changed")
    elif mode == "freeze_mismatch":
        value = json.loads((prepared / "prediction-freeze.json").read_bytes())
        value["prediction_sha256"] = "0" * 64
        _write_json(prepared / "prediction-freeze.json", value)
    else:
        (prepared / "protocol.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        route.run(repository, repository / "artifacts/source-products")


@pytest.mark.parametrize(
    "mode", ("outside", "existing", "relative", "symlink", "source_origin")
)
def test_destination_and_module_origin_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    route = swedish_core_scores
    repository = fixture_repository(tmp_path, route)
    output = repository / "artifacts/source-products"
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "existing":
        output.mkdir()
    elif mode == "relative":
        output = Path("artifacts/source-products")
    elif mode == "symlink":
        output.symlink_to(tmp_path, target_is_directory=True)
    elif mode == "source_origin":
        monkeypatch.setattr(
            importlib.util,
            "find_spec",
            lambda module: SimpleNamespace(origin=str(repository / "foreign.py")),
        )
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        route.run(repository, output)


def test_source_refusal_restores_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = nordic_heldout_scores
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
    old = sys.argv
    with pytest.raises(RuntimeError, match="source refusal"):
        route.run(repository, repository / "artifacts/source-products")
    assert sys.argv is old
