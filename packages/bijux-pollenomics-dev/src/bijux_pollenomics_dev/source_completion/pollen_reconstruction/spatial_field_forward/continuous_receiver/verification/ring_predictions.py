"""Independent continuous-ring prediction, score and matched-population audit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import combinations
from typing import Any, cast

from ..arithmetic import Interval
from .contracts import (
    OWNERS,
    Clock,
    _same_json,
    bounds,
    encoded,
    finite,
    overlaps,
    rational,
    require,
)
from .ring_sources import CORES, select_sources
from .rings import ring_linear_bounds, verify_ring_case

METRICS = (
    "mean_absolute_fraction_error",
    "total_variation",
    "hellinger_distance",
)
FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)
ENCLOSED = "continuous_law_enclosure"
UNRESOLVED = "unresolved_continuous_law"
DIRECT = "fixed_saved_point_reference"


def _exact_bounds(value: object) -> Interval:
    require(isinstance(value, list) and len(value) == 2, "Exact range pair required")
    value = cast(list[object], value)
    return Interval(rational(value[0]), rational(value[1]))


def _owner(value: Mapping[str, Any]) -> dict[str, Any]:
    require(value.get("core") in CORES, "Foreign source core")
    for key in ("site_id", "dataset_id", "collection_unit_id"):
        require(
            type(value.get(key)) is int and value[key] > 0,
            "Invalid native source owner",
        )
    window, samples = value.get("window"), value.get("sample_ids")
    require(
        isinstance(window, list)
        and len(window) == 2
        and all(type(n) is int for n in window)
        and window[1] - window[0] == 500
        and isinstance(samples, list)
        and bool(samples)
        and all(type(n) is int and n > 0 for n in samples)
        and len(set(samples)) == len(samples),
        "Invalid source window/sample owners",
    )
    return {
        key: value[key]
        for key in (
            "core",
            "site_id",
            "dataset_id",
            "collection_unit_id",
            "window",
            "sample_ids",
        )
    }


def _vector(value: object) -> tuple[Fraction, Fraction]:
    require(
        isinstance(value, list) and len(value) == 2, "Two finite components required"
    )
    value = cast(list[object], value)
    result = finite(value[0]), finite(value[1])
    require(
        all(0 <= x <= 1 for x in result) and sum(result) > 0,
        "Invalid finite composition",
    )
    return result


def _source_contexts(prediction: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = prediction.get("contexts")
    require(
        isinstance(rows, list) and len(rows) == 18,
        "Incomplete original context population",
    )
    rows = cast(list[dict[str, Any]], rows)
    result = {}
    for row in rows:
        key = row.get("context_id")
        require(
            type(key) is str and key not in result, "Duplicate or invalid context ID"
        )
        key = cast(str, key)
        owner = _owner(row["target"])
        require(
            row.get("geometry_core") == owner["core"], "Target geometry owner differs"
        )
        expected = [c for c in CORES if c != owner["core"]]
        require(
            [r["core"] for r in row["training"]] == expected,
            "Target enters its training anchors",
        )
        seen = set(owner["sample_ids"])
        for training in row["training"]:
            source = _owner(training)
            require(
                source["window"] == owner["window"]
                and not seen.intersection(source["sample_ids"]),
                "Cross-role sample/window overlap",
            )
            seen.update(source["sample_ids"])
            _vector(training["cover"])
        require(set(row["families"]) == set(FAMILIES), "Original family axis differs")
        for family in FAMILIES:
            require(
                row["families"][family]["status"] == "predicted",
                "Original family is refused",
            )
            _vector(row["families"][family]["pollen_fraction"])
        result[key] = row
    for core in CORES:
        windows = [
            tuple(row["target"]["window"])
            for row in rows
            if row["target"]["core"] == core
        ]
        require(
            sorted(windows) == [(a, a + 500) for a in range(2700, 5700, 500)],
            "Fixed six-window population differs",
        )
    return result


def normalized_deposition(values: Sequence[Interval]) -> Interval:
    """Enclose the first normalized component of two deposition intervals."""
    require(
        len(values) == 2
        and min(v.lower for v in values) >= 0
        and sum((v.lower for v in values), Fraction(0)) > 0,
        "Positive two-taxon deposition not certified",
    )
    first, second = values
    return Interval(
        first.lower / (first.lower + second.upper),
        first.upper / (first.upper + second.lower),
    )


def score_ranges(
    probability: Interval, observed: Sequence[Fraction]
) -> dict[str, Interval]:
    """Exact convex extrema and constructive Hellinger roots; no forced closure."""
    require(
        0 <= probability.lower <= probability.upper <= 1
        and len(observed) == 2
        and all(type(o) is Fraction and 0 <= o <= 1 for o in observed)
        and sum(observed, Fraction(0)) > 0,
        "Invalid observed/predicted composition",
    )
    a, b = probability.lower, probability.upper

    def absolute(p: Fraction) -> Fraction:
        return (abs(p - observed[0]) + abs(1 - p - observed[1])) / 2

    minimizer = min(b, max(a, min(observed[0], 1 - observed[1])))
    variation = Interval(absolute(minimizer), max(absolute(a), absolute(b)))

    def hellinger(p: Fraction) -> Interval:
        differences = tuple(
            Interval.point(x).root(2) - Interval.point(y).root(2)
            for x, y in zip((p, 1 - p), observed, strict=True)
        )
        squared = sum((d**2 for d in differences), Interval.point(0)) / 2
        return squared.root(2)

    stationary = min(b, max(a, observed[0] / sum(observed, Fraction(0))))
    distance = Interval(
        hellinger(stationary).lower,
        max(hellinger(a).upper, hellinger(b).upper),
    )
    return dict(zip(METRICS, (variation, variation, distance), strict=True))


def average_ranges(rows: Sequence[Mapping[str, Interval]]) -> dict[str, Interval]:
    """Average each metric's interval endpoints over the full row population."""
    require(bool(rows), "Empty score population")
    require(all(set(row) == set(METRICS) for row in rows), "Metric axis differs")
    return {
        metric: Interval(
            sum((row[metric].lower for row in rows), Fraction(0)) / len(rows),
            sum((row[metric].upper for row in rows), Fraction(0)) / len(rows),
        )
        for metric in METRICS
    }


