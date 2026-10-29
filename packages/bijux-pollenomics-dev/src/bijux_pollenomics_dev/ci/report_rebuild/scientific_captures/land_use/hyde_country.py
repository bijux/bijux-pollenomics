"""Retain exact source-reported HYDE country totals without admitting observations or rights."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file
from ...retained_source import validate_capsule

CAPTURE: Any = "data/surface-reference/hyde-country-source-capture/capture.json"
CAPTURE_SHA256: Any = "bd7d37efaa8839af0e3997707e760a8c0b12cd053881549464a50e94638cea20"
ORIGINAL_CANDIDATE: Any = "97be88f37a117a518c8c4639ccca98927e13cb24"
OWNER: Any = "regions/nordic/hyde-country-cropland/report-products"

ORIGINAL_OWNER: JsonObject = {
    "owner_id": "regions/nordic/hyde-country-cropland/report-products",
    "paths": [
        "docs/report/regions/nordic/hyde-country-cropland/country-years.csv",
        "docs/report/regions/nordic/hyde-country-cropland/report.json",
    ],
    "producer_inputs": [],
    "producer_paths": [
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/hyde_country_cropland.py"
    ],
    "role": "unresolved",
    "verification": "The retained country-year producer is "
    "`bijux_pollenomics_dev.source_completion.hyde_country_cropland "
    "--source-root <governed-HYDE-3.5-root> --output "
    "artifacts/jobs/vegetation-context-reproduction/hyde-country`. It "
    "reads the external general ZIP and three scenario country tables "
    "pinned in report.json. Bind exact HYDE release/source custody and "
    "permitted use before a fresh-output byte comparison of "
    "country-years.csv and report.json; no source grid, redistribution, "
    "calendar, CRS, or ecological reference acceptance is implied.",
}
CORRECTION_WITNESS = (
    "reports/science/source-cohorts/hyde-country-original-acceptance.json"
)
CORRECTION_WITNESS_SHA256 = (
    "5fc1b56bb41ed9e2892baaaff4dfec6484fa7cae4e57e3069eb900f8c134377f"
)
PUBLICATIONS: Any = [
    "docs/report/regions/nordic/hyde-country-cropland/country-years.csv",
    "docs/report/regions/nordic/hyde-country-cropland/report.json",
]
EXPECTED_MEMBERS: Any = {
    "source-code/artifacts/science/hyde-country-source-custody/check_contracts.py": {
        "sha256": "4c2334fbe5ba6c03aa71ae61d4fbd62739f0876cdf219473485036c4f3cb7c6b",
        "bytes": 8914,
    },
    "source-code/artifacts/science/hyde-country-source-custody/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/hyde-country-source-custody/consumer-protocol.json": {
        "sha256": "38e7c0b8efeb8464def29307cf5c35421a7b1af735d37c574951ab16e04b8cfa",
        "bytes": 5644,
    },
    "source-code/artifacts/science/hyde-country-source-custody/contracts.py": {
        "sha256": "f949760e798f7f433c36b3a751a3ac42ce0b92154397e0686dfc42fb28e03fcb",
        "bytes": 7299,
    },
    "source-code/artifacts/science/hyde-country-source-custody/declared-inputs.json": {
        "sha256": "a1f6558bea373955a6e26d5d4a15a8808c651b64dfa7b338a8c807dc6925e7b3",
        "bytes": 3647,
    },
    "source-code/artifacts/science/hyde-country-source-custody/execute_source.py": {
        "sha256": "bb79f09f15dd18bdb0a3ac8a594b084f4786d889a7274f835e4faf0995c28431",
        "bytes": 4058,
    },
    "source-code/artifacts/science/hyde-country-source-custody/independent-source-review.json": {
        "sha256": "c1ed8b019774ed640a78b0f0046ae6a2f1e8587f1286be7f62c89d4e6bba47ec",
        "bytes": 1200,
    },
    "source-code/artifacts/science/hyde-country-source-custody/metadata.py": {
        "sha256": "db73c077055af336c9ff739e406714e72b5e2e4b3defbab6677534c186e273b2",
        "bytes": 6954,
    },
    "source-code/artifacts/science/hyde-country-source-custody/observe.py": {
        "sha256": "7afb4284268ec950014a957323093bd123fbc5e91f6a4bc2de1221610d967450",
        "bytes": 5337,
    },
    "source-code/artifacts/science/hyde-country-source-custody/prepare.py": {
        "sha256": "13339b2cb998320bd6ef5d5dea5c56c57b92f13cc4a85a7ce77de0e06a3aa13e",
        "bytes": 8512,
    },
    "source-code/artifacts/science/hyde-country-source-custody/prepared-source-manifest.json": {
        "sha256": "350c12f95524f52ed458e24f99f549f648e251624efceec42d0c5f6d6c11b1a8",
        "bytes": 3404,
    },
    "source-code/artifacts/science/hyde-country-source-custody/run.py": {
        "sha256": "e9aa60b3d4a935214cdb5e1da02b2192bdc0a69c37ebee89fe3f00e385b4b39a",
        "bytes": 8214,
    },
    "source-code/artifacts/science/hyde-country-source-custody/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/hyde-country-source-custody/source-qualification.json": {
        "sha256": "2384d1e840e31596f4d0794dbd2f4d157dd9f69e9147a1ef0d90b872489fdf35",
        "bytes": 7074,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "3bf45bcc3e701fc04547c950a8aabf7588ada5d6c17f0a7aca2909debe07a27c",
        "bytes": 9619028,
    },
    "publication/country-years.csv": {
        "sha256": "35f58799ee1a77e252f00d26543d5b04e710c51bdb595181bf02daa00dfbcd68",
        "bytes": 4176,
    },
    "publication/report.json": {
        "sha256": "55d2e679fcacaabb0e64c641aae6f0ed9d5c90920adaeec91840b6117e725cbb",
        "bytes": 1829,
    },
    "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/hyde_country_cropland.py": {
        "sha256": "06302225bd7d6e49c8a5fde444813cc47f5792c6ed7298cce039179b37c1d8fa",
        "bytes": 7258,
    },
    "execution/hyde-country-terminal.json": {
        "sha256": "ffbbe83e6a8517f225ba4ee8f7331718b47cd5ca20b4923ba23a3cec7c2214b4",
        "bytes": 1605,
    },
    "execution/independent-hyde-country-metadata-observer.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-hyde-country-metadata-observer.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-source-review.json": {
        "sha256": "03786e4f5f2aa0ba9901dd447896e83b211e42ba5e751236e93c68dd4a946cf1",
        "bytes": 100279,
    },
    "execution/maintained-hyde-country-source.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/maintained-hyde-country-source.stdout": {
        "sha256": "efd35cc5fca620d5fa2b3bb4a319f578074e368bddab57fffea0976c102785dc",
        "bytes": 2352,
    },
    "execution/plan.json": {
        "sha256": "44666c0828ef818488f220b896e08abd3831f9b7959f9f47af34f7c4c4fc162b",
        "bytes": 1450565,
    },
    "execution/preparation.json": {
        "sha256": "f5e04791db33bacce85527babda37bcb49afada05f6d574a187251f599eee0c0",
        "bytes": 384,
    },
    "execution/root-launch.log": {
        "sha256": "6e2ce39f750e34333ccecbf04e75cc4d2b226ae902c3b0e659874547f0bff711",
        "bytes": 798,
    },
    "execution/source-runtime-observation.json": {
        "sha256": "712de278f7b26a6d56a752570bc7e64b57b3cc414e9461033e53ad5e58328cb8",
        "bytes": 97890,
    },
    "execution/stage-progress.json": {
        "sha256": "92c29e20d9a17af517c622279431d232040260c983eb64eb2e1baa181d8b78bd",
        "bytes": 2300,
    },
    "execution/terminal.json": {
        "sha256": "80d7bc83910576803c597b89186d0fa645984a977db767fefbb587b5a24e72d9",
        "bytes": 7850,
    },
}
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 3482,
    "private_rights_context_identity_only": 2,
    "private_country_source_identity_only": 4,
    "retained_execution_source": 16,
    "retained_produced_product": 2,
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "raw_private_tables_or_runtime_redistributed": False,
    "source_grid_reread_or_overlay_claimed": False,
    "source_scenarios_are_uncertainty_intervals": False,
    "independent_vegetation_or_pollen_covariates_admitted": False,
    "CE_BP_or_NetCDF_calendar_conversion_claimed": False,
    "release_rights_or_version_reconciled": False,
    "paired_HYDE_ablation_or_LRA_human_ecology_admitted": False,
}


DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "source-code/artifacts/science/hyde-country-source-custody/check_contracts.py",
        "source-code/artifacts/science/hyde-country-source-custody/common_runner.py",
        "source-code/artifacts/science/hyde-country-source-custody/contracts.py",
        "source-code/artifacts/science/hyde-country-source-custody/execute_source.py",
        "source-code/artifacts/science/hyde-country-source-custody/metadata.py",
        "source-code/artifacts/science/hyde-country-source-custody/observe.py",
        "source-code/artifacts/science/hyde-country-source-custody/prepare.py",
        "source-code/artifacts/science/hyde-country-source-custody/run.py",
        "source-code/artifacts/science/hyde-country-source-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/hyde_country_cropland.py",
    ]
)


def _validate_source_transport(
    repository: Path, prefix: str, members: dict[str, Any]
) -> None:
    """Authenticate exactly the declared Git-backed HYDE source roles."""
    detached = validate_capsule(repository, prefix, members)
    _exact(sorted(detached), sorted(DETACHED_SOURCE_MEMBERS))


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("HYDE country source custody: " + reason)


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
        return _regular_confined_file(root, name, "HYDE country source custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError("HYDE member missing, linked or unconfined") from error


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
        raise ReportRebuildError("HYDE JSON is invalid") from error


def _same(left: object, right: object) -> bool:
    _exact(left, right)
    return True


def validate_report(report: dict[str, Any]) -> None:
    """Check retained HYDE country totals and their source-scenario limits."""
    expected = {
        "schema_version": "hyde-source-reported-nordic-cropland.v1",
        "measure": "HYDE source-reported country cropland area in km2; modeled land use",
        "source_family": "HYDE 3.5 local gbc2025_7apr release",
        "country_codes": {"DK": "208", "FI": "246", "NO": "578", "SE": "752"},
        "source_year_ce_labels": [500, 1000, 1500, 1700, 1900, 2000, 2025],
        "scenarios": ["base", "lower", "upper"],
        "rows": 84,
        "country_years": 28,
        "rights": "Local Yoda metadata and License.txt say CC BY-NC 4.0; README and NetCDF declarations say CC BY 3.0. Derived summary retained under restrictive interpretation; redistribution review pending.",
        "interpretation": "These are native source country totals, not a new grid-country overlay, independent observed vegetation, uncertainty intervals, or pollen covariates. CE labels are retained without BP/NetCDF calendar conversion. The 2025 column exists in these tables while release coverage prose conflicts.",
        "remaining": [
            "unreviewed_grid_variables_and_years",
            "release_rights_reconciliation",
            "time_mapping_for_pollen_study",
            "paired_no_hyde_hyde_ablation",
        ],
    }
    _require(
        set(report) == {*expected, "inputs"}, "Complete HYDE report schema differs"
    )
    for key, value in expected.items():
        _require(_same(report[key], value), "HYDE scope differs: " + key)
    rows = report["inputs"]
    _require(
        type(rows) is list and len(rows) == 4, "Four source country inputs required"
    )
    _require(
        [row["path"] for row in rows]
        == [
            "original/general_files.zip",
            *[
                "original/gbc2025_7apr_" + scenario + "/txt/cropland_c.txt"
                for scenario in ["base", "lower", "upper"]
            ],
        ],
        "Source input order differs",
    )
    for row in rows:
        _require(
            set(row) == {"path", "sha256"}
            and type(row["sha256"]) is str
            and len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"]),
            "Source identity differs",
        )


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    """Bind two actual isolated native commands, source arithmetic and complete byte checks."""
    checksum = EXPECTED_MEMBERS["execution/plan.json"]["sha256"]
    for record in (plan, common, outer, review, runtime):
        _exact(record["candidate"], ORIGINAL_CANDIDATE)
    for record in (common, outer):
        _exact(record["plan_sha256"], checksum)
        _exact(record["actual_exit"], 0)
    for record in (review, runtime):
        _exact(record["plan"]["sha256"], checksum)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 3506)
    _exact(len({r["path"] for r in plan["input_pins"]}), 3506)
    _exact(
        [r["id"] for r in plan["stages"]],
        [
            "maintained-hyde-country-source",
            "independent-hyde-country-metadata-observer",
        ],
    )
    _exact(len(common["stages"]), 2)
    for declared, actual in zip(plan["stages"], common["stages"], strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            _exact(actual[key], declared[key])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    _exact(outer["common_actual_exit"], 0)
    _exact(outer["outer_timed_out"], False)
    _exact(outer["actual_native_stage_exits"], [0, 0])
    _exact(outer["tracked_byte_checker_exit"], 0)
    for key in (
        "completed_whole_wall_bound_pass",
        "framework_membership_unchanged",
        "absent_paths_unchanged",
        "memory_bound_pass",
        "storage_bound_pass",
    ):
        _exact(outer[key], True)
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
    _exact(review["complete_independent_metadata_join_typed_and_bytes_exact"], True)
    _exact(review["source_country_count"], 4)
    _exact(review["source_year_ce_labels"], [500, 1000, 1500, 1700, 1900, 2000, 2025])
    _exact(review["scenario_count"], 3)
    _exact(review["source_reported_modeled_rows"], 84)
    _exact(review["country_years"], 28)
    _exact(review["source_grid_reads"], 0)
    for key in (
        "scenario_uncertainty_interval_admitted",
        "calendar_rights_version_human_ecological_or_LRA_admitted",
        "raw_private_bytes_redistributed",
    ):
        _exact(review[key], False)
    _exact(plan["declared_owner"]["owner_id"], OWNER)
    _exact(plan["declared_owner"]["role"], "unresolved")
    _exact(plan["declared_owner"]["paths"], PUBLICATIONS)
    _exact(
        [r["path"] for r in plan["historical_reports"]],
        [str(Path(plan["repository"]) / name) for name in PUBLICATIONS],
    )
    for key, filename in [
        ("generated", "report.json"),
        ("canonical", "report.json"),
        ("generated_csv", "country-years.csv"),
        ("canonical_csv", "country-years.csv"),
    ]:
        _exact(
            {k: review[key][k] for k in ("sha256", "bytes")},
            EXPECTED_MEMBERS["publication/" + filename],
        )
    _exact(
        review["source_runtime"]["sha256"],
        EXPECTED_MEMBERS["execution/source-runtime-observation.json"]["sha256"],
    )
    _exact(runtime["source"], plan["maintained_source"])
    _exact(runtime["executed_source_argv"], plan["maintained_source_argv"])
    _exact(runtime["interpreter_flags"], ["-I", "-S", "-B"])
    _exact(runtime["source_exit"], 0)
    _exact(runtime["metadata_exit"], 0)
    _exact(runtime["metadata_error"], None)
    _require(
        type(runtime["before"]["pid"]) is int and runtime["before"]["pid"] > 0,
        "Actual positive native PID required",
    )
    _exact(runtime["before"]["pid"], runtime["after"]["pid"])
    _exact(plan["runtime_profile"]["site_initialization_disabled"], True)
    _exact(plan["runtime_profile"]["scientific_installed_runtime"], False)
    inputs = {r["path"] for r in plan["input_pins"]}
    for snapshot in (
        runtime["before"],
        runtime["after"],
        review["observer_before"],
        review["observer_after"],
    ):
        for origin in snapshot["namespace"]:
            _require(
                origin["file"] is None or origin["file"] in inputs,
                "Unpinned native source/stdlib origin",
            )
        for image in snapshot["native_images"]:
            _require(
                image in inputs
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


def _validate_original_owner(owners: list[JsonObject]) -> None:
    """Require the complete original unresolved contract, including unchanged criteria."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    _require(len(selected) == 1, "One exact original owner required")
    _exact(selected[0], ORIGINAL_OWNER)
    owned_paths = ORIGINAL_OWNER["paths"]
    assert isinstance(owned_paths, list)
    for other in owners:
        if other is selected[0]:
            continue
        paths = other.get("paths", [])
        _require(
            isinstance(paths, list)
            and all(isinstance(path, str) for path in paths)
            and not set(owned_paths).intersection(paths),
            "Another owner overlaps current evidence paths",
        )


