"""Transport a genuine closed central-age source replay without analytical admission."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

CAPTURE: Any = "data/countries/denmark/solsoe-closed-point-source-capture/capture.json"
CAPTURE_SHA256: Any = "ab6f051d348892129cc3bf91ef23e818b5c8d9611e6ec9c94cfc0d930141433e"
OWNER: Any = "countries/denmark/solsoe-source-lineage/closed-central-point-selection/report-products"
REPORT: Any = "docs/report/countries/denmark/solsoe-source-lineage/closed-central-point-selection/report.json"
EXPECTED_MEMBERS: Any = {
    "execution/plan.json": {
        "sha256": "2265fea7c867e9de1fcd6f01900376770202ce06ccfb5be5e1cb579f09b3e173",
        "bytes": 1436433,
    },
    "execution/terminal.json": {
        "sha256": "f966d666024eafd032942ab699ee81df2527e69174da5c4744563afec27863ab",
        "bytes": 7612,
    },
    "execution/solsoe-replay-terminal.json": {
        "sha256": "96f87cf9b02bd4f96c3fbe128ec41efb658dd4dda13a3e5a602160f99fd37659",
        "bytes": 2060,
    },
    "execution/independent-source-review.json": {
        "sha256": "7e91f2a55508ff18544cfaf6ecd490667b07507d1c3cf539b7e7a44708f81d68",
        "bytes": 35540,
    },
    "execution/source-runtime-observation.json": {
        "sha256": "f70c91a9665cbf1170aab4d4a765bec4efff447ac6d55514b84a9fbd311eebec",
        "bytes": 93942,
    },
    "execution/stage-progress.json": {
        "sha256": "31872bb262f76cc2b923a0bbe85625436cfbdb282203f944958a6a7afa5b3b96",
        "bytes": 2373,
    },
    "execution/solsoe-maintained-closed-central-point-replay.stdout": {
        "sha256": "73e6afe6c1b83546db8abf40d42a2a892a891632adf5ea3e37bd7c5314fdf12a",
        "bytes": 566,
    },
    "execution/solsoe-maintained-closed-central-point-replay.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-solsoe-controls-and-native-sample-joins.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-solsoe-controls-and-native-sample-joins.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/check_contract.py": {
        "sha256": "561f1bd65e1398812e87645421381aaeafbd3951c725367fd1460a31d25a0752",
        "bytes": 21753,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/contracts.py": {
        "sha256": "9e318fe5f60372ca6d5fd42a07623b47c727326790f5440a3630d8bcf2c53d9e",
        "bytes": 17595,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/execute_source.py": {
        "sha256": "39d29b0796af42118b5adb8601eece582eb6368febd220001dff2cb141189166",
        "bytes": 3027,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/independent-source-review.json": {
        "sha256": "2438b899f8a8e4fd1b9992bba4270acf92f0c92726ffbf4e80a3c4ff4fc4d75e",
        "bytes": 5021,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/observe.py": {
        "sha256": "2b17b79e5e551a49233ba48ddb223221a564e9cae3e94e984d1e501594bbe777",
        "bytes": 6421,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/preflight/actual-declared-aliases.json": {
        "sha256": "2deccc51a2b7028e42357a2e0c9dac8320052c330b2b3e0d7792bea6ea92b3cd",
        "bytes": 777,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/preflight/alias-final-style.log": {
        "sha256": "d3d4a4f118ad59577988bea41ce64ccde8da7dc7c6dc24af60a19c9f92719c97",
        "bytes": 149,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/preflight/guards.log": {
        "sha256": "b7c3a148240495d09023649eb43d9195d6e04b8e96eb7529823d5ceb5af93607",
        "bytes": 129,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/preflight/strict.log": {
        "sha256": "f9b031e5c45aa702cd4fef028d465551cb20a2c4698e0913c7b00766b20ac4d8",
        "bytes": 43,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/prepare.py": {
        "sha256": "8ef483b4051922558641e9445b215e8e566132a63341d377bbaf37b9c4159a41",
        "bytes": 7232,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/prepared-source-manifest.json": {
        "sha256": "9d192b9130eecd11da43e274dff3f483fefa91ed54617817d95eaf897b537419",
        "bytes": 3051,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/protocol.json": {
        "sha256": "1a1f3ea95bf11e3110cf9f52152059d58fe6a018d68a8f24091d99507af96563",
        "bytes": 4847,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/run.py": {
        "sha256": "0f60502e117c01a72d6c7824f5af5ef44894ee826c9d756642a0686dbeff783b",
        "bytes": 7251,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/source-correspondence.json": {
        "sha256": "df74e3070d10d7097156a03cd3ac8a6128f755ec71af32ee60d6513eb274f5db",
        "bytes": 6178,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/source-qualification.json": {
        "sha256": "0bb46c6ee1bc1a065f2e6d213adc07c35f5a4666d229229d4133eaa3aa490116",
        "bytes": 2505,
    },
    "source-code/artifacts/science/solsoe-native-loader-paths/source_style.py": {
        "sha256": "20577109ddac469ae2231bf3aba77df0f09be64ddf4297dc4bacda83651287f5",
        "bytes": 1077,
    },
    "source-code/artifacts/science/solsoe-original-source-feasibility/source-feasibility.json": {
        "sha256": "ab40cfa412e4a6e722409aba41da60167e17b6be3f0508ed3135badf2aa81d48",
        "bytes": 1539,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "1cfb17ab9880cc0c842d5c1c7d7e04fe7109fdae08baf8f270b20a3d33deb520",
        "bytes": 9725257,
    },
    "source-code/docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py": {
        "sha256": "9604574d34c2555164d75f2cfdd30475f3f1f74d1a50ff600ea7d812a33bf746",
        "bytes": 11546,
    },
    "source-code/docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json": {
        "sha256": "8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6",
        "bytes": 2417,
    },
    "publication/report.json": {
        "sha256": "999534b826902f14c0fbd08ff36a5760f191070a13179d9d1bede9ca2cfa4436",
        "bytes": 203045,
    },
}
EXPECTED_SCOPE: Any = {
    "original_v1_report_replaced": False,
    "fresh_PDF_table_extraction": False,
    "original_provider_or_copy_history_recovered": False,
    "calendar_conversion_resolved": False,
    "full_uncertainty_support_selection": False,
    "analytical_eligibility_evaluated": False,
    "LRA_admitted_samples": 0,
    "published_79_membership_recovered": False,
    "dated_georeferenced_basin_admitted": False,
    "new_rights_or_human_acceptance": False,
    "private_PDF_payload_redistributed": False,
    "runtime_payloads_redistributed": False,
    "new_native_or_metadata_producer_calls": 0,
}
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 3481,
    "private_PDF_identity_only": 1,
    "retained_first_party_source_control": 22,
    "existing_public_relation_reference": 2,
}
ORIGINAL_CANDIDATE = "c397f95cc2cbe8f451df17b4f7fa6a856ad71a75"
HISTORICAL_REPORT = "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json"
HISTORICAL_SHA256 = "8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6"
PRODUCT_SHA256 = "999534b826902f14c0fbd08ff36a5760f191070a13179d9d1bede9ca2cfa4436"


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Solsø source selection: " + reason)


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
        return _regular_confined_file(root, name, "Solsø native source selection")
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
    """Preserve actual descriptive totals, raw refusals and point-versus-support limits."""
    _exact(report["schema_version"], "solsoe-original-core-selection.v2")
    for key, value in (
        ("published_1983_controls", 7),
        ("neotoma_1983_control_rows", 14),
        ("exact_published_control_matches", 7),
        ("neotoma_calibrated_samples", 92),
        ("paper_interval_proxy_samples", 75),
        ("paper_interval_and_landclim_age_span_proxy_samples", 74),
        ("landclim_ii_reported_sample_count", 79),
        ("paper_interval_proxy_gap_to_landclim_ii", 4),
        ("bounded_proxy_gap_to_landclim_ii", 5),
        ("lra_admitted_samples", 0),
    ):
        _exact(report[key], value)
    closed = _object(report["closed_paper_interval_proxy"])
    _exact(closed["reference_epoch"], "1950 CE")
    _exact(closed["boundary_convention"], "inclusive")
    _exact(
        closed["intervals_bp_by_core"],
        {
            "neotoma:collection-unit:4303": [[-31, 3490], [7210, 11650]],
            "neotoma:collection-unit:4304": [[3700, 7180]],
        },
    )
    _exact(closed["source_chronology_equivalence_claimed"], False)
    _exact(closed["analytical_eligibility_evaluated"], False)
    _exact(
        closed["calendar_conversion_limit"],
        "BC + 1950 is the existing declared arithmetic proxy, not a resolved no-year-zero calendar conversion",
    )
    _exact(
        closed["selection_measure"],
        "Raw source central age only; neither full uncertainty containment nor overlap",
    )
    _exact(
        closed["older_endpoint_source_limit"],
        "The paper's 9700 BC boundary is extrapolated; this declared proxy does not newly calibrate it",
    )
    legacy = _object(report["legacy_unbounded_proxy"])
    _exact(legacy["historical_report_sha256"], HISTORICAL_SHA256)
    _exact(legacy["selected_samples"], 76)
    _exact(legacy["bounded_selected_samples"], 74)
    ledger = closed["native_source_proxy_ledger"]
    _require(isinstance(ledger, list), "native raw ledger required")
    _exact(len(ledger), 92)
    by_id = {}
    for raw in ledger:
        row = _object(raw)
        for key in (
            "closed_central_point_proxy_selected",
            "legacy_unbounded_central_point_proxy_selected",
            "bounded_closed_central_point_proxy_selected",
        ):
            _require(type(row[key]) is bool, "proxy selection flag must be boolean")
        _exact(row["analytical_eligibility_evaluated"], False)
        _exact(row["lra_admitted"], False)
        source = _object(row["source_record"])
        identifier = source["source_record_id"]
        _require(identifier not in by_id, "duplicate native sample")
        _exact(source["subject_id"], identifier)
        _exact(source["site_id"], "neotoma:site:3432")
        payload = _object(source["source_payload"])
        for native, projected in (
            ("age", "source_age_value"),
            ("ageyounger", "source_age_younger"),
            ("ageolder", "source_age_older"),
        ):
            _exact(payload[native], source[projected])
        by_id[identifier] = row
    _exact(
        closed["selected_native_sample_ids"],
        sorted(
            key
            for key, row in by_id.items()
            if row["closed_central_point_proxy_selected"] is True
        ),
    )
    _exact(
        closed["bounded_selected_native_sample_ids"],
        sorted(
            key
            for key, row in by_id.items()
            if row["bounded_closed_central_point_proxy_selected"] is True
        ),
    )
    _exact(len(closed["selected_native_sample_ids"]), 75)
    _exact(len(closed["bounded_selected_native_sample_ids"]), 74)
    for identifier, central, selected, younger, older in (
        ("neotoma:sample:353061", 12417, False, 11495, 13410),
        ("neotoma:sample:353060", 11507, True, 11008, 12037),
        ("neotoma:sample:352996", 7, True, -41, 60),
    ):
        row = by_id[identifier]
        _exact(row["source_record"]["source_age_value"], central)
        _exact(row["closed_central_point_proxy_selected"], selected)
        _exact(row["source_record"]["source_age_younger"], younger)
        _exact(row["source_record"]["source_age_older"], older)
    refused = by_id["neotoma:sample:352996"]["source_record"]
    _exact(refused["comparability_status"], "refused")
    _exact(refused["refusal_reason"], "negative_bp")
    _exact(refused["younger_bp"], None)
    _exact(refused["older_bp"], None)


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
    _exact(len(plan["input_pins"]), 3506)
    _exact(len({row["path"] for row in plan["input_pins"]}), 3506)
    _exact(
        plan["declared_owner"]["owner_id"],
        "countries/denmark/solsoe-source-lineage/original-core-selection/report-products",
    )
    _exact(plan["declared_owner"]["role"], "unresolved")
    _exact(
        plan["maintained_source"]["sha256"],
        "9604574d34c2555164d75f2cfdd30475f3f1f74d1a50ff600ea7d812a33bf746",
    )
    _exact(
        [row["id"] for row in plan["stages"]],
        [
            "solsoe-maintained-closed-central-point-replay",
            "independent-solsoe-controls-and-native-sample-joins",
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
    _exact(outer["tracked_byte_checker_exit"], 2)
    _exact(
        outer["common_terminal"]["sha256"],
        EXPECTED_MEMBERS["execution/terminal.json"]["sha256"],
    )
    _exact(
        outer["independent_review"]["sha256"],
        EXPECTED_MEMBERS["execution/independent-source-review.json"]["sha256"],
    )
    _exact(review["actual_exit"], 0)
    _exact(review["typed_report_exact_against_independent_raw_source"], True)
    _exact(review["historical_v1_preserved"], True)
    _exact(review["historical_v1_byte_checker_exit"], 2)
    _exact(review["generated"]["sha256"], PRODUCT_SHA256)
    _exact(review["retained"]["sha256"], HISTORICAL_SHA256)
    _exact(
        review["actual_source_runtime"]["sha256"],
        EXPECTED_MEMBERS["execution/source-runtime-observation.json"]["sha256"],
    )
    _exact(review["actual_closed_proxy_samples"], 75)
    _exact(review["actual_bounded_closed_proxy_samples"], 74)
    joins = _object(review["native_joins"])
    _exact(joins["control_rows"], 14)
    _exact(len(set(joins["native_control_view_ids"])), 14)
    _exact(len(set(joins["native_geochron_numeric_ids"])), 7)
    _exact(joins["declared_control_count"], 7)
    _exact(len(set(joins["native_sample_ids"])), 92)
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


def validated_solsoe_selection_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit the new descriptive source result while keeping historical production unresolved."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    _require(len(selected) == 1, "one exact current owner required")
    owner = selected[0]
    _exact(owner["role"], "retained_source")
    _exact(owner["paths"], [REPORT])
    _exact(owner["producer_paths"], [])
    _exact(owner["producer_inputs"], [])
    packet_path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(packet_path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(packet_path)
    for key, value in (
        ("schema_version", "solsoe-closed-point-source-capture.v1"),
        ("owner_id", OWNER),
        ("publication_path", REPORT),
        ("publication_member", "publication/report.json"),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0]),
        ("historical_v1_byte_checker_exit", 2),
        ("original_input_count", 3506),
        ("member_count", len(EXPECTED_MEMBERS)),
        ("members", EXPECTED_MEMBERS),
        ("scope", EXPECTED_SCOPE),
        ("input_scope_counts", INPUT_SCOPE_COUNTS),
    ):
        _exact(packet[key], value)
    for path in packet_path.parent.rglob("*"):
        _require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "capsule alias or special member",
        )
    physical = {
        p.relative_to(packet_path.parent).as_posix()
        for p in packet_path.parent.rglob("*")
        if p.is_file() or p.is_symlink()
    }
    _exact(physical, set(EXPECTED_MEMBERS) | {"capture.json"})
    prefix = packet_path.parent.relative_to(repository).as_posix()
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

    plan, common, outer, review, runtime = (
        record(name)
        for name in (
            "plan.json",
            "terminal.json",
            "solsoe-replay-terminal.json",
            "independent-source-review.json",
            "source-runtime-observation.json",
        )
    )
    validate_native_records(plan, common, outer, review, runtime)
    _exact(
        packet["original_execution_receipts"],
        {
            name: {
                "path": str(Path(plan["output"]) / name),
                **EXPECTED_MEMBERS["execution/" + name],
            }
            for name in (
                "plan.json",
                "terminal.json",
                "solsoe-replay-terminal.json",
                "independent-source-review.json",
                "source-runtime-observation.json",
            )
        },
    )
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
            file = _file(repository, relative)
            _exact(
                {
                    "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                    "bytes": file.stat().st_size,
                },
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        else:
            _require(
                row["scope"] in {"runtime_identity_only", "private_PDF_identity_only"},
                "undeclared input omission",
            )
    _exact(scopes, INPUT_SCOPE_COUNTS)
    historical = _file(repository, HISTORICAL_REPORT)
    _exact(hashlib.sha256(historical.read_bytes()).hexdigest(), HISTORICAL_SHA256)
    publication = _file(repository, REPORT)
    retained = _file(repository, prefix + "/publication/report.json")
    _exact(publication.read_bytes(), retained.read_bytes())
    _exact(hashlib.sha256(publication.read_bytes()).hexdigest(), PRODUCT_SHA256)
    validate_report(_json(publication))
    entry = tracked_by_path.get(REPORT)
    _require(entry is not None, "tracked current result required")
    assert entry is not None
    _exact(entry.path, REPORT.removeprefix("docs/report/"))
    _exact(entry.kind, "file")
    _exact(entry.sha256, PRODUCT_SHA256)
    _exact(entry.size, 203045)
    return (entry,), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "historical_v1_byte_checker_exit": 2,
        "closed_central_point_samples": 75,
        "bounded_central_point_samples": 74,
        "raw_source_samples": 92,
        "native_control_rows": 14,
        "distinct_declared_radiocarbon_controls": 7,
        "paths": [entry.path],
        "scope": dict(EXPECTED_SCOPE),
    }
