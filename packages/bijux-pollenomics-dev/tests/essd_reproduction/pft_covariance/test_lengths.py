"""Exact Gram-matrix and boundary checks for laminar uncertainty sums."""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.pft_covariance.lengths import (
    LengthInterval,
    assess_laminar_uncertainty,
    sum_length_range,
)


def point(value: int | F) -> LengthInterval:
    return LengthInterval(F(value), F(value))


def test_zero_child_sum_and_unary_intersection_are_exact() -> None:
    assert sum_length_range(()) == point(0)
    variable = LengthInterval(F(2), F(5))
    assert sum_length_range((variable,)) == variable
    result = assess_laminar_uncertainty(
        {"child": variable, "parent": LengthInterval(F(1), F(3)), "constant": point(1)},
        {"parent": ("child",), "constant": ()},
    )
    by_name = {node.variable: node for node in result.nodes}
    assert by_name["parent"].attainable == LengthInterval(F(2), F(3))
    assert (
        by_name["child"].attainable == variable
    )  # Subtree, not ancestor-constrained range.
    assert by_name["constant"].sum_range == point(0)
    assert by_name["constant"].upper_overlap_margin == -1
    assert not result.feasible
    assert result.roots == ("parent", "constant")
    assert not result.ungrouped_variables


@pytest.mark.parametrize("a,b,parent", product(range(5), repeat=3))
def test_two_child_point_sum_agrees_with_exact_gram_principal_minors(
    a: int, b: int, parent: int
) -> None:
    covariance = F(parent**2 - a**2 - b**2, 2)
    gram_psd = a**2 * b**2 - covariance**2 >= 0
    result = assess_laminar_uncertainty(
        {"a": point(a), "b": point(b), "sum": point(parent)}, {"sum": ("a", "b")}
    )
    assert result.feasible == gram_psd


@pytest.mark.parametrize("lengths", product(range(5), repeat=3))
def test_three_child_zero_total_agrees_with_full_exact_covariance(
    lengths: tuple[int, int, int],
) -> None:
    a, b, c = (F(value**2) for value in lengths)
    ab, ac, bc = (c - a - b) / 2, (b - a - c) / 2, (a - b - c) / 2
    determinant = a * b * c + 2 * ab * ac * bc - a * bc**2 - b * ac**2 - c * ab**2
    gram_psd = determinant >= 0 and all(
        value >= 0 for value in (a, b, c, a * b - ab**2, a * c - ac**2, b * c - bc**2)
    )
    # These are the unique pairwise covariances satisfying all three zero row sums.
    assert a + ab + ac == b + ab + bc == c + ac + bc == 0
    result = assess_laminar_uncertainty(
        {
            "a": point(lengths[0]),
            "b": point(lengths[1]),
            "c": point(lengths[2]),
            "total": point(0),
        },
        {"total": ("a", "b", "c")},
    )
    assert result.feasible == gram_psd


@pytest.mark.parametrize(
    "children,expected",
    [
        (
            (LengthInterval(F(4), F(6)), LengthInterval(F(1), F(2))),
            LengthInterval(F(2), F(8)),
        ),
        (
            (LengthInterval(F(1), F(4)), LengthInterval(F(2), F(3))),
            LengthInterval(F(0), F(7)),
        ),
        ((point(0), point(0)), point(0)),
        ((point(5), point(2), point(1)), LengthInterval(F(2), F(8))),
    ],
)
def test_interval_sum_range_preserves_all_declared_endpoints(
    children: tuple[LengthInterval, ...], expected: LengthInterval
) -> None:
    assert sum_length_range(children) == expected


def test_explicit_rounding_intervals_are_conditional_and_never_an_implicit_tolerance() -> (
    None
):
    epsilon = F(1, 10**30)
    groups = {"total": ("a", "b")}
    recorded = {"a": point(1), "b": point(1 + epsilon), "total": point(0)}
    exact = assess_laminar_uncertainty(recorded, groups)
    total = next(node for node in exact.nodes if node.variable == "total")
    assert not exact.feasible
    assert total.lower_overlap_margin == -epsilon
    assert total.refusal == "sum_length_outside_supplied_interval"
    admitted = {**recorded, "b": LengthInterval(F(1), 1 + epsilon)}
    assert assess_laminar_uncertainty(admitted, groups).feasible
    assert recorded["b"] == point(1 + epsilon)


def test_subtree_constraints_propagate_to_ancestors_without_changing_supplied_intervals() -> (
    None
):
    lengths = {
        "a": point(1),
        "b": point(1),
        "group": LengthInterval(F(0), F(10)),
        "parent": point(3),
        "root": point(0),
    }
    result = assess_laminar_uncertainty(
        lengths, {"group": ("a", "b"), "parent": ("group",), "root": ("parent",)}
    )
    nodes = {node.variable: node for node in result.nodes}
    assert nodes["group"].attainable == LengthInterval(F(0), F(2))
    assert nodes["parent"].upper_overlap_margin == -1
    assert nodes["parent"].refusal == "sum_length_outside_supplied_interval"
    assert nodes["root"].refusal == "child_sum_infeasible"
    assert nodes["root"].sum_range is None
    assert lengths["group"] == LengthInterval(F(0), F(10))


