"""Authenticate the immutable current-source sample chronology browser packet."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts import ReportRebuildError
from ..ownership import _regular_confined_file
from .atlas_source_views import (
    CASE_IDS,
    OWNER_IDS,
    ValidatedAtlasCapture,
    _relative,
    _require,
    _sha,
    read_object,
)

CURRENT_CAPTURE_PATH = "data/atlas/sample-chronology-source-view-capture/capture.json"
CURRENT_CAPTURE_SHA256 = (
    "6e1cc3147e45449d5741999337eba180ef8727489e82288927a9f362cea85f69"
)
CURRENT_SOURCE_CANDIDATE = "dc3fe6f99b29c16f78e939164ad2d0609ac588bb"
CURRENT_CASE_IDS = CASE_IDS | {"sample-owned-chronology-components"}


def _validate_current_reader_custody(
    packet: dict[str, Any],
    members: dict[str, Path],
    review: dict[str, Any],
    generation_inputs: dict[str, str],
) -> None:
    """Join successful readers to the original producer's explicit partial result."""
    current = packet.get("current_reader_reference")
    reused = packet.get("reused_source_producer_reference")
    _require(
        isinstance(current, dict)
        and set(current)
        == {"plan", "terminal", "locality-producer", "reader", "observer"}
        and isinstance(reused, dict)
        and set(reused) == {"plan", "terminal", "producer-import-origins"},
        "current reader and reused producer reference coverage differs",
    )
    assert isinstance(current, dict) and isinstance(reused, dict)
    objects: dict[str, dict[str, Any]] = {}
    for group, references in (("current", current), ("reused", reused)):
        observed = review.get(
            "current_reader_reference"
            if group == "current"
            else "reused_source_producer_reference"
        )
        _require(
            isinstance(observed, dict) and set(observed) == set(references),
            "independent reader reference coverage differs",
        )
        assert isinstance(observed, dict)
        for role, name in references.items():
            member = members[_relative(name)]
            _require(
                observed[role]["sha256"] == _sha(member),
                "independent reader reference digest differs",
            )
            objects[f"{group}/{role}"] = read_object(member)
    plan = objects["current/plan"]
    terminal = objects["current/terminal"]
    producer = objects["current/locality-producer"]
    reader = objects["current/reader"]
    observer = objects["current/observer"]
    old_plan = objects["reused/plan"]
    old_terminal = objects["reused/terminal"]
    origins = objects["reused/producer-import-origins"]
    stages = terminal["stages"]
    _require(
        plan["candidate"] == terminal["candidate"] == CURRENT_SOURCE_CANDIDATE
        and terminal["plan_sha256"] == _sha(members[current["plan"]])
        and type(terminal["native_exit_code"]) is int
        and terminal["native_exit_code"] == 0
        and terminal["status"] == "passed"
        and terminal["protected_inputs_unchanged"] is True
        and len(stages) == len(plan["stages"]) == 2
        and [stage["name"] for stage in stages]
        == [stage["name"] for stage in plan["stages"]]
        and all(
            type(stage["native_exit_code"]) is int
            and stage["native_exit_code"] == 0
            and stage["timed_out"] is False
            and stage["actual_argv"] == declared["argv"]
            for stage, declared in zip(stages, plan["stages"], strict=True)
        ),
        "current reader native execution differs",
    )
    reused_producer = plan["reused_source_producer"]
    _require(
        reused_producer["original_plan_sha256"] == _sha(members[reused["plan"]])
        and reused_producer["original_terminal_sha256"]
        == _sha(members[reused["terminal"]])
        and reused_producer["reused_source_producer_proof_sha256"]
        == _sha(members[current["locality-producer"]])
        and old_plan["candidate"]
        == old_terminal["candidate"]
        == CURRENT_SOURCE_CANDIDATE
        and old_terminal["plan_sha256"] == _sha(members[reused["plan"]])
        and type(old_terminal["native_exit_code"]) is int
        and old_terminal["native_exit_code"] == 1
        and old_terminal["status"] == "failed"
        and old_terminal["protected_inputs_unchanged"] is True
        and old_terminal["stages"][0] == reused_producer["reused_source_producer_stage"]
        and type(old_terminal["stages"][0]["native_exit_code"]) is int
        and old_terminal["stages"][0]["native_exit_code"] == 0
        and old_terminal["stages"][0]["timed_out"] is False
        and old_terminal["stages"][0]["actual_argv"] == old_plan["stages"][0]["argv"]
        and plan["source_directory"]
        == old_plan["source_directory"]
        == reused_producer["source_directory"]
        == origins["source_root"],
        "reused producer partial native result differs",
    )
    _require(
        all(
            type(result["native_exit"]) is int and result["native_exit"] == 0
            for result in (producer, reader, observer, origins)
        )
        and producer["animal_localities"] == 547
        and producer["human_selected_localities"] == 2
        and producer["animal_source_samples"] == 1468
        and producer["human_source_samples"] == 55
        and reader["actual_sample_records"]
        == observer["actual_original_samples"]
        == 2699
        and reader["new_locality_records"] == 549
        and reader["new_locality_producer_proof_sha256"]
        == observer["locality_producer_sha256"]
        == _sha(members[current["locality-producer"]])
        and observer["reader_proof_sha256"] == _sha(members[current["reader"]])
        and observer["original_sample_producer_sha256"]
        == _sha(members[packet["source_normalization_reference"]["producer"]])
        and observer["all_reader_cases_joined_to_exact_source_membership"] is True,
        "current reader source membership differs",
    )
    source = Path(origins["source_root"])
    observed_modules: set[str] = set()
    _require(bool(origins["actual_origins"]), "reused producer origins are absent")
    for origin in origins["actual_origins"]:
        path = Path(origin["path"])
        _require(path.is_relative_to(source), "reused producer origin escapes source")
        relative = _relative(path.relative_to(source).as_posix())
        _require(
            isinstance(origin["module"], str)
            and origin["module"] not in observed_modules
            and generation_inputs.get(relative) == origin["sha256"],
            "reused producer captured source differs",
        )
        observed_modules.add(origin["module"])


