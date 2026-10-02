"""Fake source routing and metadata-only difference checks for selected transfer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import sys
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    nordic_selected_transfer_replay as replay,
)

ROOT = Path(__file__).resolve().parents[5]
NUMERICAL_ORACLES = ROOT / "docs/report/regions/nordic/selected-pollen-transfer"
HISTORICAL_RECEIPTS = ROOT / replay.TRANSFER_PACKET


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    shutil.copytree(
        ROOT / replay.DEVELOPMENT_PACKET,
        repository / replay.DEVELOPMENT_PACKET,
    )
    shutil.copytree(
        ROOT / replay.TRANSFER_PACKET,
        repository / replay.TRANSFER_PACKET,
    )
    for source in (
        replay.DIRECT / "cohort.csv",
        replay.DIRECT / "scores.csv",
        replay.DEVELOPMENT,
    ):
        destination = repository / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, destination)
    return repository


def fake_source_writer(module: str, source: Path, args: list[str]) -> None:
    assert module == "fixed.current.transfer"
    assert source.name == "nordic_pollen_transfer.py"
    command = args[0]
    data_root = Path(args[2])
    inputs = Path(args[4])
    assert data_root != inputs
    assert (
        sha(data_root / replay.DIRECT / "manifest.json")
        == replay.HISTORICAL_MANIFEST_SHA
    )
    assert (
        sha(inputs / "inputs/metadata-NO.json")
        == replay.HISTORICAL_PREPARED["metadata-NO.json"]
    )
    if command == "predict":
        output = Path(args[6])
        output.mkdir()
        frozen = (
            (HISTORICAL_RECEIPTS / "historical-freeze.json")
            .read_bytes()
            .replace(
                replay.HISTORICAL_SOURCE_SHA.encode(),
                replay.CURRENT_SOURCE_SHA.encode(),
            )
        )
        (output / "freeze.json").write_bytes(frozen)
        for country in replay.COUNTRIES:
            shutil.copyfile(
                NUMERICAL_ORACLES / f"predictions-{country}.json",
                output / f"predictions-{country}.json",
            )
    elif command == "score":
        frozen_path = Path(args[6])
        assert args[7] == "--freeze-sha256"
        assert args[8] == sha(frozen_path / "freeze.json")
        output = Path(args[10])
        output.mkdir()
        shutil.copyfile(
            NUMERICAL_ORACLES / "paired-scores.csv", output / "paired-scores.csv"
        )
        report = (
            (HISTORICAL_RECEIPTS / "historical-report.json")
            .read_bytes()
            .replace(replay.HISTORICAL_FREEZE_SHA.encode(), args[8].encode())
        )
        (output / "report.json").write_bytes(report)
    else:
        raise AssertionError("unexpected source command")


def test_current_source_route_changes_only_two_metadata_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        replay, "_source_module", lambda _repository: "fixed.current.transfer"
    )
    monkeypatch.setattr(replay, "_relational_files", lambda _repository: [])
    monkeypatch.setattr(replay, "_invoke", fake_source_writer)
    original_argv = list(sys.argv)
    historical_bytes = {
        "freeze.json": sha(HISTORICAL_RECEIPTS / "historical-freeze.json"),
        "report.json": sha(HISTORICAL_RECEIPTS / "historical-report.json"),
        **{
            name: sha(NUMERICAL_ORACLES / name)
            for name in replay.OUTPUTS - {"freeze.json", "report.json"}
        },
    }
    receipt = replay.run(repository, repository / "artifacts/products")
    assert sys.argv == original_argv
    assert receipt["metadata_differences"] == [
        "freeze.json:producer_sha256",
        "report.json:freeze_sha256",
    ]
    assert receipt["current_freeze_sha256"] != replay.HISTORICAL_FREEZE_SHA
    assert receipt["current_report_sha256"] != replay.HISTORICAL_REPORT_SHA
    for name in (
        "paired-scores.csv",
        *(f"predictions-{country}.json" for country in replay.COUNTRIES),
    ):
        assert sha(repository / "artifacts/products" / name) == sha(
            NUMERICAL_ORACLES / name
        )
    assert (
        sha(repository / replay.TRANSFER_PACKET / "historical-freeze.json")
        == replay.HISTORICAL_FREEZE_SHA
    )
    assert historical_bytes == {
        "freeze.json": sha(HISTORICAL_RECEIPTS / "historical-freeze.json"),
        "report.json": sha(HISTORICAL_RECEIPTS / "historical-report.json"),
        **{
            name: sha(NUMERICAL_ORACLES / name)
            for name in replay.OUTPUTS - {"freeze.json", "report.json"}
        },
    }
    assert not (
        repository / "docs/report/regions/nordic/selected-pollen-transfer"
    ).exists()


def test_tracked_development_packet_has_full_exact_digests(tmp_path: Path) -> None:
    repository = fixture_repository(tmp_path)
    manifest = repository / replay.DEVELOPMENT_PACKET / "prepared/input-manifest.json"
    assert len(replay.HISTORICAL_PREPARED["input-manifest.json"]) == 64
    assert (
        sha(manifest)
        == "d1e20733eeabde12ab8ab2ee3ff687cd854c2fee4269fb20fe175365267d99d5"
    )
    assert all(len(digest) == 64 for digest in replay.HISTORICAL_PREPARED.values())
    replay._packet(repository)
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="historical prepared byte"):
        replay._packet(repository)


def test_current_relational_source_is_exact_manifest_selected_set() -> None:
    selected = replay._relational_files(ROOT)
    assert len(selected) == 11
    assert len({str(path) for path, _ in selected}) == 11
    assert {path.parent.name for path, _ in selected} == {
        "relational",
        "samples",
        "age_claims",
        "observations",
    }
    assert all(
        len(digest) == 64 and sha(ROOT / path) == digest for path, digest in selected
    )


@pytest.mark.parametrize("tamper", ["metadata", "extra", "receipt", "symlink"])
def test_historical_packet_refuses_changed_bytes(tmp_path: Path, tamper: str) -> None:
    repository = fixture_repository(tmp_path)
    packet = repository / replay.TRANSFER_PACKET
    if tamper == "metadata":
        (packet / "metadata-FI.json").write_bytes(b"changed")
    elif tamper == "extra":
        (packet / "unexpected.json").write_bytes(b"{}")
    elif tamper == "symlink":
        (packet / "metadata-NO.json").unlink()
        (packet / "metadata-NO.json").symlink_to(packet / "metadata-FI.json")
    else:
        (packet / "historical-freeze.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="historical"):
        replay._packet(repository)


def test_foreign_source_origin_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    source = repository / replay.SOURCE
    source.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / replay.SOURCE, source)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda _module: SimpleNamespace(origin="/foreign/source.py"),
    )
    with pytest.raises(ValueError, match="module origin"):
        replay._source_module(repository)


def test_changed_current_source_bytes_refused(tmp_path: Path) -> None:
    repository = fixture_repository(tmp_path)
    source = repository / replay.SOURCE
    source.parent.mkdir(parents=True)
    source.write_bytes((ROOT / replay.SOURCE).read_bytes() + b"\n")
    with pytest.raises(ValueError, match="current selected-transfer source changed"):
        replay._source_module(repository)


@pytest.mark.parametrize(
    "change",
    [
        "prediction-byte",
        "freeze-extra-field",
        "historical-freeze",
        "score-byte",
        "report-extra-field",
    ],
)
def test_unreviewed_output_never_reaches_final_products(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        replay, "_source_module", lambda _repository: "fixed.current.transfer"
    )
    monkeypatch.setattr(replay, "_relational_files", lambda _repository: [])

    def altered_writer(module: str, source: Path, args: list[str]) -> None:
        fake_source_writer(module, source, args)
        if args[0] == "predict":
            frozen = Path(args[6])
            if change == "prediction-byte":
                path = frozen / "predictions-DK.json"
                path.write_bytes(path.read_bytes() + b"\n")
            elif change == "freeze-extra-field":
                path = frozen / "freeze.json"
                data = json.loads(path.read_bytes())
                data["unsupported_admission"] = True
                path.write_text(json.dumps(data))
            elif change == "historical-freeze":
                shutil.copyfile(
                    HISTORICAL_RECEIPTS / "historical-freeze.json",
                    frozen / "freeze.json",
                )
        elif args[0] == "score":
            scored = Path(args[10])
            if change == "score-byte":
                path = scored / "paired-scores.csv"
                path.write_bytes(path.read_bytes() + b"\n")
            elif change == "report-extra-field":
                path = scored / "report.json"
                data = json.loads(path.read_bytes())
                data["independent_confirmation"] = True
                path.write_text(json.dumps(data))

    monkeypatch.setattr(replay, "_invoke", altered_writer)
    output = repository / "artifacts/products"
    with pytest.raises(ValueError, match="differ"):
        replay.run(repository, output)
    assert not output.exists()
    assert (
        sha(repository / replay.TRANSFER_PACKET / "historical-freeze.json")
        == replay.HISTORICAL_FREEZE_SHA
    )


def test_output_reuse_and_escape_refused(tmp_path: Path) -> None:
    repository = fixture_repository(tmp_path)
    with pytest.raises(ValueError, match="outside repository"):
        replay._absent_output(repository, tmp_path / "outside")
    output = repository / "artifacts/products"
    output.mkdir()
    with pytest.raises(ValueError, match="absent absolute"):
        replay._absent_output(repository, output)


def test_argv_restored_on_source_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    original = list(sys.argv)

    def refuse(_module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        raise ValueError("source refused")

    monkeypatch.setattr(runpy, "run_module", refuse)
    with pytest.raises(ValueError, match="source refused"):
        replay._invoke("source.module", Path("source.py"), ["predict"])
    assert sys.argv == original


def test_retained_current_products_name_actual_producer_and_preserve_history() -> None:
    """Bind published metadata to current source while retaining original receipts."""
    replay._packet(ROOT)
    current = ROOT / "docs/report/regions/nordic/selected-pollen-transfer"
    freeze = json.loads((current / "freeze.json").read_bytes())
    report = json.loads((current / "report.json").read_bytes())
    old_freeze = json.loads(
        (HISTORICAL_RECEIPTS / "historical-freeze.json").read_bytes()
    )
    old_report = json.loads(
        (HISTORICAL_RECEIPTS / "historical-report.json").read_bytes()
    )
    assert freeze == {**old_freeze, "producer_sha256": sha(ROOT / replay.SOURCE)}
    assert report == {**old_report, "freeze_sha256": sha(current / "freeze.json")}
    assert freeze["producer_sha256"] != old_freeze["producer_sha256"]
    assert (
        sha(HISTORICAL_RECEIPTS / "historical-freeze.json")
        == replay.HISTORICAL_FREEZE_SHA
    )
    assert (
        sha(HISTORICAL_RECEIPTS / "historical-report.json")
        == replay.HISTORICAL_REPORT_SHA
    )
    for country in replay.COUNTRIES:
        assert (
            sha(current / f"predictions-{country}.json")
            == old_freeze["prediction_sha256"][country]
        )
    assert sha(current / "paired-scores.csv") == old_report["paired_scores_sha256"]
