"""Supplied joint-law propagation, whole-axis leakage and refusal regressions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    ValidationRefusal,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.prediction import ForwardInputs
from bijux_pollenomics.analysis.lra_validation.spatial import (
    JointSpatialDraw,
    SiteCoordinate,
    SpatialConfig,
    UnavailableSpatialDraw,
    propagate_withheld_spatial_draws,
)
from bijux_pollenomics.analysis.lra_validation.spatial.uncertainty import workflow
from bijux_pollenomics.analysis.lra_validation.spatial.uncertainty.contracts import (
    CONDITIONED_SOURCES,
    UPSTREAM_SOURCES,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

RECORDS = (
    SiteRecord("r1", "site1"),
    SiteRecord("r2", "site2"),
    SiteRecord("p10", "target"),
    SiteRecord("p10-alias", "other", ("p10",)),
)
FOLD = next(
    fold for fold in grouped_leave_one_out(RECORDS) if "p10" in fold.test_record_ids
)
G1, G2 = site_group_id(("r1",)), site_group_id(("r2",))
GROUPS = tuple(sorted((G1, G2)))
TARGET = FOLD.test_group_ids[0]
CONFIG = SpatialConfig(100, 0.1, "support:fixed")
CONTEXT = ForwardInputs(
    ("a", "b"),
    (0.1, 0.1),
    ((1.0, 1.0),),
    (1.0,),
    (1.0, 1.0),
    ("regional",),
    ("parameters",),
    ("geometry",),
    "time",
    "controlled",
    "build:controlled",
)


@dataclass(frozen=True)
class ForwardResult:
    pollen_fraction: tuple[float, ...]
    method_profile: str = "controlled"


def atom(name: str, weight: Fraction, first: float) -> JointSpatialDraw:
    return JointSpatialDraw(
        name,
        weight,
        "a" * 64,
        tuple(
            sorted(
                (
                    (G1, (("a", first), ("b", 1 - first))),
                    (G2, (("a", 1 - first), ("b", first))),
                )
            )
        ),
        tuple(sorted(((G1, SiteCoordinate(0, 0)), (G2, SiteCoordinate(0, 1))))),
        CONTEXT,
        ("r1", "r2"),
        (
            ("geometry", ()),
            ("parameters", ()),
            ("r1", ()),
            ("r2", ()),
            ("regional", ("r1", "r2")),
            ("time", ()),
        ),
        ("geometry", "parameters", "regional", "time"),
    )


def arguments(
    draws: tuple[JointSpatialDraw | UnavailableSpatialDraw, ...],
) -> dict[str, Any]:
    return {
        "support_id": CONFIG.support_id,
        "temporal_support_id": "time",
        "site_records": RECORDS,
        "config": CONFIG,
        "predictor_group_ids": GROUPS,
        "draw_ids": tuple(d.draw_id for d in draws),
        "draws": draws,
        "law_evidence_sha256": "b" * 64,
        "upstream_sources": ("local_reconstruction",),
        "omitted_sources": tuple(
            sorted((UPSTREAM_SOURCES | CONDITIONED_SOURCES) - {"local_reconstruction"})
        ),
        "forward_model": lambda cover, *rest: ForwardResult(cover),
    }


def run(
    draws: tuple[JointSpatialDraw | UnavailableSpatialDraw, ...], **changes: Any
) -> dict[str, Any]:
    kwargs = arguments(draws)
    kwargs.update(changes)
    return propagate_withheld_spatial_draws(
        FOLD, TARGET, SiteCoordinate(0, 0), **kwargs
    )


def test_refit_each_joint_atom_and_reuse_exact_finite_law_moments() -> None:
    draws = (atom("d1", Fraction(1, 4), 0.8), atom("d2", Fraction(3, 4), 0.6))
    result = run(draws)
    rows = result["rows"]
    assert result["summary"]["complete"] is True
    assert rows[0]["model_sha256"] != rows[1]["model_sha256"]
    assert all(
        row["spatial_fit_attempted"] and row["forward_attempted"] for row in rows
    )
    vectors = [row["values"] for row in rows]
    expected = [0.25 * a + 0.75 * b for a, b in zip(*vectors, strict=True)]
    assert result["summary"]["mean"] == pytest.approx(expected)
    expected_cov = [
        [
            0.25 * (vectors[0][i] - expected[i]) * (vectors[0][j] - expected[j])
            + 0.75 * (vectors[1][i] - expected[i]) * (vectors[1][j] - expected[j])
            for j in range(4)
        ]
        for i in range(4)
    ]
    for actual, expected_row in zip(
        result["summary"]["population_covariance"], expected_cov, strict=True
    ):
        assert actual == pytest.approx(expected_row)
    assert result["summary"]["intervals"] is None
    assert (
        result["law_authenticity_verified"] is False
        and result["outcome_accesses"] == []
    )
    assert json.loads(result["canonical_result_json"])["draw_ids"] == ["d1", "d2"]


def test_failed_mass_is_not_renormalized() -> None:
    draws = (atom("d1", Fraction(1, 4), 0), atom("d2", Fraction(3, 4), 0.6))
    result = run(draws)
    assert [row["status"] for row in result["rows"]] == ["refused", "success"]
    assert result["rows"][0]["reason_code"] == "spatial_zero_composition_unsupported"
    assert result["rows"][0]["forward_attempted"] is False
    assert result["summary"]["failed_mass"] == {"numerator": 1, "denominator": 4}
    assert (
        result["summary"]["mean"] is None
        and result["summary"]["population_covariance"] is None
    )


def test_known_forward_failure_retains_all_draws_but_unknown_failure_is_fatal() -> None:
    draws = (atom("d1", Fraction(1, 2), 0.8), atom("d2", Fraction(1, 2), 0.6))

    def refuse(*args: Any) -> ForwardResult:
        raise ValidationRefusal("forward_model_refused", "Controlled zero forward mass")

    result = run(draws, forward_model=refuse)
    assert [row["reason_code"] for row in result["rows"]] == [
        "forward_model_refused"
    ] * 2
    assert result["summary"]["successful_mass"] == {"numerator": 0, "denominator": 1}

    def broken(*args: Any) -> ForwardResult:
        raise RuntimeError("Infrastructure failure")

    with pytest.raises(RuntimeError, match="Infrastructure"):
        run(draws, forward_model=broken)

    def unknown_typed(*args: Any) -> ForwardResult:
        raise ValidationRefusal("unqualified_engine_state", "Unknown typed refusal")

    with pytest.raises(ValidationRefusal, match="Unknown typed") as unknown:
        run(draws, forward_model=unknown_typed)
    assert unknown.value.reason_code == "unqualified_engine_state"

    def unavailable(*args: Any) -> ForwardResult:
        raise LRARefusal(
            "lra_extension_missing", "Missing engine", diagnostics={"ready": False}
        )

    with pytest.raises(LRARefusal) as unavailable_error:
        run(draws, forward_model=unavailable)
    assert unavailable_error.value.reason_code == "lra_extension_missing"
    assert unavailable_error.value.diagnostics == {"ready": False}

    def numerical(*args: Any) -> ForwardResult:
        raise LRARefusal(
            "no_valid_local_rings", "No accepted ring", diagnostics={"finite_rings": 0}
        )

    numerical_rows = run(draws, forward_model=numerical)["rows"]
    assert all(row["reason_code"] == "no_valid_local_rings" for row in numerical_rows)
    assert all(
        row["error"]["diagnostics"] == {"finite_rings": 0} for row in numerical_rows
    )

    def untyped(*args: Any) -> ForwardResult:
        raise ValueError("Unclassified implementation failure")

    with pytest.raises(ValueError, match="Unclassified") as untyped_error:
        run(draws, forward_model=untyped)
    assert type(untyped_error.value) is ValueError


@pytest.mark.parametrize(
    "mode",
    [
        "draw-order",
        "missing-draw",
        "duplicate-draw",
        "mass",
        "taxa",
        "rings",
        "coordinate-axis",
        "target-direct",
        "target-indirect",
        "target-alias",
        "target-chronology",
        "split-alias",
        "unsupported-scope",
        "support",
        "profile",
    ],
)
def test_complete_axis_and_ancestry_preflight_before_first_fit(
    mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = atom("d1", Fraction(1, 2), 0.8), atom("d2", Fraction(1, 2), 0.6)
    kwargs = arguments((first, second))
    if mode == "draw-order":
        kwargs["draws"] = (second, first)
    elif mode == "missing-draw":
        kwargs["draws"] = (first,)
    elif mode == "duplicate-draw":
        kwargs["draws"] = (first, first)
    elif mode == "mass":
        kwargs["draws"] = (first, replace(second, mass=Fraction(1, 3)))
    elif mode == "taxa":
        kwargs["draws"] = (
            first,
            replace(
                second,
                forward=replace(CONTEXT, taxa=("b", "a")),
                compositions=tuple(
                    (key, tuple(reversed(values)))
                    for key, values in second.compositions
                ),
            ),
        )
    elif mode == "rings":
        kwargs["draws"] = (
            first,
            replace(second, forward=replace(CONTEXT, local_k=((1.0,),))),
        )
    elif mode == "coordinate-axis":
        kwargs["draws"] = (
            first,
            replace(second, coordinates=((G1, SiteCoordinate(0, 0)),)),
        )
    elif mode == "target-direct":
        kwargs["draws"] = (
            first,
            replace(
                second,
                input_ids=("r1", "r2", "p10"),
                input_lineage=tuple(sorted((*second.input_lineage, ("p10", ())))),
            ),
        )
    elif mode == "target-indirect":
        kwargs["draws"] = (
            first,
            replace(
                second,
                input_lineage=tuple(
                    (key, ("p10",) if key == "regional" else deps)
                    for key, deps in second.input_lineage
                ),
            ),
        )
    elif mode == "target-alias":
        kwargs["draws"] = (
            first,
            replace(
                second,
                input_ids=("r1", "r2", "p10-alias"),
                input_lineage=tuple(sorted((*second.input_lineage, ("p10-alias", ())))),
                admitted_external_ids=(*second.admitted_external_ids, "p10-alias"),
            ),
        )
    elif mode == "target-chronology":
        kwargs["draws"] = (
            first,
            replace(
                second,
                input_ids=(*second.input_ids, "chronology:target"),
                input_lineage=tuple(
                    sorted(
                        (*second.input_lineage, ("chronology:target", ("p10-alias",)))
                    )
                ),
                admitted_external_ids=(
                    *second.admitted_external_ids,
                    "chronology:target",
                ),
            ),
        )
    elif mode == "split-alias":
        kwargs["site_records"] = tuple(
            replace(row, identity_keys=()) for row in RECORDS
        )
    elif mode == "unsupported-scope":
        kwargs["upstream_sources"] = ("spatial_residual_process",)
    elif mode == "support":
        kwargs["support_id"] = "wrong"
    else:
        kwargs["draws"] = (
            first,
            replace(second, forward=replace(CONTEXT, method_profile="other")),
        )

    def forbidden(*args: Any, **changes: Any) -> Any:
        pytest.fail(
            "No training fit may precede complete population and ancestry validation"
        )

    monkeypatch.setattr(workflow, "fit_spatial_model", forbidden)
    with pytest.raises(ValidationRefusal):
        propagate_withheld_spatial_draws(FOLD, TARGET, SiteCoordinate(0, 0), **kwargs)


def test_forward_draws_remain_coupled_to_their_training_draws() -> None:
    first, second = atom("d1", Fraction(1, 2), 0.8), atom("d2", Fraction(1, 2), 0.6)
    second = replace(
        second,
        forward=replace(
            CONTEXT, ppe=(2.0, 1.0), parameter_input_ids=("parameters:d2",)
        ),
        input_lineage=tuple(
            sorted(
                ("parameters:d2" if key == "parameters" else key, deps)
                for key, deps in second.input_lineage
            )
        ),
        admitted_external_ids=tuple(
            "parameters:d2" if value == "parameters" else value
            for value in second.admitted_external_ids
        ),
    )
    calls = []

    def coupled(
        cover: tuple[float, ...],
        regional: tuple[float, ...],
        kernel: tuple[tuple[float, ...], ...],
        terrestrial: tuple[float, ...],
        ppe: tuple[float, ...],
    ) -> ForwardResult:
        calls.append((cover, ppe))
        masses = tuple(x * p for x, p in zip(cover, ppe, strict=True))
        return ForwardResult(tuple(x / sum(masses) for x in masses))

    result = run(
        (first, second),
        forward_model=coupled,
        upstream_sources=("local_reconstruction", "ppe"),
        omitted_sources=tuple(
            sorted(
                (UPSTREAM_SOURCES | CONDITIONED_SOURCES)
                - {"local_reconstruction", "ppe"}
            )
        ),
    )
    assert [ppe for _, ppe in calls] == [(1.0, 1.0), (2.0, 1.0)]
    for row, (cover, ppe) in zip(result["rows"], calls, strict=True):
        expected = (
            cover[0] * ppe[0] / sum(x * p for x, p in zip(cover, ppe, strict=True))
        )
        assert row["values"][2] == pytest.approx(expected)
    with pytest.raises(ValidationRefusal, match="contradictory"):
        run(
            (
                first,
                replace(
                    second,
                    forward=replace(
                        second.forward, parameter_input_ids=("parameters",)
                    ),
                ),
            )
        )
