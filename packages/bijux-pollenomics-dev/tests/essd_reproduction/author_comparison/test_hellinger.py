"""Arithmetic provenance dispatch on artificial complete author support."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


@pytest.fixture
def consumer() -> ModuleType:
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (
            parent / "docs/report/pollen-reconstruction/author-lra-constrained"
        ).is_dir()
    )
    path = (
        root
        / "docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py"
    )
    spec = importlib.util.spec_from_file_location("author_direct_comparison", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def paired_inputs(
    tmp_path: Path, consumer: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, ...]:
    inputs = tmp_path / "inputs"
    direct = tmp_path / "direct"
    taxa = [f"taxon-{i}" for i in range(30)]
    fraction = dict.fromkeys(taxa, 1 / 30)
    sites = []
    predictions: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    lra: list[dict[str, Any]] = []
    for target in [f"author:site-{i:02d}" for i in range(14)] + ["author:BECKHAM"]:
        raw = inputs / f"{target.split(':')[1]}.json"
        _json(raw, {"taxa": taxa, "sample": {"counts": [1] * 30}})
        sites.append(
            SimpleNamespace(
                record=SimpleNamespace(record_id=target),
                raw=SimpleNamespace(path=raw.name, sha256=_sha(raw)),
            )
        )
        for method in consumer.METHODS:
            predictions.append(
                {
                    "target_record_id": target,
                    "method": method,
                    "pollen_fraction": fraction,
                    "training_manifest_sha256": "training",
                }
            )
            scores.append(
                {
                    "target_record_id": target,
                    "method": method,
                    "status": "refused" if target == "author:BECKHAM" else "scored",
                    "prediction_identity": "prediction",
                }
            )
            if target != "author:BECKHAM":
                lra.extend(
                    {
                        "target_record_id": target,
                        "method": method,
                        "taxon": taxon,
                        "prediction_identity": "prediction",
                        "forward_pollen_fraction": fraction[taxon],
                    }
                    for taxon in taxa
                )
    monkeypatch.setattr(
        consumer, "_source", lambda _: (SimpleNamespace(sites=sites), "source")
    )
    _json(direct / "predictions.json", predictions)
    _json(
        direct / "manifest.json",
        {"prediction_rows_sha256": _sha(direct / "predictions.json")},
    )
    lra_csv, scores_csv = tmp_path / "predictions.csv", tmp_path / "scores.csv"
    _csv(lra_csv, lra)
    _csv(scores_csv, scores)
    reference, comparison = tmp_path / "report.json", tmp_path / "comparison.json"
    _json(
        reference,
        {
            "source_experiment_sha256": "source",
            "requested_folds": 15,
            "predicted_folds": 14,
            "scored_method_rows": 42,
            "refused_site": "author:BECKHAM",
            "prediction_manifest_sha256": "lra-manifest",
        },
    )
    _json(
        comparison,
        {
            "source_experiment_sha256": "source",
            "matched_method_rows": 42,
            "excluded_site": "author:BECKHAM",
            "direct_prediction_manifest_sha256": _sha(direct / "manifest.json"),
            "lra_score_csv_sha256": _sha(scores_csv),
        },
    )
    return inputs, direct, lra_csv, scores_csv, reference, comparison


@pytest.mark.parametrize("profile", ["stable", "source-compatible-22c6e480"])
def test_all_paired_calls_use_selected_arithmetic_outside_original_schema(
    tmp_path: Path,
    consumer: ModuleType,
    paired_inputs: tuple[Path, ...],
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
) -> None:
    selected: list[str] = []

    def distance(predicted: Any, observed: Any, *, arithmetic_profile: str) -> float:
        assert len(predicted) == len(observed) == 30
        selected.append(arithmetic_profile)
        return 0.125

    monkeypatch.setattr(consumer, "hellinger_distance", distance)
    output, receipt = tmp_path / "paired.json", tmp_path / "arithmetic.json"
    report = consumer.paired_hellinger(
        *paired_inputs, output, arithmetic_profile=profile, arithmetic_receipt=receipt
    )
    assert selected == [profile] * 84
    assert report["matched_method_rows"] == 42 and report["matched_sites"] == 14
    assert report["excluded_site"] == "author:BECKHAM"
    assert "arithmetic_profile" not in report
    assert json.loads(receipt.read_text())["paired_output"] == {
        "sha256": _sha(output),
        "bytes": output.stat().st_size,
    }
    assert json.loads(receipt.read_text())["arithmetic_profile"] == profile
    selected.clear()
    default = consumer.paired_hellinger(*paired_inputs, tmp_path / "default.json")
    assert selected == ["stable"] * 84
    assert default == report


@pytest.mark.parametrize(
    "mode", ["unknown", "missing_receipt", "same_output", "existing_receipt"]
)
def test_invalid_profile_or_receipt_refuses_before_source_read(
    tmp_path: Path, consumer: ModuleType, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    def forbidden(_: Path) -> None:
        raise AssertionError("Source must not be read")

    monkeypatch.setattr(consumer, "_source", forbidden)
    output = tmp_path / "paired.json"
    receipt = tmp_path / "receipt.json"
    kwargs: dict[str, Any] = {"arithmetic_profile": "source-compatible-22c6e480"}
    if mode == "unknown":
        kwargs["arithmetic_profile"] = "unreviewed"
    elif mode == "same_output":
        kwargs["arithmetic_receipt"] = output
    elif mode == "existing_receipt":
        receipt.write_text("retained")
        kwargs["arithmetic_receipt"] = receipt
    with pytest.raises(ValueError):
        consumer.paired_hellinger(*([tmp_path] * 6), output, **kwargs)
    assert not output.exists()


@pytest.mark.parametrize("explicit", [False, True])
def test_cli_preserves_default_and_dispatches_explicit_profile(
    consumer: ModuleType, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    captured: list[dict[str, Any]] = []

    def paired(*args: Any, **kwargs: Any) -> dict[str, Any]:
        assert len(args) == 7
        captured.append(kwargs)
        return {}

    monkeypatch.setattr(consumer, "paired_hellinger", paired)
    argv = ["direct_comparison.py", "hellinger"]
    for name in (
        "inputs",
        "direct-predictions",
        "lra-predictions",
        "lra-scores",
        "lra-report",
        "comparison",
        "output",
    ):
        argv.extend([f"--{name}", name])
    if explicit:
        argv.extend(
            [
                "--arithmetic-profile",
                "source-compatible-22c6e480",
                "--arithmetic-receipt",
                "receipt.json",
            ]
        )
    monkeypatch.setattr(sys, "argv", argv)
    consumer.main()
    assert captured == [
        {
            "arithmetic_profile": "source-compatible-22c6e480"
            if explicit
            else "stable",
            "arithmetic_receipt": Path("receipt.json") if explicit else None,
        }
    ]
