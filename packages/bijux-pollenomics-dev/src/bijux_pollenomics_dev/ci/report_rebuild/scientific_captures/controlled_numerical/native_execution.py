"""Authenticate the completed current-source R/Python controlled execution and prospective limits."""

from __future__ import annotations

from typing import Any

from ...contracts import ReportRebuildError

ORIGINAL_CANDIDATE = "60bf419979bdc682ef227fb01e42a4f5ed6e2722"
ORIGINAL_IDENTITIES = {
    "plan.json": "05ec9e3e9b62b2fd66adc46b03b35a84d8160af62cfe0aa870f73d324f732992",
    "terminal.json": "61f5caac7974da3153499002e48ced4cf776122c374e34c3d1d87be8da7e02cc",
    "controlled-numerical-terminal.json": "383fa532d64a8164888af7f07dc0e93217dee472709694c932bb80b9d6ae7c56",
    "independent-numerical-review.json": "3052379e212388c95c3c1da6e885acc95edde313e4426a7a7e8b5ec14bc09b86",
}
FAMILIES = {
    "optimizer-solution-quality": [
        "python-fits.csv",
        "r-fits.csv",
        "r-session.txt",
        "report.json",
        "summary.csv",
    ],
    "paired-love-draws": [
        "draws.json",
        "python-values.csv",
        "r-session.txt",
        "r-values.csv",
        "report.json",
        "setup.json",
    ],
}


def _require(value: object, message: str) -> None:
    if not value:
        raise ReportRebuildError(message)


def _exact(left: Any, right: Any) -> None:
    _require(type(left) is type(right), "Controlled numerical JSON type differs")
    if isinstance(left, dict):
        _require(set(left) == set(right), "Controlled numerical JSON keys differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list):
        _require(
            len(left) == len(right), "Controlled numerical list membership differs"
        )
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "Controlled numerical JSON value differs")


def native_records(
    plan: dict[str, Any],
    terminal: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
) -> None:
    _require(
        all(
            v["candidate"] == ORIGINAL_CANDIDATE
            for v in (plan, terminal, outer, review)
        ),
        "Original numerical source epoch differs",
    )
    _require(
        all(
            v["plan_sha256"] == ORIGINAL_IDENTITIES["plan.json"]
            for v in (terminal, outer, review)
        ),
        "Original native plan binding differs",
    )
    _require(
        all(
            type(x) is int and x == 0
            for x in (
                terminal["actual_exit"],
                outer["actual_exit"],
                outer["common_actual_exit"],
                review["native_exit"],
            )
        ),
        "Original numerical job was not native zero",
    )
    _require(
        terminal["canonical_before"]
        == terminal["canonical_after"]
        == plan["canonical_identity"]
        and terminal["before_pin_mismatches"] == terminal["after_pin_mismatches"] == []
        and (terminal["absent_input_paths_unchanged"] is True),
        "Original source/runtime custody changed",
    )
    _require(
        outer["common_terminal"]["sha256"] == ORIGINAL_IDENTITIES["terminal.json"]
        and outer["memory_bound_pass"] is True
        and (outer["storage_bound_pass"] is True),
        "Original terminal/resource custody differs",
    )
    _require(
        len(plan["stages"]) == len(terminal["stages"]) == 3,
        "Original three-stage membership differs",
    )
    for intended, actual in zip(plan["stages"], terminal["stages"], strict=True):
        _require(
            intended["id"] == actual["id"]
            and intended["argv"] == actual["argv"]
            and (type(actual["actual_exit"]) is int)
            and (actual["actual_exit"] == 0)
            and (actual["timed_out"] is False),
            "Original native argv/status differs",
        )
    _require(
        [row["id"] for row in review["actual_two_producers"]]
        == [row["id"] for row in plan["stages"][:2]]
        and all(
            type(row["actual_exit"]) is int and row["actual_exit"] == 0
            for row in review["actual_two_producers"]
        ),
        "Original two producer witnesses differ",
    )
    _require(
        review["historical_execution_proofs_recovered"] is False
        and review["fresh_source_R_executed"] is True
        and (review["source_functions_and_tolerances_unchanged"] is True)
        and (review["fresh_scientific_acceptance"] == "not_evaluated"),
        "Original scientific acceptance changed",
    )
    _exact(plan["expected_public_products"], FAMILIES)
    _require(
        len(review["eleven_complete_public_product_comparisons"]) == 11,
        "Original complete product comparison missing",
    )
    expected = {(family, name) for family, names in FAMILIES.items() for name in names}
    _require(
        {
            (row["family"], row["path"])
            for row in review["eleven_complete_public_product_comparisons"]
        }
        == expected,
        "Original product comparison membership differs",
    )
    optimizer = review["findings"]["optimizer-solution-quality"]["scientific_checks"]
    _require(
        optimizer["ordered_cases"] == 3
        and optimizer["cross_evaluation_threshold"] == 1e-10
        and (optimizer["optimum_gap_threshold"] == 0.0001)
        and (optimizer["scientific_acceptance"] == "not_evaluated")
        and all(
            row["R_iteration_cap_not_convergence"] is True for row in optimizer["cases"]
        ),
        "Controlled optimizer limits changed",
    )
    paired = review["findings"]["paired-love-draws"]["scientific_checks"]
    _require(
        paired["paired_finite_values"] == 120
        and paired["paired_missing_values"] == 280
        and (paired["prospective_absolute_tolerance"] == 3e-10)
        and (paired["same_seed_trajectory_claim"] is False)
        and (paired["scientific_acceptance"] == "not_evaluated"),
        "Paired draw limits changed",
    )
    for family in FAMILIES:
        _require(
            review["findings"][family]["namespace_counts"]
            == {
                "before_namespaces": 40,
                "before_DLLs": 29,
                "after_namespaces": 40,
                "after_DLLs": 29,
            },
            "Actual namespace/DLL custody differs",
        )
