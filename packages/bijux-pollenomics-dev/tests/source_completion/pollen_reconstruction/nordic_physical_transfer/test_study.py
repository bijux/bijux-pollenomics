"""Portable serialized source-to-forecast-to-score ownership controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    reopen as real_reopen,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    write as real_write,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer import (
    evaluation,
    study,
)

from .fixtures import (
    forward_callback,
    inverse_callback,
    saved_inputs,
    synthetic_response,
)


def setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path, Path]:
    profile, path = saved_inputs(tmp_path)
    monkeypatch.setattr(
        study,
        "source_state",
        lambda _: {
            "head": "f" * 40,
            "index_sha256": "e" * 64,
            "python_files": {},
            "r_files": {},
        },
    )
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    return profile, path, tmp_path / "artifacts" / "study"


def test_real_serialized_adapter_closes_all_predictions_before_first_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, path, output = setup(tmp_path, monkeypatch)
    authenticated = []
    calls: list[bool] = []

    def reopen(directory: Path, pin: dict[str, Any]) -> Any:
        result = real_reopen(directory, pin)
        authenticated.append(pin["path"])
        return result

    def score(prediction: list[float], vector: tuple[int, int]) -> dict[str, Any]:
        assert authenticated[:2] == ["responses.json", "prediction-freeze.json"]
        if not calls:
            freeze = json.loads((output / "prediction-freeze.json").read_bytes())
            assert (
                len(freeze["contexts"]) == 216
                and sum(len(r["families"]) for r in freeze["contexts"]) == 432
            )
        calls.append(True)
        return evaluation.native_score(prediction, vector)

    def closed(
        directory: Path,
        prediction: dict[str, Any],
        response: dict[str, Any],
        packet: dict[str, Any],
        protocol: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return evaluation.score_closed(
            directory, prediction, response, packet, protocol, score=score
        )

    monkeypatch.setattr(evaluation, "reopen", reopen)
    monkeypatch.setattr(study, "score_closed", closed)
    result = study.produce(
        tmp_path,
        path,
        output,
        compute_response=synthetic_response,
        inverse=inverse_callback,
        forward=forward_callback,
    )
    assert calls and result["source_guards_passed"] is True
    assert set(result["products"]) == {
        "responses",
        "prediction_freeze",
        "scores",
        "summary",
    }
    assert {p.name for p in output.iterdir()} == {
        "responses.json",
        "prediction-freeze.json",
        "scores.json",
        "summary.json",
        "result.json",
    }
    assert (
        real_reopen(output, result["products"]["prediction_freeze"])["response_file"]
        == result["products"]["responses"]
    )
    assert len(real_reopen(output, result["products"]["scores"])["rows"]) == 432
    assert len(real_reopen(output, result["products"]["summary"])["matched"]) == 5
    assert (
        sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file()) < 8 * 1024**2
    )


@pytest.mark.parametrize("member", ["prediction-freeze.json", "responses.json"])
def test_closed_byte_tamper_prevents_dependent_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, member: str
) -> None:
    _, path, output = setup(tmp_path, monkeypatch)
    calls = []

    def write(directory: Path, name: str, value: Any, maximum: int) -> dict[str, Any]:
        pin = real_write(directory, name, value, maximum)
        if name == "prediction-freeze.json":
            p = directory / member
            p.write_bytes(p.read_bytes() + b" ")
        return pin

    def scored(*_: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append(True)
        raise AssertionError("score accessed")

    def closed(
        directory: Path,
        prediction: dict[str, Any],
        response: dict[str, Any],
        packet: dict[str, Any],
        protocol: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return evaluation.score_closed(
            directory, prediction, response, packet, protocol, score=scored
        )

    monkeypatch.setattr(study, "write", write)
    monkeypatch.setattr(study, "score_closed", closed)
    with pytest.raises(ValueError, match="changed"):
        study.produce(
            tmp_path,
            path,
            output,
            compute_response=synthetic_response,
            inverse=inverse_callback,
            forward=forward_callback,
        )
    assert (
        not calls
        and not (output / "scores.json").exists()
        and not (output / "result.json").exists()
    )


@pytest.mark.parametrize("damage", ["input", "epoch"])
def test_final_source_epoch_refusal_preserves_partial_products(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    profile, path, output = setup(tmp_path, monkeypatch)
    calls = []

    def compute(**kwargs: Any) -> Any:
        calls.append(True)
        if damage == "input" and len(calls) == 1:
            (
                tmp_path / profile["scientific_sources"]["metadata_workbook"]["path"]
            ).write_bytes(b"changed")
        return synthetic_response(**kwargs)

    if damage == "epoch":
        monkeypatch.setattr(
            study,
            "source_state",
            lambda _: {
                "head": "changed" if calls else "f" * 40,
                "index_sha256": "e" * 64,
                "python_files": {},
                "r_files": {},
            },
        )
    with pytest.raises(ValueError, match="identity differs|changed"):
        study.produce(
            tmp_path,
            path,
            output,
            compute_response=compute,
            inverse=inverse_callback,
            forward=forward_callback,
        )
    assert (output / "prediction-freeze.json").exists() and not (
        output / "result.json"
    ).exists()
