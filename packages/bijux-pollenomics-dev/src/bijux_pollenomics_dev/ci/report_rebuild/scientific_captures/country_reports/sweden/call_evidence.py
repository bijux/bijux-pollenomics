"""Qualify one preserved successful country return inside its failed native wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .clock import certify
from .contracts import require, strict_equal

CODE_FIELDS = (
    "co_argcount",
    "co_posonlyargcount",
    "co_kwonlyargcount",
    "co_nlocals",
    "co_stacksize",
    "co_flags",
    "co_code",
    "co_consts",
    "co_names",
    "co_varnames",
    "co_filename",
    "co_name",
    "co_qualname",
    "co_firstlineno",
    "co_linetable",
    "co_exceptiontable",
    "co_freevars",
    "co_cellvars",
)

ORIGINAL_PLAN_SHA = "b4458d45c74b43e96cea0b468ba0885b579253273e685185e37aa49ac2347cef"
ORIGINAL_SOURCE_SHA = "32700b3d6977d648f338a1fab3265af426b702224967d21ff753c9ba5c8eec98"
ZIP = "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/lib/python311.zip"
DENIAL = "Undeclared maintained country input read: " + ZIP


def qualify_original(
    plan: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    clock: dict[str, Any],
    proof: dict[str, Any],
    progress: list[dict[str, Any]],
    references: dict[str, dict[str, Any]],
    runtime_plan: dict[str, Any],
) -> dict[str, Any]:
    """No original failure becomes zero and no missing in-memory telemetry is invented."""
    require(
        references["plan.json"]["sha256"] == ORIGINAL_PLAN_SHA
        and inner["plan_sha256"] == outer["plan_sha256"] == ORIGINAL_PLAN_SHA,
        "Original registered plan authority differs",
    )
    for receipt in (inner, outer):
        require(
            type(receipt["actual_exit"]) is int
            and receipt["actual_exit"] == 1
            and receipt["candidate"] == plan["candidate"]
            and receipt["memory_bound_pass"] is True
            and receipt["inclusive_storage_bound_pass"] is True,
            "Actual original failure or resource scope was relabeled",
        )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["completed_whole_wall_bound_pass"] is True
        and outer["completed_outer_wall_bound_pass"] is True
        and outer["registered_plan_unchanged"] is True
        and outer["child_timed_out"] is False
        and type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 1
        and outer["inner_terminal"]
        == references["sweden-country-semantic-terminal.json"]
        and inner["products_manifest"] == references["output-products.json"],
        "Original completed custody or native receipt join differs",
    )
    require(
        strict_equal(progress, inner["stages"]) and len(progress) == 1,
        "One preserved failed producer controller required",
    )
    stage = progress[0]
    require(
        strict_equal({key: stage[key] for key in plan["stages"][0]}, plan["stages"][0])
        and stage["id"] == "maintained-full-Sweden-country-consumer"
        and stage["action"] == "producer"
        and type(stage["actual_exit"]) is int
        and stage["actual_exit"] == 1
        and stage["timed_out"] is False,
        "Original controller identity differs",
    )
    for key in ("stdout", "stderr"):
        require(
            stage[key] == references["maintained-full-Sweden-country-consumer." + key]
            and outer[key] == references["launch." + key],
            "Complete original streams differ",
        )
    owned = Path(plan["owned_repository"])
    output = Path(plan["output"])
    expected_call = {
        "country": "Sweden",
        "version_dir": str(owned / "data/aadr/v66"),
        "output_dir": str(output / "producer/candidate"),
        "context_root": str(owned / "data"),
        "map_reference": None,
        "published_output_dir": None,
    }
    require(
        clock["schema_version"] == "sweden-native-country-clock-observation.v1"
        and strict_equal(clock["actual_country_calls"], [expected_call])
        and strict_equal(
            clock["actual_return_events"],
            [{"object_present": True, "object_type": "CountryReport"}],
        )
        and clock["telemetry_errors"] == []
        and clock["clock_observation_error"] is None
        and clock["maintained_exception"] is None
        and clock["IO_denials"] == [DENIAL]
        and clock["clock_qualification_not_yet_applied"] is True,
        "Actual call/return/clock or exact refused attempt differs",
    )
    qualified_clock = certify(
        clock["before"], clock["after"], clock["source_returned_generated_on"]
    )
    require(
        proof["schema_version"] == "cpython-complete-typed-code-correspondence.v1"
        and proof["all_code_fields"] == list(CODE_FIELDS)
        and proof["complete_typed_graphs_equal"] is True
        and proof["differing_code_fields"] == []
        and proof["expected_code_graph_sha256"] == proof["actual_code_graph_sha256"]
        and proof["marshal_reference_or_intern_identity_compared"] is False
        and proof[
            "bytecode_filename_lines_flags_exception_tables_or_constant_types_ignored"
        ]
        is False,
        "Complete native typed callable correspondence differs",
    )
    absent = runtime_plan["absent_input_paths"]
    require(
        type(absent) is list and absent.count(ZIP) == 1,
        "Exact original qualified ZIP absence missing",
    )
    covering = [
        row
        for row in runtime_plan["base_namespaces"]
        if Path(ZIP).is_relative_to(Path(row["root"]))
        and not any(Path(ZIP).is_relative_to(Path(name)) for name in row["excluded"])
    ]
    require(
        len(covering) == 1
        and covering[0]["root"] == str(Path(ZIP).parents[1])
        and covering[0]["excluded"]
        == [str(Path(ZIP).parents[1] / "lib/python3.11/site-packages")]
        and "lib/python311.zip" not in covering[0]["entries"],
        "ZIP absence not protected by complete original base namespace",
    )
    watched = [
        row
        for row in plan["input_pins"]
        if row["path"].endswith(
            "/sweden-country-callable-evidence-custody/prepared-source-manifest.json"
        )
    ]
    require(
        len(watched) == 1 and watched[0]["sha256"] == ORIGINAL_SOURCE_SHA,
        "Actual original executed source epoch differs",
    )
    return {
        "country_call_returned_normally": True,
        "native_UTC_clock": qualified_clock,
        "actual_country_call_arguments": expected_call,
        "actual_country_call_and_return_events": 1,
        "original_controller_actual_exit": 1,
        "original_whole_actual_exit": 1,
        "original_stage_actual_exits": [1],
        "exact_absent_default_import_attempt": {
            "path": ZIP,
            "denied_before_bytes_read": True,
            "original_qualified_runtime_absence_protected": True,
        },
        "full_returned_object_witness_recovered": False,
        "original_read_or_import_origin_ledger_recovered": False,
        "source_code_graph_sha256": proof["expected_code_graph_sha256"],
    }
