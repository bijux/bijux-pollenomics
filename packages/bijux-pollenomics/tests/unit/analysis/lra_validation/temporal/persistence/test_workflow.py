"""Temporal failures preserve requested units and every successfully consumed source."""

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence import workflow

from .support import fixture_payload, spec_from_payload


def _publication(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def publish(stage: Path, destination: Path, **kwargs: object) -> ExperimentProduct:
        captured.update(kwargs)
        return ExperimentProduct(stage, "a" * 64, "b" * 64)

    monkeypatch.setattr(workflow, "publish_phase", publish)
    return captured


def test_temporal_refusal_never_loads_engine_and_keeps_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        object_mapping,
    )

    spec = spec_from_payload(fixture_payload(tmp_path / "inputs"), maximum_lead=400)
    captured = _publication(monkeypatch)

    def forbidden() -> None:
        pytest.fail("Refused chronology must not load numerical engine")

    monkeypatch.setattr(workflow, "load_engine", forbidden)
    workflow.prepare_temporal_persistence_predictions(
        spec,
        input_root=tmp_path / "missing",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "result",
    )
    scientific = object_mapping(captured["scientific"], "scientific")
    assert scientific["requested_predictions"] == 1
    assert scientific["generated_predictions"] == 0
    assert scientific["failed_folds"] == 1
    assert scientific["engine_identity"] is None
    assert scientific["consumed_pollen_record_ids"] == []
    assert scientific["folds"] == [spec.temporal_plan.fold.as_dict()]
    assert scientific["source_admission"] is not None


def test_input_publication_roots_cannot_overlap(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path / "inputs"))
    with pytest.raises(ValidationRefusal, match="disjoint"):
        workflow.prepare_temporal_persistence_predictions(
            spec,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "inputs" / "output",
        )
    assert not (tmp_path / "inputs" / "output").exists()


def test_admitted_geometry_mutation_after_failure_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path / "inputs"))
    captured = _publication(monkeypatch)
    from bijux_pollenomics.analysis.lra_validation.temporal.persistence.admission import (
        admit_temporal_sources,
    )

    actual = admit_temporal_sources

    def fail_after_admission(*args: object, **kwargs: object) -> object:
        # The real admission tracks actual source reads before this later failure.
        actual(
            spec,
            input_root=tmp_path / "inputs",
            consumed_geometry=cast(set[str], kwargs["consumed_geometry"]),
        )
        (tmp_path / "inputs" / spec.older_experiment.sites[0].geometry.path).write_text(
            "{}"
        )
        raise ValidationRefusal(
            "injected_after_geometry", "fault after actual admission"
        )

    monkeypatch.setattr(workflow, "admit_temporal_sources", fail_after_admission)
    with pytest.raises(ValidationRefusal, match="frozen reference"):
        workflow.prepare_temporal_persistence_predictions(
            spec,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "result",
        )
    assert captured == {}
    assert not (tmp_path / "result").exists()
