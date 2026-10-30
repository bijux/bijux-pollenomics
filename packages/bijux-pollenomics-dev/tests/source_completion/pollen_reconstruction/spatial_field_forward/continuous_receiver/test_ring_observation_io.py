"""Exercise closed-file identity and source-epoch gates without numerical replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    ring_verification as observer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.ring_inputs import (
    BASE,
    CAPTURE,
    RADIAL_PROTOCOL,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    VerificationError,
    identity,
)


def _packet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Path, Path, Path, Path]:
    repository = tmp_path / "repository"
    repository.mkdir()
    artifacts = repository / "artifacts"
    artifacts.mkdir()
    study = artifacts / "closed"
    study.mkdir()
    (repository / "input.json").write_text("{}\n")
    protocol = repository / "protocol.json"
    protocol.write_text(json.dumps({"input_files": {"input.json": identity(b"{}\n")}}))
    source = "f" * 40
    protocol_pin = {"path": "protocol.json", **identity(protocol.read_bytes())}

    def write(name: str, value: Any) -> dict[str, str | int]:
        raw = (json.dumps(value, sort_keys=True) + "\n").encode()
        (study / name).write_bytes(raw)
        return {"path": name, **identity(raw)}

    certificate = write("certificates.json", {"cases": []})
    prediction = write(
        "prediction-ranges.json",
        {
            "source_commit": source,
            "protocol_file": protocol_pin,
            "certificate_file": certificate,
        },
    )
    write(
        "result.json",
        {
            "source_commit": source,
            "protocol_file": protocol_pin,
            "certificate_file": certificate,
            "prediction_file": prediction,
        },
    )
    parsed = {
        BASE + "result.json": {},
        BASE + "protocol.json": {},
        CAPTURE: {},
        RADIAL_PROTOCOL: {
            "source_prediction": "old-prediction",
            "source_result": "old-result",
        },
        "old-prediction": {},
        "old-result": {},
    }
    monkeypatch.setattr(observer, "bind_raw_inputs", lambda *_: parsed)
    monkeypatch.setattr(observer, "source_guard", lambda *_: (source, "index"))
    monkeypatch.setattr(observer, "_peak_rss", lambda: 1000)
    monkeypatch.setattr(
        observer, "audit", lambda **_: {"status": "passed", "accounting_verified": True}
    )
    return repository, protocol, study, artifacts / "observer" / "check.json"


def test_closed_identity_epoch_and_fresh_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository, protocol, study, output = _packet(monkeypatch, tmp_path)
    result = observer.run_verification(repository, protocol, study, output)
    assert (
        result["observer_source_commit"] == result["producer_source_commit"] == "f" * 40
    )
    assert json.loads(output.read_bytes())["accounting_verified"] is True
    with pytest.raises(VerificationError, match="Fresh owned"):
        observer.run_verification(repository, protocol, study, output)


def test_changed_proof_bytes_refuse_before_audit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository, protocol, study, output = _packet(monkeypatch, tmp_path)
    (study / "certificates.json").write_text('{"cases":[1]}\n')
    with pytest.raises(VerificationError, match="identity differs"):
        observer.run_verification(repository, protocol, study, output)
    assert not output.exists()


def test_index_drift_does_not_publish_observer_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository, protocol, study, output = _packet(monkeypatch, tmp_path)
    calls = 0

    def guard(*_args: object) -> tuple[str, str]:
        nonlocal calls
        calls += 1
        return "f" * 40, "index" if calls == 1 else "changed"

    monkeypatch.setattr(observer, "source_guard", guard)
    with pytest.raises(VerificationError, match="changed during observation"):
        observer.run_verification(repository, protocol, study, output)
    assert not output.exists()
