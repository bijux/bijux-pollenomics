"""Authenticate primary pollen count-lineage receipts without ecological or LRA admission."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file
from ...retained_source import validate_capsule

CAPTURE = "data/countries/denmark/solsoe-primary-pollen-source-capture/capture.json"
CAPTURE_SHA256 = "18201ca5a0670298415bf5b9efab574b4b60733f84f7a1149cb64dee83fccf65"
OWNER = "countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report-products"
REPORT = "docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report.json"
SAMPLES = "docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/samples.csv"
ORIGINAL_CANDIDATE = "d87e7ff50c7c21c9a3dab5125db2e2cfdd6c4a9b"
EXPECTED_MEMBERS: dict[str, Any] = {
    "execution/independent-solsoe-pollen-source-count-and-name-vectors.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-solsoe-pollen-source-count-and-name-vectors.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-source-review.json": {
        "sha256": "86bfd205474a1fd30ef0e1c5029c4ad9f5b189b8ac78c818bce9b6c348c977fb",
        "bytes": 46945,
    },
    "execution/maintained-solsoe-primary-pollen-lineage.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/maintained-solsoe-primary-pollen-lineage.stdout": {
        "sha256": "053af9b0a210b5dccfe980688dbb8be5907d16f0ebae6de4361dac3483bb315f",
        "bytes": 590,
    },
    "execution/plan.json": {
        "sha256": "5cb4bce88d84bbd3c9ff734e800d1c9dd4a47a9e40ff1900fc1fb75870b2c6f6",
        "bytes": 1444493,
    },
    "execution/solsoe-replay-terminal.json": {
        "sha256": "fa006fc5c51235a6ad9aab8be4745feec3f2c754eb6f2a1542e266f7736ac57f",
        "bytes": 1913,
    },
    "execution/source-runtime-observation.json": {
        "sha256": "b2867c71e1618aeb47b9d55fa7d30e84f5af7939c1469d156a4903a89852df90",
        "bytes": 96588,
    },
    "execution/stage-progress.json": {
        "sha256": "f001457aec5b6bbd9a26d63d8c4dba1afef9b2ba95a02d29bdef41c5556073fe",
        "bytes": 2406,
    },
    "execution/terminal.json": {
        "sha256": "9deb99e676bf685ab92e6999004d4329f957584b54c65356f7b7d307fd156557",
        "bytes": 7777,
    },
    "publication/report.json": {
        "sha256": "e71e6ef7fb52afd2abf5540d1a003d4008e9520e58a39980296cba88d1003c2b",
        "bytes": 9302,
    },
    "publication/samples.csv": {
        "sha256": "a4f41777c1b4cbe104aaa7fb78355b9d7ad249bb81b4ace401eb07e9cceef010",
        "bytes": 2657,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/check_contract.py": {
        "sha256": "88deb241c275de4bede06ac11febb4ef8c908c2814c2ada02984d98ada9b5ebc",
        "bytes": 14788,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/contracts.py": {
        "sha256": "07fec76f6cdde01a2176d5cd5b554c76f94b42034f60ed8af0bf48faa6c04e34",
        "bytes": 13958,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/declared-inputs.json": {
        "sha256": "2ec374b8b5481cfb561388784a7ceaba5f03e71e7b4b074c1fb26fac80e0257c",
        "bytes": 3227,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/execute_source.py": {
        "sha256": "39d29b0796af42118b5adb8601eece582eb6368febd220001dff2cb141189166",
        "bytes": 3027,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/independent-source-review.json": {
        "sha256": "1bc67a113732a176a4d28a01d6719e5ce5825de0b870838563b924b2c07a37d7",
        "bytes": 1722,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/observe.py": {
        "sha256": "14c9d8414666e53571970b77fb0598352fbf6d82ecde895c97b0233530675c20",
        "bytes": 6253,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/prepare.py": {
        "sha256": "be74a6cc24cf68bac1efda0338ac0df452b28d1424eb540c7481682c0fa10ecc",
        "bytes": 7671,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/prepared-source-manifest.json": {
        "sha256": "2428a2e06504df05f5605225bbeacba83aefbd77bd9f24958c677673dfbc1025",
        "bytes": 1886,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/protocol.json": {
        "sha256": "1cd5b560f518c647fc43228d7873099eaad2cb869c1f201ccecff597bc06b758",
        "bytes": 5072,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/run.py": {
        "sha256": "0f60502e117c01a72d6c7824f5af5ef44894ee826c9d756642a0686dbeff783b",
        "bytes": 7251,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/source-qualification.json": {
        "sha256": "12c65fc74908e1234aa533e9be0659d9fdaa8dc951c6762387dc640351350baf",
        "bytes": 10725,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "59a0f53d4dee3e6098aee2a1e3fa75ccfb7d820155e2979f46a2d89c03afd166",
        "bytes": 9615808,
    },
    "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py": {
        "sha256": "787832b1af5d7878f782c138fca151a70e42112190b91a11d9e52bb4103324f6",
        "bytes": 12125,
    },
}
INPUT_SCOPE_COUNTS = {
    "runtime_identity_only": 3482,
    "private_primary_identity_only": 1,
    "retained_execution_source": 15,
    "existing_public_relation_reference": 10,
    "retained_produced_product": 2,
}
EXPECTED_SCOPE: dict[str, Any] = {
    "raw_primary_redistributed": False,
    "new_retention_native_execution_claimed": False,
    "original_source_acquisition_recovered": False,
    "ecological_taxonomy_approved": False,
    "original_author79_selection_identified": False,
    "author_chronology_identified": False,
    "age_specific_basin_identified": False,
    "lra_admitted_samples": 0,
    "rights_or_human_acceptance_claimed": False,
    "runtime_role": "original execution identity only; no installed distribution or current runtime qualification",
}
EXPECTED_COUNTS: dict[str, Any] = {
    "primary_profile_rows": 66,
    "primary_parameter_count": 147,
    "primary_count_cells": 9702,
    "primary_positive_count_cells": 2881,
    "primary_zero_count_cells": 6821,
    "primary_total_count": 128653,
    "neotoma_1981_sample_count": 66,
    "neotoma_positive_observation_count": 2881,
    "exact_same_name_parameter_count": 129,
    "numeric_rename_candidate_count": 18,
    "numeric_rename_candidates": [
        {
            "pangaea_parameter_name": "Caryophyllaceae undifferentiated",
            "neotoma_source_reported_name": "Caryophyllaceae undiff.",
            "positive_sample_count": 1,
            "source_count_sum": 1,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Chenopodiaceae",
            "neotoma_source_reported_name": "Amaranthaceae",
            "positive_sample_count": 44,
            "source_count_sum": 105,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Cruciferae",
            "neotoma_source_reported_name": "Brassicaceae",
            "positive_sample_count": 24,
            "source_count_sum": 59,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Diphasium complanatum-type",
            "neotoma_source_reported_name": "Diphasiastrum complanatum-type",
            "positive_sample_count": 1,
            "source_count_sum": 1,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Gramineae undifferentiated",
            "neotoma_source_reported_name": "Poaceae undiff.",
            "positive_sample_count": 66,
            "source_count_sum": 10598,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Hippophae rhamnoides",
            "neotoma_source_reported_name": "Hippophaë rhamnoides",
            "positive_sample_count": 2,
            "source_count_sum": 2,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Isoetes lacustris",
            "neotoma_source_reported_name": "Isoëtes lacustris",
            "positive_sample_count": 62,
            "source_count_sum": 12787,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Isoetes setacea",
            "neotoma_source_reported_name": "Isoëtes setacea",
            "positive_sample_count": 53,
            "source_count_sum": 8663,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Leguminosae undifferentiated",
            "neotoma_source_reported_name": "Fabaceae undiff.",
            "positive_sample_count": 3,
            "source_count_sum": 4,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Littorella uniflora",
            "neotoma_source_reported_name": "Plantago uniflora",
            "positive_sample_count": 52,
            "source_count_sum": 604,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Lychnis-type",
            "neotoma_source_reported_name": "Silene-type undiff.",
            "positive_sample_count": 9,
            "source_count_sum": 9,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Polygonum amphibium",
            "neotoma_source_reported_name": "Persicaria amphibia",
            "positive_sample_count": 3,
            "source_count_sum": 9,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Polygonum persicaria-type",
            "neotoma_source_reported_name": "Persicaria maculosa-type",
            "positive_sample_count": 5,
            "source_count_sum": 7,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Ranunculaceae undifferentiated",
            "neotoma_source_reported_name": "Ranunculaceae undiff.",
            "positive_sample_count": 3,
            "source_count_sum": 3,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Rhamnus catharticus",
            "neotoma_source_reported_name": "Rhamnus cathartica",
            "positive_sample_count": 1,
            "source_count_sum": 1,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Sanguisorba minor",
            "neotoma_source_reported_name": "Poterium sanguisorba",
            "positive_sample_count": 1,
            "source_count_sum": 1,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Scirpus lacustris-type",
            "neotoma_source_reported_name": "Schoenoplectus lacustris-type",
            "positive_sample_count": 14,
            "source_count_sum": 35,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
        {
            "pangaea_parameter_name": "Umbelliferae undifferentiated",
            "neotoma_source_reported_name": "Apiaceae undiff.",
            "positive_sample_count": 1,
            "source_count_sum": 1,
            "vector_equal_at_all_66_depths": True,
            "status": "numeric_source_name_candidate_not_ecological_approval",
        },
    ],
}


_DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/check_contract.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/common_runner.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/contracts.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/execute_source.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/observe.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/prepare.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/run.py",
        "source-code/artifacts/science/solsoe-pollen-source-lineage-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py",
    ]
)


def _validate_source_transport(
    repository: Path, prefix: str, members: dict[str, Any]
) -> None:
    """Validate the original logical members without embedding package source trees."""
    detached = validate_capsule(
        repository,
        prefix,
        members,
    )
    _exact(
        sorted(detached),
        sorted(_DETACHED_SOURCE_MEMBERS),
    )


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Solsø primary pollen custody: " + reason)


def _exact(left: object, right: object) -> None:
    _require(type(left) is type(right), "metadata type differs")
    if isinstance(left, dict) and isinstance(right, dict):
        _require(left.keys() == right.keys(), "metadata fields differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        _require(len(left) == len(right), "metadata list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "metadata value differs")


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "JSON object required",
    )
    assert isinstance(value, dict)
    return value


def _file(root: Path, name: str) -> Path:
    try:
        return _regular_confined_file(root, name, "Solsø primary pollen custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Solsø member missing, linked or unconfined"
        ) from error


def _json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            _require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Solsø JSON is invalid") from error


def validate_report(report: dict[str, Any]) -> None:
    """Keep count-vector identity distinct from ecological or chronological acceptance."""
    _exact(report["schema_version"], "solsoe-primary-pollen-lineage.v1")
    _exact(report["primary_doi"], "10.1594/PANGAEA.739834")
    _exact(report["primary_event"], "SOLSOE81")
    for key, value in EXPECTED_COUNTS.items():
        _exact(report[key], value)
    for key in (
        "all_source_sample_depths_match_exactly_cm",
        "all_positive_source_counts_match_exactly",
        "neotoma_zero_cells_are_sparse_absences",
    ):
        _exact(report[key], True)
    _exact(report["author_79_sample_selection_identified"], False)
    _exact(report["author_chronology_identified"], False)
    _exact(report["lra_admitted_samples"], 0)
    _exact(
        report["source_rights"],
        "PANGAEA CC BY-NC 3.0; primary raw text remains external",
    )
    for row in report["numeric_rename_candidates"]:
        _exact(row["vector_equal_at_all_66_depths"], True)
        _exact(row["status"], "numeric_source_name_candidate_not_ecological_approval")


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    """Bind the actual producer, observer, same-process origin and original input identities."""
    digest = EXPECTED_MEMBERS["execution/plan.json"]["sha256"]
    for row in (plan, common, outer, review, runtime):
        _exact(row["candidate"], ORIGINAL_CANDIDATE)
    for row in (common, outer):
        _exact(row["plan_sha256"], digest)
        _exact(row["actual_exit"], 0)
    for row in (review, runtime):
        _exact(row["plan"]["sha256"], digest)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 3510)
    _exact(len({row["path"] for row in plan["input_pins"]}), 3510)
    _exact(
        plan["declared_owner"]["owner_id"],
        "countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report-products",
    )
    _exact(plan["declared_owner"]["role"], "unresolved")
    _exact(
        plan["maintained_source"]["sha256"],
        "787832b1af5d7878f782c138fca151a70e42112190b91a11d9e52bb4103324f6",
    )
    _exact(
        [row["id"] for row in plan["stages"]],
        [
            "maintained-solsoe-primary-pollen-lineage",
            "independent-solsoe-pollen-source-count-and-name-vectors",
        ],
    )
    _exact(len(plan["stages"]), 2)
    _exact(len(common["stages"]), 2)
    for wanted, actual in zip(plan["stages"], common["stages"], strict=True):
        for key in ("id", "argv"):
            _exact(wanted[key], actual[key])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    for key in ("common_actual_exit", "actual_exit"):
        _exact(outer[key], 0)
    for key in (
        "memory_bound_pass",
        "storage_bound_pass",
        "framework_membership_unchanged",
        "absent_paths_unchanged",
        "completed_whole_wall_bound_pass",
    ):
        _exact(outer[key], True)
    _exact(outer["actual_native_stage_exits"], [0, 0])
    _exact(outer["outer_timed_out"], False)
    _exact(outer["tracked_byte_checker_exit"], 0)
    _exact(
        outer["common_terminal"]["sha256"],
        EXPECTED_MEMBERS["execution/terminal.json"]["sha256"],
    )
    _exact(
        outer["independent_review"]["sha256"],
        EXPECTED_MEMBERS["execution/independent-source-review.json"]["sha256"],
    )
    _exact(review["actual_exit"], 0)
    _exact(review["tracked_byte_checker_exit"], 0)
    _exact(review["complete_typed_report_and_ordered_CSV_exact"], True)
    _exact(review["raw_primary_redistributed"], False)
    _exact(
        review["generated"],
        [
            {
                "path": str(Path(plan["output"]) / "producer" / name),
                **EXPECTED_MEMBERS["publication/" + name],
            }
            for name in ("report.json", "samples.csv")
        ],
    )
    _exact(review["canonical"], [plan["historical_report"], plan["historical_samples"]])
    _exact(
        review["actual_source_runtime"]["sha256"],
        EXPECTED_MEMBERS["execution/source-runtime-observation.json"]["sha256"],
    )
    _exact(review["independently_derived_source_counts"], EXPECTED_COUNTS)
    ledger = review["independent_sample_rows"]
    _require(isinstance(ledger, list), "independent native sample ledger required")
    _exact(len(ledger), 66)
    _exact(len({row["neotoma_sample_id"] for row in ledger}), 66)
    _exact(len({row["depth_cm"] for row in ledger}), 66)
    for row in ledger:
        _exact(row["positive_counts_equal"], True)
    _exact(sum(row["positive_source_taxa"] for row in ledger), 2881)
    _exact(sum(row["source_count_sum"] for row in ledger), 128653)
    _exact(runtime["source"], plan["maintained_source"])
    _exact(runtime["executed_source_argv"], plan["maintained_source_argv"])
    _exact(runtime["interpreter_flags"], ["-I", "-S", "-B"])
    _exact(runtime["source_exit"], 0)
    _exact(runtime["metadata_exit"], 0)
    _exact(runtime["metadata_error"], None)
    _require(
        type(runtime["before"]["pid"]) is int and runtime["before"]["pid"] > 0,
        "native PID required",
    )
    _exact(runtime["before"]["pid"], runtime["after"]["pid"])
    _exact(plan["runtime_profile"]["profile"], "isolated-base-standard-library")
    _exact(plan["runtime_profile"]["scientific_installed_runtime"], False)
    _exact(plan["runtime_profile"]["site_initialization_disabled"], True)
    pins = {row["path"] for row in plan["input_pins"]}
    for side in ("before", "after"):
        snapshot = _object(runtime[side])
        for origin in snapshot["namespace"]:
            _require(
                origin["file"] is None or origin["file"] in pins,
                "unowned actual Python origin",
            )
        for image in snapshot["native_images"]:
            _require(
                image in pins
                or str(image).startswith(("/System/Library/", "/usr/lib/")),
                "unowned actual native image",
            )


def validated_solsoe_pollen_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only the two genuinely produced source-lineage products."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    _require(len(selected) == 1, "one exact owner required")
    owner = selected[0]
    for key, owner_value in (
        ("role", "retained_source"),
        ("paths", [REPORT, SAMPLES]),
        ("producer_paths", []),
        ("producer_inputs", []),
    ):
        _exact(owner[key], owner_value)
    packet_path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(packet_path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(packet_path)
    for key, value in (
        ("schema_version", "solsoe-primary-pollen-source-capture.v1"),
        ("owner_id", OWNER),
        ("publication_paths", [REPORT, SAMPLES]),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0]),
        ("original_tracked_byte_checker_exit", 0),
        ("member_count", len(EXPECTED_MEMBERS)),
        ("members", EXPECTED_MEMBERS),
        ("original_input_count", 3510),
        ("input_scope_counts", INPUT_SCOPE_COUNTS),
        ("scope", EXPECTED_SCOPE),
    ):
        _exact(packet[key], value)
    prefix = packet_path.parent.relative_to(repository).as_posix()
    _validate_source_transport(repository, prefix, EXPECTED_MEMBERS)

    records = [
        _json(_file(repository, prefix + "/execution/" + name))
        for name in (
            "plan.json",
            "terminal.json",
            "solsoe-replay-terminal.json",
            "independent-source-review.json",
            "source-runtime-observation.json",
        )
    ]
    plan, common, outer, review, runtime = records
    validate_native_records(plan, common, outer, review, runtime)
    _exact(
        [row["original"] for row in packet["original_input_custody"]],
        plan["input_pins"],
    )
    scopes: dict[str, int] = {}
    for row in packet["original_input_custody"]:
        scopes[row["scope"]] = scopes.get(row["scope"], 0) + 1
        if row["member"] is not None:
            _exact(
                EXPECTED_MEMBERS[row["member"]],
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        elif row["scope"] == "existing_public_relation_reference":
            relative = (
                Path(row["original"]["path"])
                .relative_to(Path(plan["repository"]))
                .as_posix()
            )
            member = _file(repository, relative)
            _exact(
                {
                    "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                    "bytes": member.stat().st_size,
                },
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        else:
            _require(
                row["scope"]
                in {"runtime_identity_only", "private_primary_identity_only"},
                "undeclared input omission",
            )
    _exact(scopes, INPUT_SCOPE_COUNTS)
    entries = []
    for path, name in ((REPORT, "report.json"), (SAMPLES, "samples.csv")):
        publication = _file(repository, path)
        wanted = EXPECTED_MEMBERS["publication/" + name]
        _exact(
            publication.read_bytes(),
            _file(repository, prefix + "/publication/" + name).read_bytes(),
        )
        entry = tracked_by_path.get(path)
        _require(entry is not None, "tracked current product required")
        assert entry is not None
        for value, expected in (
            (entry.path, path.removeprefix("docs/report/")),
            (entry.kind, "file"),
            (entry.sha256, wanted["sha256"]),
            (entry.size, wanted["bytes"]),
        ):
            _exact(value, expected)
        entries.append(entry)
    validate_report(_json(_file(repository, REPORT)))
    rows = list(csv.DictReader(io.StringIO(_file(repository, SAMPLES).read_text())))
    _exact(len(rows), 66)
    return tuple(entries), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "tracked_byte_checker_exit": 0,
        "paths": [entry.path for entry in entries],
        "scope": dict(EXPECTED_SCOPE),
    }
