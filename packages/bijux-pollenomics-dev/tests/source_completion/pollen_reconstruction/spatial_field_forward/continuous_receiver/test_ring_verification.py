"""Literal survival-ring and composition controls, independent of the producer."""

from copy import deepcopy
from fractions import Fraction as Q
from itertools import combinations
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    rings as ring_oracle,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    Clock,
    VerificationError,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.geometry import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.ring_predictions import (
    METRICS,
    audit,
    average_ranges,
    normalized_deposition,
    score_ranges,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.rings import (
    CONTRIBUTION_STOP,
    Q_UNCERTAINTY_TARGET,
    coefficient_q_spreads,
    constrain_survival,
    ring_coefficients,
    ring_linear_bounds,
    telescope,
    verify_ring_case,
    width_account,
)

from .test_ring_sources import source_fixture


def symmetric_geometry() -> Geometry:
    return Geometry(Q(3, 5), Q(1), Q(4), (Q(3), Q(1)), (Q(-3), Q(-1)))


def test_telescoping_preserves_shared_middle_endpoint() -> None:
    q = (Interval(Q(7, 8), Q(1)), Interval(Q(1, 4), Q(3, 4)), Interval(Q(0), Q(1, 8)))
    # Equal adjacent weights cancel the uncertain middle endpoint completely.
    actual = telescope(q, (Q(1, 2), Q(1, 2)))
    assert actual == Interval(Q(3, 8), Q(1, 2))
    independent_mass_differences = (q[0] - q[1] + q[1] - q[2]) / 2
    assert independent_mass_differences.width > actual.width


def test_telescoping_negative_weights_and_signs() -> None:
    q = (
        Interval(Q(3, 4), Q(7, 8)),
        Interval(Q(1, 4), Q(1, 2)),
        Interval(Q(0), Q(1, 8)),
    )
    # -2*(Q0-Q1)+3*(Q1-Q2) = -2*Q0+5*Q1-3*Q2.
    assert telescope(q, (Q(-2), Q(3))) == Interval(Q(-7, 8), Q(1))


def test_survival_constraints_use_entire_chain() -> None:
    values = (
        Interval(Q(-1), Q(3, 4)),
        Interval(Q(1, 4), Q(2)),
        Interval(Q(1, 2), Q(5, 8)),
    )
    assert constrain_survival(values) == (
        Interval(Q(1, 2), Q(3, 4)),
        Interval(Q(1, 2), Q(3, 4)),
        Interval(Q(1, 2), Q(5, 8)),
    )


def test_contribution_forms_cancel_irrelevant_interior_survival_width() -> None:
    survival = (
        Interval.point(Q(3, 4)),
        Interval(Q(1, 4), Q(3, 4)),
        Interval.point(Q(1, 4)),
    )
    actual = coefficient_q_spreads(symmetric_geometry(), (Q(1), Q(2), Q(4)), survival)
    assert actual == {
        key: Q(0) for key in ("K", "B1_lower", "B1_upper", "B2_lower", "B2_upper")
    }
    assert survival[1].width == Q(1, 2) > Q_UNCERTAINTY_TARGET


def test_exact_five_form_spreads_use_signed_complement_coefficients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geometry = Geometry(Q(3, 5), Q(1), Q(4), (Q(1), Q(0)), (Q(3), Q(0)))
    means = {
        Q(1): Interval.point(Q(3, 4)),
        Q(2): Interval.point(Q(1, 2)),
        Q(4): Interval.point(Q(1, 4)),
    }
    monkeypatch.setattr(Geometry, "mean", lambda _, radius: means[radius])
    survival = (
        Interval(Q(7, 8), Q(1)),
        Interval(Q(3, 8), Q(5, 8)),
        Interval(Q(0), Q(1, 4)),
    )
    # k=(1,0,-1), l=(1/2,-1/4,-1/4), u=(3/4,-1/4,-1/2).
    # The complementary forms are k-u and k-l, not interval differences.
    assert coefficient_q_spreads(geometry, (Q(1), Q(2), Q(4)), survival) == {
        "K": Q(3, 8),
        "B1_lower": Q(3, 16),
        "B1_upper": Q(9, 32),
        "B2_lower": Q(7, 32),
        "B2_upper": Q(5, 16),
    }


@pytest.mark.parametrize(
    "values",
    [
        (Interval.point(Q(1, 2)),),
        (Interval.point(Q(1, 2)), Interval.point(Q(1, 2))),
        (Interval.point(Q(1, 4)), Interval.point(Q(1, 2))),
    ],
)
def test_missing_or_impossible_survival_chain_refuses(
    values: tuple[Interval, ...],
) -> None:
    with pytest.raises((VerificationError, ValueError)):
        constrain_survival(values)


def test_symmetric_anchor_complement_and_affine_deposition() -> None:
    geometry = symmetric_geometry()
    edges = (Q(1), Q(2), Q(4))
    q = (Interval.point(Q(7, 8)), Interval.point(Q(1, 2)), Interval.point(Q(1, 8)))
    coefficients = ring_coefficients(geometry, edges, q)
    assert coefficients == {
        "K": Interval.point(Q(3, 4)),
        "B1": Interval.point(Q(3, 8)),
        "B2": Interval.point(Q(3, 8)),
    }
    # h=1/2 identically, so any two cover values reduce to their exact average.
    assert ring_linear_bounds(geometry, edges, q, Q(1, 8), Q(7, 8)) == Interval.point(
        Q(3, 8)
    )
    assert ring_linear_bounds(geometry, edges, q, Q(7, 8), Q(1, 8)) == Interval.point(
        Q(3, 8)
    )
    assert width_account(coefficients)["all_original_epsilon_widths_pass"] is True


def test_wide_valid_ring_interval_does_not_pass_original_epsilon() -> None:
    geometry = symmetric_geometry()
    result = ring_coefficients(
        geometry,
        (Q(1), Q(4)),
        (Interval(Q(3, 4), Q(7, 8)), Interval(Q(0), Q(1, 8))),
    )
    assert result["K"] == Interval(Q(5, 8), Q(7, 8))
    assert width_account(result)["all_original_epsilon_widths_pass"] is False
    assert width_account(result)["positive_lower_bounds"] is True


@pytest.mark.parametrize("edges", [(Q(1), Q(2)), (Q(1), Q(4), Q(2)), (Q(0), Q(4))])
def test_foreign_incomplete_or_reordered_edges_refuse(edges: tuple[Q, ...]) -> None:
    with pytest.raises(VerificationError):
        ring_coefficients(
            symmetric_geometry(),
            edges,
            (Interval.point(Q(3, 4)), Interval.point(Q(1, 4))),
        )


def test_unequal_anchor_ring_envelope_contains_endpoint_weight_extrema() -> None:
    geometry = Geometry(Q(3, 5), Q(1), Q(4), (Q(1), Q(2)), (Q(-7), Q(3)))
    q = (Interval.point(Q(3, 4)), Interval.point(Q(1, 4)))
    first = ring_coefficients(geometry, (Q(1), Q(4)), q)["B1"]
    left, right = geometry.mean(Q(1)), geometry.mean(Q(4))
    assert left.lower > right.upper
    assert first.lower <= right.lower / 2
    assert first.upper >= left.upper / 2


def test_normalization_uses_monotone_ratio_not_sum_of_independent_intervals() -> None:
    assert normalized_deposition(
        (Interval(Q(1), Q(2)), Interval(Q(2), Q(4)))
    ) == Interval(Q(1, 5), Q(1, 2))
    with pytest.raises(VerificationError, match="Positive"):
        normalized_deposition((Interval(Q(0), Q(2)), Interval(Q(0), Q(4))))


def test_two_component_metric_extrema_keep_nonclosed_observation() -> None:
    observed = (Q(1, 4), Q(1, 2))
    result = score_ranges(Interval(Q(0), Q(1)), observed)
    assert result[METRICS[0]] == result[METRICS[1]] == Interval(Q(1, 8), Q(5, 8))
    # The nonclosed observation cannot have zero Hellinger distance to a closed p.
    assert result[METRICS[2]].lower > 0
    assert result[METRICS[2]].upper <= 1


def test_hellinger_constructive_roots_include_exact_match() -> None:
    ranges = score_ranges(Interval.point(Q(1, 4)), (Q(1, 4), Q(3, 4)))
    assert ranges[METRICS[0]] == Interval.point(Q(0))
    assert ranges[METRICS[2]].lower == 0
    # Squaring rounds to 2^-96 before the final root, hence 2^-48 granularity.
    assert ranges[METRICS[2]].upper <= Q(1, 2**48)


def test_aggregation_keeps_all_metrics_and_exact_equal_weights() -> None:
    rows = [
        {key: Interval.point(value) for key in METRICS} for value in (Q(1, 4), Q(3, 4))
    ]
    assert average_ranges(rows) == {key: Interval.point(Q(1, 2)) for key in METRICS}
    with pytest.raises(VerificationError):
        average_ranges([])
    with pytest.raises(VerificationError):
        average_ranges([{"total_variation": Interval.point(Q(0))}])


def literal_case() -> dict[str, Any]:
    endpoints = []
    for value in (Q(1, 2), Q(1, 4), Q(1, 8)):
        interval = [str(value), str(value)]
        endpoints.append(
            {
                "bounds": interval,
                "status": "certified_width",
                "refusal": None,
                "quadrature_rule": "closed-newton-cotes-seven.v1",
                "leaves": [
                    {
                        "box": [["0", "1"]],
                        "node_sum": interval,
                        "error_radius": "0",
                        "directional_radii": ["0"],
                        "quadrature_rule": "closed-newton-cotes-seven.v1",
                    }
                ],
            }
        )
    return {
        "case_index": 0,
        "core": "BOKE",
        "taxon": "Betula",
        "geometry": symmetric_geometry().encoded(),
        "edges_exact": ["1", "2", "4"],
        "endpoints": endpoints,
        "endpoint_refusals": [None, None, None],
        "backend_refusal": None,
        "coefficient_bounds": {
            "K": ["3/8", "3/8"],
            "B1": ["3/16", "3/16"],
            "B2": ["3/16", "3/16"],
        },
        "raw_endpoint_widths_pass": True,
        "all_final_widths_pass": True,
        "positive_bounds_usable": True,
        "work": {
            "attempted_panels": 3,
            "reserved_node_evaluations": 21,
            "completed_node_evaluations": 21,
            "derivative_boxes": 3,
            "leaf_reservations": 3,
        },
    }


def polynomial_endpoint(self: Geometry, index: int) -> Any:
    # A constant analytic witness isolates coverage/Peano/accounting contracts;
    # it is not asserted to equal a physical disk survival function.
    value = Q(1, 2) if index == 0 else 1 / (2 * self.outer)
    return lambda arguments: Jet.constant(value, arguments[0].order)


def contribution_case() -> dict[str, Any]:
    value = literal_case()
    value["q_uncertainty_spreads_exact"] = dict.fromkeys(
        ("K", "B1_lower", "B1_upper", "B2_lower", "B2_upper"), "0"
    )
    value["q_uncertainty_target_pass"] = True
    endpoint = value["endpoints"][1]
    error = Q(1, 2**32)
    endpoint["leaves"][0].update(
        error_radius=str(error), directional_radii=[str(error)]
    )
    endpoint.update(
        bounds=[str(Q(1, 4) - error), str(Q(1, 4) + error)],
        status="refuse_unresolved",
        refusal=CONTRIBUTION_STOP,
    )
    value["endpoint_refusals"][1] = CONTRIBUTION_STOP
    value["backend_refusal"] = CONTRIBUTION_STOP
    value["raw_endpoint_widths_pass"] = False
    return value


def test_wide_auxiliary_endpoint_retains_explicit_contribution_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = contribution_case()
    result = verify_ring_case(
        value,
        symmetric_geometry(),
        (Q(1), Q(2), Q(4)),
        Clock(seconds=5),
        contribution=True,
    )
    assert result["complete"] is True
    assert result["q_uncertainty_target_pass"] is True
    assert value["raw_endpoint_widths_pass"] is False
    with pytest.raises(VerificationError, match="Undeclared"):
        verify_ring_case(
            value, symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "flag",
        "negative",
        "numeric",
        "forms",
        "backend",
        "endpoint",
        "condition",
    ],
)
def test_contribution_metadata_or_stop_reason_drift_refuses(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = contribution_case()
    if mutation == "missing":
        del value["q_uncertainty_spreads_exact"]
    elif mutation == "flag":
        value["q_uncertainty_target_pass"] = False
    elif mutation == "negative":
        value["q_uncertainty_spreads_exact"]["K"] = "-1"
    elif mutation == "numeric":
        value["q_uncertainty_spreads_exact"]["K"] = 0.0
    elif mutation == "forms":
        value["q_uncertainty_spreads_exact"]["B2"] = "0"
    elif mutation == "backend":
        value["backend_refusal"] = "wall_seconds"
    elif mutation == "endpoint":
        value["endpoint_refusals"][1] = value["endpoints"][1]["refusal"] = (
            "wall_seconds"
        )
    else:
        value["q_uncertainty_spreads_exact"]["K"] = "1"
        value["q_uncertainty_target_pass"] = False
    with pytest.raises(VerificationError):
        verify_ring_case(
            value,
            symmetric_geometry(),
            (Q(1), Q(2), Q(4)),
            Clock(seconds=5),
            contribution=True,
        )


def test_incomplete_contribution_case_keeps_null_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = literal_case()
    value.update(
        q_uncertainty_spreads_exact=None,
        q_uncertainty_target_pass=False,
        coefficient_bounds=None,
        raw_endpoint_widths_pass=False,
        all_final_widths_pass=False,
        positive_bounds_usable=False,
        backend_refusal="incomplete_endpoint_population:wall_seconds",
    )
    value["endpoints"][1] = None
    value["endpoint_refusals"][1] = "not_executed:wall_seconds"
    result = verify_ring_case(
        value,
        symmetric_geometry(),
        (Q(1), Q(2), Q(4)),
        Clock(seconds=5),
        contribution=True,
    )
    assert result["q_uncertainty_spreads_exact"] is None
    assert result["q_uncertainty_target_pass"] is False
    value["q_uncertainty_target_pass"] = True
    with pytest.raises(VerificationError, match="Incomplete"):
        verify_ring_case(
            value,
            symmetric_geometry(),
            (Q(1), Q(2), Q(4)),
            Clock(seconds=5),
            contribution=True,
        )


def test_literal_closed_endpoint_partition_and_complement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    result = verify_ring_case(
        literal_case(), symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
    )
    assert result["complete"] is True
    assert result["own_coefficients"] == {
        "K": Interval.point(Q(3, 8)),
        "B1": Interval.point(Q(3, 16)),
        "B2": Interval.point(Q(3, 16)),
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_partition",
        "duplicate_leaf",
        "negative_radius",
        "unknown_rule",
        "derivative_reset",
        "changed_edge",
        "false_width",
        "disjoint_coefficient",
    ],
)
def test_damaged_closed_ring_certificate_refuses(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = literal_case()
    leaf = value["endpoints"][0]["leaves"][0]
    if mutation == "missing_partition":
        leaf["box"] = [["0", "1/2"]]
    elif mutation == "duplicate_leaf":
        value["endpoints"][0]["leaves"].append(deepcopy(leaf))
    elif mutation == "negative_radius":
        leaf["error_radius"] = "-1"
    elif mutation == "unknown_rule":
        leaf["quadrature_rule"] = "unreviewed-rule"
    elif mutation == "derivative_reset":
        value["work"]["derivative_boxes"] = 0
    elif mutation == "changed_edge":
        value["edges_exact"][1] = "3"
    elif mutation == "false_width":
        value["all_final_widths_pass"] = False
    else:
        value["coefficient_bounds"]["B1"] = ["1", "1"]
    with pytest.raises(VerificationError):
        verify_ring_case(
            value, symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
        )


def test_unexecuted_endpoint_cannot_become_a_complete_coefficient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = literal_case()
    value.update(
        coefficient_bounds=None,
        raw_endpoint_widths_pass=False,
        all_final_widths_pass=False,
        positive_bounds_usable=False,
        backend_refusal="incomplete_endpoint_population:wall_seconds",
    )
    value["endpoints"][1] = None
    value["endpoint_refusals"][1] = "not_executed:wall_seconds"
    result = verify_ring_case(
        value, symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
    )
    assert result["complete"] is False
    assert result["own_coefficients"] is None


def test_last_leaf_reservation_before_panel_refusal_remains_charged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", polynomial_endpoint)
    value = literal_case()
    value.update(
        coefficient_bounds=None,
        raw_endpoint_widths_pass=False,
        all_final_widths_pass=False,
        positive_bounds_usable=False,
        backend_refusal="incomplete_endpoint_population:attempt_or_node_ceiling",
    )
    value["endpoints"][1:] = [None, None]
    value["endpoint_refusals"][1:] = [
        "attempt_or_node_ceiling",
        "not_executed:attempt_or_node_ceiling",
    ]
    value["work"] = {
        "attempted_panels": 1,
        "reserved_node_evaluations": 7,
        "completed_node_evaluations": 7,
        "derivative_boxes": 1,
        "leaf_reservations": 2,
    }
    result = verify_ring_case(
        value, symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
    )
    assert result["complete"] is False
    value["work"]["leaf_reservations"] = 3
    with pytest.raises(VerificationError, match="underreported"):
        verify_ring_case(
            value, symmetric_geometry(), (Q(1), Q(2), Q(4)), Clock(seconds=5)
        )


def packet_fixture() -> dict[str, Any]:
    protocol, public, original, capture_freeze, prediction = source_fixture()
    families = (
        "direct_pollen_idw",
        "centre_cover_idw_forward",
        "spatial_cover_idw_forward",
    )
    cores = ("BOKE", "BUS", "SOLSOE83")
    prediction.update(source_commit="b" * 40, ppe=[1.0, 2.0], contexts=[])
    saved_hellinger = math.sqrt(
        ((math.sqrt(0.5) - 0.5) ** 2 + (math.sqrt(0.5) - math.sqrt(0.75)) ** 2) / 2
    )
    legacy = dict(zip(METRICS, (0.25, 0.25, saved_hellinger), strict=True))
    old: dict[str, Any] = {
        "source_commit": "b" * 40,
        "scores": [],
        "summaries": {
            "families": [
                {"family": f, "equal_place": {"metrics": legacy}} for f in families
            ],
            "pairwise": [
                {
                    "first_family": a,
                    "second_family": b,
                    "metrics": {m: {"point_difference": 0.0} for m in METRICS},
                }
                for a, b in combinations(families, 2)
            ],
        },
    }
    proof: dict[str, Any] = {
        "schema_version": "continuous-receiver-ring-certificates.v1",
        "cases": [],
    }
    mass = Q(255, 512)
    for i, ((core, taxon), captured) in enumerate(
        zip(
            ((c, t) for c in cores for t in ("Betula", "Ulmus")),
            capture_freeze["cases"],
            strict=True,
        )
    ):
        endpoints = []
        for text in protocol["edges_exact"][core]:
            q = 1 - Q(text) / 512
            endpoints.append(
                {
                    "bounds": [str(q), str(q)],
                    "status": "certified_width",
                    "refusal": None,
                    "quadrature_rule": "closed-newton-cotes-seven.v1",
                    "leaves": [
                        {
                            "box": [["0", "1"]],
                            "node_sum": [str(q), str(q)],
                            "error_radius": "0",
                            "directional_radii": ["0"],
                            "quadrature_rule": "closed-newton-cotes-seven.v1",
                        }
                    ],
                }
            )
        proof["cases"].append(
            {
                "case_index": i,
                "core": core,
                "taxon": taxon,
                "geometry": captured["geometry"],
                "edges_exact": protocol["edges_exact"][core],
                "endpoints": endpoints,
                "endpoint_refusals": [None] * 129,
                "backend_refusal": None,
                "coefficient_bounds": {
                    "K": [str(mass), str(mass)],
                    "B1": [str(mass / 2), str(mass / 2)],
                    "B2": [str(mass / 2), str(mass / 2)],
                },
                "raw_endpoint_widths_pass": True,
                "all_final_widths_pass": True,
                "positive_bounds_usable": True,
                "work": {
                    "attempted_panels": 129,
                    "reserved_node_evaluations": 903,
                    "completed_node_evaluations": 903,
                    "derivative_boxes": 129,
                    "leaf_reservations": 129,
                },
            }
        )
    packet: dict[str, Any] = {
        "schema_version": "continuous-receiver-ring-predictions.v1",
        "source_commit": "c" * 40,
        "source_prediction_commit": "b" * 40,
        "contexts": [],
    }
    scores = []
    native_ranges = {
        METRICS[0]: ["3/28", "3/28"],
        METRICS[1]: ["3/28", "3/28"],
        METRICS[2]: ["0", "1"],
    }
    for index, core in enumerate(cores):
        for j, start in enumerate(range(2700, 5700, 500)):
            window = [start, start + 500]
            owners = [
                {
                    "core": c,
                    "site_id": 10 + k,
                    "dataset_id": 100 + k,
                    "collection_unit_id": 1000 + k,
                    "window": window,
                    "sample_ids": [10000 + j * 10 + k],
                }
                for k, c in enumerate(cores)
            ]
            target = {**owners[index], "radius_m": 1.0}
            training = [
                {**owners[k], "radius_m": 1.0, "cover": [0.25, 0.75]}
                for k in range(3)
                if k != index
            ]
            key = f"{core}:{start}"
            prediction["contexts"].append(
                {
                    "context_id": key,
                    "geometry_core": core,
                    "target": target,
                    "training": training,
                    "families": {
                        f: {"status": "predicted", "pollen_fraction": [0.5, 0.5]}
                        for f in families
                    },
                }
            )
            direct = {
                "status": "fixed_saved_point_reference",
                "prediction_bounds_exact": [["1/2", "1/2"], ["1/2", "1/2"]],
                "deposition_bounds_exact": None,
                "coefficient_precision_pass": None,
                "refusal": None,
            }
            physical = {
                "status": "continuous_law_enclosure",
                "prediction_bounds_exact": [["1/7", "1/7"], ["6/7", "6/7"]],
                "deposition_bounds_exact": [
                    [str(mass / 4), str(mass / 4)],
                    [str(mass * Q(3, 2)), str(mass * Q(3, 2))],
                ],
                "coefficient_precision_pass": True,
                "refusal": None,
            }
            packet["contexts"].append(
                {
                    "context_id": key,
                    "core": core,
                    "window": window,
                    "sample_ids": target["sample_ids"],
                    "target_owner": owners[index],
                    "training_owners": [owners[k] for k in range(3) if k != index],
                    "geometry_refusals": [
                        {"taxon": t, "refusal": None} for t in ("Betula", "Ulmus")
                    ],
                    "families": {
                        families[0]: direct,
                        families[1]: deepcopy(physical),
                        families[2]: deepcopy(physical),
                    },
                }
            )
            for family in families:
                old["scores"].append(
                    {
                        "context_id": key,
                        "core": core,
                        "window": window,
                        "sample_ids": target["sample_ids"],
                        "family": family,
                        "observed_fraction": [0.25, 0.75],
                        "predicted_fraction": [0.5, 0.5],
                        "status": "scored",
                        **legacy,
                    }
                )
                ranges = (
                    {m: [str(Q(v)), str(Q(v))] for m, v in legacy.items()}
                    if family == families[0]
                    else native_ranges
                )
                scores.append(
                    {
                        "context_id": key,
                        "core": core,
                        "window": window,
                        "sample_ids": target["sample_ids"],
                        "family": family,
                        "observed_fraction": [0.25, 0.75],
                        "legacy_point_score": legacy,
                        "status": "fixed_saved_point_reference"
                        if family == families[0]
                        else "continuous_law_enclosure",
                        "conditional_metric_ranges_exact": deepcopy(ranges),
                    }
                )
    summaries = []
    for family in families:
        ranges = (
            {m: [str(Q(v)), str(Q(v))] for m, v in legacy.items()}
            if family == families[0]
            else native_ranges
        )
        summaries.append(
            {
                "family": family,
                "status": "fixed_saved_point_reference"
                if family == families[0]
                else "continuous_law_enclosure",
                "legacy_point_metrics": legacy,
                "places": [
                    {"core": c, "conditional_metric_ranges_exact": ranges}
                    for c in cores
                ],
                "equal_place": {
                    "conditional_metric_ranges_exact": ranges,
                    "legacy_point_metrics": legacy,
                },
            }
        )
    pairs = []
    for first, second in combinations(families, 2):
        metrics = {}
        for metric in METRICS:
            if first == families[0]:
                lower, upper = (
                    (Q(1, 7), Q(1, 7))
                    if metric != METRICS[2]
                    else (Q(saved_hellinger) - 1, Q(saved_hellinger))
                )
            else:
                lower, upper = (Q(0), Q(0)) if metric != METRICS[2] else (Q(-1), Q(1))
            metrics[metric] = {
                "conditional_difference_range_exact": [str(lower), str(upper)],
                "legacy_point_difference": 0.0,
                "conditional_resolution": "unresolved_continuous_law"
                if lower <= 0 <= upper
                else "separated_continuous_law",
            }
        pairs.append(
            {
                "first_family": first,
                "second_family": second,
                "status": "continuous_law_enclosure",
                "metrics": metrics,
            }
        )
    result = {
        "schema_version": "continuous-receiver-ring-result.v1",
        "source_commit": "c" * 40,
        "source_guards_pass": True,
        "resource_guards_pass": True,
        "elapsed_seconds": 1.0,
        "integration_elapsed_seconds": 0.5,
        "peak_rss_bytes": 1_000_000,
        "status": "continuous_law_bounds",
        "all_endpoint_partitions_complete": True,
        "all_774_raw_endpoint_widths_pass": True,
        "all_18_coefficient_widths_pass": True,
        "counts": {
            "cases": 6,
            "endpoint_slots": 774,
            "contexts": 18,
            "family_slots": 54,
        },
        "scores": scores,
        "summary": {"families": summaries, "pairwise": pairs},
    }
    return {
        "protocol": protocol,
        "public_source": public,
        "original_protocol": original,
        "capture_freeze": capture_freeze,
        "original_prediction": prediction,
        "original_scored": old,
        "certificates": proof,
        "prediction_packet": packet,
        "result": result,
    }


def packet_endpoint(self: Geometry, index: int) -> Any:
    value = 1 - (self.receiver if index == 0 else self.outer) / 512
    return lambda arguments: Jet.constant(value, arguments[0].order)


def test_complete_literal_18_context_54_score_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", packet_endpoint)
    checked = audit(**packet_fixture(), clock=Clock(seconds=30))
    assert checked["status"] == "passed"
    assert checked["accounting_verified"] is True
    assert checked["complete_cases"] == 6
    assert checked["usable_prediction_contexts"] == 18
    assert "own_all_case_q_uncertainty_targets_pass" not in checked
    assert len(checked["contexts"]) == 18 and len(checked["scores"]) == 54
    assert (
        checked["summary"]["pairwise"][2]["metrics"][METRICS[0]][
            "conditional_resolution"
        ]
        == "unresolved_continuous_law"
    )


def test_independent_contribution_flag_is_diagnostic_for_valid_full_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", packet_endpoint)
    packet = packet_fixture()
    packet["protocol"]["frontier"] = {
        "priority": "coefficient_contribution",
        "q_uncertainty_full_width_exact": "1/16000000000",
    }
    forms = ("K", "B1_lower", "B1_upper", "B2_lower", "B2_upper")
    for case in packet["certificates"]["cases"]:
        case.update(
            q_uncertainty_spreads_exact=dict.fromkeys(forms, "0"),
            q_uncertainty_target_pass=True,
            raw_endpoint_widths_pass=False,
            backend_refusal=CONTRIBUTION_STOP,
        )
        endpoint = case["endpoints"][1]
        midpoint = Q(endpoint["bounds"][0])
        error = Q(1, 2**32)
        endpoint["leaves"][0].update(
            error_radius=str(error), directional_radii=[str(error)]
        )
        endpoint.update(
            bounds=[str(midpoint - error), str(midpoint + error)],
            status="refuse_unresolved",
            refusal=CONTRIBUTION_STOP,
        )
        case["endpoint_refusals"][1] = CONTRIBUTION_STOP
    for context in packet["prediction_packet"]["contexts"]:
        for refusal in context["geometry_refusals"]:
            refusal["refusal"] = CONTRIBUTION_STOP
    packet["result"]["all_774_raw_endpoint_widths_pass"] = False
    # A conservatively wider independent representation must remain diagnostic.
    # All actual proof/deposition/score replay continues through the real oracle.
    monkeypatch.setattr(
        ring_oracle,
        "coefficient_q_spreads",
        lambda *_: {key: Q(1, 10**9) for key in forms},
    )
    checked = audit(**packet, clock=Clock(seconds=30))
    assert checked["status"] == "passed"
    assert checked["own_all_case_q_uncertainty_targets_pass"] is False
    assert all(
        case["native_q_uncertainty_target_pass"] is True for case in checked["cases"]
    )
    assert all(
        case["own_q_uncertainty_target_pass"] is False for case in checked["cases"]
    )
    assert packet["result"]["all_774_raw_endpoint_widths_pass"] is False


def test_valid_prediction_certificate_does_not_require_original_coefficient_precision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "function", packet_endpoint)
    packet = packet_fixture()
    for row in packet["public_source"]["geometry"]:
        row["anchor_xy_m"][1] = [-7.0, 2.0]
    for row in packet["original_prediction"]["geometry"]:
        row["anchor_xy_m"][1] = [-7.0, 2.0]
    for row in packet["capture_freeze"]["cases"]:
        row["geometry"]["second_anchor_xy_m"] = ["-7", "2"]
    for row in packet["certificates"]["cases"]:
        row["geometry"]["second_anchor_xy_m"] = ["-7", "2"]
        row["coefficient_bounds"]["B1"] = ["0", "255/512"]
        row["coefficient_bounds"]["B2"] = ["0", "255/512"]
        row["all_final_widths_pass"] = False
        row["positive_bounds_usable"] = False
    packet["result"]["all_18_coefficient_widths_pass"] = False
    for row in packet["prediction_packet"]["contexts"]:
        for family in ("centre_cover_idw_forward", "spatial_cover_idw_forward"):
            row["families"][family]["coefficient_precision_pass"] = False
    checked = audit(**packet, clock=Clock(seconds=30))
    assert checked["status"] == "passed"
    assert checked["own_18_original_epsilon_widths_pass"] is False
    assert checked["usable_prediction_contexts"] == 18


