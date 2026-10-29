"""Authenticate source-production and saved-observation histories without changing refusals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SOURCE_CANDIDATE = "61eb1bfe697d0e7f15831b9c23bc45322ce042e8"
REFERENCE_SHAS = {
    "production": {
        "plan.json": "f8a5eda54d8a8c66f7cfe7362a4cbe8876ebe15d548c335725524d9227e58ac8",
        "terminal.json": "55ecb4539701e1d580c6cc9b3ed9762b60bb47822be026cb0fd71998fdedaf5c",
        "amsoldingersee-terminal.json": "bc55eaf93d31a736263894af13a85cd567928991e276a5869a5cbf79ad5ca979",
    },
    "observation": {
        "plan.json": "252001815e90a22b5f85c1690311ea5c6f349973ceef9099d157fd9aeeee5e8c",
        "terminal.json": "7b5a6881bc015cc0587a91d6fc2b79b97e1bc351f5b773d2f2c07eab643f9d53",
        "amsoldingersee-terminal.json": "ba7d3be26e683d68bc2dff294561c8aa94b5d450ccf6668d0664c09fe8543776",
        "independent-source-review.json": "07b9673fcd7bac18bed6069aa69ce7fadee57f3aa267f3f837e086beca71ca8d",
    },
}


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            exact(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def native_histories(jobs: dict[str, dict[str, Any]]) -> None:
    for label, exits, whole, count in (
        ("production", [0, 1], 1, 10058),
        ("observation", [0], 0, 10094),
    ):
        documents = jobs[label]
        plan = documents["plan.json"]
        common = documents["terminal.json"]
        outer = documents["amsoldingersee-terminal.json"]
        require(
            plan["candidate"]
            == common["candidate"]
            == outer["candidate"]
            == SOURCE_CANDIDATE,
            "Native source candidate changed",
        )
        require(
            exact(common["actual_exit"], whole) and exact(outer["actual_exit"], whole),
            "Original whole history changed",
        )
        repository = Path(plan["repository"])
        output = Path(plan["output"])
        expected_roles = (
            (
                (
                    "maintained-amsoldingersee-source-refusal",
                    "produce",
                    "amsoldingersee-source-refusal-custody",
                ),
                (
                    "independent-amsoldingersee-source-joins",
                    "observe",
                    "amsoldingersee-source-refusal-custody",
                ),
            )
            if label == "production"
            else (
                (
                    "independent-saved-amsoldingersee-source-joins",
                    "observe",
                    "amsoldingersee-saved-observation-custody",
                ),
            )
        )
        base = "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
        for stage, (role, action, directory) in zip(
            plan["stages"], expected_roles, strict=True
        ):
            require(
                exact(stage["id"], role)
                and exact(
                    stage["argv"],
                    [
                        base,
                        "-I",
                        "-S",
                        "-B",
                        str(repository / "artifacts/science" / directory / "entry.py"),
                        action,
                        "--plan",
                        str(output / "plan.json"),
                    ],
                )
                and exact(stage["timeout_seconds"], 45)
                and stage["must_succeed"] is True,
                "Declared native role/argv/bound differs",
            )
        require(
            len(plan["input_pins"]) == count
            and len({row["path"] for row in plan["input_pins"]}) == count,
            "Original complete input membership changed",
        )
        require(
            common["plan_sha256"]
            == outer["plan_sha256"]
            == REFERENCE_SHAS[label]["plan.json"],
            "Native plan reference changed",
        )
        require(
            common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
            and common["absent_input_paths_unchanged"] is True,
            "Original input custody failed",
        )
        require(
            outer["timed_out"] is False
            and outer["error"] is None
            and outer["after_input_error"] is None
            and outer["completed_whole_wall_bound_pass"] is True
            and outer["memory_bound_pass"] is True,
            "Native bounded custody differs",
        )
        require(
            exact(outer["actual_native_stage_exits"], exits)
            and len(common["stages"]) == len(plan["stages"]) == len(exits),
            "Actual stage count differs",
        )
        for row, declared, code in zip(
            common["stages"], plan["stages"], exits, strict=True
        ):
            require(
                all(
                    exact(row[key], declared[key])
                    for key in ("id", "argv", "timeout_seconds", "must_succeed")
                )
                and exact(row["actual_exit"], code)
                and row["timed_out"] is False,
                "Actual native stage binding changed",
            )
    review = jobs["observation"]["independent-source-review.json"]
    require(
        exact(review["actual_exit"], 0)
        and exact(review["tracked_byte_checker_exit"], 0)
        and exact(review["original_whole_actual_exit"], 1)
        and exact(review["original_native_stage_exits"], [0, 1]),
        "Saved observer result changed",
    )
    require(
        review["complete_ordered_typed_report_equal"] is True
        and review["producer_repeated"] is False
        and review["source_refusal_unchanged"] is True,
        "Source reconstruction scope changed",
    )
    require(
        review["historical_E69_identity_admitted"] is False
        and review["rights_human_ecology_or_LRA_admitted"] is False,
        "Saved source refusal inflated",
    )
    ledger = review["source_ledger"]
    require(
        exact(ledger["original_source_files_verified"], 14)
        and len(ledger["original_response_events"]) == 11
        and exact(ledger["author_example_rows"], 17),
        "Original source denominator changed",
    )
    require(
        exact(ledger["declared_dataset_requests"], [3873, 3874, 3875])
        and exact(ledger["selected_provider_site"], 2973),
        "Declared request or native site identity changed",
    )
    require(
        exact(ledger["new_HTTP_requests"], 0)
        and exact(ledger["tree_outcomes_or_model_calls"], 0)
        and ledger["rights_human_or_LRA_admission"] is False,
        "Metadata became new source/model admission",
    )


def refusal(report: dict[str, Any]) -> None:
    require(
        report["schema_version"] == "landclim-amsoldingersee-source-review.v1"
        and report["admission"] == "refused_historical_input_identity",
        "Historical source refusal changed",
    )
    for name in (
        "candidate_with_exact_e69_bridge",
        "candidate_with_authenticated_author_chronology",
        "reproduction_ready",
    ):
        require(
            exact(report["denominators"][name], 0), "Missing historical input promoted"
        )
    require(
        exact(report["site_id"], 2973)
        and exact(
            [row["dataset_id"] for row in report["candidates"]], [3873, 3874, 3875]
        ),
        "Original source request labels changed",
    )
    require(
        exact([row["sample_id_count"] for row in report["candidates"]], [23, 24, 52])
        and all(
            row["publication_code_e69_present"] is False for row in report["candidates"]
        ),
        "Original candidate source evidence changed",
    )
