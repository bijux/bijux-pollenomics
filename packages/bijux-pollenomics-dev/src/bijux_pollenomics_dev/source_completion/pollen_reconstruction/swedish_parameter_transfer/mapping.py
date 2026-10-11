"""Separate actual native count support from explicitly hypothesized complete input."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any


def source_to_parameter_map(
    source_names: set[str], public_targets: set[str], mappings: list[dict[str, str]]
) -> dict[str, str]:
    """Allocate each literal source count to at most one public parameter target."""
    mapping = {name: name for name in source_names if name in public_targets}
    provided = set()
    for row in mappings:
        source, target = row["source"], row["target"]
        if source in provided or source in mapping:
            raise ValueError("source count cannot be allocated more than once")
        provided.add(source)
        if target not in public_targets:
            raise ValueError("source transfer lacks a public parameter target")
        if source in source_names:
            mapping[source] = target
    return mapping


def scenario_input(
    sample: dict[str, Any],
    mapping: dict[str, str],
    targets: list[str],
    *,
    sparse_zero_hypothesis: bool,
    mutually_exclusive_partition_hypothesis: bool,
    ambiguous_parent_child_pairs: tuple[tuple[str, str], ...] = (),
) -> dict[str, Any]:
    """Separate observed count support from the declared completeness hypotheses."""
    if not sparse_zero_hypothesis:
        raise ValueError(
            "broad sparse panel needs a separately declared missing-row hypothesis"
        )
    if not mutually_exclusive_partition_hypothesis:
        raise ValueError(
            "native count rows need a separately declared partition hypothesis"
        )
    if len(set(targets)) != len(targets) or not targets:
        raise ValueError("parameter target axis must be unique and nonempty")
    source_axis = sorted(mapping)
    if set(targets) != set(mapping.values()):
        raise ValueError(
            "parameter axis must equal the targets of declared source routes"
        )
    counts = sample["counts"]
    for _name, value in counts.items():
        if type(value) is not int or value < 0 or not math.isfinite(value):
            raise ValueError("source NISP count must be a nonnegative integer")
    for parent, child in ambiguous_parent_child_pairs:
        if parent in counts and child in counts:
            raise ValueError(
                "parent and child rows require an explicit residual-aggregation decision"
            )
    mapped: Counter[str] = Counter()
    explicit = dict.fromkeys(targets, False)
    residual = 0
    actual_zero_rows = 0
    for name, value in counts.items():
        if name not in mapping:
            residual += value
            continue
        target = mapping[name]
        if target not in explicit:
            raise ValueError(
                "allocated source target is outside the declared parameter axis"
            )
        mapped[target] += value
        explicit[target] = True
        actual_zero_rows += value == 0
    ordered = [mapped[target] for target in targets]
    reported = sample["reported_pollen_NISP_sum"]
    if sum(counts.values()) != reported or sum(ordered) + residual != reported:
        raise ValueError(
            "mapped plus residual mass does not conserve reported source NISP"
        )
    source_presence = [name in counts for name in source_axis]
    complete_target = [
        all(
            name in counts
            for name, destination in mapping.items()
            if destination == target
        )
        for target in targets
    ]
    return {
        "counts": ordered,
        "selected_source_name_axis": source_axis,
        "actual_selected_source_name_presence": source_presence,
        "any_source_label_present_on_parameter_axis": [
            explicit[target] for target in targets
        ],
        "all_contributing_source_labels_present_on_parameter_axis": complete_target,
        "hypothesized_complete_input": [True for _ in targets],
        "assumed_zero_source_cells": sum(not present for present in source_presence),
        "assumed_zero_parameter_cells": sum(not explicit[target] for target in targets),
        "actual_explicit_zero_rows": actual_zero_rows,
        "unparameterized_reported_pollen_NISP": residual,
        "reported_all_pollen_NISP": reported,
        "source_measurement_complete_claimed": False,
    }
