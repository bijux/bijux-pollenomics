"""Fake routing checks for exact retained Nordic development input custody."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    nordic_development_replay as replay,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    packet = repository / replay.PACKET
    (packet / "prepared/inputs").mkdir(parents=True)
    identity = {
        "runner_sha256": "65fd5dd1fd55390360ce118ff137f6fba6e43803074e21d23159fe340292f97b"
    }
    payloads = {
        "publication-manifest.json": json.dumps({"input_identity": identity}).encode(),
        "prepared/input-manifest.json": json.dumps(identity).encode(),
        **{
            f"prepared/inputs/training-{country}.json": b"{}"
            for country in ("DK", "FI", "NO")
        },
    }
    for name, data in payloads.items():
        (packet / name).write_bytes(data)
    hashes = {name: digest(data) for name, data in payloads.items()}
    monkeypatch.setattr(replay, "ORIGINAL_INPUT_HASHES", hashes)
    (packet / "custody.json").write_text(
        json.dumps(
            {
                "schema_version": "nordic-development-retained-input-custody.v1",
                "historical_creation_commit": "27ff47c4a829f59ae37b6a0e85b136b01a36cfa9",
                "publication_git_blob": "7c61600e883f2603a75d7287d6071a99485c56da",
                "files_sha256": hashes,
            }
        )
    )
    return repository


def fake_writer(module: str, source: Path, args: list[str]) -> None:
    assert module == "fixed.current.module"
    assert source.name == "nordic_pollen_development.py"
    assert args[0] == "--repository" and args[2] == "--inputs"
    assert args[4] == "--output"
    data_root, inputs, output = Path(args[1]), Path(args[3]), Path(args[5])
    assert data_root != inputs and data_root != output
    assert (
        (data_root / replay.HISTORICAL_PUBLICATION).read_bytes()
        == b'{"input_identity": {"runner_sha256": "65fd5dd1fd55390360ce118ff137f6fba6e43803074e21d23159fe340292f97b"}}'
    )
    assert (inputs / "inputs/training-DK.json").read_bytes() == b"{}"
    output.mkdir()
    trial = b"fixed-fake-trials"
    (output / "trial-scores.csv.gz").write_bytes(trial)
    report = {
        "schema_version": "nordic-observed-pollen-development.v1",
        "trial_score_rows": 40932,
        "outer_target_outcome_files_read": 0,
        "lra_or_vegetation_validation": False,
        "trial_scores_sha256": digest(trial),
        "inputs": [
            {
                "path": str(replay.HISTORICAL_PUBLICATION),
                "sha256": replay.ORIGINAL_INPUT_HASHES["publication-manifest.json"],
            },
            {
                "path": "input-manifest.json",
                "sha256": replay.ORIGINAL_INPUT_HASHES["prepared/input-manifest.json"],
            },
            *[
                {
                    "path": f"inputs/training-{country}.json",
                    "sha256": replay.ORIGINAL_INPUT_HASHES[
                        f"prepared/inputs/training-{country}.json"
                    ],
                }
                for country in ("DK", "FI", "NO")
            ],
        ],
    }
    (output / "report.json").write_text(json.dumps(report))


def test_isolated_historical_packet_routing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    monkeypatch.setattr(
        replay, "_source_module", lambda _repository: "fixed.current.module"
    )
    monkeypatch.setattr(replay, "_invoke", fake_writer)
    output = repository / "artifacts/output"
    before = list(sys.argv)
    receipt = replay.run(repository, output)
    assert sys.argv == before
    assert receipt["output_sha256"]["trial-scores.csv.gz"] == digest(
        b"fixed-fake-trials"
    )
    stage = repository / receipt["complete_input_stage_path"]
    assert (stage / "prepared/input-manifest.json").is_file()
    assert (stage / "data-root" / replay.HISTORICAL_PUBLICATION).is_file()


@pytest.mark.parametrize("tamper", ["bytes", "extra", "symlink"])
def test_packet_refuses_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    packet = repository / replay.PACKET
    if tamper == "bytes":
        (packet / "prepared/input-manifest.json").write_bytes(b"changed")
    elif tamper == "extra":
        (packet / "extra.json").write_bytes(b"{}")
    else:
        (packet / "extra.json").symlink_to(packet / "publication-manifest.json")
    with pytest.raises(ValueError, match="packet|input"):
        replay.run(repository, repository / "artifacts/output")


def test_foreign_source_module_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    source = repository / replay.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("pass\n")
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda _module: SimpleNamespace(origin="/other/source.py"),
    )
    with pytest.raises(ValueError, match="module origin"):
        replay.run(repository, repository / "artifacts/output")


def test_output_escape_and_reuse_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="outside repository"):
        replay.run(repository, tmp_path / "outside")
    output = repository / "artifacts/output"
    output.mkdir()
    with pytest.raises(ValueError, match="absent artifact output"):
        replay.run(repository, output)


def test_unexpected_output_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    monkeypatch.setattr(
        replay, "_source_module", lambda _repository: "fixed.current.module"
    )

    def writer(module: str, source: Path, args: list[str]) -> None:
        fake_writer(module, source, args)
        (Path(args[5]) / "extra.json").write_text("{}")

    monkeypatch.setattr(replay, "_invoke", writer)
    with pytest.raises(ValueError, match="output population"):
        replay.run(repository, repository / "artifacts/output")


def test_argv_restored_after_original_cli_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = list(sys.argv)

    def refuse(_module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        assert sys.argv[-1] == "output"
        raise ValueError("writer refused")

    monkeypatch.setattr(runpy, "run_module", refuse)
    with pytest.raises(ValueError, match="writer refused"):
        replay._invoke("source.module", Path("source.py"), ["output"])
    assert sys.argv == original


def test_integrated_historical_packet_matches_production_identity() -> None:
    """Authenticate real retained inputs rather than fixture-replaced hash constants."""
    repository = Path(__file__).resolve().parents[5]
    assert all(len(value) == 64 for value in replay.ORIGINAL_INPUT_HASHES.values())
    assert replay._packet(repository) == repository / replay.PACKET


@pytest.mark.parametrize(
    "field,value",
    [("lra_or_vegetation_validation", True), ("outer_target_outcome_files_read", 1)],
)
def test_historical_replay_rejects_scientific_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: bool | int
) -> None:
    repository = fixture_repository(tmp_path, monkeypatch)
    monkeypatch.setattr(
        replay, "_source_module", lambda _repository: "fixed.current.module"
    )

    def writer(module: str, source: Path, args: list[str]) -> None:
        fake_writer(module, source, args)
        report_path = Path(args[5]) / "report.json"
        report = json.loads(report_path.read_bytes())
        report[field] = value
        report_path.write_text(json.dumps(report))

    monkeypatch.setattr(replay, "_invoke", writer)
    with pytest.raises(ValueError, match="report identity"):
        replay.run(repository, repository / "artifacts/output")
