"""Admit retained lake-source checking and current prerequisite production as distinct roles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....ownership import ReportOwnershipError, _regular_confined_file
from .execution import exact, require, validate_lake_execution
from .members import validate_catalog, validate_members

CAPTURE = "data/source-custody/neotoma/lakeparameters/capture.json"
CAPTURE_SHA256 = "25442e43479b87f7cf53a3476f9a825992616e15ab2587f43bfdaffa5ed37305"
CAPTURE_BYTES = 1177390
ORIGINAL_CANDIDATE = "82c8fc4ed3d847909d14162f51b77dc59ccc0a70"
PLANS = {
    "lake": "98041b225c3f85399289a2d9911ce5a9aedb7602a5084fb9037436bc2650462d",
    "prerequisites": "dd9524f9316a08c04059b1324aca81533c0635fcd5128fffe8328c2901d2d435",
}
PUBLICATIONS: dict[str, dict[str, Any]] = {
    "docs/report/source-relations/neotoma/lakeparameters/report.json": {
        "owner_id": "source-relations/neotoma/lakeparameters/source-review",
        "member": "execution/lake/independently-reconstructed-lakeparameter-report.json",
        "sha256": "9c5c48936b10f62b2501a9d26ddad102d606929ee55fbe76614431e731a21fa7",
        "bytes": 2818,
        "role": "checker_and_independent_source_reconstruction",
    },
    "docs/report/source-relations/neotoma/lra-prerequisites/projection.json": {
        "owner_id": "source-relations/neotoma/lra-prerequisites/report-products",
        "member": "execution/prerequisites/prerequisite-projection.json",
        "sha256": "26135d91bbe5d729dcca3a1f6f0ea69f5cec4dc00a54a6dd740d5004d4e4b809",
        "bytes": 22907955,
        "role": "maintained_current_prerequisite_producer_and_independent_observer",
    },
}


def file(repository: Path, name: str) -> Path:
    """Require an ordinary confined source-custody file."""
    try:
        return _regular_confined_file(repository, name, "Neotoma lake-source capture")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Missing, linked or unconfined lake-source member"
        ) from error


def pin(path: Path) -> dict[str, Any]:
    """Describe exact retained bytes without interpreting their contents."""
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def load(path: Path) -> Any:
    """Decode retained JSON with duplicate and nonfinite refusals."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "Duplicate lake-source JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return value
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Invalid lake-source JSON") from error


def validate_owners(owners: list[JsonObject]) -> None:
    """Require exact declared owners and publication paths."""
    for name, publication in PUBLICATIONS.items():
        selected = [
            row for row in owners if row.get("owner_id") == publication["owner_id"]
        ]
        exact(len(selected), 1)
        row = selected[0]
        for key, expected in (
            ("role", "retained_source"),
            ("paths", [name]),
            ("producer_paths", []),
            ("producer_inputs", []),
        ):
            exact(row[key], expected)
        for other in owners:
            if other is not row:
                other_paths = other.get("paths", [])
                require(isinstance(other_paths, list), "Owner path list required")
                assert isinstance(other_paths, list)
                require(name not in other_paths, "Lake-source owner overlap")


