"""Admit exact Neotoma publication products with a finite two-leaf provenance bridge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....ownership import ReportOwnershipError, _regular_confined_file
from .execution import (
    exact,
    metadata_bridge,
    require,
    validate_history,
    validate_review,
    validate_source_role,
)
from .members import validate_catalog, validate_members

CAPTURE = "data/source-custody/neotoma/publication-attribution/capture.json"
CAPTURE_SHA256 = "6a647a0962bf75e924b84f5c785980df8726e66dc664baaf7601bf38ce0b1c7d"
CAPTURE_BYTES = 536650
MEMBERS = 2355
CANDIDATE = "82c8fc4ed3d847909d14162f51b77dc59ccc0a70"
OWNER = "regions/nordic/source-capability/neotoma-attribution/report-products"
BASE = "docs/report/regions/nordic/source-capability/neotoma-attribution/"
PLANS = {
    "production": "ca4003d9c94379843d7803d8cc213c7fe89be4789615dce58fcc4a0c779fb11f",
    "observation": "930fcdf6ea3378124877bee4cf14b23276ae57696cac33d1db9b408d31dba393",
}
PRODUCTS: dict[str, dict[str, Any]] = {
    BASE + "report.json": {
        "sha256": "983286a711b37be4db3dccac200fe24f814ff2b350a906e1a0fd99717104142d",
        "bytes": 188753,
    },
    BASE + "doi-review.json": {
        "sha256": "61dde7cc0e8943bb8464d907c7927bd795ecb8ec377ba910a2dba9d9c3356823",
        "bytes": 30891,
    },
}


def file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(repository, name, "Neotoma publication capsule")
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "Unconfined or missing Neotoma publication member"
        ) from error


def pin(path: Path) -> dict[str, Any]:
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    try:
        result = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(result, allow_nan=False)
        return result
    except (ValueError, OSError) as error:
        raise ReportRebuildError("Invalid Neotoma publication JSON") from error


def validate_owner(owners: list[JsonObject]) -> None:
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    exact(len(selected), 1)
    row = selected[0]
    for key, value in {
        "role": "retained_source",
        "paths": sorted(PRODUCTS),
        "producer_paths": [],
        "producer_inputs": [],
    }.items():
        exact(row[key], value)
    for other in owners:
        if other is not row:
            other_paths = other.get("paths", [])
            require(isinstance(other_paths, list), "Owner path sequence required")
            assert isinstance(other_paths, list)
            require(
                not set(PRODUCTS).intersection(other_paths),
                "Publication owner overlap",
            )


def validated_neotoma_publication_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    if not (repository / CAPTURE).exists() and not any(
        row.get("owner_id") == OWNER and row.get("role") == "retained_source"
        for row in owners
    ):
        return (), {}
    validate_owner(owners)
    capture_path = file(repository, CAPTURE)
    exact(pin(capture_path), {"sha256": CAPTURE_SHA256, "bytes": CAPTURE_BYTES})
    capture = load(capture_path)
    exact(capture["schema_version"], "neotoma-publication-retained-source-capture.v1")
    exact(capture["retention_mode"], "authored_source_and_completed_execution_custody")
    exact(capture["original_execution_candidate"], CANDIDATE)
    for key in (
        "new_metadata_native_execution_claimed",
        "private_provider_or_DataCite_runtime_or_bytecode_payloads_published",
        "original_acquisition_predecessor_06f08e_authenticated",
        "HTTP_rights_citation_selection_human_ecological_or_LRA_admission",
    ):
        exact(capture[key], False)
    exact(capture["original_whole_failed_and_raw_checker_failures_preserved"], True)
    members = capture["members"]
    exact(len(members), MEMBERS)
    exact(capture["member_count"], MEMBERS)
    validate_members(capture_path.parent, members)
    prefix = Path(CAPTURE).parent.as_posix()

    def member(name: str) -> Path:
        require(name in members, "Unknown execution member")
        return file(repository, prefix + "/" + name)

    original_roles = load(
        member(
            capture["retention_authority_members"][
                "ordered-original-input-identities.json"
            ]
        )
    )
    exact(len(original_roles), 66723)
    role_map = {row["path"]: row for row in original_roles}
    exact(len(role_map), 66723)
    retention = load(
        member(capture["retention_authority_members"]["source-retention.json"])
    )
    exact(retention["original_execution_candidate"], CANDIDATE)
    aliases = {
        str(
            Path(retention["original_plan"]["path"]).parents[1]
            / "neotoma-publication-execution-source-retention"
            / name
        ): name
        for name in retention["members"]
    }
    runtime = load(member(capture["runtime_authority_members"]["plan"]))
    runtime_paths = {row["path"] for row in runtime["input_pins"]}
    contexts = {}
    exact(set(capture["executions"]), set(PLANS))
    for label, expected in PLANS.items():
        record = capture["executions"][label]
        refs = record["execution_members"]
        plan = load(member(refs["plan.json"]))
        common = load(member(refs["terminal.json"]))
        inner_name = (
            "neotoma-publication-terminal.json"
            if label == "production"
            else "neotoma-publication-observer-terminal.json"
        )
        inner = load(member(refs[inner_name]))
        outer = load(member(refs["runtime-custody-terminal.json"]))
        exact(members[refs["plan.json"]]["sha256"], expected)
        validate_history(
            plan,
            common,
            inner,
            outer,
            label=label,
            candidate=CANDIDATE,
            plan_sha256=expected,
        )
        exact(
            record["native_stage_exits"],
            [row["actual_exit"] for row in common["stages"]],
        )
        exact(record["original_whole_exit"], common["actual_exit"])
        exact(record["original_candidate"], CANDIDATE)
        exact(record["original_plan_sha256"], expected)
        exact(record["original_input_count"], 66723 if label == "production" else 68978)
        catalog = load(member(record["original_input_catalog_member"]))
        counts = validate_catalog(
            catalog,
            plan["input_pins"],
            members,
            original_roles=role_map,
            runtime_paths=runtime_paths,
            repository=plan["repository"],
            retained_aliases=aliases,
        )
        exact(counts, record["source_retention_role_counts"])
        exact(counts["private_source_identity_only"], 256)
        exact(counts["bytecode_identity_only"], 4356)
        exact(counts["runtime_dependency_identity_only"], 59856)
        for original in common["products"]:
            name = Path(original["path"]).relative_to(Path(plan["output"])).as_posix()
            raw = member(refs[name]).read_bytes()
            exact(
                hashlib.sha256(raw[: original["bytes"]]).hexdigest(), original["sha256"]
            )
            tails = [
                row
                for row in record["post_inventory_stream_tails"]
                if row["relative_path"] == name
            ]
            if tails:
                exact(len(tails), 1)
                exact(name, "runtime-delegate.stdout")
                exact(tails[0]["original_pin"], original)
                exact(raw[original["bytes"] :].hex(), tails[0]["tail_hex"])
                expected_tail = [
                    {
                        "terminal": str(Path(plan["output"]) / "terminal.json"),
                        "sha256": members[refs["terminal.json"]]["sha256"],
                        "status": "failed" if label == "production" else "passed",
                    }
                ]
                exact(
                    [
                        json.loads(line)
                        for line in raw[original["bytes"] :].splitlines()
                    ],
                    expected_tail,
                )
                exact(tails[0]["tail_records"], expected_tail)
            else:
                exact(len(raw), original["bytes"])
        for stage in common["stages"]:
            for stream in ("stdout", "stderr"):
                name = Path(stage[stream]).relative_to(Path(plan["output"])).as_posix()
                exact(members[refs[name]]["sha256"], stage[stream + "_sha256"])
        contexts[label] = (plan, common, inner, outer, refs)
    production, _, _, _, produced_refs = contexts["production"]
    observation, _, _, _, observed_refs = contexts["observation"]
    pins = {row["path"]: row for row in production["input_pins"]}
    receipts = {}
    for kind in ("publication", "doi"):
        receipt = load(member(produced_refs[kind + "-source-execution.json"]))
        original = role_map[receipt["source"]["path"]]
        validate_source_role(
            kind, member(original["retained_member"]).read_bytes(), receipt, pins
        )
        exact(
            receipt["plan"],
            {
                "path": str(Path(production["output"]) / "plan.json"),
                **members[produced_refs["plan.json"]],
            },
        )
        exact(receipt["candidate"], CANDIDATE)
        stage = contexts["production"][1]["stages"][0 if kind == "publication" else 1]
        exact(receipt["actual_launcher_argv"], [stage["argv"][0], *stage["argv"][3:]])
        receipts[kind] = receipt
    report_member = produced_refs["producer/" + BASE + "report.json"]
    exact(
        receipts["doi"]["stage2_generated_input"],
        {
            "path": str(Path(production["output"]) / "producer" / BASE / "report.json"),
            **members[report_member],
        },
    )
    review = load(member(observed_refs["independent-publication-review.json"]))
    validate_review(review)
    exact(review["actual_maintained_stages"], contexts["production"][1]["stages"][:2])
    exact(
        review["plan"],
        {
            "path": str(Path(production["output"]) / "plan.json"),
            **members[produced_refs["plan.json"]],
        },
    )
    exact(
        review["observer_plan"],
        {
            "path": str(Path(observation["output"]) / "plan.json"),
            **members[observed_refs["plan.json"]],
        },
    )
    exact(
        capture["only_named_metadata_bridges"],
        [row["sole_metadata_delta"] for row in review["whole_product_comparisons"]],
    )
    exact(
        capture["only_named_metadata_bridges"],
        [
            {
                "field": "provider_policy.governed_review_sha256",
                "governed": "ce5d0a81584e5f0a93015b1045dc8ce4a2c828065368e9a0760dcfa92dbef720",
                "generated": "1b0e9ca73263132c62ab521957a4fb14120f7d1a3fa0a8583df3552ca0c7411d",
            },
            {
                "field": "attribution_ledger_sha256",
                "governed": "db84557f4b19ba47f44b122e482b157ca91a3dc327c0b0435809599a41b769b3",
                "generated": "983286a711b37be4db3dccac200fe24f814ff2b350a906e1a0fd99717104142d",
            },
        ],
    )
    policy = capture["policy_authority_members"]
    exact(
        members[policy["historical_policy_review"]]["sha256"],
        "ce5d0a81584e5f0a93015b1045dc8ce4a2c828065368e9a0760dcfa92dbef720",
    )
    exact(
        members[policy["current_policy_review"]]["sha256"],
        "1b0e9ca73263132c62ab521957a4fb14120f7d1a3fa0a8583df3552ca0c7411d",
    )
    for comparison, name in zip(
        review["whole_product_comparisons"],
        (BASE + "report.json", BASE + "doi-review.json"),
        strict=True,
    ):
        current = produced_refs["producer/" + name]
        governed = role_map[str(Path(production["repository"]) / name)][
            "retained_member"
        ]
        delta = comparison["sole_metadata_delta"]
        metadata_bridge(
            load(member(current)),
            load(member(governed)),
            delta["field"],
            delta["governed"],
            delta["generated"],
        )
        exact(comparison["whole_byte_checker_exit"], 2)
        exact(comparison["complete_ordered_typed_values_equal"], False)
        exact(comparison["strict_named_metadata_bridge_equal"], True)
    exact(len(capture["current_source_bindings"]), 3)
    for name, expected_pin in capture["current_source_bindings"].items():
        exact(pin(file(repository, name)), expected_pin)
    entries = []
    for name, expected_pin in PRODUCTS.items():
        source = member(produced_refs["producer/" + name])
        exact(pin(source), expected_pin)
        exact(file(repository, name).read_bytes(), source.read_bytes())
        entry = tracked_by_path.get(name)
        require(entry is not None, "Tracked publication output missing")
        assert entry is not None
        exact(entry.path, name.removeprefix("docs/report/"))
        exact(entry.kind, "file")
        exact(entry.sha256, expected_pin["sha256"])
        exact(entry.size, expected_pin["bytes"])
        entries.append(entry)
    return tuple(entries), {
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": CANDIDATE,
        "original_native_exits": [0, 0, 1],
        "original_whole_exit": 1,
        "original_tracked_checker_exits": [2, 2],
        "observer_only_native_exits": [0],
        "used_datasets": 85,
        "distinct_DOI_pairs": 13,
        "original_HTTP_rights_citation_selection_human_or_LRA_admission": False,
    }