def _capture_required(repository: Path) -> bool:
    """A published correction keeps its existing physical evidence mandatory."""
    capture = repository / CAPTURE
    present = bool(capture.exists() or capture.is_symlink())
    witness = repository / CORRECTION_WITNESS
    _require(
        not any(node.is_symlink() for node in (witness, *witness.parents)),
        "Original-acceptance witness ancestry alias",
    )
    if witness.exists() or witness.is_symlink():
        path = _file(repository, CORRECTION_WITNESS)
        _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CORRECTION_WITNESS_SHA256)
        _require(present, "Published partial evidence requires its exact capture")
    return present


def validated_hyde_country_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Validate partial current evidence while original owner acceptance stays unresolved."""
    present = _capture_required(repository)
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not present:
        return (), {}
    _validate_original_owner(owners)
    if not present:
        return (), {}
    capture = _file(repository, CAPTURE)
    _exact(hashlib.sha256(capture.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(capture)
    for key, value in [
        ("schema_version", "hyde-country-source-capture.v1"),
        ("owner_id", OWNER),
        ("publication_paths", PUBLICATIONS),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_native_stage_exits", [0, 0]),
        ("original_tracked_byte_checker_exit", 0),
        ("original_input_count", 3506),
        ("member_count", len(EXPECTED_MEMBERS)),
        ("members", EXPECTED_MEMBERS),
        ("input_scope_counts", INPUT_SCOPE_COUNTS),
        ("scope", EXPECTED_SCOPE),
    ]:
        _exact(packet[key], value)
    prefix = capture.parent.relative_to(repository).as_posix()
    _validate_source_transport(repository, prefix, EXPECTED_MEMBERS)

    def record(name: str) -> dict[str, Any]:
        return _json(_file(repository, prefix + "/execution/" + name))

    plan, common, outer, review, runtime = [
        record(n)
        for n in (
            "plan.json",
            "terminal.json",
            "hyde-country-terminal.json",
            "independent-source-review.json",
            "source-runtime-observation.json",
        )
    ]
    validate_native_records(plan, common, outer, review, runtime)
    _exact(
        [r["original"] for r in packet["original_input_custody"]], plan["input_pins"]
    )
    counts: dict[str, int] = {}
    for row in packet["original_input_custody"]:
        scope = row["scope"]
        counts[scope] = counts.get(scope, 0) + 1
        if row["member"] is not None:
            _require(
                scope in {"retained_execution_source", "retained_produced_product"},
                "Unexpected retained payload role",
            )
            _exact(
                EXPECTED_MEMBERS[row["member"]],
                {key: row["original"][key] for key in ("sha256", "bytes")},
            )
        else:
            _require(
                scope
                in {
                    "runtime_identity_only",
                    "private_country_source_identity_only",
                    "private_rights_context_identity_only",
                },
                "Undeclared omission",
            )
            _require(
                not Path(row["original"]["path"]).is_relative_to(
                    Path(plan["repository"])
                ),
                "First-party source cannot be omitted",
            )
    _exact(counts, INPUT_SCOPE_COUNTS)
    entries = []
    for name in PUBLICATIONS:
        public = _file(repository, name)
        retained = _file(repository, prefix + "/publication/" + Path(name).name)
        _exact(public.read_bytes(), retained.read_bytes())
        if name.endswith(".json"):
            validate_report(_json(public))
        wanted = EXPECTED_MEMBERS["publication/" + Path(name).name]
        entry = tracked_by_path.get(name)
        _require(entry is not None, "Tracked source product required")
        assert entry is not None
        for actual, value in [
            (entry.path, name.removeprefix("docs/report/")),
            (entry.kind, "file"),
            (entry.sha256, wanted["sha256"]),
            (entry.size, wanted["bytes"]),
        ]:
            _exact(actual, value)
        entries.append(entry)
    return (), {
        "selected_retained_entries": 0,
        "original_owner_acceptance_discharged": False,
        "owner_remains_unresolved": True,
        "original_acceptance_criterion": ORIGINAL_OWNER["verification"],
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "tracked_byte_checker_exit": 0,
        "paths": [entry.path for entry in entries],
        "scope": dict(EXPECTED_SCOPE),
    }
