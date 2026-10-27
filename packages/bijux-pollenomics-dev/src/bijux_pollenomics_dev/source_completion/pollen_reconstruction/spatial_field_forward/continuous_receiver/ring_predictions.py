"""Count-free continuous-ring prediction bounds and closed-packet scoring."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any

from .. import radial_envelope as exact
from ..radial_envelope_workflow import average_ranges
from .arithmetic import Interval
from .coefficients import EPSILON
from .ring_bounds import RingCaseResult, deposition_bounds
from .study_inputs import AXIS, CORES, OWNERS, decode_json, finite, require

FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)
PREDICTION_SCHEMA = "continuous-receiver-ring-predictions.v1"
ENCLOSED = "continuous_law_enclosure"
UNRESOLVED = "unresolved_continuous_law"
DIRECT = "fixed_saved_point_reference"


def _owner(record: dict[str, Any]) -> dict[str, Any]:
    require(record["core"] in CORES, "Foreign physical core")
    for name in ("site_id", "dataset_id", "collection_unit_id"):
        require(
            type(record[name]) is int and record[name] > 0,
            "Invalid native source owner",
        )
    window = record["window"]
    require(
        type(window) is list
        and len(window) == 2
        and all(type(value) is int for value in window)
        and window[0] < window[1],
        "Invalid source window",
    )
    samples = record["sample_ids"]
    require(
        type(samples) is list
        and bool(samples)
        and all(type(value) is int and value > 0 for value in samples)
        and len(samples) == len(set(samples)),
        "Invalid native sample population",
    )
    return {
        name: record[name]
        for name in (
            "core",
            "site_id",
            "dataset_id",
            "collection_unit_id",
            "window",
            "sample_ids",
        )
    }


def _vector(values: Any) -> tuple[Fraction, Fraction]:
    require(
        type(values) is list and len(values) == 2,
        "Two original finite components required",
    )
    result = finite(values[0]), finite(values[1])
    require(
        all(0 <= value <= 1 for value in result) and sum(result) > 0,
        "Invalid original cover/fraction domain",
    )
    # Both source components remain exact; neither is reclosed or imputed.
    return result


def _contexts(
    prediction: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    require(prediction["axis"] == list(AXIS), "Prediction taxon axis differs")
    require(
        len(prediction["ppe"]) == 2
        and all(finite(value) > 0 for value in prediction["ppe"]),
        "Invalid fixed PPE axis",
    )
    geometries = prediction["geometry"]
    require(
        type(geometries) is list and [row["core"] for row in geometries] == list(CORES),
        "Geometry owner/order differs",
    )
    geometry = {row["core"]: row for row in geometries}
    rows = prediction["contexts"]
    require(
        type(rows) is list
        and len(rows) == 18
        and len({row["context_id"] for row in rows}) == 18,
        "Eighteen unique contexts required",
    )
    windows: dict[str, set[tuple[int, int]]] = {core: set() for core in CORES}
    for context in rows:
        owner = _owner(context["target"])
        core = owner["core"]
        require(
            type(context["context_id"]) is str and context["geometry_core"] == core,
            "Context geometry owner differs",
        )
        window = owner["window"][0], owner["window"][1]
        require(window not in windows[core], "Duplicate core/window")
        windows[core].add(window)
        require(
            finite(context["target"]["radius_m"]) == finite(geometry[core]["radius_m"]),
            "Target radius/geometry owner differs",
        )
        anchors = [name for name in CORES if name != core]
        require(
            geometry[core]["anchor_order"] == anchors
            and [row["core"] for row in context["training"]] == anchors,
            "Held-place anchor order differs",
        )
        target_samples = set(owner["sample_ids"])
        seen: set[int] = set()
        for row in context["training"]:
            source = _owner(row)
            require(
                source["window"] == owner["window"]
                and not target_samples.intersection(source["sample_ids"])
                and not seen.intersection(source["sample_ids"]),
                "Training window/sample ownership differs",
            )
            seen.update(source["sample_ids"])
            require(
                finite(row["radius_m"]) == finite(geometry[row["core"]]["radius_m"]),
                "Training radius/geometry owner differs",
            )
            _vector(row["cover"])
        require(
            set(context["families"]) == set(FAMILIES),
            "Source family population differs",
        )
        for family in FAMILIES:
            require(
                context["families"][family]["status"] == "predicted",
                "Saved prediction is refused",
            )
            _vector(context["families"][family]["pollen_fraction"])
    require(
        all(len(value) == 6 for value in windows.values())
        and windows[CORES[0]] == windows[CORES[1]] == windows[CORES[2]],
        "Six matched windows per physical place required",
    )
    return rows, geometry


def _encoded(interval: Interval) -> list[str]:
    return exact.encoded((interval.lower, interval.upper))


def prediction_contexts(
    prediction: dict[str, Any], case_results: tuple[RingCaseResult, ...]
) -> list[dict[str, Any]]:
    contexts, geometry = _contexts(prediction)
    require(
        type(case_results) is tuple and len(case_results) == len(OWNERS),
        "All six ordered geometry/taxon cases required",
    )
    by_owner = dict(zip(OWNERS, case_results, strict=True))
    captured: dict[str, Fraction] = {}
    for (core, taxon), case in by_owner.items():
        if case.bounds is None:
            continue
        model, source = case.bounds.geometry, geometry[core]
        points = source["anchor_xy_m"]
        require(
            type(points) is list
            and len(points) == 2
            and all(type(point) is list and len(point) == 2 for point in points),
            "Two source anchor vectors required",
        )
        require(
            model.first == tuple(finite(value) for value in points[0])
            and model.second == tuple(finite(value) for value in points[1])
            and model.receiver == finite(source["radius_m"])
            and model.outer == 100000,
            "Continuous case has foreign geometry",
        )
        require(
            taxon not in captured or captured[taxon] == model.coefficient,
            "Mixed captured-A law across cores",
        )
        captured[taxon] = model.coefficient
    result = []
    for context in contexts:
        owner = _owner(context["target"])
        core = owner["core"]
        family_rows: dict[str, Any] = {}
        direct = context["families"][FAMILIES[0]]["pollen_fraction"]
        family_rows[FAMILIES[0]] = {
            "status": DIRECT,
            "prediction_bounds_exact": [
                exact.encoded((value, value)) for value in _vector(direct)
            ],
            "deposition_bounds_exact": None,
            "coefficient_precision_pass": None,
            "refusal": None,
        }
        cases = tuple(by_owner[(core, taxon)] for taxon in AXIS)
        precision = all(
            case.bounds is not None
            and all(
                value.width <= EPSILON
                for value in (
                    case.bounds.homogeneous,
                    case.bounds.first,
                    case.bounds.second,
                )
            )
            for case in cases
        )
        for family in FAMILIES[1:]:
            record: dict[str, Any] = {
                "status": UNRESOLVED,
                "prediction_bounds_exact": None,
                "deposition_bounds_exact": None,
                "coefficient_precision_pass": precision,
                "refusal": None,
            }
            if any(case.bounds is None for case in cases):
                record["refusal"] = "incomplete_continuous_geometry"
                family_rows[family] = record
                continue
            deposits = []
            for index, case in enumerate(cases):
                bounds = case.bounds
                assert bounds is not None
                first, second = (
                    finite(row["cover"][index]) for row in context["training"]
                )
                if family == FAMILIES[2]:
                    deposit = deposition_bounds(bounds, first, second)
                else:
                    aa = sum(
                        (value * value for value in bounds.geometry.first), Fraction(0)
                    )
                    bb = sum(
                        (value * value for value in bounds.geometry.second), Fraction(0)
                    )
                    require(aa + bb > 0, "Undefined exact centre weights")
                    cover = (bb * first + aa * second) / (aa + bb)
                    deposit = bounds.homogeneous * cover
                deposits.append(deposit * finite(prediction["ppe"][index]))
            record["deposition_bounds_exact"] = [_encoded(value) for value in deposits]
            if any(value.lower <= 0 for value in deposits):
                record["refusal"] = "positive_deposition_not_established"
            else:
                probability = exact.normalized(
                    (
                        (deposits[0].lower, deposits[0].upper),
                        (deposits[1].lower, deposits[1].upper),
                    )
                )
                record.update(
                    status=ENCLOSED,
                    prediction_bounds_exact=[
                        exact.encoded(probability),
                        exact.encoded((1 - probability[1], 1 - probability[0])),
                    ],
                )
            family_rows[family] = record
        result.append(
            {
                "context_id": context["context_id"],
                "core": core,
                "window": owner["window"],
                "sample_ids": owner["sample_ids"],
                "target_owner": owner,
                "training_owners": [_owner(row) for row in context["training"]],
                "geometry_refusals": [
                    {"taxon": taxon, "refusal": case.refusal}
                    for taxon, case in zip(AXIS, cases, strict=True)
                ],
                "families": family_rows,
            }
        )
    return result


def score_closed(
    path: Path, original_scored: dict[str, Any], original_prediction: dict[str, Any]
) -> list[dict[str, Any]]:
    """Load the closed count-free packet before consulting exposed observations."""
    packet = decode_json(path.read_bytes())
    require(
        packet["schema_version"] == PREDICTION_SCHEMA
        and packet["source_prediction_commit"] == original_prediction["source_commit"],
        "Closed prediction source identity differs",
    )
    native_contexts, _ = _contexts(original_prediction)
    references = {row["context_id"]: row for row in native_contexts}
    closed_rows = packet["contexts"]
    require(
        len(closed_rows) == 18
        and len({row["context_id"] for row in closed_rows}) == 18
        and {row["context_id"] for row in closed_rows} == set(references),
        "Closed prediction context population differs",
    )
    closed = {row["context_id"]: row for row in closed_rows}
    for key, context in closed.items():
        reference = references[key]
        owner = _owner(reference["target"])
        require(
            context["core"] == owner["core"]
            and context["window"] == owner["window"]
            and context["sample_ids"] == owner["sample_ids"]
            and context["target_owner"] == owner
            and context["training_owners"]
            == [_owner(row) for row in reference["training"]]
            and set(context["families"]) == set(FAMILIES),
            "Closed prediction native ownership differs",
        )
    require(
        original_scored["source_commit"] == original_prediction["source_commit"]
        and len(original_scored["scores"]) == 54,
        "Saved score source/population differs",
    )
    scores = []
    seen: set[tuple[str, str]] = set()
    observed: dict[str, list[float]] = {}
    for old in original_scored["scores"]:
        key, family = old["context_id"], old["family"]
        require(
            key in references
            and family in FAMILIES
            and (key, family) not in seen
            and old["status"] == "scored",
            "Duplicate, foreign or refused saved score",
        )
        seen.add((key, family))
        reference, context = references[key], closed[key]
        require(
            old["core"] == context["core"]
            and old["window"] == context["window"]
            and old["sample_ids"] == context["sample_ids"]
            and old["predicted_fraction"]
            == reference["families"][family]["pollen_fraction"],
            "Saved score/prediction ownership differs",
        )
        _vector(old["observed_fraction"])
        require(
            key not in observed or observed[key] == old["observed_fraction"],
            "Observed vector differs across families",
        )
        observed[key] = old["observed_fraction"]
        legacy = {metric: old[metric] for metric in exact.METRICS}
        require(
            all(finite(value) >= 0 for value in legacy.values()), "Invalid saved metric"
        )
        result: dict[str, Any] = {
            "context_id": key,
            "core": old["core"],
            "window": old["window"],
            "sample_ids": old["sample_ids"],
            "family": family,
            "observed_fraction": old["observed_fraction"],
            "legacy_point_score": legacy,
            "status": UNRESOLVED,
            "conditional_metric_ranges_exact": None,
        }
        row = context["families"][family]
        if family == FAMILIES[0]:
            expected = [
                exact.encoded((value, value))
                for value in _vector(old["predicted_fraction"])
            ]
            require(
                row["status"] == DIRECT and row["prediction_bounds_exact"] == expected,
                "Direct saved finite vector changed",
            )
            result.update(
                status=DIRECT,
                conditional_metric_ranges_exact={
                    metric: exact.encoded((finite(value), finite(value)))
                    for metric, value in legacy.items()
                },
            )
        elif row["status"] == ENCLOSED:
            ranges = row["prediction_bounds_exact"]
            require(
                type(ranges) is list and len(ranges) == 2,
                "Two continuous prediction bounds required",
            )
            first, second = exact.decoded(ranges[0]), exact.decoded(ranges[1])
            require(
                0 <= first[0] <= first[1] <= 1
                and second == (1 - first[1], 1 - first[0]),
                "Continuous closure bounds differ",
            )
            result.update(
                status=ENCLOSED,
                conditional_metric_ranges_exact=exact.metric_ranges(
                    first, old["observed_fraction"]
                ),
            )
        else:
            require(
                row["status"] == UNRESOLVED and row["prediction_bounds_exact"] is None,
                "Unknown continuous prediction status",
            )
        scores.append(result)
    require(
        seen == {(key, family) for key in references for family in FAMILIES},
        "Incomplete 54-slot score population",
    )
    return scores


def summarize(
    scores: list[dict[str, Any]], old_scored: dict[str, Any]
) -> dict[str, Any]:
    require(
        len(scores) == 54
        and len({(row["context_id"], row["family"]) for row in scores}) == 54,
        "Complete unique score population required",
    )
    old_rows = {(row["context_id"], row["family"]): row for row in old_scored["scores"]}
    require(
        len(old_scored["scores"]) == len(old_rows) == 54
        and set(old_rows) == {(row["context_id"], row["family"]) for row in scores},
        "Aggregate context/family owners differ",
    )
    for row in scores:
        old = old_rows[(row["context_id"], row["family"])]
        require(
            all(row[name] == old[name] for name in ("core", "window", "sample_ids")),
            "Aggregate native source ownership differs",
        )
    summaries = old_scored["summaries"]
    old_families = {row["family"]: row for row in summaries["families"]}
    require(
        len(summaries["families"]) == 3 and set(old_families) == set(FAMILIES),
        "Saved family aggregate population differs",
    )
    families = []
    for family in FAMILIES:
        rows = [row for row in scores if row["family"] == family]
        require(
            len(rows) == 18 and {row["core"] for row in rows} == set(CORES),
            "Eighteen family contexts required",
        )
        for core in CORES:
            selected = [row for row in rows if row["core"] == core]
            require(
                len(selected) == 6
                and len({tuple(row["window"]) for row in selected}) == 6,
                "Six unique windows per place required",
            )
        record: dict[str, Any] = {
            "family": family,
            "status": UNRESOLVED,
            "legacy_point_metrics": old_families[family]["equal_place"]["metrics"],
        }
        if all(row["conditional_metric_ranges_exact"] is not None for row in rows):
            places = [
                {
                    "core": core,
                    "conditional_metric_ranges_exact": average_ranges(
                        [row for row in rows if row["core"] == core]
                    ),
                }
                for core in CORES
            ]
            record.update(
                status=DIRECT if family == FAMILIES[0] else ENCLOSED,
                places=places,
                equal_place={
                    "conditional_metric_ranges_exact": average_ranges(places),
                    "legacy_point_metrics": old_families[family]["equal_place"][
                        "metrics"
                    ],
                },
            )
        families.append(record)
    old_pairs = {
        (row["first_family"], row["second_family"]): row
        for row in summaries["pairwise"]
    }
    require(
        len(summaries["pairwise"]) == 3
        and set(old_pairs) == set(combinations(FAMILIES, 2)),
        "Saved pairwise population differs",
    )
    pairs = []
    for first, second in combinations(families, 2):
        key = first["family"], second["family"]
        pair_record: dict[str, Any] = {
            "first_family": key[0],
            "second_family": key[1],
            "status": UNRESOLVED,
            "metrics": None,
        }
        if first["status"] != UNRESOLVED and second["status"] != UNRESOLVED:
            metrics = {}
            for metric in exact.METRICS:
                a, b = (
                    exact.decoded(
                        first["equal_place"]["conditional_metric_ranges_exact"][metric]
                    ),
                    exact.decoded(
                        second["equal_place"]["conditional_metric_ranges_exact"][metric]
                    ),
                )
                difference = a[0] - b[1], a[1] - b[0]
                metrics[metric] = {
                    "conditional_difference_range_exact": exact.encoded(difference),
                    "legacy_point_difference": old_pairs[key]["metrics"][metric][
                        "point_difference"
                    ],
                    "conditional_resolution": "unresolved_continuous_law"
                    if difference[0] <= 0 <= difference[1]
                    else "separated_continuous_law",
                }
            pair_record.update(status=ENCLOSED, metrics=metrics)
        pairs.append(pair_record)
    return {"families": families, "pairwise": pairs}
