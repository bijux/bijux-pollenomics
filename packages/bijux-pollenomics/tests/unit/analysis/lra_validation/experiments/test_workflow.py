"""Public experiment orchestration refuses invalid budgets before work starts."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
)

from .test_inputs import fixture_inputs


@pytest.mark.parametrize("workers", [0, -1, True, 1_000_000])
def test_worker_budget_is_validated_before_work(tmp_path: Path, workers: int) -> None:
    payload = fixture_inputs(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_experiment_predictions(
            payload,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "prediction",
            workers=workers,
        )
    assert not (tmp_path / "prediction").exists()
    assert not (tmp_path / "cache").exists()


@pytest.mark.parametrize("source", ["raw", "geometry", "parameters"])
def test_consumed_source_mutation_is_refused_before_publication(
    tmp_path: Path, source: str
) -> None:
    from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.experiments import ExperimentSpec
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        verify_consumed_sources,
    )

    payload = fixture_inputs(tmp_path)
    spec = ExperimentSpec(payload)
    path = tmp_path / (
        spec.sites[0].raw.path
        if source == "raw"
        else spec.sites[0].geometry.path
        if source == "geometry"
        else "parameters.json"
    )
    verify_consumed_sources(
        spec,
        tmp_path,
        pollen_record_ids={"p01"},
        geometry_record_ids={"p01", "p04"},
        template_used=True,
    )
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValidationRefusal):
        verify_consumed_sources(
            spec,
            tmp_path,
            pollen_record_ids={"p01"},
            geometry_record_ids={"p01", "p04"},
            template_used=True,
        )


def test_unconsumed_target_pollen_is_never_opened_by_final_source_check(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import ExperimentSpec
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        verify_consumed_sources,
    )

    spec = ExperimentSpec(fixture_inputs(tmp_path))
    (tmp_path / spec.sites[-1].raw.path).unlink()
    verify_consumed_sources(
        spec,
        tmp_path,
        pollen_record_ids={"p01"},
        geometry_record_ids={"p01", "p04"},
        template_used=True,
    )