@pytest.mark.parametrize(
    "mutation",
    [
        "case",
        "training",
        "missing_score",
        "score_owner",
        "observed",
        "metric",
        "summary",
        "epsilon_flag",
    ],
)
def test_full_packet_tampering_is_rejected(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    monkeypatch.setattr(Geometry, "function", packet_endpoint)
    packet = packet_fixture()
    if mutation == "case":
        packet["certificates"]["cases"][1]["taxon"] = "Betula"
    elif mutation == "training":
        packet["prediction_packet"]["contexts"][0]["training_owners"][0]["core"] = (
            "BOKE"
        )
    elif mutation == "missing_score":
        packet["result"]["scores"].pop()
    elif mutation == "score_owner":
        packet["result"]["scores"][0]["sample_ids"] = [999]
    elif mutation == "observed":
        packet["result"]["scores"][1]["observed_fraction"] = [0.5, 0.5]
    elif mutation == "metric":
        packet["result"]["scores"][1]["conditional_metric_ranges_exact"][METRICS[0]] = [
            "0",
            "0",
        ]
    elif mutation == "summary":
        packet["result"]["summary"]["families"][0]["equal_place"][
            "conditional_metric_ranges_exact"
        ][METRICS[0]] = ["0", "0"]
    else:
        packet["prediction_packet"]["contexts"][0]["families"][
            "spatial_cover_idw_forward"
        ]["coefficient_precision_pass"] = False
    with pytest.raises(VerificationError):
        audit(**packet, clock=Clock(seconds=30))
