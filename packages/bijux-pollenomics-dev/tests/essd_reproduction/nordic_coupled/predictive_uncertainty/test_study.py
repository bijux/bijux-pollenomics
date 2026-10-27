"""Guard the prediction freeze, serialized readback and exposed-outcome boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty import (
    study,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.inputs import (
    METHODS,
    load_inputs,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.products import (
    StudyError,
    _write,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.scoring import (
    score_diagnostics,
)

from .test_inputs import saved_inputs


@pytest.fixture(scope="module")
def source_tree(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("bootstrap-source")
    original = saved_inputs(root)
    (root / "artifacts").mkdir(exist_ok=True)
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads(
        (
            repository
            / "reports/science/pollen-reconstruction/krageholm-regional-coupled/predictive-uncertainty/protocol.json"
        ).read_text()
    )
    protocol["sources"] = original["sources"]
    path = root / "protocol.json"
    path.write_text(json.dumps(protocol))
    return root, path


def _mock_numerics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        study, "_git_state", lambda repository: ("1" * 40, b"synthetic-index")
    )
    monkeypatch.setattr(
        study,
        "_nominal",
        lambda packet, bank, tolerance: list(packet.nominal_predictions),
    )

    def prediction(case: Any, bank: Any) -> dict[str, Any]:
        return {
            "case_id": case.case_id,
            "target_id": case.target_id,
            "methods": {
                method: {
                    "pollen": [[0.75, 0.25] for _ in range(bank.replicates)],
                    "direct_pollen": [[0.5, 0.5] for _ in range(bank.replicates)],
                    "valid_mask": [True] * bank.replicates,
                }
                for method in METHODS
            },
        }

    monkeypatch.setattr(study, "predict_case", prediction)


def test_outcomes_open_only_after_all_closed_predictions_are_read_back(
    source_tree: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, protocol = source_tree
    _mock_numerics(monkeypatch)
    output = root / "artifacts/closed-bootstrap"
    original = score_diagnostics
    calls = []

    def guarded(inputs: dict[str, Any], predictions: dict[str, Any]) -> dict[str, Any]:
        manifest = json.loads((output / "prediction-manifest.json").read_text())
        assert set(manifest["files"]) == {"inputs", "draws", "predictions"}
        for ref in manifest["files"].values():
            raw = (output / ref["path"]).read_bytes()
            assert len(raw) == ref["bytes"]
            assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
        assert predictions == json.loads((output / "predictions.json").read_text())
        calls.append("postfreeze")
        return original(inputs, predictions)

    monkeypatch.setattr(study, "score_diagnostics", guarded)
    result = study.produce(root, protocol, output)
    assert calls == ["postfreeze"]
    assert result["status"] == "produced_awaiting_independent_verification"
    assert result["source_guards_passed"] is True
    summary = json.loads((output / "summary.json").read_text())
    assert summary["outcome_access"]["readback_verified"] is True
    assert len(summary["score_diagnostics"]["observed"]) == 3
    assert len(summary["score_diagnostics"]["cases"]) == 9


@pytest.mark.parametrize(
    "corruption_target", ["predictions.json", "prediction-manifest.json"]
)
def test_changed_serialized_prediction_blocks_outcome_access(
    source_tree: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    corruption_target: str,
) -> None:
    root, protocol = source_tree
    _mock_numerics(monkeypatch)
    output = root / "artifacts" / ("changed-" + corruption_target)
    original = _write

    def corrupt(path: Path, value: Any, maximum: int) -> dict[str, Any]:
        pin = original(path, value, maximum)
        if path.name == "prediction-manifest.json":
            prediction = path.parent / corruption_target
            prediction.write_bytes(prediction.read_bytes() + b" ")
        return pin

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Changed prediction reached outcomes")

    monkeypatch.setattr(study, "_write", corrupt)
    monkeypatch.setattr(study, "score_diagnostics", forbidden)
    with pytest.raises(StudyError, match="product changed"):
        study.produce(root, protocol, output)
    assert not (output / "summary.json").exists()


def test_nominal_correspondence_is_a_gate_not_a_changed_expectation(
    source_tree: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, path = source_tree
    packet = load_inputs(root, json.loads(path.read_text()))
    case = packet.cases[0]
    reference = next(
        row for row in packet.nominal_predictions if row["case_id"] == case.case_id
    )

    def wrong(case: Any, bank: Any) -> dict[str, Any]:
        return {
            "methods": {
                method: {
                    "valid_mask": [True],
                    "pollen": [[0.0, 1.0]],
                    "cover": [reference["vegetation_fraction"]],
                }
                for method in METHODS
            }
        }

    monkeypatch.setattr(study, "predict_case", wrong)
    with pytest.raises(StudyError, match="Nominal source correspondence"):
        study._nominal(packet, object(), 1e-12)


def test_changed_source_is_refused_before_sampling(
    source_tree: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, path = source_tree
    packet = load_inputs(root, json.loads(path.read_text()))
    source = root / packet.source_files[0]["path"]
    raw = source.read_bytes()
    monkeypatch.setattr(study, "load_inputs", lambda repository, protocol: packet)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Changed source reached sampling")

    monkeypatch.setattr(study, "generate_draw_bank", forbidden)
    try:
        source.write_bytes(raw + b" ")
        with pytest.raises(StudyError, match="source size changed"):
            study.produce(root, path, root / "artifacts/source-refused-bootstrap")
    finally:
        source.write_bytes(raw)
