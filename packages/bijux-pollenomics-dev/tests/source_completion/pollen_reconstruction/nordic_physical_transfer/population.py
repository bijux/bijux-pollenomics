"""Independent structural cohorts, exact weights and complete loss populations."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

from .algebra import PRECISION, compare, number, require

METHODS = ("physical_forward", "direct_panel_mean")
METRICS = ("mae_fraction", "hellinger_stable", "total_variation")


def cohort(
    protocol: dict[str, Any], profile: dict[str, Any], target: str, scope: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cores = {c["key"]: c for c in protocol["cores"]}
    owner = cores[target]
    require(target in profile["cores"], "target in structural profile")
    allowed, excluded = [], []
    for source in protocol["cores"]:
        key = source["key"]
        if key not in profile["cores"]:
            reason = "outside_profile_core_selection"
        elif source["physical_family"] == owner["physical_family"]:
            reason = "whole_target_physical_family_excluded"
        elif (
            scope == "outside_target_country" and source["country"] == owner["country"]
        ):
            reason = "whole_target_country_excluded"
        elif scope == "swedish_only" and source["country"] != "SE":
            reason = "outside_declared_training_scope"
        else:
            allowed.append(source)
            continue
        excluded.append(
            {
                "core": key,
                "physical_family": source["physical_family"],
                "country": source["country"],
                "reason": reason,
            }
        )
    require(
        bool(allowed) and len({c["physical_family"] for c in allowed}) == len(allowed),
        "nonempty distinct structural places",
    )
    countries = Counter(c["country"] for c in allowed)
    weighted = []
    for source in allowed:
        if profile["weighting"] == "equal_physical_place":
            weight = Fraction(1, len(allowed))
        else:
            require(
                profile["weighting"] == "equal_country_then_place",
                "known place weighting",
            )
            weight = Fraction(1, len(countries) * countries[source["country"]])
        with localcontext() as context:
            context.prec = PRECISION
            decimal_weight = Decimal(weight.numerator) / Decimal(weight.denominator)
        weighted.append(
            {
                "core": source["key"],
                "weight_exact": str(weight),
                "weight_decimal": decimal_weight,
            }
        )
    require(
        sum(Fraction(row["weight_exact"]) for row in weighted) == 1,
        "exact structural weight conservation",
    )
    return weighted, excluded


def plan(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    """Enumerate absent/refused windows too; no quantitative input is accepted."""
    out = []
    for profile in protocol["profiles"]:
        for experiment in protocol["experiments"]:
            for declared in experiment["targets"]:
                target = (
                    "solsoe81"
                    if declared == "solsoe83" and "solsoe81" in profile["cores"]
                    else declared
                )
                for window in protocol["windows"]:
                    for scope in experiment["scopes"]:
                        required, excluded = cohort(protocol, profile, target, scope)
                        out.append(
                            {
                                "profile": profile["id"],
                                "experiment": experiment["id"],
                                "target_core": target,
                                "window_cal_bp": window,
                                "scope": scope,
                                "required": required,
                                "excluded": excluded,
                            }
                        )
    require(
        len(out) == protocol["population"]["contexts"] == 216,
        "complete prospective context population",
    )
    return out


def loss_summary(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    scored = [row for row in rows if row["status"] == "scored"]
    by_target: dict[str, list[dict[str, Any]]] = {}
    for row in scored:
        by_target.setdefault(row["identity"]["target_core"], []).append(row)
    with localcontext() as context:
        context.prec = PRECISION
        macro = (
            None
            if not by_target
            else {
                metric: sum(
                    sum(number(r["metrics"][metric]) for r in values) / len(values)
                    for values in by_target.values()
                )
                / len(by_target)
                for metric in METRICS
            }
        )
        denominator = sum(row["target_owner_count"] for row in scored)
        weighted = (
            None
            if not denominator
            else {
                metric: sum(
                    number(row["metrics"][metric]) * row["target_owner_count"]
                    for row in scored
                )
                / denominator
                for metric in METRICS
            }
        )
    return macro, {"owner_denominator": denominator, "metrics": weighted}


def channel(row: dict[str, Any]) -> dict[str, str]:
    return {key: row["identity"][key] for key in ("profile", "experiment", "scope")} | {
        "method": row["method"]
    }


def channel_key(value: dict[str, Any]) -> tuple[str, ...]:
    require(
        set(value) == {"profile", "experiment", "scope", "method"},
        "closed channel identity",
    )
    return tuple(value[key] for key in ("profile", "experiment", "scope", "method"))


def compare_targets(
    actual: list[dict[str, Any]], expected: list[dict[str, Any]], label: str
) -> None:
    require(
        len(actual) == len(expected)
        and len({row["target_core"] for row in actual}) == len(actual),
        label + " target inventory",
    )
    compare(
        sorted(actual, key=lambda row: row["target_core"]),
        sorted(expected, key=lambda row: row["target_core"]),
        label,
    )


def summaries(
    value: dict[str, Any], protocol: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    require(
        set(value) == {"schema_version", "groups", "matched"}
        and value["schema_version"] == "nordic-physical-summary.v1",
        "summary schema",
    )
    cores = {core["key"]: core for core in protocol["cores"]}
    expected: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        identity = row["identity"]
        base = channel_key(channel(row))
        for country in ("ALL", identity["country"]):
            expected.setdefault((*base, country), []).append(row)
    require(len(value["groups"]) == len(expected), "all country and overall groups")
    seen = set()
    for group in value["groups"]:
        key = tuple(
            group[k] for k in ("profile", "experiment", "scope", "method", "country")
        )
        require(key in expected and key not in seen, "unique requested loss group")
        seen.add(key)
        members = expected[key]
        targets = list(dict.fromkeys(row["identity"]["target_core"] for row in members))
        macro, weighted = loss_summary(members)
        expected_group = {
            key: group[key]
            for key in ("profile", "experiment", "scope", "method", "country")
        }
        expected_group.update(
            {
                "requested": len(members),
                "predicted": sum(row["pollen_fraction"] is not None for row in members),
                "refused": sum(row["pollen_fraction"] is None for row in members),
                "unavailable_targets": sum(
                    row["status"] == "unavailable_target_observation" for row in members
                ),
                "scored": sum(row["status"] == "scored" for row in members),
                "target_count": len(targets),
                "macro": macro,
                "native_owner_weighted": weighted,
                "per_target": [],
            }
        )
        for target in targets:
            selected = [
                row for row in members if row["identity"]["target_core"] == target
            ]
            expected_group["per_target"].append(
                {
                    "target_core": target,
                    "physical_family": cores[target]["physical_family"],
                    "requested": len(selected),
                    "predicted": sum(
                        row["pollen_fraction"] is not None for row in selected
                    ),
                    "refused": sum(row["pollen_fraction"] is None for row in selected),
                    "scored": sum(row["status"] == "scored" for row in selected),
                    "macro": loss_summary(selected)[0],
                }
            )
        compare_targets(
            group["per_target"], expected_group["per_target"], "group target means"
        )
        compare(
            {k: v for k, v in group.items() if k != "per_target"},
            {k: v for k, v in expected_group.items() if k != "per_target"},
            "group",
        )
    comparisons = {
        "swedish_scope_methods:" + p["id"]: [p["id"]] for p in protocol["profiles"]
    }
    comparisons["density_sensitivity_swedish"] = [
        protocol["profiles"][i]["id"] for i in (0, 1)
    ]
    comparisons["core_sensitivity_swedish"] = [
        protocol["profiles"][i]["id"] for i in (0, 2)
    ]
    require(
        len(value["matched"]) == len(comparisons), "five prospective paired comparisons"
    )
    seen_comparisons = set()
    for comparison in value["matched"]:
        name = comparison["comparison_id"]
        require(
            name in comparisons and name not in seen_comparisons,
            "unique prescribed comparison",
        )
        seen_comparisons.add(name)
        channels = [
            (profile, "swedish_training_scope", scope, method)
            for profile in comparisons[name]
            for scope in ("swedish_only", "pooled_nordic")
            for method in METHODS
        ]
        supplied = [channel_key(c) for c in comparison["channels"]]
        require(
            set(supplied) == set(channels) and len(supplied) == len(channels),
            "prespecified matched channels",
        )
        by_channel: dict[tuple[str, ...], dict[tuple[Any, ...], dict[str, Any]]] = {
            c: {} for c in channels
        }
        for row in rows:
            key = channel_key(channel(row))
            if key in by_channel:
                identity = row["identity"]
                target_window = (identity["target_core"], *identity["window_cal_bp"])
                require(
                    target_window not in by_channel[key], "unique matched target-window"
                )
                by_channel[key][target_window] = row
        candidates = list(by_channel[channels[0]])
        require(
            len(candidates) == 18
            and all(set(by_channel[c]) == set(candidates) for c in channels),
            "identical Swedish requested target-windows",
        )
        common = [
            k
            for k in candidates
            if all(by_channel[c][k]["status"] == "scored" for c in channels)
        ]
        require(
            comparison["requested_target_windows"] == 18
            and comparison["matched_target_windows"] == len(common),
            "complete common support population",
        )
        unmatched = [
            {
                "target_core": k[0],
                "physical_family": cores[k[0]]["physical_family"],
                "window_cal_bp": list(k[1:]),
                "reason": "incomplete_common_support",
            }
            for k in candidates
            if k not in common
        ]

        def order(row: dict[str, Any]) -> tuple[Any, ...]:
            return (row["target_core"], *row["window_cal_bp"])

        compare(
            sorted(comparison["unmatched"], key=order),
            sorted(unmatched, key=order),
            "unmatched",
        )
        channel_summaries = {}
        for saved in comparison["channels_summary"]:
            key = channel_key(saved["channel"])
            require(
                key in channels and key not in channel_summaries,
                "unique matched channel summary",
            )
            members = [by_channel[key][k] for k in common]
            targets = list(dict.fromkeys(k[0] for k in common))
            macro, weighted = loss_summary(members)
            expected_channel = {
                "channel": saved["channel"],
                "physical_targets": len(targets),
                "matched_windows": len(common),
                "macro": macro,
                "native_owner_weighted": weighted,
                "per_target": [
                    {
                        "target_core": target,
                        "physical_family": cores[target]["physical_family"],
                        "matched_windows": sum(k[0] == target for k in common),
                        "macro": loss_summary(
                            [
                                r
                                for r in members
                                if r["identity"]["target_core"] == target
                            ]
                        )[0],
                    }
                    for target in targets
                ],
            }
            compare_targets(
                saved["per_target"],
                expected_channel["per_target"],
                "matched target means",
            )
            compare(
                {k: v for k, v in saved.items() if k != "per_target"},
                {k: v for k, v in expected_channel.items() if k != "per_target"},
                "matched summary",
            )
            channel_summaries[key] = expected_channel
        require(
            set(channel_summaries) == set(channels), "all matched channel summaries"
        )
        seen_pairs = set()
        for pair in comparison["pairwise"]:
            first, second = channel_key(pair["first"]), channel_key(pair["second"])
            unordered = frozenset((first, second))
            require(
                first in channels
                and second in channels
                and len(unordered) == 2
                and unordered not in seen_pairs,
                "unique matched pair",
            )
            seen_pairs.add(unordered)
            left, right = (
                channel_summaries[first]["macro"],
                channel_summaries[second]["macro"],
            )
            difference = (
                None
                if left is None
                else {metric: left[metric] - right[metric] for metric in METRICS}
            )
            compare(
                pair,
                {
                    "first": pair["first"],
                    "second": pair["second"],
                    "mean_difference": difference,
                },
                "paired difference",
            )
        require(
            len(seen_pairs) == len(channels) * (len(channels) - 1) // 2,
            "all prescribed pairs",
        )