def validated_sample_chronology_capture(repository: Path) -> ValidatedAtlasCapture:
    """Admit a fixed native packet, never an arbitrary ownership role or receipt.

    Captured source and verifier bytes must still match the candidate whose
    displays are described. Retained transport does not execute a browser and
    does not extend the scientific admission of the displayed records.
    """
    repository = repository.absolute()
    path = _regular_confined_file(repository, CURRENT_CAPTURE_PATH, "atlas capture")
    _require(_sha(path) == CURRENT_CAPTURE_SHA256, "certificate digest differs")
    packet = read_object(path)
    _require(
        packet["schema_version"] == "atlas-sample-chronology-source-capture.v2"
        and packet["source_candidate"] == CURRENT_SOURCE_CANDIDATE
        and packet["scientific_admission"] is False
        and packet["numerical_execution"] is False
        and packet["browser"] == "Chrome/155.0.8059.40",
        "capture identity or admission differs",
    )
    members: dict[str, Path] = {}
    directory = path.parent
    for row in packet["files"]:
        name = _relative(row["path"])
        _require(name not in members, "duplicate physical member")
        member = _regular_confined_file(
            repository,
            f"{directory.relative_to(repository).as_posix()}/{name}",
            "atlas capture member",
        )
        _require(
            member.stat().st_nlink == 1
            and type(row["bytes"]) is int
            and member.stat().st_size == row["bytes"]
            and _sha(member) == row["sha256"],
            "physical member bytes differ: " + name,
        )
        members[name] = member
    actual = set()
    for member in directory.rglob("*"):
        _require(not member.is_symlink(), "symlink packet member")
        if member.is_file() and member != path:
            actual.add(member.relative_to(directory).as_posix())
    _require(actual == set(members), "physical member inventory differs")
    _require(
        set(packet["source_members"]) == set(packet["source_footprint"]),
        "captured source coverage differs",
    )
    for name, expected in packet["source_footprint"].items():
        captured = members[_relative(packet["source_members"][name])]
        _require(_sha(captured) == expected, "captured source bytes differ: " + name)
        source = _regular_confined_file(
            repository, _relative(name), "current captured source"
        )
        _require(_sha(source) == expected, "current source footprint differs: " + name)
    runtime_resources = packet.get("runtime_resources", {})
    _require(isinstance(runtime_resources, dict), "runtime resource inventory differs")
    generated_version = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
    )
    _require(
        set(runtime_resources) <= {generated_version},
        "unrecognized generated runtime resource",
    )
    _require(
        not set(runtime_resources) & set(packet["source_footprint"]),
        "runtime resource overlaps maintained source",
    )
    resource_digests: dict[str, str] = {}
    for name, resource in runtime_resources.items():
        _require(
            resource["generated_by"] == "vcs-versioning",
            "generated runtime producer differs",
        )
        member = members[_relative(resource["member"])]
        _require(
            _sha(member) == resource["sha256"],
            "retained generated runtime bytes differ",
        )
        resource_digests[name] = resource["sha256"]
    generation_inputs = {**packet["source_footprint"], **resource_digests}
    for name, expected in packet["verifier_sources"].items():
        source = _regular_confined_file(
            repository, _relative(name), "atlas verifier source"
        )
        _require(_sha(source) == expected, "verifier source footprint differs: " + name)
    _require(
        {row["id"] for row in packet["generator_executions"]}
        == {
            "generate-source-details",
            "generate-Nordic-source-contexts",
            "generate-modeled-panels",
            "generate-context-frames",
            "generate-sample-chronology",
        }
        and len(packet["generator_executions"]) == 5,
        "generator coverage differs",
    )
    for execution in packet["generator_executions"]:
        _require(
            type(execution["native_exit"]) is int
            and execution["native_exit"] == 0
            and execution["timeout"] is False,
            "candidate generator did not pass",
        )
    cases: set[str] = set()
    generations = packet["generations"]
    _require(len(generations) == 5, "candidate generation coverage differs")
    for member in generations.values():
        generation = read_object(members[_relative(member)])
        _require(
            all(
                generation_inputs.get(name) == digest
                for name, digest in generation["inputs_sha256"].items()
            ),
            "generation source footprint differs",
        )
    review = read_object(members[packet["independent_review"]["member"]])
    _require(
        review["candidate"] == CURRENT_SOURCE_CANDIDATE
        and review["counts"]["successful_probes"] == 9
        and review["counts"]["visually_inspected_PNGs"] == 12
        and review["counts"]["authentic_component_source_sample_rows"] == 55
        and review["counts"]["normalized_sample_chronologies_checked"] == 55
        and review["counts"]["authentic_disjoint_components"] == 3
        and review["counts"]["native_browser_viewports"] == 2
        and review["served_and_output_hashes_all_match"] is True
        and review["all_selected_source_tables_exact"] is True,
        "independent current source/browser review differs",
    )
    references = packet["source_normalization_reference"]
    _require(
        set(references)
        == {
            "plan",
            "terminal",
            "producer",
            "observer",
            "human-sweden",
            "human-denmark",
        },
        "source normalization reference coverage differs",
    )
    source_execution = read_object(members[_relative(references["terminal"])])
    source_proof = read_object(members[_relative(references["producer"])])
    source_review = read_object(members[_relative(references["observer"])])
    _require(
        type(source_execution["native_exit_code"]) is int
        and source_execution["native_exit_code"] == 0
        and source_execution["status"] == "passed"
        and source_execution["protected_inputs_unchanged"] is True
        and source_execution["plan_sha256"]
        == _sha(members[_relative(references["plan"])])
        and type(source_proof["human_records"]) is int
        and source_proof["human_records"] == 1231
        and type(source_proof["animal_records"]) is int
        and source_proof["animal_records"] == 1468
        and type(source_review["native_exit"]) is int
        and source_review["native_exit"] == 0
        and type(source_review["counts"]["samples"]) is int
        and source_review["counts"]["samples"] == 2699
        and source_review[
            "exact_cross_format_chronology_native_identity_and_provenance"
        ]
        is True,
        "source normalization native proof differs",
    )
    _validate_current_reader_custody(packet, members, review, generation_inputs)
    for case in packet["cases"]:
        case_id = case["case_id"]
        _require(
            case_id in CURRENT_CASE_IDS and case_id not in cases,
            "case coverage differs",
        )
        cases.add(case_id)
        receipt = read_object(members[_relative(case["receipt"])])
        _require(case["generation"] in generations.values(), "case generation differs")
        execution = case["native_execution"]
        _require(
            case["source_candidate"] == CURRENT_SOURCE_CANDIDATE
            and type(execution["native_exit"]) is int
            and execution["native_exit"] == 0
            and execution["timeout"] is False
            and receipt["status"] == "PASS"
            and receipt["runtime_errors"] == []
            and receipt["browser"]["product"] == packet["browser"],
            "native browser execution did not pass",
        )
        for key in ("candidate_generation_sha256", "generation_sha256"):
            if key in receipt:
                _require(
                    receipt[key] == _sha(members[case["generation"]]),
                    "browser generation digest differs",
                )
        if "scientific_admission" in receipt:
            _require(
                receipt["scientific_admission"] is False,
                "browser scientific admission differs",
            )
        verifier = (
            "sample_chronology/components.mjs"
            if case_id == "sample-owned-chronology-components"
            else Path(execution["actual_argv"][1]).name
        )
        verifier_path = (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/"
            "atlas_browser/" + verifier
        )
        _require(
            packet["verifier_sources"].get(verifier_path) == receipt["verifier_sha256"],
            "native verifier identity differs",
        )
        served = receipt.get("served_files_sha256", receipt.get("served_files"))
        if not isinstance(served, dict):
            raise ReportRebuildError(
                "Atlas source capture: served inventory is not an object"
            )
        _require(set(served) == set(case["served_files"]), "served coverage differs")
        for name, digest in served.items():
            _relative(name)
            digest = digest["sha256"] if isinstance(digest, dict) else digest
            member = members[_relative(case["served_files"][name])]
            _require(_sha(member) == digest, "actual served bytes differ")
    _require(cases == CURRENT_CASE_IDS, "browser observations are incomplete")
    products: set[str] = set()
    owners: set[str] = set()
    for product in packet["products"]:
        _require(product["owner_id"] in OWNER_IDS, "unknown governed owner")
        owners.add(product["owner_id"])
        name = _relative(product["output_path"])
        _require(name not in products and name.startswith("atlas/"), "product overlaps")
        products.add(name)
        operation = product["operation"]
        _require(
            operation
            in {"copy", "keyless-identity", "provider-review", "modeled-review"},
            "unknown retained projection",
        )
        if operation == "copy":
            _require(
                _relative(product["source"]) in members, "product source is absent"
            )
    _require(
        frozenset(owners) == OWNER_IDS and len(products) == 43,
        "product coverage differs",
    )
    expected_stage_ids = {
        "generate-source-details",
        "generate-Nordic-source-contexts",
        "generate-modeled-panels",
        "generate-context-frames",
        "generate-sample-chronology",
        *("capture-" + name for name in CURRENT_CASE_IDS),
    }
    execution = read_object(members[_relative(packet["native_terminal"])])
    stages = {stage["id"]: stage for stage in execution["stages"]}
    _require(
        execution["candidate"] == CURRENT_SOURCE_CANDIDATE
        and type(execution["native_exit"]) is int
        and execution["native_exit"] == 0
        and execution["status"] == "passed"
        and execution["resource_bounds_met"] is True
        and len(stages) == len(execution["stages"]) == 14
        and set(stages) == expected_stage_ids
        and all(
            stage["passed"] is True
            and type(stage["native_exit"]) is int
            and stage["native_exit"] == 0
            and stage["timeout"] is False
            for stage in stages.values()
        ),
        "complete current native generator/browser scope did not pass",
    )
    _require(
        review["qualified_current_plan_sha256"]
        == _sha(members[_relative(packet["native_plan"])])
        and review["qualified_current_terminal_sha256"]
        == _sha(members[_relative(packet["native_terminal"])]),
        "independent review native execution binding differs",
    )
    for case in packet["cases"]:
        stage = stages["capture-" + case["case_id"]]
        _require(
            all(
                case["native_execution"][key] == stage[key]
                for key in (
                    "id",
                    "actual_argv",
                    "native_exit",
                    "timeout",
                    "stdout_sha256",
                    "stderr_sha256",
                )
            )
            and stage["browser_receipt"]["sha256"] == _sha(members[case["receipt"]]),
            "browser case native lineage differs",
        )
    for generation in packet["generator_executions"]:
        stage = stages[generation["id"]]
        _require(
            all(
                generation[key] == stage[key]
                for key in (
                    "id",
                    "actual_argv",
                    "native_exit",
                    "timeout",
                    "stdout_sha256",
                    "stderr_sha256",
                )
            ),
            "candidate generator native lineage differs",
        )
    _require(
        packet["scientific_admission"] is False
        and packet["sample_chronology_admission"] is False
        and packet["source_context"].get("not_a_clean_git_tree") is True,
        "selected-source/browser scope differs",
    )
    return ValidatedAtlasCapture(directory, packet, members)
