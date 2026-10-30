"""All-replicate scalar audit, conditional on independently authenticated inputs."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from .algebra import (
    METHODS,
    case_arrays,
    compare,
    finite,
    owner_stream_key,
    pair,
    replay_draws,
    require,
)
from .summaries import reference_summaries

__all__ = ["audit"]

NAMES = tuple(f"cal-bp-{younger}-{younger + 500}" for younger in range(2700, 5700, 500))
SOURCES = {
    "BOKE": (54001, 39241),
    "BUS": (53995, 39238),
    "SOLSOE83": (4446, 4304),
    "KRAGMJNY": (23013, 16622),
}


def _owner(core: str, window: str) -> str:
    dataset, unit = SOURCES[core]
    return f"neotoma-{dataset}-{unit}-{window}"


def _profile(packet: Mapping[str, Any]) -> tuple[int, int, float, float]:
    protocol = packet["protocol"]
    sampling = protocol["sampling"]
    require(
        protocol["schema_version"] == "krageholm-predictive-uncertainty.v1",
        "protocol schema",
    )
    for field, expected in (("replicates", 1024), ("seed", 20261027)):
        require(
            type(sampling[field]) is int and sampling[field] == expected,
            "fixed " + field,
        )
    compare(sampling["taxa"], ["Betula", "Ulmus"])
    compare(sampling["ppe_means"], [5.106, 1.27], tolerance=0)
    compare(sampling["ppe_sds"], [0.303, 0.05], tolerance=0)
    require(sampling["bit_generator"] == "PCG64", "declared bit generator")
    require(
        sampling["count_stream"]
        == "SeedSequence(seed, spawn_key=(0, *eight_big_endian_uint32_words_of_SHA256_UTF8_owner_id))"
        and sampling["ppe_stream"] == "SeedSequence(seed, spawn_key=(1,))",
        "declared independent source streams",
    )
    compare(packet["accounting"]["sampling"], sampling, tolerance=0)
    population = protocol["population"]
    for field, expected in {
        "original_folds": 18,
        "original_method_dispositions": 54,
        "active_folds": 3,
        "propagated_method_slots": 9,
        "original_refused_slots_retained": 45,
        "draw_owner_count": 4,
        "other_metadata_owner_count": 20,
    }.items():
        require(
            type(population[field]) is int and population[field] == expected,
            "fixed population " + field,
        )
    compare(population["active_window_cal_bp"], [2700, 3200])
    checks = protocol["numerical_checks"]
    require(
        checks["no_clipping_or_single_predictor_fallback"] is True,
        "no fallback/clip contract",
    )
    require(
        finite(checks["nominal_prediction_absolute_tolerance"]) == 1e-12,
        "nominal tolerance",
    )
    atol, rtol = (
        finite(checks["independent_absolute_tolerance"]),
        finite(checks["independent_relative_tolerance"]),
    )
    require(atol == 1e-13 and rtol == 1e-10, "prospective numerical tolerances")
    summaries = protocol["summaries"]
    require(
        type(summaries["conditional_population_covariance_ddof"]) is int
        and summaries["conditional_population_covariance_ddof"] == 0,
        "population covariance divisor",
    )
    compare(summaries["quantile_probabilities"], [0.025, 0.5, 0.975], tolerance=0)
    require(summaries["quantile_method"] == "linear", "quantile method")
    return sampling["replicates"], sampling["seed"], atol, rtol


def _population(
    packet: Mapping[str, Any],
) -> tuple[dict[str, list[int]], list[dict[str, Any]]]:
    owners = packet["owners"]
    expected = {_owner(core, window) for window in NAMES for core in SOURCES}
    require(
        len(owners) == 24 and {row["owner_id"] for row in owners} == expected,
        "all 24 original owner/windows",
    )
    counts: dict[str, list[int]] = {}
    for row in owners:
        require(set(row) == {"owner_id", "counts"}, "owner fields")
        values = row["counts"]
        require(
            len(values) == 2
            and all(type(value) is int and value >= 0 for value in values)
            and 0 < sum(values) <= 2**53,
            "native owner counts",
        )
        counts[row["owner_id"]] = list(values)
        lineage = packet["accounting"]["owner_lineage"][row["owner_id"]]
        require(
            type(lineage["panel_N"]) is int and lineage["panel_N"] == sum(values),
            "source panel denominator",
        )
        require(
            type(lineage["projection"]["projected_panel_N"]) is int
            and lineage["projection"]["projected_panel_N"] == sum(values),
            "qualified projected panel denominator",
        )
    require(
        set(packet["accounting"]["owner_lineage"]) == expected,
        "source lineage owner set",
    )
    require(
        packet["accounting"]["all_source_fingerprints_role"]
        == "accounting_only_not_fold_scientific_ancestry",
        "source-wide accounting role",
    )
    folds, cases = packet["folds"], packet["cases"]
    require(
        len(folds) == len({row["case_id"] for row in folds}) == 18,
        "all 18 unique folds",
    )
    require(
        len(cases) == len({row["case_id"] for row in cases}) == 3,
        "all three active folds",
    )
    active = {row["case_id"] for row in cases}
    for case in cases:
        require(
            set(case)
            == {
                "case_id",
                "target_id",
                "regional_owner_id",
                "local_owners",
                "regional_deposition",
                "forward_local_k",
                "forward_regional_k",
                "terrestrial_fraction",
                "distances_km",
                "selected_ring_index",
            },
            "closed numerical fold fields",
        )
        pair(case["regional_deposition"], positive=True)
        pair(case["forward_regional_k"])
        pair(case["distances_km"], positive=True)
        require(
            len(case["local_owners"]) == len(case["forward_local_k"]) == 2,
            "two saved predictor/ring axes",
        )
        compare(case["terrestrial_fraction"], [1.0, 1.0], tolerance=0)
        for ring in case["forward_local_k"]:
            pair(ring)
        for local in case["local_owners"]:
            require(
                set(local) == {"owner_id", "local_k", "regional_k"},
                "closed local kernel fields",
            )
            for field in ("local_k", "regional_k"):
                require(len(local[field]) == 2, "two inversion rings")
                for ring in local[field]:
                    pair(ring, positive=True)
    require(
        {row["target_id"] for row in cases}
        == {_owner(core, NAMES[0]) for core in SOURCES if core != "KRAGMJNY"},
        "three original active targets",
    )
    for window in NAMES:
        rows = [row for row in folds if row["bin"] == window]
        require(
            len(rows) == 3
            and {row["target_id"] for row in rows}
            == {_owner(core, window) for core in SOURCES if core != "KRAGMJNY"},
            "three targets in every original bin",
        )
    for fold in folds:
        require(fold["case_id"] == fold["bin"] + ":" + fold["fold_id"], "fold identity")
        regional = _owner("KRAGMJNY", fold["bin"])
        locals_ = sorted(
            expected.intersection({_owner(core, fold["bin"]) for core in SOURCES})
            - {regional, fold["target_id"]}
        )
        require(
            fold["regional_owner_id"] == regional
            and fold["local_owner_ids"] == locals_,
            "regional-only KRAG and exact local training owners",
        )
        require(
            fold["nominal_status"]
            == ("predicted" if fold["case_id"] in active else "refused"),
            "immutable nominal eligibility",
        )
        references = [
            packet["accounting"]["owner_lineage"][owner_id]["raw"]
            for owner_id in [regional, *locals_]
        ]
        compare(fold["scientific_count_refs"], references, tolerance=0)
        if fold["case_id"] in active:
            case = next(row for row in cases if row["case_id"] == fold["case_id"])
            require(
                case["target_id"] == fold["target_id"]
                and case["regional_owner_id"] == regional
                and [row["owner_id"] for row in case["local_owners"]] == locals_,
                "active numerical source roles",
            )
            require(fold["nominal_refusal"] is None, "active nominal refusal")
    dispositions = packet["dispositions"]
    require(len(dispositions) == 54, "all original method dispositions")
    expected_dispositions = [
        (row["bin"], row["fold_id"], method) for row in folds for method in METHODS
    ]
    require(
        [(row["bin"], row["fold_id"], row["method"]) for row in dispositions]
        == expected_dispositions,
        "ordered complete dispositions",
    )
    for fold in folds:
        rows = [
            row
            for row in dispositions
            if row["bin"] == fold["bin"] and row["fold_id"] == fold["fold_id"]
        ]
        require(
            all(row["status"] == fold["nominal_status"] for row in rows),
            "preserved disposition status",
        )
        if fold["nominal_status"] == "refused":
            compare(
                fold["nominal_refusal"],
                [
                    {
                        key: value
                        for key, value in row.items()
                        if key not in ("bin", "fold_id", "method")
                    }
                    for row in rows
                ],
                tolerance=0,
            )
    active_ids = sorted(
        {row["regional_owner_id"] for row in cases}
        | {local["owner_id"] for row in cases for local in row["local_owners"]}
    )
    require(len(active_ids) == 4, "only four active draw owners")
    compare(packet["accounting"]["active_draw_owner_ids"], active_ids)
    return {owner_id: counts[owner_id] for owner_id in active_ids}, list(cases)


def _draws(
    packet: Mapping[str, Any], active: Mapping[str, list[int]], total: int, seed: int
) -> dict[str, Any]:
    ppe, owners = replay_draws(
        active, [5.106, 1.27], [0.303, 0.05], replicates=total, seed=seed
    )
    expected = {
        "replicates": total,
        "seed": seed,
        "ppe_means": [5.106, 1.27],
        "ppe_sds": [0.303, 0.05],
        "ppe": ppe,
        "owners": [
            {
                "owner_id": owner_id,
                "stream_index": list(owner_stream_key(owner_id)[1:]),
                "counts": active[owner_id],
                "samples": owners[owner_id],
            }
            for owner_id in sorted(active)
        ],
    }
    compare(packet, expected, tolerance=0)
    return expected


def _nominal(
    packet: Mapping[str, Any], cases: list[dict[str, Any]], bank: dict[str, Any]
) -> list[dict[str, Any]]:
    nominal = packet["nominal_predictions"]
    require(
        len(nominal) == 9
        and len({(row["case_id"], row["method"]) for row in nominal}) == 9,
        "all nine closed nominal predictions",
    )
    nominal_bank = {
        **bank,
        "replicates": 1,
        "ppe": [[5.106, 1.27]],
        "owners": [{**row, "samples": [row["counts"]]} for row in bank["owners"]],
    }
    references = []
    for case in cases:
        expected = case_arrays(case, nominal_bank)
        for method in METHODS:
            matches = [
                row
                for row in nominal
                if row["case_id"] == case["case_id"] and row["method"] == method
            ]
            require(len(matches) == 1, "exact nominal case/method")
            row = matches[0]
            require(
                expected["methods"][method]["valid_mask"] == [True],
                "nominal eligibility replay",
            )
            compare(
                row["pollen_fraction"],
                expected["methods"][method]["pollen"][0],
                tolerance=1e-12,
            )
            compare(
                row["vegetation_fraction"],
                expected["methods"][method]["cover"][0],
                tolerance=1e-12,
            )
            compare(
                row["regional_cover"], expected["regional_cover"][0], tolerance=1e-12
            )
            references.append(
                {
                    "case_id": case["case_id"],
                    "target_id": case["target_id"],
                    "method": method,
                    "pollen_fraction": expected["methods"][method]["pollen"][0],
                    "vegetation_fraction": expected["methods"][method]["cover"][0],
                    "reference_prediction_manifest_sha256": row[
                        "prediction_manifest_sha256"
                    ],
                }
            )
    return references


def audit(
    input_packet: Mapping[str, Any],
    draw_packet: Mapping[str, Any],
    prediction_packet: Mapping[str, Any],
    summary_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify the complete finite experiment after its source/readback guards close."""
    total, seed, atol, rtol = _profile(input_packet)
    active, cases = _population(input_packet)
    bank = _draws(draw_packet, active, total, seed)
    nominal = _nominal(input_packet, cases, bank)
    expected_predictions = [case_arrays(case, bank) for case in cases]
    require(
        set(prediction_packet)
        == {"schema_version", "cases", "original_dispositions", "nominal_predictions"},
        "prediction packet fields",
    )
    require(
        prediction_packet["schema_version"] == "krageholm-predictive-ensemble.v1",
        "prediction schema",
    )
    compare(
        prediction_packet["cases"],
        expected_predictions,
        tolerance=atol,
        relative_tolerance=rtol,
    )
    compare(
        prediction_packet["original_dispositions"],
        input_packet["dispositions"],
        tolerance=0,
    )
    compare(prediction_packet["nominal_predictions"], nominal, tolerance=1e-12)
    observed = summary_packet["score_diagnostics"]["observed"]
    require(
        len(observed) == 3 and len({row["case_id"] for row in observed}) == 3,
        "three observed diagnostic owners",
    )
    for row in observed:
        matching = [case for case in cases if case["case_id"] == row["case_id"]]
        require(
            len(matching) == 1 and row["target_id"] == matching[0]["target_id"],
            "diagnostic target owner",
        )
        counts = active[row["target_id"]]
        compare(row["counts"], counts, tolerance=0)
        compare(
            row["counts_source_reference"],
            input_packet["accounting"]["owner_lineage"][row["target_id"]]["raw"],
            tolerance=0,
        )
        compare(
            row["pollen_fraction"],
            [value / sum(counts) for value in counts],
            tolerance=0,
        )
    access = summary_packet["outcome_access"]
    require(
        set(access) == {"prediction_manifest_sha256", "readback_verified", "scope"},
        "outcome access fields",
    )
    require(
        isinstance(access["prediction_manifest_sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", access["prediction_manifest_sha256"])
        is not None,
        "prediction readback identity",
    )
    require(
        access["readback_verified"] is True
        and access["scope"] == "previously exposed; postfreeze diagnostic only",
        "postfreeze diagnostic scope",
    )
    expected_summary = reference_summaries(expected_predictions, observed, access)
    compare(summary_packet, expected_summary, tolerance=atol, relative_tolerance=rtol)
    return {
        "status": "passed",
        "accounting_verified": True,
        "replicates": total,
        "draw_owners": len(active),
        "original_folds": 18,
        "method_dispositions": 54,
        "retained_nominal_refusals": 45,
        "nominal_predictions_verified": 9,
        "replicate_method_slots_verified": total * 9,
        "joint_defined_replicates": {
            method: expected_summary["joint_predictions"][method]["physical"][
                "defined_replicates"
            ]
            for method in METHODS
        },
        "primitive_reuse": "NumPy PCG64/SeedSequence only; independent scalar reconstruction, admission, interpolation, forward, summaries and losses",
        "scope": "Conditional count/PPE working law on saved finite kernels and static geometry; no field coverage or untouched confirmation",
    }
