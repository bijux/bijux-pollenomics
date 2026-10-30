"""Two fixed training fits retain source exclusions, old failures and new refusals."""

from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    fit_resolution as study,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    inputs,
    producer,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.comparison import (
    CSV_FIELDS,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.inputs import (
    RADII,
    SITES,
    TAXA,
    NativeSource,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood import (
    multisite_likelihood as engine,
)

REPOSITORY = Path(__file__).resolve().parents[6]


@pytest.fixture
def native() -> NativeSource:
    counts = dict.fromkeys(SITES, (135, 135, 135, 135, 135))
    counts[SITES[0]] = (137, 135, 135, 135, 135)
    areas = {
        (site, radius): (1.0, 2.0, 3.0, 4.0, 5.0)
        if radius == 200
        else (5.0, 4.0, 3.0, 2.0, 1.0)
        for site in SITES
        for radius in study.RADII
    }
    return NativeSource(counts, areas, {}, {})


def old_body() -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for radius in RADII:
        for site in SITES:
            row = dict.fromkeys(CSV_FIELDS, "")
            row.update(radius_label_m=str(radius), heldout_site=site)
            if site == study.HELDOUT and radius in study.RADII:
                row.update(
                    heldout_group=site,
                    fit_id=f"{radius}:{site}",
                    training_sites="|".join(study.TRAINING),
                    training_grains="6077",
                    fit_status="not_converged",
                    fit_stop_reason="step_limit",
                    fit_steps="200",
                    empirical_status="fit_not_converged",
                )
            writer.writerow(row)
    return stream.getvalue().encode()


def historical() -> dict[int, dict[str, object]]:
    return study.historical_fits(old_body())


def test_exact_two_training_calls_preserve_options_and_analytic_reduction(
    native: NativeSource,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fit = engine.fit_multisite_likelihood
    calls = []

    def observed(counts: Any, areas: Any, **options: Any) -> Any:
        calls.append((counts.copy(), areas.copy(), options))
        return fit(counts, areas, **options)

    monkeypatch.setattr(engine, "fit_multisite_likelihood", observed)
    results = study.evaluate(native, historical())
    assert len(calls) == len(results) == 2
    total_counts = np.array([native.counts[site] for site in study.TRAINING]).sum(
        axis=0
    )
    expected = total_counts / total_counts.sum()
    for radius, result, (counts, areas, options) in zip(
        study.RADII, results, calls, strict=True
    ):
        assert result["radius_label_m"] == radius and result["status"] == "converged"
        np.testing.assert_array_equal(
            counts, [native.counts[site] for site in study.TRAINING]
        )
        np.testing.assert_array_equal(
            areas, [native.areas[(site, radius)] for site in study.TRAINING]
        )
        assert options["score_tolerance"] == 1e-12
        assert options["relative_count_tolerance"] == 1e-10
        assert options["max_steps"] == 200
        np.testing.assert_array_equal(
            options["taxon_measured"], np.ones((9, 5), dtype=bool)
        )
        assert isinstance(result["training_probabilities"], list)
        assert isinstance(result["response_multipliers"], tuple)
        np.testing.assert_allclose(
            result["training_probabilities"],
            np.tile(expected, (9, 1)),
            rtol=0,
            atol=2e-15,
        )
        weights = expected / areas[0]
        np.testing.assert_allclose(
            result["response_multipliers"], weights / weights[-1], rtol=2e-14
        )
        assert isinstance(result["response_multipliers"], tuple)
        assert result["response_multipliers"][-1] == 1
        assert result["mean_negative_log_likelihood"] == pytest.approx(
            -np.sum(expected * np.log(expected)), abs=2e-15
        )
        assert not any("heldout" in key for key in result)


def test_heldout_counts_and_unselected_radii_cannot_change_training(
    native: NativeSource,
) -> None:
    before = study.evaluate(native, historical())
    counts = dict(native.counts, Namibia_T7=(99999, 99999, 99999, 99999, 99999))
    areas = {
        key: value for key, value in native.areas.items() if key[0] != study.HELDOUT
    }
    assert (
        study.evaluate(replace(native, counts=counts, areas=areas), historical())
        == before
    )
    assert "Namibia_T4" in study.TRAINING and "Namibia_T5" in study.TRAINING


@pytest.mark.parametrize("status", ["not_converged", "refused"])
def test_failed_fits_are_retained_without_success_looking_outputs(
    native: NativeSource,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    if status == "not_converged":
        fit = engine.fit_multisite_likelihood(
            [native.counts[s] for s in study.TRAINING],
            [native.areas[(s, 200)] for s in study.TRAINING],
            taxon_measured=np.ones((9, 5), dtype=bool),
        )
        value = replace(
            fit,
            converged=False,
            steps=200,
            stop_reason="step_limit",
            hessian_condition_number=float("inf"),
        )
        monkeypatch.setattr(engine, "fit_multisite_likelihood", lambda *_a, **_k: value)
    else:

        def refuse(*_a: Any, **_k: Any) -> Any:
            raise ValidationError("controlled numerical refusal")

        monkeypatch.setattr(engine, "fit_multisite_likelihood", refuse)
    results = study.evaluate(native, historical())
    assert len(results) == 2
    for result in results:
        assert result["status"] == status
        assert (
            result["response_multipliers"] is result["training_probabilities"] is None
        )
        if status == "not_converged":
            assert result["steps"] == 200 and result["stop_reason"] == "step_limit"
            assert result["hessian_condition_number"] == "inf"
            assert result["mean_negative_log_likelihood"] is not None
        else:
            assert result["steps"] is result["mean_negative_log_likelihood"] is None
            assert result["stop_reason"] == "controlled numerical refusal"
    json.dumps(results, allow_nan=False)


@pytest.mark.parametrize("value", [False, 0, -1, 1.5])
def test_invalid_training_counts_cannot_be_cast_into_native_inputs(
    native: NativeSource,
    value: object,
) -> None:
    counts: Any = dict(native.counts)
    counts[SITES[0]] = (value, 135, 135, 135, 135)
    with pytest.raises(ValueError, match="integer training counts"):
        study.evaluate(replace(native, counts=counts), historical())


@pytest.mark.parametrize(
    "change", ["reason", "steps", "population", "missing", "extra_output"]
)
def test_old_failure_selection_is_not_relabelled(change: str) -> None:
    body = old_body()
    if change == "reason":
        body = body.replace(b"step_limit", b"other_reason")
    elif change == "steps":
        body = body.replace(b",step_limit,200,", b",step_limit,199,")
    elif change == "population":
        body += body.splitlines(keepends=True)[1]
    elif change == "missing":
        body = body.replace(b"200:Namibia_T7", b"200:Namibia_T8")
    else:
        reader = csv.DictReader(io.StringIO(body.decode(), newline=""))
        rows = list(reader)
        next(row for row in rows if row["fit_id"] == "200:Namibia_T7")[
            "empirical_Acacia"
        ] = "0.1"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        body = stream.getvalue().encode()
    with pytest.raises(ValueError):
        study.historical_fits(body)


@pytest.fixture
def prepared(
    tmp_path: Path, native: NativeSource, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, bytes]:
    store = tmp_path / "shared-source"
    store.mkdir()
    old = tmp_path / "historical.csv"
    body = old_body()
    old.write_bytes(body)
    output = tmp_path / "resolution.json"
    monkeypatch.setattr(producer, "revision", lambda _: "a" * 40)
    monkeypatch.setattr(study, "safe_source_file", lambda *_: old)
    monkeypatch.setattr(
        study, "_historical_pin", lambda _: hashlib.sha256(body).hexdigest()
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: body)
    monkeypatch.setattr(inputs, "load", lambda *_: native)
    return store, output, body


def test_bounded_result_preserves_old_bytes_and_exposes_only_training_outputs(
    prepared: tuple[Path, Path, bytes],
) -> None:
    store, output, body = prepared
    report = study.run(REPOSITORY, store, output)
    written = json.loads(output.read_bytes())
    assert written["training_sites"] == list(study.TRAINING)
    assert written["taxa"] == list(TAXA)
    assert len(written["fits"]) == 2
    assert written["historical_point_source_revision"] == study.HISTORICAL_POINT_SOURCE
    assert report["source_revision"] == "a" * 40
    assert (store.parent / "historical.csv").read_bytes() == body
    assert output.stat().st_size < 16 * 1024
    with pytest.raises(ReportRebuildError, match="absent"):
        study.run(REPOSITORY, store, output)


@pytest.mark.parametrize(
    "change",
    ["source", "old_report", "revision", "pin", "deadline", "size", "committed"],
)
def test_no_result_is_published_on_input_or_resource_refusal(
    prepared: tuple[Path, Path, bytes],
    native: NativeSource,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    store, output, body = prepared
    if change in {"source", "old_report"}:
        calls = 0

        def load(*_a: Any) -> NativeSource:
            nonlocal calls
            calls += 1
            if calls > 1:
                if change == "old_report":
                    (store.parent / "historical.csv").write_bytes(body + b" ")
                else:
                    return replace(native, counts={})
            return native

        monkeypatch.setattr(inputs, "load", load)
    elif change in {"revision", "pin"}:
        values = (
            iter(["a" * 40, "b" * 40])
            if change == "revision"
            else iter([hashlib.sha256(body).hexdigest(), "b" * 64])
        )
        monkeypatch.setattr(
            producer if change == "revision" else study,
            "revision" if change == "revision" else "_historical_pin",
            lambda _: next(values),
        )
    elif change == "deadline":
        times = iter([0.0, 31.0])
        monkeypatch.setattr(
            study, "time", SimpleNamespace(monotonic=lambda: next(times))
        )
    elif change == "size":
        monkeypatch.setattr(study, "MAX_OUTPUT_BYTES", 1)
    else:
        monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: b"different")
    with pytest.raises(ValueError):
        study.run(REPOSITORY, store, output)
    assert not output.exists()


def test_cli_exposes_only_explicit_shared_inputs_and_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    received = []
    monkeypatch.setattr(study, "run", lambda *args: received.append(args))
    output = tmp_path / "result.json"
    assert (
        study.main(
            [
                "--repository",
                str(REPOSITORY),
                "--source-store",
                str(tmp_path),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert received == [(REPOSITORY, tmp_path, output)]
    assert capsys.readouterr().out.strip() == str(output)