def test_isolated_zero_variable_does_not_impose_composition_closure() -> None:
    lengths = {"a": point(1), "b": point(1), "c": point(3), "total": point(0)}
    unconstrained = assess_laminar_uncertainty(lengths, {})
    assert unconstrained.feasible
    assert unconstrained.ungrouped_variables == tuple(lengths)
    assert not assess_laminar_uncertainty(lengths, {"total": ("a", "b", "c")}).feasible


def test_declared_partial_pft_tree_keeps_other_taxon_variables_ungrouped() -> None:
    groups = {
        "ET": ("TBE1", "TBE2", "IBE", "MTBE", "TSE", "MTSE"),
        "ST": ("IBS", "ISTS", "TBS", "TSD"),
        "OL": ("LSE", "GL", "AL"),
        "ISTS": ("Corylus.avellana", "Fraxinus", "Quercus.deciduous"),
        "TBS": (
            "Carpinus.betulus",
            "Carpinus.orientalis",
            "Castanea",
            "Fagus.sylvatica",
            "Tilia",
            "Ulmus",
        ),
        "total": ("ET", "ST", "OL"),
    }
    lengths = {name: point(1) for children in groups.values() for name in children}
    lengths["total"] = point(0)
    other_taxa = tuple(f"unmapped-taxon:{i}" for i in range(22))
    lengths.update({name: point(1000) for name in other_taxa})
    result = assess_laminar_uncertainty(lengths, groups)
    assert result.feasible
    assert result.ungrouped_variables == other_taxa
    assert result.roots == ("total", *other_taxa)
    # Equal descriptive labels never merge distinct source variable codes.
    assert {"TBE1", "TBE2"}.issubset(node.variable for node in result.nodes)


@pytest.mark.parametrize("scale", [F(1, 100), F(100), F(7, 3)])
def test_only_common_unit_rescaling_preserves_the_assessment(scale: F) -> None:
    lengths = {"a": point(1), "b": point(1), "parent": point(F(3, 2))}
    groups = {"parent": ("a", "b")}
    original = assess_laminar_uncertainty(lengths, groups)
    scaled = assess_laminar_uncertainty(
        {
            name: LengthInterval(v.lower * scale, v.upper * scale)
            for name, v in lengths.items()
        },
        groups,
    )
    assert original.feasible == scaled.feasible
    for a, b in zip(original.nodes, scaled.nodes, strict=True):
        if a.sum_range is not None:
            assert b.sum_range == LengthInterval(
                a.sum_range.lower * scale, a.sum_range.upper * scale
            )
    assert not assess_laminar_uncertainty(
        {**lengths, "parent": point(150)}, groups
    ).feasible


@pytest.mark.parametrize(
    "groups",
    [
        {"parent": ("a", "a")},
        {"parent": ("a",), "other": ("a",)},
        {"a": ("parent",), "parent": ("a",)},
        {"a": ("a",)},
        {"parent": ("missing",)},
        {"missing": ("a",)},
        {"parent": ["a"]},
    ],
)
def test_rejects_duplicate_overlapping_cyclic_and_unbound_identities(
    groups: Any,
) -> None:
    with pytest.raises(ValueError):
        assess_laminar_uncertainty(
            {"a": point(1), "parent": point(1), "other": point(1)}, groups
        )


@pytest.mark.parametrize(
    "lower,upper",
    [
        (True, F(1)),
        (0.0, F(1)),
        (F(0), float("inf")),
        (float("nan"), F(1)),
        (F(-1), F(1)),
        (F(2), F(1)),
        (0, F(1)),
    ],
)
def test_intervals_refuse_flags_nonfinite_inexact_negative_and_reversed_bounds(
    lower: Any, upper: Any
) -> None:
    with pytest.raises(ValueError, match="Fraction"):
        LengthInterval(lower, upper)


@pytest.mark.parametrize(
    "lengths,groups",
    [
        ({}, {}),
        ({" bad ": point(0)}, {}),
        ({"a": (F(0), F(1))}, {}),
        ({"a": point(0)}, {" bad ": ()}),
        ({"a": point(0)}, {"a": (True,)}),
    ],
)
def test_rejects_untyped_or_ambiguous_input_populations(
    lengths: Any, groups: Any
) -> None:
    with pytest.raises(ValueError):
        assess_laminar_uncertainty(lengths, groups)


def test_long_unary_chain_has_no_python_recursion_dependency() -> None:
    names = tuple(f"variable:{i}" for i in range(1100))
    result = assess_laminar_uncertainty(
        dict.fromkeys(names, point(1)),
        {parent: (child,) for parent, child in zip(names, names[1:], strict=False)},
    )
    assert result.feasible and result.roots == names[:1]
