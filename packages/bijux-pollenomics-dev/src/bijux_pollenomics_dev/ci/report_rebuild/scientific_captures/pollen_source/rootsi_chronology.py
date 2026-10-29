"""Retain source-native Rootsi chronology witnesses without admitting dates or models."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

CAPTURE: Any = "data/surface-reference/rootsi-chronology-source-capture/capture.json"
CAPTURE_SHA256: Any = "0339b575f5fd22a1a60ce04f616bb4635d8c923306f49d535962c9f21045d31f"
ORIGINAL_CANDIDATE: Any = "c292dafa60f9d992f162c92dd327207d9aefd76b"
LANES: Any = {
    "neotoma": {
        "owner": "source-relations/landclim/neotoma-chronology-witness/paired-source-report",
        "report": "docs/report/source-relations/landclim/neotoma-chronology-witness/report.json",
    },
    "workbook": {
        "owner": "source-relations/landclim/workbook-chronology/source-age-audit",
        "report": "docs/report/source-relations/landclim/workbook-chronology/report.json",
    },
}
EXPECTED_MEMBERS: Any = {
    "source-code/artifacts/science/rootsi-controller-import-custody/cache_contract.py": {
        "sha256": "48200bbef762f3d98c00ca17ff3d6419dbf08dc0b7038af254fadad067ebf607",
        "bytes": 4682,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/check_contracts.py": {
        "sha256": "b14fcfed9bc3a6d05b34cd82bf77b3e36e0cae3d44348ec263e8c3d5a0ea77ef",
        "bytes": 15628,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/contracts.py": {
        "sha256": "ff1043e52af1cc2798d83d6dd987220295741710152705cb4cf1d2400ec1ec85",
        "bytes": 5819,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/declared-inputs.json": {
        "sha256": "efc78c325b178620b4c36eb2ef6f89296b5bc0657546c41289173836052c5b06",
        "bytes": 3303,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/execute_source.py": {
        "sha256": "f57b0474f31f4b3026bacbb3fb057589b106cb0de829d9bedeb66b2f58f6432e",
        "bytes": 4816,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/independent-source-review.json": {
        "sha256": "ecd806713017dec3c30ff589d562b8fe9dbc44aff95c981ee716ff9ff5e7672f",
        "bytes": 2248,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/independent.py": {
        "sha256": "e10d3e45d9f03c1730f75c1006e83e079797440e3f67d81d0298395a53157fc0",
        "bytes": 12675,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/observe.py": {
        "sha256": "b212a6e923f2e4624c1b7f27dac27d47823d99c0e67149a7cb8ed3f8fcb819b1",
        "bytes": 9750,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/predecessor-source-manifest.json": {
        "sha256": "43410c50057074abc867fc677ca51a17372e3553efd0862d9f07dc3be7981050",
        "bytes": 5037,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/predecessor-source-qualification.json": {
        "sha256": "358a98226102e3bac836c1706d9eee37a4723f4b102acc212947d21b4b3d668b",
        "bytes": 7240,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/cache-guard-local-typing-refusal.log": {
        "sha256": "0d8ba7d86217ad47ff43a11ee87cf339a8be974776a84ac0e84c10ef7b917675",
        "bytes": 2844,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/final-Ruff.log": {
        "sha256": "850dc2321776b7585f5f38c3f8370acd18e5f2f61abc6873e22fa4f135e97d0c",
        "bytes": 1513,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/final-style.log": {
        "sha256": "8da41606701af2ea674df060105fe53bd5bd5ec0dfc88c96f7d8b333989ed8d0",
        "bytes": 64,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/guards.log": {
        "sha256": "55d5df4eed27943e3044de0d1891c33ef1dcb9150e03feae778683a617c9fd36",
        "bytes": 146,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/held-Ruff.log": {
        "sha256": "82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18",
        "bytes": 19,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/held-format.log": {
        "sha256": "2ce9758b9f8abd876ec3e76c589e099e8b05377b1e7ea2331e81ee80f07bdff8",
        "bytes": 26,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/held-guards.log": {
        "sha256": "a7f09dcbfb22a75b24d6baae21397af799f792d9db187d8b4c86732427c2b546",
        "bytes": 146,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/held-strict.log": {
        "sha256": "46984ca20bf69f7b14ec1fd9bd82101d56a4e109e68f016fd2a04f22481b09b3",
        "bytes": 43,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/import-Ruff.log": {
        "sha256": "6ccc9a61df2db2596a5c18424f19d27e92a748b1122b97275b596a232c4ae042",
        "bytes": 3308,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/module-origin-typing-refusal.log": {
        "sha256": "adb052c4922cce0dba47e5cebf1c5e71d34cbb5702c55bc9d1c6f46e80d1e4f3",
        "bytes": 330,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/owned-origin-control-refusal.log": {
        "sha256": "cdc79e60a40497eb1b6ea5e492a82e76b78d9b83e1c5d2bc7d3dfa8d468ba6d9",
        "bytes": 1444,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/source-construction-refusal.json": {
        "sha256": "6cbc0e9b2e00f94330660748cf4b25a0a382b39d41e5dc00c8fc347e4003ae14",
        "bytes": 250,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/source-correspondence.json": {
        "sha256": "c2089f80ac189c7c43fa4d7f4e6283dad789426c7b40ba4ddf1c342ffb2264eb",
        "bytes": 1260,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/strict.log": {
        "sha256": "46984ca20bf69f7b14ec1fd9bd82101d56a4e109e68f016fd2a04f22481b09b3",
        "bytes": 43,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preflight/style-construction.log": {
        "sha256": "8cb468b09f954ac9e05180d2270ec92201adf071bbbab48ab6ea81e142cb79f1",
        "bytes": 551,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/preparation-recipe.json": {
        "sha256": "94c334d87588073d3d6dde1f87820636eaa614a36d2ad82b373adec251acb865",
        "bytes": 1130,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/prepare.py": {
        "sha256": "0181d49fc395899b42e38bf87e24eb268f168d4fccbd4a5f29af3fe59cb2837e",
        "bytes": 9670,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/prepared-source-manifest.json": {
        "sha256": "e1057ba6290003d44b3bd5d06f13a761b187cc92c23ab0f01e8905d01ebb82a5",
        "bytes": 6959,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/protocol.json": {
        "sha256": "57a8bed2fcec4d1039b831c70af34533ab7502b345fed2422a87f8ff90cf4567",
        "bytes": 7399,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/raw-source-shape.json": {
        "sha256": "582dc61b530b61e59e0123e32d28920139ec5b2960d631526a3bff5e71fd4255",
        "bytes": 1048,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/run.py": {
        "sha256": "9e9bf4b017510dc387dd3239211b4edd0cd85a209cc9bc17891a956938a285a4",
        "bytes": 8614,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/runtime.py": {
        "sha256": "e4e8317940c5160ce938b24a351cb96d4f7b5ceb31836bfa0583e566ab94f568",
        "bytes": 18846,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/source-prefix.diff": {
        "sha256": "39ae9f0571cb70fe3a016cebe8c39a93c992a37730b7fa99158ca6ffa71f194d",
        "bytes": 11006,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/source-qualification.json": {
        "sha256": "c793cde6acdc4e33f89532ee74446d99d3ce53a93020f48cfc92c7819cd613ed",
        "bytes": 6723,
    },
    "source-code/artifacts/science/rootsi-controller-import-custody/xlrd-cache-contract.json": {
        "sha256": "874b257f67c9e3210821274f5b72b94addfcd9c97b32ee0ede3e407c85212e57",
        "bytes": 3665,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "8f18d4a69e6eab167a4c9559cada8ec1532d02e75124d9f024bbfadec00950d3",
        "bytes": 9617683,
    },
    "source-code/docs/report/source-relations/landclim/neotoma-chronology-witness/replay.py": {
        "sha256": "ada77946596b45af2d08c56f0c9b6569e44c764dccf599e1a8d977b8de063f60",
        "bytes": 11268,
    },
    "publication/neotoma/report.json": {
        "sha256": "9f9ae65c538a1aac79966324abf081d4ea0028fbced6b1a343633acbd6372058",
        "bytes": 3232,
    },
    "source-code/docs/report/source-relations/landclim/workbook-chronology/replay.py": {
        "sha256": "49d9592d355418feb6d91142302bf7d65f2ce55caaca7acd4bc95e4f9827c23e",
        "bytes": 6442,
    },
    "publication/workbook/report.json": {
        "sha256": "b2c732c11669837c9aa75b8b0a5bfb7568dbf86071014ccfb4b30d3dcfc2eb13",
        "bytes": 4671,
    },
    "execution/plan.json": {
        "sha256": "7d4324376456c356c2a2efff38f1d2e70ebd1a1edcffa86ccc3394c5d5f06322",
        "bytes": 1496559,
    },
    "execution/terminal.json": {
        "sha256": "9d652edc652be73c97d7b8c880f0d28c7fdede361b650fef8ed7fbf977f77924",
        "bytes": 12341,
    },
    "execution/rootsi-replay-terminal.json": {
        "sha256": "5add207e7084e99cbdbb0b7e07f411bb7439dc57cc0c74f413426565ac251d70",
        "bytes": 2084,
    },
    "execution/independent-source-review.json": {
        "sha256": "bc5ad009fb9a0f58662c4b888f3551d12a77f772594ec3c55225516146ccc6d8",
        "bytes": 1819,
    },
    "execution/neotoma-independent-review.json": {
        "sha256": "e2b9e16a9e08e115a0e791b2b575e1d8e1e43f7076da9865ee6caef9960505c7",
        "bytes": 122741,
    },
    "execution/workbook-independent-review.json": {
        "sha256": "93d787dacc1824bf64b2c14c9a475bfc4d1c1c46904c5e19550c95ab798cb3fc",
        "bytes": 118215,
    },
    "execution/neotoma-source-runtime.json": {
        "sha256": "f5307989bfc5b59ccfa81127facd5d8fcdf650025acaaa9f421165b92dca136d",
        "bytes": 116575,
    },
    "execution/workbook-source-runtime.json": {
        "sha256": "e5ea6eb785d32d1042b775966f74f510d47bf215a35ea2b39cab20d207e1c9e1",
        "bytes": 116563,
    },
    "execution/stage-progress.json": {
        "sha256": "3b6ce1576e1922fcce00bd536bad73a3c0333805a042c00a6e0eac9c149fdc73",
        "bytes": 4695,
    },
    "execution/maintained-rootsi-neotoma.stdout": {
        "sha256": "b39aaaa1710ef941f3aba4c55bc496f995a6e130e11cef51ebd78b6ddb720d57",
        "bytes": 538,
    },
    "execution/maintained-rootsi-neotoma.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-rootsi-neotoma.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-rootsi-neotoma.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/maintained-rootsi-workbook.stdout": {
        "sha256": "c1e0ec443646b422c72989a154572247ee41a91a95beced8d17df3c581e25d1f",
        "bytes": 540,
    },
    "execution/maintained-rootsi-workbook.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-rootsi-workbook.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-rootsi-workbook.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
}
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 3498,
    "private_source_identity_only": 7,
    "retained_execution_source": 39,
    "existing_public_relation_reference": 2,
    "retained_produced_product": 2,
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "raw_private_sources_redistributed": False,
    "runtime_or_xlrd_payloads_redistributed": False,
    "original_author_acquisition_or_historical_input_recovered": False,
    "calendar_or_no_year_zero_conversion_admitted": False,
    "source_age_correction_or_interpolation_admitted": False,
    "independent_chronology_or_ecological_taxonomy_admitted": False,
    "rights_human_basin_uncertainty_or_LRA_admitted": False,
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Rootsi chronology source custody: " + reason)


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
        return _regular_confined_file(root, name, "Rootsi chronology source custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Rootsi member missing, linked or unconfined"
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
        raise ReportRebuildError("Rootsi JSON is invalid") from error


def validate_report(report: dict[str, Any], lane: str) -> None:
    """Retain literal source points, omissions and refusals; arithmetic is not a date model."""
    if lane == "neotoma":
        _exact(report["schema_version"], "rootsi-neotoma-chronology-witness.v1")
        _exact([r["sequence"] for r in report["findings"]], ["FLINK", "STAV"])
        for row in report["findings"]:
            _exact(row["historical_landclim_input_authenticated"], False)
            _exact(row["lra_admitted_samples"], 0)
            _exact(row["neotoma_samples_with_age_bounds"], 0)
        flink, stav = report["findings"]
        _exact(flink["neotoma_age_min_bp"], -50.0)
        _exact(flink["age_labels_within_0_05"], 108)
        _exact(flink["paired_depth_rows"], 109)
        _exact(len(flink["unmatched_age_rows"]), 1)
        _exact(flink["unmatched_age_rows"][0]["workbook_age_label"], 3910.84326171875)
        _exact(flink["unmatched_age_rows"][0]["neotoma_implied_ad_bc"], -3910.8)
        _exact(stav["workbook_age_column"], False)
        _exact(
            stav["neotoma_age_vector_transfer"], "candidate_only_no_workbook_age_field"
        )
    else:
        _exact(lane, "workbook")
        _exact(report["schema_version"], "rootsi-workbook-chronology-audit.v1")
        _exact(report["sequence_count"], 4)
        _exact(report["source_age_column_sequences"], ["FLINK", "HOLK"])
        _exact(report["no_source_age_column_sequences"], ["RANV", "STAV"])
        _exact(
            [r["sequence"] for r in report["findings"]],
            ["FLINK", "HOLK", "RANV", "STAV"],
        )
        for row in report["findings"]:
            _exact(row["dated_event_admitted"], False)
            if row["sequence"] in {"RANV", "STAV"}:
                for key in (
                    "source_age_basis",
                    "source_age_min",
                    "source_age_max",
                    "strict_age_reversals_in_sheet_order",
                    "numeric_1950_minus_age_extrema_bp",
                ):
                    _exact(row[key], None)
            else:
                _exact(len(row["strict_age_reversals_in_sheet_order"]), 1)
                _exact(
                    row["single_reversal_row_omission_diagnostic"]["status"],
                    "diagnostic_only_not_an_age_correction",
                )


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    summary: dict[str, Any],
    reviews: dict[str, dict[str, Any]],
    runtimes: dict[str, dict[str, Any]],
) -> None:
    """Bind all four actual native commands and two independent typed-byte checks."""
    plan_sha = EXPECTED_MEMBERS["execution/plan.json"]["sha256"]
    for record in (plan, common, outer, summary, *reviews.values(), *runtimes.values()):
        _exact(record["candidate"], ORIGINAL_CANDIDATE)
    _exact(common["plan_sha256"], plan_sha)
    _exact(outer["plan_sha256"], plan_sha)
    _exact(common["actual_exit"], 0)
    _exact(outer["actual_exit"], 0)
    _exact(outer["common_actual_exit"], 0)
    _exact(outer["outer_timed_out"], False)
    _exact(outer["actual_native_stage_exits"], [0, 0, 0, 0])
    _exact(outer["tracked_byte_checker_exit"], 0)
    for key in (
        "completed_whole_wall_bound_pass",
        "framework_membership_unchanged",
        "absent_paths_unchanged",
        "memory_bound_pass",
        "storage_bound_pass",
    ):
        _exact(outer[key], True)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 3548)
    _exact(len({p["path"] for p in plan["input_pins"]}), 3548)
    _exact(
        [r["id"] for r in plan["stages"]],
        [
            "maintained-rootsi-neotoma",
            "independent-rootsi-neotoma",
            "maintained-rootsi-workbook",
            "independent-rootsi-workbook",
        ],
    )
    _exact(len(common["stages"]), 4)
    for declared, actual in zip(plan["stages"], common["stages"], strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            _exact(actual[key], declared[key])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    _exact(
        outer["common_terminal"]["sha256"],
        EXPECTED_MEMBERS["execution/terminal.json"]["sha256"],
    )
    _exact(
        outer["independent_review"]["sha256"],
        EXPECTED_MEMBERS["execution/independent-source-review.json"]["sha256"],
    )
    _exact(summary["actual_exit"], 0)
    _exact(summary["tracked_byte_checker_exit"], 0)
    _exact(summary["complete_both_typed_reports_and_bytes_exact"], True)
    _exact(
        [r["sha256"] for r in summary["two_independent_reviews"]],
        [
            EXPECTED_MEMBERS["execution/" + lane + "-independent-review.json"]["sha256"]
            for lane in LANES
        ],
    )
    pins = {p["path"] for p in plan["input_pins"]}
    for position, lane in enumerate(LANES):
        declared = plan["lanes"][lane]
        _exact(declared["owner"]["owner_id"], LANES[lane]["owner"])
        _exact(declared["owner"]["role"], "unresolved")
        review, runtime = reviews[lane], runtimes[lane]
        for record in (review, runtime):
            _exact(record["plan"]["sha256"], plan_sha)
            _exact(record["lane"], lane)
        _exact(review["producer_stage"], common["stages"][position * 2])
        _exact(review["actual_exit"], 0)
        _exact(review["complete_independent_typed_report_exact"], True)
        _exact(review["tracked_byte_checker_exit"], 0)
        for key in (
            "raw_workbooks_redistributed",
            "calendar_conversion_or_age_correction_claimed",
            "dated_event_or_LRA_admission_claimed",
            "rights_or_human_acceptance_claimed",
        ):
            _exact(review[key], False)
        _exact(review["canonical"], declared["historical_report"])
        _exact(
            review["generated"]["sha256"],
            EXPECTED_MEMBERS["publication/" + lane + "/report.json"]["sha256"],
        )
        _exact(runtime["source"], declared["source"])
        _exact(runtime["executed_source_argv"], declared["source_argv"])
        _exact(runtime["interpreter_flags"], ["-I", "-S", "-B"])
        _exact(runtime["source_exit"], 0)
        _exact(runtime["metadata_exit"], 0)
        _exact(runtime["metadata_error"], None)
        _require(
            type(runtime["before"]["pid"]) is int and runtime["before"]["pid"] > 0,
            "Actual native PID required",
        )
        _exact(runtime["before"]["pid"], runtime["after"]["pid"])
        for snapshot in (
            runtime["before"],
            runtime["after"],
            review["observer_before"],
            review["observer_after"],
        ):
            for origin in snapshot["namespace"]:
                _require(
                    origin["file"] is None or origin["file"] in pins,
                    "Unpinned source/xlrd/stdlib origin",
                )
            for image in snapshot["native_images"]:
                _require(
                    image in pins
                    or image.startswith(
                        (
                            "/usr/lib/",
                            "/System/Library/",
                            "/System/Volumes/Preboot/Cryptexes/OS/usr/lib/",
                            "/System/Volumes/Preboot/Cryptexes/OS/System/Library/",
                        )
                    ),
                    "Unpinned native image",
                )
    _exact(
        plan["runtime_profile"]["profile"], "source-bound-isolated-base-with-pure-xlrd"
    )


def validated_rootsi_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit two source receipts while keeping their native chronology refusals unchanged."""
    value: Any
    selected = [
        r for r in owners if r.get("owner_id") in {v["owner"] for v in LANES.values()}
    ]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    _require(
        len(selected) == len({r["owner_id"] for r in selected}) == 2,
        "Two unique source owners required",
    )
    reports = {v["report"] for v in LANES.values()}
    for other in owners:
        if other not in selected:
            other_paths = other.get("paths", [])
            _require(isinstance(other_paths, list), "Owner paths must be a list")
            assert isinstance(other_paths, list)
            _require(
                not reports.intersection(other_paths),
                "Another owner overlaps source receipt",
            )
    for lane in LANES.values():
        owner = next(r for r in selected if r["owner_id"] == lane["owner"])
        for key, value in (
            ("role", "retained_source"),
            ("paths", [lane["report"]]),
            ("producer_paths", []),
            ("producer_inputs", []),
        ):
            _exact(owner[key], value)
    path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(path)
    for key, value in (
        ("schema_version", "rootsi-workbook-chronology-source-capture.v1"),
        ("owner_ids", [v["owner"] for v in LANES.values()]),
        ("publication_paths", [v["report"] for v in LANES.values()]),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0, 0, 0]),
        ("original_tracked_byte_checker_exit", 0),
        ("original_input_count", 3548),
        ("member_count", 58),
        ("members", EXPECTED_MEMBERS),
        ("input_scope_counts", INPUT_SCOPE_COUNTS),
        ("scope", EXPECTED_SCOPE),
    ):
        _exact(packet[key], value)
    physical = set()
    for member in path.parent.rglob("*"):
        _require(
            not member.is_symlink() and (member.is_file() or member.is_dir()),
            "Capture alias/special member",
        )
        if member.is_file():
            physical.add(member.relative_to(path.parent).as_posix())
    _exact(physical, set(EXPECTED_MEMBERS) | {"capture.json"})
    prefix = path.parent.relative_to(repository).as_posix()
    for name, wanted in EXPECTED_MEMBERS.items():
        member = _file(repository, prefix + "/" + name)
        _exact(
            {
                "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                "bytes": member.stat().st_size,
            },
            wanted,
        )

    def record(name: str) -> dict[str, Any]:
        return _json(_file(repository, prefix + "/execution/" + name))

    plan, common, outer, summary = [
        record(n)
        for n in (
            "plan.json",
            "terminal.json",
            "rootsi-replay-terminal.json",
            "independent-source-review.json",
        )
    ]
    reviews = {lane: record(lane + "-independent-review.json") for lane in LANES}
    runtimes = {lane: record(lane + "-source-runtime.json") for lane in LANES}
    validate_native_records(plan, common, outer, summary, reviews, runtimes)
    _exact(
        [r["original"] for r in packet["original_input_custody"]], plan["input_pins"]
    )
    counts: dict[str, int] = {}
    for row in packet["original_input_custody"]:
        counts[row["scope"]] = counts.get(row["scope"], 0) + 1
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
            source = _file(repository, relative)
            _exact(
                {
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "bytes": source.stat().st_size,
                },
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        else:
            _require(
                row["scope"]
                in {"runtime_identity_only", "private_source_identity_only"},
                "Undeclared source omission",
            )
            _require(
                not Path(row["original"]["path"]).is_relative_to(
                    Path(plan["repository"])
                ),
                "First-party source cannot be omitted",
            )
    _exact(counts, INPUT_SCOPE_COUNTS)
    entries = []
    for name, lane in LANES.items():
        publication = _file(repository, lane["report"])
        retained = _file(repository, prefix + "/publication/" + name + "/report.json")
        _exact(publication.read_bytes(), retained.read_bytes())
        validate_report(_json(publication), name)
        wanted = EXPECTED_MEMBERS["publication/" + name + "/report.json"]
        entry = tracked_by_path.get(lane["report"])
        _require(entry is not None, "Tracked source receipt required")
        assert entry is not None
        for actual, value in (
            (entry.path, lane["report"].removeprefix("docs/report/")),
            (entry.kind, "file"),
            (entry.sha256, wanted["sha256"]),
            (entry.size, wanted["bytes"]),
        ):
            _exact(actual, value)
        entries.append(entry)
    return tuple(entries), {
        "owner_ids": [v["owner"] for v in LANES.values()],
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0, 0, 0],
        "tracked_byte_checker_exit": 0,
        "paths": [entry.path for entry in entries],
        "scope": dict(EXPECTED_SCOPE),
    }
