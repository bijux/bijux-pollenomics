"""Original upstream mass and fixed temporal estimand survive predictive handoff."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial import UnavailableSpatialDraw
from bijux_pollenomics.analysis.lra_validation.spatial.uncertainty import workflow

from .test_uncertainty import CONTEXT, atom, run


def upstream(
    name: str, weight: Fraction, *, numerical: bool = False
) -> UnavailableSpatialDraw:
    from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
    from bijux_pollenomics.analysis.lra.uncertainty.contracts import canonical
    from bijux_pollenomics.analysis.lra.uncertainty.projection import project

    # Exercise the maintained source projection's genuine serialized refusal shape;
    # no engine/child request exists when this source-role allocation is empty.
    projected, request, files = project(
        None,  # type: ignore[arg-type]
        {"regional": {"samples": [{"sample_id": "r1"}]}, "local": {"samples": []}},
        {
            "draw_id": name,
            "mass": {"numerator": weight.numerator, "denominator": weight.denominator},
            "ages_by_sample_id": {"r1": 5},
        },
        {"bin_id": "original-calendar-bin", "younger_bp": 0, "older_bp": 10},
    )
    assert (
        request is None
        and files == {}
        and projected["reason_code"] == "missing_role_in_bin"
    )
    if numerical:
        projected.update(
            status="refused",
            reason_code="numerical_refusal",
            error=LRARefusal(
                "no_valid_local_rings",
                "no admissible source ring",
                diagnostics={"finite_rings": 0},
            ).as_dict(),
        )
    original = atom(name, weight, 0.8)
    return UnavailableSpatialDraw(
        canonical(projected).decode(),
        "c" * 64,
        "time",
        original.input_ids,
        original.input_lineage,
        original.admitted_external_ids,
    )


@pytest.mark.parametrize("numerical", [False, True])
def test_serialized_upstream_refusal_retains_original_mass_and_cause(
    numerical: bool,
) -> None:
    unavailable = upstream("d1", Fraction(1, 4), numerical=numerical)
    ready = atom("d2", Fraction(3, 4), 0.6)
    result = run((unavailable, ready))
    row = result["rows"][0]
    assert row["upstream"]["source_row"] == json.loads(unavailable.source_row_json)
    assert row["upstream"]["source_evidence_sha256"] == "c" * 64
    assert row["refusal_stage"] == "upstream" and row["status"] == "refused"
    assert row["spatial_fit_attempted"] is False and row["forward_attempted"] is False
    assert "forward_inputs" not in row and "values" not in row
    assert result["summary"]["failed_mass"] == {"numerator": 1, "denominator": 4}
    assert (
        result["summary"]["mean"] is None
        and result["summary"]["population_covariance"] is None
    )
    assert result["temporal_support_id"] == "time"
    assert all(row["bin_id"] == "time" for row in result["rows"])


def test_all_upstream_atoms_unavailable_need_no_fabricated_numerical_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    atoms = (
        upstream("d1", Fraction(1, 4)),
        upstream("d2", Fraction(3, 4), numerical=True),
    )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail(
            "No spatial/forward call is permitted for upstream-unavailable atoms"
        )

    monkeypatch.setattr(workflow, "fit_spatial_model", forbidden)
    result = run(atoms, forward_model=forbidden)
    assert len(result["rows"]) == 2
    assert result["summary"]["successful_mass"] == {"numerator": 0, "denominator": 1}
    assert result["summary"]["failed_mass"] == {"numerator": 1, "denominator": 1}
    assert (
        result["summary"]["mean"] is None
        and result["summary"]["population_covariance"] is None
    )
    assert result["summary"]["coordinates"] is None
    assert result["temporal_support_id"] == "time"


@pytest.mark.parametrize(
    "mode",
    ["ready-time", "unavailable-time", "unavailable-target", "unknown-upstream-cause"],
)
def test_upstream_and_temporal_preflight_before_any_fit(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    unavailable = upstream("d1", Fraction(1, 4), numerical=True)
    ready = atom("d2", Fraction(3, 4), 0.6)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Invalid source population/estimand must fail before fitting")

    monkeypatch.setattr(workflow, "fit_spatial_model", forbidden)
    with pytest.raises(ValidationRefusal):
        if mode == "ready-time":
            ready = replace(
                ready, forward=replace(CONTEXT, temporal_support_id="another-window")
            )
        elif mode == "unavailable-time":
            unavailable = replace(unavailable, temporal_support_id="another-window")
        elif mode == "unavailable-target":
            unavailable = replace(
                unavailable,
                input_ids=(*unavailable.input_ids, "p10-alias"),
                admitted_external_ids=(*unavailable.admitted_external_ids, "p10-alias"),
            )
        else:
            row = json.loads(unavailable.source_row_json)
            row["error"]["reason_code"] = "lra_extension_missing"
            unavailable = replace(unavailable, source_row_json=json.dumps(row))
        run((unavailable, ready))