def _audit_contexts(
    original: Mapping[str, Any],
    packet: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]],
    independent: Sequence[Mapping[str, Any]],
    geometries: Sequence[Any],
    edges: Sequence[tuple[Fraction, ...]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    sources = _source_contexts(original)
    rows = packet.get("contexts")
    require(
        isinstance(rows, list) and [r.get("context_id") for r in rows] == list(sources),
        "Closed context order/population differs",
    )
    rows = cast(list[dict[str, Any]], rows)
    ppe = original.get("ppe")
    require(
        isinstance(ppe, list) and len(ppe) == 2 and all(finite(x) > 0 for x in ppe),
        "Positive PPE axis required",
    )
    ppe = cast(list[object], ppe)
    own_contexts = {}
    for row in rows:
        key = row["context_id"]
        source = sources[key]
        owner = _owner(source["target"])
        require(
            _same_json(row.get("target_owner"), owner)
            and row.get("core") == owner["core"]
            and _same_json(row.get("window"), owner["window"])
            and _same_json(row.get("sample_ids"), owner["sample_ids"])
            and _same_json(
                row.get("training_owners"), [_owner(r) for r in source["training"]]
            )
            and set(row["families"]) == set(FAMILIES),
            "Closed native context ancestry differs",
        )
        offset = CORES.index(owner["core"]) * 2
        selected = tuple(independent[offset + j] for j in range(2))
        native_cases = tuple(cases[offset + j] for j in range(2))
        require(
            _same_json(
                row.get("geometry_refusals"),
                [
                    {"taxon": taxon, "refusal": case["backend_refusal"]}
                    for taxon, case in zip(
                        ("Betula", "Ulmus"), native_cases, strict=True
                    )
                ],
            ),
            "Geometry refusal owner differs",
        )
        native_precision = all(c["all_final_widths_pass"] for c in native_cases)
        own_families: dict[str, Any] = {}
        for family in FAMILIES:
            claim = row["families"][family]
            if family == FAMILIES[0]:
                values = _vector(source["families"][family]["pollen_fraction"])
                require(
                    _same_json(
                        claim,
                        {
                            "status": DIRECT,
                            "prediction_bounds_exact": [
                                [str(v), str(v)] for v in values
                            ],
                            "deposition_bounds_exact": None,
                            "coefficient_precision_pass": None,
                            "refusal": None,
                        },
                    ),
                    "Saved direct finite reference changed",
                )
                own_families[family] = {
                    "status": DIRECT,
                    "prediction_bounds_exact": [[str(v), str(v)] for v in values],
                }
                continue
            require(
                claim.get("coefficient_precision_pass") is native_precision,
                "Coefficient precision promoted or hidden",
            )
            if any(c["coefficient_bounds"] is None for c in native_cases):
                require(
                    claim.get("status") == UNRESOLVED
                    and claim.get("refusal") == "incomplete_continuous_geometry"
                    and claim.get("prediction_bounds_exact") is None
                    and claim.get("deposition_bounds_exact") is None,
                    "Missing geometry promoted to prediction",
                )
                own_families[family] = {
                    "status": UNRESOLVED,
                    "prediction_bounds_exact": None,
                }
                continue
            deposits = []
            claimed_deposits = claim.get("deposition_bounds_exact")
            require(
                isinstance(claimed_deposits, list) and len(claimed_deposits) == 2,
                "Two deposition intervals required",
            )
            native_deposits = [bounds(v) for v in claimed_deposits]
            for j in range(2):
                geometry = geometries[offset + j]
                first, second = (finite(r["cover"][j]) for r in source["training"])
                if family == FAMILIES[2]:
                    deposit = ring_linear_bounds(
                        geometry, edges[offset + j], selected[j]["own_q"], first, second
                    )
                else:
                    aa, bb, _, _, _ = geometry.anchors()
                    cover = (bb * first + aa * second) / (aa + bb)
                    deposit = selected[j]["own_coefficients"]["K"] * cover
                    native_expected = (
                        bounds(native_cases[j]["coefficient_bounds"]["K"])
                        * cover
                        * finite(ppe[j])
                    )
                    require(
                        native_expected == native_deposits[j],
                        "Centre-cover coefficient ancestry differs",
                    )
                deposits.append(deposit * finite(ppe[j]))
                overlaps(deposits[j], native_deposits[j], "continuous deposition")
            native_positive = all(v.lower > 0 for v in native_deposits)
            require(
                claim.get("status") == (ENCLOSED if native_positive else UNRESOLVED)
                and claim.get("refusal")
                == (None if native_positive else "positive_deposition_not_established"),
                "Prediction positivity/refusal flag differs",
            )
            if native_positive:
                probability = normalized_deposition(native_deposits)
                require(
                    _same_json(
                        claim.get("prediction_bounds_exact"),
                        [
                            encoded(probability),
                            encoded(
                                Interval(1 - probability.upper, 1 - probability.lower)
                            ),
                        ],
                    ),
                    "Normalized closed prediction falsified",
                )
            else:
                require(
                    claim.get("prediction_bounds_exact") is None,
                    "Unusable deposition promoted",
                )
            own_positive = all(v.lower > 0 for v in deposits)
            own_probability = normalized_deposition(deposits) if own_positive else None
            own_families[family] = {
                "status": ENCLOSED if own_positive else UNRESOLVED,
                "deposition_bounds_exact": [encoded(v) for v in deposits],
                "prediction_bounds_exact": None
                if own_probability is None
                else [
                    encoded(own_probability),
                    encoded(
                        Interval(1 - own_probability.upper, 1 - own_probability.lower)
                    ),
                ],
            }
        own_contexts[key] = {
            "context_id": key,
            "core": owner["core"],
            "window": owner["window"],
            "families": own_families,
        }
    return sources, own_contexts


def _audit_scores(
    sources: Mapping[str, Mapping[str, Any]],
    own_contexts: Mapping[str, Mapping[str, Any]],
    packet: Mapping[str, Any],
    original: Mapping[str, Any],
    result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    old_rows, rows = original.get("scores"), result.get("scores")
    require(
        isinstance(old_rows, list)
        and isinstance(rows, list)
        and len(old_rows) == len(rows) == 54,
        "Incomplete 54-slot score inventory",
    )
    old_rows = cast(list[dict[str, Any]], old_rows)
    rows = cast(list[dict[str, Any]], rows)
    closed = {r["context_id"]: r for r in packet["contexts"]}
    seen = set()
    observations: dict[str, object] = {}
    own_rows = []
    for old, row in zip(old_rows, rows, strict=True):
        key, family = old["context_id"], old["family"]
        require(
            key in sources
            and family in FAMILIES
            and (key, family) not in seen
            and old.get("status") == "scored",
            "Duplicate/foreign/refused saved score",
        )
        seen.add((key, family))
        source = sources[key]
        for name in (
            "context_id",
            "core",
            "window",
            "sample_ids",
            "family",
            "observed_fraction",
        ):
            require(
                _same_json(row.get(name), old[name]), "Score native ancestry differs"
            )
        require(
            old["core"] == source["target"]["core"]
            and _same_json(old["window"], source["target"]["window"])
            and _same_json(old["sample_ids"], source["target"]["sample_ids"])
            and _same_json(
                old["predicted_fraction"], source["families"][family]["pollen_fraction"]
            ),
            "Saved score/prediction owner differs",
        )
        observed = _vector(old["observed_fraction"])
        require(
            key not in observations
            or _same_json(observations[key], old["observed_fraction"]),
            "Observed components changed across families",
        )
        observations[key] = old["observed_fraction"]
        legacy = {metric: old[metric] for metric in METRICS}
        require(
            _same_json(row.get("legacy_point_score"), legacy)
            and all(finite(x) >= 0 for x in legacy.values()),
            "Legacy finite score changed",
        )
        native_family = closed[key]["families"][family]
        require(
            row.get("status") == native_family["status"], "Score disposition changed"
        )
        own_family = own_contexts[key]["families"][family]
        own_ranges: dict[str, Interval] | None
        if family == FAMILIES[0]:
            expected = {
                metric: [str(finite(value)), str(finite(value))]
                for metric, value in legacy.items()
            }
            require(
                _same_json(row.get("conditional_metric_ranges_exact"), expected),
                "Saved direct score replaced",
            )
            own_ranges = {
                metric: Interval.point(finite(value))
                for metric, value in legacy.items()
            }
        else:
            if native_family["status"] == ENCLOSED:
                claimed = row.get("conditional_metric_ranges_exact")
                require(
                    isinstance(claimed, dict) and set(claimed) == set(METRICS),
                    "Metric enclosure axis differs",
                )
                claimed = cast(dict[str, Any], claimed)
                check = score_ranges(
                    _exact_bounds(native_family["prediction_bounds_exact"][0]), observed
                )
                for metric in METRICS:
                    interval = _exact_bounds(claimed[metric])
                    if metric != METRICS[2]:
                        require(
                            interval == check[metric],
                            "Exact absolute-error extrema differ",
                        )
                    else:
                        overlaps(interval, check[metric], "Hellinger enclosure")
            else:
                require(
                    row.get("conditional_metric_ranges_exact") is None,
                    "Unresolved prediction acquired a score",
                )
            own_ranges = (
                score_ranges(
                    _exact_bounds(own_family["prediction_bounds_exact"][0]), observed
                )
                if own_family["status"] == ENCLOSED
                else None
            )
        own_rows.append(
            {
                "context_id": key,
                "core": old["core"],
                "window": old["window"],
                "family": family,
                "status": own_family["status"],
                "conditional_metric_ranges_exact": None
                if own_ranges is None
                else {m: encoded(v) for m, v in own_ranges.items()},
            }
        )
    require(
        seen == {(key, family) for key in sources for family in FAMILIES},
        "Missing family/context disposition",
    )
    return own_rows


def _summary(
    scores: Sequence[Mapping[str, Any]], legacy: Mapping[str, Any]
) -> dict[str, Any]:
    old_families = {row["family"]: row for row in legacy["summaries"]["families"]}
    old_pairs = {
        (row["first_family"], row["second_family"]): row
        for row in legacy["summaries"]["pairwise"]
    }
    require(
        set(old_families) == set(FAMILIES)
        and len(legacy["summaries"]["families"]) == 3
        and set(old_pairs) == set(combinations(FAMILIES, 2))
        and len(legacy["summaries"]["pairwise"]) == 3,
        "Legacy aggregate population differs",
    )
    families: list[dict[str, Any]] = []
    for family in FAMILIES:
        selected = [r for r in scores if r["family"] == family]
        row: dict[str, Any] = {
            "family": family,
            "status": UNRESOLVED,
            "legacy_point_metrics": old_families[family]["equal_place"]["metrics"],
        }
        require(len(selected) == 18, "Incomplete family aggregate")
        if all(r["conditional_metric_ranges_exact"] is not None for r in selected):
            places: list[dict[str, Any]] = []
            for core in CORES:
                subset = [r for r in selected if r["core"] == core]
                require(
                    len(subset) == 6 and len({tuple(r["window"]) for r in subset}) == 6,
                    "Aggregate dropped a window",
                )
                averages = average_ranges(
                    [
                        {
                            m: _exact_bounds(r["conditional_metric_ranges_exact"][m])
                            for m in METRICS
                        }
                        for r in subset
                    ]
                )
                places.append(
                    {
                        "core": core,
                        "conditional_metric_ranges_exact": {
                            m: encoded(v) for m, v in averages.items()
                        },
                    }
                )
            averages = average_ranges(
                [
                    {
                        m: _exact_bounds(r["conditional_metric_ranges_exact"][m])
                        for m in METRICS
                    }
                    for r in places
                ]
            )
            row.update(
                status=DIRECT if family == FAMILIES[0] else ENCLOSED,
                places=places,
                equal_place={
                    "conditional_metric_ranges_exact": {
                        m: encoded(v) for m, v in averages.items()
                    },
                    "legacy_point_metrics": old_families[family]["equal_place"][
                        "metrics"
                    ],
                },
            )
        families.append(row)
    pairs = []
    for first, second in combinations(families, 2):
        key = first["family"], second["family"]
        row = {
            "first_family": key[0],
            "second_family": key[1],
            "status": UNRESOLVED,
            "metrics": None,
        }
        if first["status"] != UNRESOLVED and second["status"] != UNRESOLVED:
            metrics = {}
            for metric in METRICS:
                a = _exact_bounds(
                    first["equal_place"]["conditional_metric_ranges_exact"][metric]
                )
                b = _exact_bounds(
                    second["equal_place"]["conditional_metric_ranges_exact"][metric]
                )
                lower, upper = a.lower - b.upper, a.upper - b.lower
                metrics[metric] = {
                    "conditional_difference_range_exact": [str(lower), str(upper)],
                    "legacy_point_difference": old_pairs[key]["metrics"][metric][
                        "point_difference"
                    ],
                    "conditional_resolution": UNRESOLVED
                    if lower <= 0 <= upper
                    else "separated_continuous_law",
                }
            row.update(status=ENCLOSED, metrics=metrics)
        pairs.append(row)
    return {"families": families, "pairwise": pairs}


def audit(
    protocol: Mapping[str, Any],
    public_source: Mapping[str, Any],
    original_protocol: Mapping[str, Any],
    capture_freeze: Mapping[str, Any],
    original_prediction: Mapping[str, Any],
    original_scored: Mapping[str, Any],
    certificates: Mapping[str, Any],
    prediction_packet: Mapping[str, Any],
    result: Mapping[str, Any],
    clock: Clock,
) -> dict[str, Any]:
    """Qualify own wider score bounds without promoting the old EPS diagnostic."""
    geometries, edges = select_sources(
        protocol, public_source, original_protocol, capture_freeze, original_prediction
    )
    contribution = "frontier" in protocol
    require(
        certificates.get("schema_version") == "continuous-receiver-ring-certificates.v1"
        and prediction_packet.get("schema_version")
        == "continuous-receiver-ring-predictions.v1"
        and result.get("schema_version") == "continuous-receiver-ring-result.v1"
        and prediction_packet.get("source_commit") == result.get("source_commit")
        and prediction_packet.get("source_prediction_commit")
        == original_prediction.get("source_commit")
        == original_scored.get("source_commit"),
        "Closed packet source/schema identity differs",
    )
    cases = certificates.get("cases")
    require(
        isinstance(cases, list) and len(cases) == 6,
        "Incomplete six-case proof population",
    )
    cases = cast(list[dict[str, Any]], cases)
    independent = []
    for i, ((core, taxon), row) in enumerate(zip(OWNERS, cases, strict=True)):
        require(
            type(row.get("case_index")) is int
            and row["case_index"] == i
            and row.get("core") == core
            and row.get("taxon") == taxon,
            "Case index/owner/order differs",
        )
        clock.current_case = (core, taxon)
        independent.append(
            verify_ring_case(
                row, geometries[i], edges[i], clock, contribution=contribution
            )
        )
    complete = all(r["complete"] for r in independent)
    require(
        result.get("all_endpoint_partitions_complete") is complete,
        "Complete partition flag differs",
    )
    require(
        result.get("all_774_raw_endpoint_widths_pass")
        is all(r["raw_endpoint_widths_pass"] for r in cases)
        and result.get("all_18_coefficient_widths_pass")
        is all(r["all_final_widths_pass"] for r in cases),
        "Native diagnostic precision flags differ",
    )
    require(
        _same_json(
            result.get("counts"),
            {"cases": 6, "endpoint_slots": 774, "contexts": 18, "family_slots": 54},
        ),
        "Fixed scientific population counts differ",
    )
    elapsed, integration = (
        finite(result.get("elapsed_seconds")),
        finite(result.get("integration_elapsed_seconds")),
    )
    peak = result.get("peak_rss_bytes")
    require(
        type(peak) is int and peak > 0 and 0 <= integration <= elapsed,
        "Invalid actual resource facts",
    )
    peak = cast(int, peak)
    resource_pass = elapsed < 180 and peak <= 805306368
    require(
        result.get("source_guards_pass") is True
        and result.get("resource_guards_pass") is resource_pass,
        "Source/resource guard falsely promoted",
    )
    expected_status = (
        "continuous_law_bounds"
        if resource_pass and complete
        else "refuse_incomplete"
        if resource_pass
        else "refuse_resources"
    )
    require(
        result.get("status") == expected_status, "Producer terminal disposition differs"
    )
    sources, own_contexts = _audit_contexts(
        original_prediction, prediction_packet, cases, independent, geometries, edges
    )
    own_scores = _audit_scores(
        sources, own_contexts, prediction_packet, original_scored, result
    )
    require(
        _same_json(result.get("summary"), _summary(result["scores"], original_scored)),
        "Saved equal-place/pairwise aggregate falsified",
    )
    usable = sum(
        all(row["families"][family]["status"] == ENCLOSED for family in FAMILIES[1:])
        for row in own_contexts.values()
    )
    own_epsilon = complete and all(
        row["width_account"]["all_original_epsilon_widths_pass"] for row in independent
    )
    endpoint_precision = complete and all(
        q is not None and q.width <= Fraction(1, 10**10)
        for row in independent
        for q in row["own_q"]
    )
    own_cases = [
        {
            "case_index": i,
            "core": core,
            "taxon": taxon,
            "complete": row["complete"],
            "width_account": row.get("width_account"),
            **(
                {
                    "own_q_uncertainty_spreads_exact": row[
                        "q_uncertainty_spreads_exact"
                    ],
                    "own_q_uncertainty_target_pass": row["q_uncertainty_target_pass"],
                    "native_q_uncertainty_spreads_exact": cases[i][
                        "q_uncertainty_spreads_exact"
                    ],
                    "native_q_uncertainty_target_pass": cases[i][
                        "q_uncertainty_target_pass"
                    ],
                }
                if contribution
                else {}
            ),
        }
        for i, ((core, taxon), row) in enumerate(zip(OWNERS, independent, strict=True))
    ]
    return {
        "status": "passed"
        if resource_pass and complete and usable == 18
        else "refuse_unresolved",
        "accounting_verified": True,
        "complete_cases": sum(row["complete"] for row in independent),
        "own_774_endpoint_widths_pass": endpoint_precision,
        "own_18_original_epsilon_widths_pass": own_epsilon,
        **(
            {
                "own_all_case_q_uncertainty_targets_pass": complete
                and all(row["q_uncertainty_target_pass"] for row in independent)
            }
            if contribution
            else {}
        ),
        "usable_prediction_contexts": usable,
        "cases": own_cases,
        "contexts": list(own_contexts.values()),
        "scores": own_scores,
        "summary": _summary(own_scores, original_scored),
        "scope": "Independent fixed-leaf geometry/Peano/ring/score audit reuses reviewed elementary Interval/Jet primitives. Wider valid prediction bounds do not satisfy the separate original coefficient EPS, authenticate historical A or validate field vegetation.",
    }
