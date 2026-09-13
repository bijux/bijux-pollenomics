"""Generation binds authentic parent bytes, planned effort and actual engine draws."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    generate_pollen_observation_uncertainty,
    workflow,
)

from .support import fixture


def test_actual_draws_repeat_without_outcome_access(tmp_path: Path) -> None:
    product, plan, _ = fixture(tmp_path)
    for p in (tmp_path / "outcomes").glob("*"):
        p.write_text("OUTCOMES MUST NOT BE OPENED")
    first = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "first",
    )
    second = generate_pollen_observation_uncertainty(
        product.directory,
        replace(plan, entries=tuple(reversed(plan.entries))),
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "second",
    )
    assert (first.directory / "uncertainty.json").read_bytes() == (
        second.directory / "uncertainty.json"
    ).read_bytes()
    rows = json.loads((first.directory / "uncertainty.json").read_text())
    assert len(rows) == 6
    for row in rows:
        assert row["status"] == "generated"
        result = row["engine_result"]
        assert len(result["counts"]) == plan.repeats
        assert all(sum(draw) == 10 for draw in result["counts"])
        assert result["interval_kind"] == "conditional_predictive_observation"
        assert result["simultaneous_coverage_claimed"] is False
    payload = json.loads((first.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    assert payload["outcome_accesses"] == []
    assert payload["declaration_timing_authenticated"] is False


def test_parent_tamper_refuses_before_effort_or_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan, _ = fixture(tmp_path)
    (product.directory / "predictions.json").write_text("[]")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Dependent evidence or engine accessed before parent admission")

    monkeypatch.setattr(workflow, "effort_evidence", forbidden)
    monkeypatch.setattr(workflow, "load_engine", forbidden)
    with pytest.raises(ValidationRefusal):
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert not (tmp_path / "result").exists()


def test_failed_prediction_and_bad_effort_remain_requested(tmp_path: Path) -> None:
    product, plan, _ = fixture(tmp_path, failed=True)
    (tmp_path / "effort/p2.json").write_text("changed")
    result = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "result",
    )
    rows = json.loads((result.directory / "uncertainty.json").read_text())
    assert len(rows) == 6
    assert [r["status"] for r in rows].count("prediction_refused") == 2
    assert [r["status"] for r in rows].count("effort_refused") == 2
    assert [r["status"] for r in rows].count("generated") == 2


def test_complete_denominator_before_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan, _ = fixture(tmp_path)

    def forbidden() -> None:
        pytest.fail("Engine must not load for an incomplete plan")

    monkeypatch.setattr(workflow, "load_engine", forbidden)
    with pytest.raises(ValidationRefusal) as error:
        generate_pollen_observation_uncertainty(
            product.directory,
            replace(plan, entries=plan.entries[:-1]),
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert error.value.reason_code == "observation_denominator_mismatch"


def test_consumed_effort_mutation_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, plan, _ = fixture(tmp_path)
    from bijux_pollenomics.analysis.lra_validation.experiments.outputs import write_json

    original = write_json

    def changed(stage: Path, name: str, value: object) -> None:
        original(stage, name, value)
        if name == "uncertainty.json":
            (tmp_path / "effort/p1.json").write_text("changed after sampling")

    monkeypatch.setattr(workflow, "write_json", changed)
    with pytest.raises(ValidationRefusal):
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert not (tmp_path / "result").exists()


def test_unsupported_purpose_before_access(tmp_path: Path) -> None:
    product, plan, _ = fixture(tmp_path)
    with pytest.raises(ValidationRefusal) as error:
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "absent",
            destination=tmp_path / "result",
            purpose="final",
        )
    assert error.value.reason_code == "unsupported_observation_purpose"


def test_local_profile_refuses_before_effort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        LOCAL_PROFILE,
    )

    from .support import rewrite

    product, plan, _ = fixture(tmp_path)
    product = rewrite(product, profile=LOCAL_PROFILE)
    plan = replace(plan, prediction_manifest_sha256=product.manifest_sha256)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Local diagnostic profile must not read effort")

    monkeypatch.setattr(workflow, "effort_evidence", forbidden)
    with pytest.raises(ValidationRefusal) as error:
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert error.value.reason_code == "experiment_outcome_profile_mismatch"


def test_parent_mutation_after_sampling_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.outputs import write_json

    product, plan, _ = fixture(tmp_path)

    def changed(stage: Path, name: str, value: object) -> None:
        write_json(stage, name, value)
        if name == "uncertainty.json":
            (product.directory / "predictions.json").write_text("changed")

    monkeypatch.setattr(workflow, "write_json", changed)
    with pytest.raises(ValidationRefusal):
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert not (tmp_path / "result").exists()


def test_engine_interrupt_preserves_all_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra.engine.discovery import load_engine

    product, plan, _ = fixture(tmp_path)
    binding = load_engine()
    original = binding.api.sample_pollen_observations
    calls = 0

    def interrupted(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise KeyboardInterrupt
        return original(*args, **kwargs)

    monkeypatch.setattr(binding.api, "sample_pollen_observations", interrupted)
    output = generate_pollen_observation_uncertainty(
        product.directory,
        plan,
        evidence_root=tmp_path / "effort",
        destination=tmp_path / "result",
    )
    rows = json.loads((output.directory / "uncertainty.json").read_text())
    assert [r["status"] for r in rows] == ["generated"] * 2 + ["not_run"] * 4
    assert calls == 3


def test_missing_optional_engine_has_explicit_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal

    product, plan, _ = fixture(tmp_path)

    def absent() -> None:
        raise LRARefusal("lra_extension_missing", "Install supported optional engine")

    monkeypatch.setattr(workflow, "load_engine", absent)
    with pytest.raises(LRARefusal) as error:
        generate_pollen_observation_uncertainty(
            product.directory,
            plan,
            evidence_root=tmp_path / "effort",
            destination=tmp_path / "result",
        )
    assert error.value.reason_code == "lra_extension_missing"
    assert not (tmp_path / "result").exists()