def validated_neotoma_lake_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only exact retained source-native lake-parameter receipts."""
    if not (repository / CAPTURE).exists() and not any(
        row.get("owner_id") in {p["owner_id"] for p in PUBLICATIONS.values()}
        and row.get("role") == "retained_source"
        for row in owners
    ):
        return (), {}
    validate_owners(owners)
    capture_path = file(repository, CAPTURE)
    exact(pin(capture_path), {"sha256": CAPTURE_SHA256, "bytes": CAPTURE_BYTES})
    capture = load(capture_path)
    exact(capture["schema_version"], "neotoma-lake-retained-source-capture.v1")
    exact(capture["retention_mode"], "authored_source_and_completed_execution_custody")
    for key in (
        "new_metadata_native_execution_claimed",
        "private_pages_runtime_bytecode_raw_relational_payloads_published",
        "independent_pollen_eligibility_recomputation_claimed",
        "new_HTTP_acquisition_basin_rights_human_ecology_LRA_or_release_admission",
    ):
        exact(capture[key], False)
    exact(capture["original_lake_source_sites"], 54)
    exact(capture["current_prerequisite_source_sites"], 163)
    members = capture["members"]
    exact(len(members), 2276)
    exact(capture["member_count"], 2276)
    validate_members(repository, capture_path.parent, members)
    prefix = Path(CAPTURE).parent.as_posix()

    def member(name: str) -> Path:
        require(name in members, "Undeclared native member")
        return file(repository, prefix + "/" + name)

    exact(set(capture["executions"]), set(PLANS))
    for label, plan_sha256 in PLANS.items():
        execution = capture["executions"][label]
        expected_count = 66482 if label == "lake" else 66513
        exact(execution["original_candidate"], ORIGINAL_CANDIDATE)
        exact(execution["original_plan_sha256"], plan_sha256)
        exact(execution["original_input_count"], expected_count)
        records = execution["execution_members"]
        plan = load(member(records["plan.json"]))
        common = load(member(records["terminal.json"]))
        outer = load(member(records["lakeparameter-terminal.json"]))
        checker = load(member(records["maintained-reader-checker.json"]))
        review = load(member(records["independent-source-review.json"]))
        report = load(
            member(records["independently-reconstructed-lakeparameter-report.json"])
        )
        exact(members[records["plan.json"]]["sha256"], plan_sha256)
        validate_lake_execution(
            plan,
            common,
            outer,
            checker,
            review,
            report,
            expected_candidate=ORIGINAL_CANDIDATE,
            expected_plan_sha256=plan_sha256,
        )
        exact(
            outer["common_terminal"],
            {
                "path": str(Path(plan["output"]) / "terminal.json"),
                **members[records["terminal.json"]],
            },
        )
        exact(
            review["reconstructed_report"],
            {
                "path": str(
                    Path(plan["output"])
                    / "independently-reconstructed-lakeparameter-report.json"
                ),
                **members[
                    records["independently-reconstructed-lakeparameter-report.json"]
                ],
            },
        )
        for stage in common["stages"]:
            for stream in ("stdout", "stderr"):
                name = Path(stage[stream]).relative_to(Path(plan["output"])).as_posix()
                exact(members[records[name]]["sha256"], stage[stream + "_sha256"])
        tails = execution["post_inventory_stream_tails"]
        exact(len(tails), 1)
        for original in common["products"]:
            name = Path(original["path"]).relative_to(Path(plan["output"])).as_posix()
            path = member(records[name])
            raw = path.read_bytes()
            exact(
                hashlib.sha256(raw[: original["bytes"]]).hexdigest(), original["sha256"]
            )
            if name == "root-launch.log":
                tail = tails[0]
                exact(tail["relative_path"], name)
                exact(tail["original_pin"], original)
                exact(raw[original["bytes"] :].hex(), tail["tail_hex"])
                expected_tail = [
                    {
                        "terminal": str(Path(plan["output"]) / "terminal.json"),
                        "sha256": members[records["terminal.json"]]["sha256"],
                        "status": "passed",
                    },
                    {
                        "terminal": {
                            "path": str(
                                Path(plan["output"]) / "lakeparameter-terminal.json"
                            ),
                            **members[records["lakeparameter-terminal.json"]],
                        },
                        "actual_exit": 0,
                    },
                ]
                exact(
                    [
                        json.loads(line)
                        for line in raw[original["bytes"] :].splitlines()
                    ],
                    expected_tail,
                )
                exact(tail["tail_records"], expected_tail)
            else:
                exact(len(raw), original["bytes"])
        authority = execution["runtime_authority_members"]
        runtime = load(member(authority["plan"]))
        runtime_paths = {row["path"] for row in runtime["input_pins"]}
        for key in ("plan", "common", "outer", "independent_review"):
            reference = plan["qualified_source_runtime"][key]
            exact(
                members[authority[key]], {k: reference[k] for k in ("sha256", "bytes")}
            )
            runtime_paths.add(reference["path"])
        catalog = load(member(execution["original_input_catalog_member"]))
        exact(len(catalog), expected_count)
        counts = validate_catalog(
            catalog,
            plan["input_pins"],
            members,
            private_root=execution["private_source_root"],
            repository=plan["repository"],
            public_paths=set(execution["public_input_paths"]),
            runtime_paths=runtime_paths,
            raw_relational_paths=set(plan["optional_inputs"]),
        )
        exact(counts, execution["source_retention_role_counts"])
        exact(counts["public_first_party_source_or_resource"], 2168)
        exact(counts["private_source_identity_only"], 28)
        exact(counts["bytecode_identity_only"], 4356)
        exact(
            counts.get("raw_relational_input_identity_only", 0),
            0 if label == "lake" else 30,
        )
        if label == "prerequisites":
            produced = load(member(records["maintained-projection-execution.json"]))
            exact(produced["actual_exit"], 0)
            exact(
                produced["actual_module"],
                "bijux_pollenomics_dev.taxa_review.lra_prerequisites",
            )
            exact(
                produced["generated_projection"],
                {
                    "path": str(Path(plan["output"]) / "prerequisite-projection.json"),
                    **members[records["prerequisite-projection.json"]],
                },
            )
            exact(
                members[records["prerequisite-projection.json"]],
                {
                    k: PUBLICATIONS[
                        "docs/report/source-relations/neotoma/lra-prerequisites/projection.json"
                    ][k]
                    for k in ("sha256", "bytes")
                },
            )
    exact(len(capture["current_source_bindings"]), 9)
    for name, expected in capture["current_source_bindings"].items():
        exact(pin(file(repository, name)), expected)
    entries = []
    for name, publication in PUBLICATIONS.items():
        source = member(publication["member"])
        expected = {k: publication[k] for k in ("sha256", "bytes")}
        exact(pin(source), expected)
        exact(file(repository, name).read_bytes(), source.read_bytes())
        entry = tracked_by_path.get(name)
        require(entry is not None, "Tracked lake-source publication missing")
        assert entry is not None
        exact(entry.path, name.removeprefix("docs/report/"))
        exact(entry.kind, "file")
        exact(entry.sha256, publication["sha256"])
        exact(entry.size, publication["bytes"])
        entries.append(entry)
    return tuple(entries), {
        "capture_sha256": CAPTURE_SHA256,
        "original_source_candidate": ORIGINAL_CANDIDATE,
        "lake_checker_and_independent_reconstruction_exits": [0, 0],
        "prerequisite_checker_producer_and_observer_exits": [0, 0, 0],
        "original_lake_sites": 54,
        "current_prerequisite_source_sites": 163,
        "current_prerequisite_source_samples": 10637,
        "independent_pollen_eligibility_recomputed": False,
        "LRA_or_basin_or_rights_or_human_admission": False,
        "whole_current_source_equivalence_claimed": False,
    }
