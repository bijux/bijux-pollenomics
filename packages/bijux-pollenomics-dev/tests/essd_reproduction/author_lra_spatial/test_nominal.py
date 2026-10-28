"""Known-vector baseline and native-forward handoff correspondence controls."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import nominal


def packet(axis: int = 2) -> dict[str, Any]:
    """Use analytically known covers and deposition, with untouched zero taxa."""
    taxa = [f"taxon-{index}" for index in range(axis)]
    predictors = [
        {
            "record_id": group,
            "group_id": group,
            "covers_by_ring": [
                [1.0, 0.0, *([0.0] * (axis - 2))],
                [first, 1 - first, *([0.0] * (axis - 2))],
            ],
        }
        for group, first in (("a", 0.0), ("b", 0.5), ("c", 1.0))
    ]
    inputs = {
        "taxa": taxa,
        "regional_deposition": [1.0, 2.0, *([0.0] * (axis - 2))],
        "local_k": [
            [2.0, 1.0, *([1.0] * (axis - 2))],
            [1.0, 4.0, *([1.0] * (axis - 2))],
        ],
        "terrestrial_fraction": [0.5, 0.25],
        "ppe": [2.0, 3.0, *([1.0] * (axis - 2))],
    }
    references = []
    for method, first in zip(nominal.BASELINES, (0.5, 0.25, 1 / 3), strict=True):
        cover = [first, 1 - first, *([0.0] * (axis - 2))]
        # Direct rational equation: local=(2.5*c0,4.5*c1), regional=(1,2).
        total = [1 + 2.5 * first, 2 + 4.5 * (1 - first)]
        pollen = [value / sum(total) for value in total] + [0.0] * (axis - 2)
        references.append(
            {
                "baseline": method,
                "vegetation_fraction": dict(zip(taxa, cover, strict=True)),
                "pollen_fraction": dict(zip(taxa, pollen, strict=True)),
            }
        )
    contexts = []
    for outer in range(15):
        for inner in range(15):
            contexts.append(
                deepcopy(
                    {
                        "context_id": f"context:{outer}:{inner}",
                        "kind": "outer" if inner == 0 else "inner",
                        "target": f"target:{outer}:{inner}",
                        "outer_target": f"outer:{outer}",
                        "scientific_refs": {
                            "training_record_ids": ["a", "b", "c", "anchor"]
                        },
                        "predictors": predictors,
                        "forward": {
                            "distances_km": {"a": 1.0, "b": 1.0, "c": 2.0},
                            "forward_inputs": inputs,
                        },
                        "reference_baselines": references,
                    }
                )
            )
    return {"taxa": taxa, "contexts": contexts}


@pytest.mark.parametrize("axis", [2, 3, 30])
def test_all675_known_vectors_and_native_forward(axis: int) -> None:
    source = packet(axis)
    original = deepcopy(source)
    facts = nominal.check_nominal(source)
    assert facts["passed"] is True
    assert facts["contexts"] == 225
    assert (
        facts["reference_baselines"]
        == facts["forward_calls"]
        == facts["pollen_comparisons"]
        == 675
    )
    assert (
        facts["vegetation_component_checks"]
        == facts["pollen_component_checks"]
        == 675 * axis
    )
    assert facts["maximum_vegetation_absolute_error"] <= 1e-15
    assert facts["maximum_pollen_absolute_error"] <= 1e-15
    assert facts["failures"] == []
    assert source == original


def test_nearest_and_coincident_ties_use_only_exact_ties() -> None:
    source = packet()
    context = source["contexts"][0]
    for method in ("nearest_site", "inverse_distance_squared"):
        assert nominal._reconstruct(
            context["predictors"],
            {"a": 0.0, "b": 0.0, "c": 1e-300},
            source["taxa"],
            method,
        ) == [0.25, 0.75]
    assert nominal._reconstruct(
        context["predictors"],
        {"a": 1.0, "b": 1.0, "c": 2.0},
        source["taxa"],
        "nearest_site",
    ) == [0.25, 0.75]
    assert nominal._reconstruct(
        context["predictors"],
        {"a": 1.0, "b": 1.0 + 2**-52, "c": 2.0},
        source["taxa"],
        "nearest_site",
    ) == [0.0, 1.0]


def test_idw_uses_scaled_weights_at_extreme_distances() -> None:
    source = packet()
    context = source["contexts"][0]
    for scale in (1e-200, 1.0, 1e200):
        values = nominal._reconstruct(
            context["predictors"],
            {"a": scale, "b": scale, "c": 2 * scale},
            source["taxa"],
            "inverse_distance_squared",
        )
        assert values == [1 / 3, 2 / 3]


@pytest.mark.parametrize("field", ["ppe", "local_k", "regional_deposition"])
def test_wrong_forward_handoff_retains_all675_failures(field: str) -> None:
    source = packet()
    for context in source["contexts"]:
        values = context["forward"]["forward_inputs"][field]
        if field == "local_k":
            values[0][0] *= 2
        else:
            values[0] *= 2
    facts = nominal.check_nominal(source)
    assert facts["passed"] is False
    assert facts["forward_calls"] == 675
    assert len(facts["failures"]) == 675
    assert {row["stage"] for row in facts["failures"]} == {"pollen"}


def test_regional_deposition_is_not_multiplied_by_ppe_twice() -> None:
    source = packet()
    nearest = source["contexts"][0]["reference_baselines"][1]
    assert list(nearest["pollen_fraction"].values()) == [13 / 56, 43 / 56]
    assert nominal.check_nominal(source)["passed"] is True
    for context in source["contexts"]:
        for reference in context["reference_baselines"]:
            cover = list(reference["vegetation_fraction"].values())
            total = [2 + 2.5 * cover[0], 6 + 4.5 * cover[1]]
            reference["pollen_fraction"] = dict(
                zip(
                    source["taxa"], [value / sum(total) for value in total], strict=True
                )
            )
    assert nominal.check_nominal(source)["passed"] is False


def test_native_refusals_retain_every_slot() -> None:
    source = packet()
    for context in source["contexts"]:
        context["forward"]["forward_inputs"]["local_k"] = [[0.0, 0.0], [0.0, 0.0]]
        context["forward"]["forward_inputs"]["regional_deposition"] = [0.0, 0.0]
    facts = nominal.check_nominal(source)
    assert facts["passed"] is False
    assert facts["forward_calls"] == 675
    assert facts["pollen_comparisons"] == 0
    assert len(facts["failures"]) == 675
    assert {row["stage"] for row in facts["failures"]} == {"native_forward"}


@pytest.mark.parametrize(
    "mutation",
    [
        "context_missing",
        "context_duplicate",
        "baseline_duplicate",
        "target_leak",
        "axis",
        "negative_distance",
        "boolean_cover",
    ],
)
def test_malformed_packet_refuses(mutation: str) -> None:
    source = packet()
    context = source["contexts"][0]
    if mutation == "context_missing":
        source["contexts"].pop()
    elif mutation == "context_duplicate":
        source["contexts"][-1] = deepcopy(context)
    elif mutation == "baseline_duplicate":
        context["reference_baselines"][-1] = deepcopy(context["reference_baselines"][0])
    elif mutation == "target_leak":
        context["scientific_refs"]["training_record_ids"].append(context["target"])
    elif mutation == "axis":
        context["reference_baselines"][0]["vegetation_fraction"].popitem()
    elif mutation == "negative_distance":
        context["forward"]["distances_km"]["a"] = -1.0
    elif mutation == "boolean_cover":
        context["predictors"][0]["covers_by_ring"][1][0] = False
    with pytest.raises(ValueError):
        nominal.check_nominal(source)


def test_unknown_method_refuses() -> None:
    source = packet()
    context = source["contexts"][0]
    with pytest.raises(ValueError, match="Unknown nominal"):
        nominal._reconstruct(
            context["predictors"],
            context["forward"]["distances_km"],
            source["taxa"],
            "unregistered",
        )
