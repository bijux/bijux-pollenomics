"""Producer sequencing/refusal checks use fake inputs and a stubbed solver only."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    study,
    study_inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    EPSILON,
    CoefficientResult,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.population import (
    PopulationResult,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    IntegralResult,
    Panel,
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    RadialPartition,
)

from .test_study_inputs import fake_files, packets


def fake_certificate(geometry: Geometry) -> CoefficientResult:
    """A pipeline stub, not a kernel certificate or a numerical study result."""
    partition = RadialPartition.build(geometry)
    zero = Interval.point(0)
    integrals = []
    for index in range(len(partition.domains) + 2):
        value = Interval.point(
            Fraction(1, 2)
            if index == 0
            else Fraction(1, 5)
            if index == 1
            else Fraction(0)
        )
        dimensions = 1 if index < 2 else 2
        panel = Panel(
            ((Fraction(0), Fraction(1)),) * dimensions,
            value,
            Fraction(0),
            (Fraction(0),) * dimensions,
            SEVEN_NODE_RULE,
        )
        integrals.append(
            IntegralResult(value, (panel,), "certified_width", None, SEVEN_NODE_RULE)
        )
    first, second = Interval.point(Fraction(0.1)), Interval.point(Fraction(0.2))
    return CoefficientResult(
        tuple(integrals),
        first + second,
        first,
        second,
        (first, zero),
        "refuse_unresolved",
        SEVEN_NODE_RULE,
        partition,
        zero,
    )


def environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    protocol = fake_files(tmp_path)
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts" / "study-output"
    monkeypatch.setattr(study_inputs, "gpm_values", lambda *args: 0.5)
    monkeypatch.setattr(
        study, "source_guard", lambda *args: study.SourceGuard("a" * 40, "index", ())
    )
    monkeypatch.setattr(study, "_peak_rss", lambda: 1000)
    return protocol, output


def frontier(
    geometries: tuple[Geometry, ...], **limits: int | float
) -> PopulationResult:
    assert all(type(geometry) is Geometry for geometry in geometries)
    assert limits == {
        "wall_seconds": 160,
        "max_leaves": 4096,
        "max_attempts": 8191,
        "max_nodes": 73719,
        "max_queue": 4096,
    }
    return PopulationResult(
        tuple(fake_certificate(geometry) for geometry in geometries),
        (None,) * 6,
        tuple(WorkBudget() for _ in geometries),
        0.25,
    )


def test_input_freeze_and_aggregate_proofs_close_before_reference_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, output = environment(tmp_path, monkeypatch)
    baseline_compare = study.compare_references
    compared = []

    def solver(
        geometries: tuple[Geometry, ...], **limits: int | float
    ) -> PopulationResult:
        assert (output / "input-freeze.json").is_file()
        assert not (output / "certificates.json").exists()
        return frontier(geometries, **limits)

    def compare(
        case: study_inputs.StudyCase, result: CoefficientResult
    ) -> list[dict[str, Any]]:
        assert (output / "certificates.json").is_file()
        assert len(json.loads((output / "certificates.json").read_bytes())) == 6
        compared.append((case.core, case.taxon))
        return baseline_compare(case, result)

    monkeypatch.setattr(study, "enclose_population", solver)
    monkeypatch.setattr(study, "compare_references", compare)
    result = study.run_study(tmp_path, protocol, output)
    assert compared == list(study_inputs.OWNERS)
    assert result["status"] == "all_coefficients_certified"
    assert all(
        row["backend_status"] == "refuse_unresolved" and row["all_final_widths_pass"]
        for row in result["cases"]
    )
    assert len(result["certificate_cases"]) == 6
    assert result["protocol_file"]["bytes"] == protocol.stat().st_size
    assert (
        result["input_freeze_file"]["bytes"]
        == (output / "input-freeze.json").stat().st_size
    )
    assert (
        result["certificate_identity"]["bytes"]
        == (output / "certificates.json").stat().st_size
    )
    freeze = json.loads((output / "input-freeze.json").read_bytes())
    assert freeze["historical_A_authenticated"] is False
    assert "consumed" not in result and "source_sha256" not in result


def test_partial_population_keeps_all_owners_and_only_maps_existing_proofs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, output = environment(tmp_path, monkeypatch)

    def partial(
        geometries: tuple[Geometry, ...], **limits: int | float
    ) -> PopulationResult:
        result = frontier(geometries, **limits)
        return PopulationResult(
            (result.results[0],) + (None,) * 5,
            (None,) + ("not_executed:wall_seconds",) * 5,
            result.budgets,
            160.0,
        )

    monkeypatch.setattr(study, "enclose_population", partial)
    result = study.run_study(tmp_path, protocol, output)
    assert (
        result["status"] == "refuse_unresolved"
        and not result["all_population_complete"]
    )
    assert len(result["cases"]) == 6 and len(result["certificate_cases"]) == 1
    assert result["cases"][0]["references"] is not None
    assert all(
        row["references"] is None and not row["complete_geometry_certificate"]
        for row in result["cases"][1:]
    )


@pytest.mark.parametrize("failure", ["certificate_bytes", "source_index", "rss"])
def test_resource_or_source_failure_never_promotes_reference_accuracy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    protocol, output = environment(tmp_path, monkeypatch)
    monkeypatch.setattr(study, "enclose_population", frontier)
    if failure == "certificate_bytes":
        monkeypatch.setattr(study, "CERTIFICATE_BYTE_LIMIT", 1)
    elif failure == "rss":
        monkeypatch.setattr(study, "_peak_rss", lambda: 805306369)
    else:
        calls: list[None] = []

        def guard(*args: object) -> study.SourceGuard:
            calls.append(None)
            return study.SourceGuard(
                "a" * 40, "before" if len(calls) == 1 else "after", ()
            )

        monkeypatch.setattr(study, "source_guard", guard)
    result = study.run_study(tmp_path, protocol, output)
    assert (
        result["status"] == "refuse_unresolved"
        and not result["all_population_complete"]
    )
    assert all(
        row["references"] is None
        and not row["all_final_widths_pass"]
        and not row["complete_geometry_certificate"]
        for row in result["cases"]
    )


def test_saved_error_checks_both_endpoints_and_keeps_legacy_tolerance_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, original, protocol = packets()
    monkeypatch.setattr(study_inputs, "gpm_values", lambda *args: 0.5)
    case = study_inputs.prepare_inputs(result, original, protocol).cases[0]
    math_result = fake_certificate(case.geometry)
    value = case.references[0].value
    changed = replace(
        math_result, homogeneous=Interval(value - EPSILON / 2, value + 2 * EPSILON)
    )
    row = study.compare_references(case, changed)[0]
    assert Fraction(row["max_absolute_error_exact"]) == 2 * EPSILON
    assert not row["absolute_error_certified"] and row["correspondence_pass"]
    assert Fraction(
        row["correspondence_tolerance_exact"]
    ) == study_inputs.LEGACY_ATOL + study_inputs.LEGACY_RTOL * abs(value)


def test_foreign_returned_geometry_and_existing_destination_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, output = environment(tmp_path, monkeypatch)

    def foreign(
        geometries: tuple[Geometry, ...], **limits: int | float
    ) -> PopulationResult:
        returned = frontier(geometries, **limits)
        return replace(returned, results=(returned.results[2],) + returned.results[1:])

    monkeypatch.setattr(study, "enclose_population", foreign)
    with pytest.raises(ValueError, match="foreign"):
        study.run_study(tmp_path, protocol, output)
    assert (output / "input-freeze.json").is_file()
    with pytest.raises(ReportRebuildError):
        study.run_study(tmp_path, protocol, output)
