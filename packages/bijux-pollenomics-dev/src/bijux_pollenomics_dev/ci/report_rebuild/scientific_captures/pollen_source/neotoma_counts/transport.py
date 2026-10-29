"""Reconstruct a closed Neotoma selected-count execution packet from literal sealed metadata only."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

SCHEMA = "neotoma-selected-count-source-capture.v1"
PLAN_SHA = "05f915932c2e803680a98609e2bf449dafd693621c9356b5f0edf31c80e4dfb9"
SOURCE_SHA = "1b6021cd87c5d370635dbd7343bdafd964fa86d8d1bfa7c9990d81fa054700b2"
SAMPLE_IDS = ("neotoma:sample:173174", "neotoma:sample:552101", "neotoma:sample:552389")
INNER_SHA = "c5d1bc9a91a19dc3d3d08551e3f82c9008965595a382733279dc3c018f837fce"
OUTER_SHA = "e034ca2902f8f70c25c2570fa9cbd74f1a18ade7e87595e5f6d448e4f3f9d0ed"
REVIEW_SHA = "7a1ce54ac4816a5f580922085dcdc8694b99615c48e845f50299c4e789c28334"
SCOPE = {
    "metadata_retention_only": True,
    "raw_normalization_or_source_consumer_repeated": False,
    "historical_manifest_ownership_changed": False,
    "original_mass_or_manifest_construction_recovered": False,
    "complete_private_raw_normalized_runtime_bytecode_generated_payloads_included": False,
    "selected_derived_native_observation_and_age_excerpts_included": True,
    "physical_core_chronology_denominator_rights_human_or_LRA_admitted": False,
}


def require(value: object, text: str) -> None:
    if not value:
        raise ValueError(text)


def json_object(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(items) == len({key for key, _ in items}), "Duplicate metadata key")
        return dict(items)

    def constant(token: str) -> None:
        raise ValueError("Nonfinite metadata: " + token)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(isinstance(result, dict), "Object required")
    assert isinstance(result, dict)
    return result


def normalized(row: dict[str, Any]) -> dict[str, Any]:
    path = PurePosixPath(row["path"])
    checksum = row["sha256"]
    require(
        path.is_absolute()
        and path.as_posix() == row["path"]
        and ".." not in path.parts
        and "\\" not in row["path"],
        "Absolute normalized identity required",
    )
    require(
        type(row["bytes"]) is int
        and row["bytes"] >= 0
        and isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum),
        "Typed identity required",
    )
    return {k: row[k] for k in ("path", "sha256", "bytes")}


def indexed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        value = normalized(row)
        require(value["path"] not in result, "Duplicate identity path")
        result[value["path"]] = value
    return result


def member_name(name: object) -> str:
    require(isinstance(name, str), "Text member required")
    assert isinstance(name, str)
    path = PurePosixPath(name)
    require(
        bool(path.parts)
        and not path.is_absolute()
        and path.as_posix() == name
        and ".." not in path.parts
        and "\\" not in name
        and len(path.parts) == 2
        and path.parts[0] == "payloads"
        and len(path.parts[1]) == 64
        and all(c in "0123456789abcdef" for c in path.parts[1]),
        "Closed content-addressed member required",
    )
    return name


def blob(row: dict[str, Any]) -> str:
    return member_name("payloads/" + normalized(row)["sha256"])


def same(left: object, right: object) -> None:
    require(type(left) is type(right), "Metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        require(list(left) == list(right), "Metadata keys/order differ")
        for key in left:
            same(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Metadata list sizes differ")
        for a, b in zip(left, right, strict=True):
            same(a, b)
    else:
        require(left == right, "Metadata values differ")


def same_count_row(left: object, right: object) -> None:
    """Compare scientific JSON rows by fields/types, retaining ordered lists and exact values."""
    require(type(left) is type(right), "Scientific row metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        require(
            all(type(key) is str for key in left)
            and all(type(key) is str for key in right)
            and set(left) == set(right),
            "Scientific row key population differs",
        )
        for key in left:
            same_count_row(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Scientific row list sizes differ")
        for a, b in zip(left, right, strict=True):
            same_count_row(a, b)
    elif isinstance(left, float) and isinstance(right, float):
        require(
            left == left
            and right == right
            and abs(left) != float("inf")
            and abs(right) != float("inf")
            and left.hex() == right.hex(),
            "Scientific row finite binary64 values differ",
        )
    else:
        require(left == right, "Scientific row values differ")


def qualify_scope(
    plan: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    producer: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    candidate = plan["candidate"]
    require(
        isinstance(candidate, str)
        and len(candidate) == 40
        and all(c in "0123456789abcdef" for c in candidate),
        "Source epoch required",
    )
    require(
        plan["schema_version"] == "neotoma-owned-selected-count-plan.v1"
        and plan["canonical_identity_at_source_freeze"]["candidate"] == candidate
        and plan["canonical_identity_at_source_freeze"]["status"] == "",
        "Original source-freeze epoch differs",
    )
    require(
        len(plan["input_pins"]) == 62148,
        "Original fixed ordered input population differs",
    )
    selected = [
        "neotoma:sample:" + str(row["sample_id"]) for row in plan["selected_samples"]
    ]
    same(selected, list(SAMPLE_IDS))
    for obj in (inner, outer, producer, review):
        require(
            obj["candidate"] == candidate
            and type(obj["actual_exit"]) is int
            and obj["actual_exit"] == 0,
            "Exact successful native epoch required",
        )
    require(
        inner["plan_sha256"] == outer["plan_sha256"] == PLAN_SHA,
        "Original registered plan differs",
    )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["live_canonical_equality_claimed"] is False
        and all(
            inner[k] is True
            for k in (
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_whole_wall_bound_pass",
            )
        ),
        "Inner custody/resource failure",
    )
    require(
        type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 0
        and outer["child_timed_out"] is False
        and all(
            outer[k] is True
            for k in (
                "registered_plan_unchanged",
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_outer_wall_bound_pass",
            )
        ),
        "Outer custody/resource failure",
    )
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2,
        "Exactly two native stages required",
    )
    for declared, actual, name, action, seconds in zip(
        plan["stages"],
        inner["stages"],
        (
            "maintained-selected-source-series",
            "independent-native-count-locator-observer",
        ),
        ("producer", "observer"),
        (180, 120),
        strict=True,
    ):
        require(
            declared["id"] == actual["id"] == name
            and declared["action"] == actual["action"] == action
            and type(declared["timeout_seconds"]) is int
            and declared["timeout_seconds"] == seconds
            and type(actual["timeout_seconds"]) is int
            and actual["timeout_seconds"] == seconds
            and declared["argv"] == actual["argv"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Native role/argv/time/exit mismatch",
        )
    same(producer["selected_sample_ids"], selected)
    same(producer["distinct_native_request_roles"], plan["selected_samples"])
    same(
        producer["maintained_public_calls"],
        [
            "read_neotoma_evidence(raw_root, normalized_root)",
            "build_neotoma_candidate_series(evidence, selected_sample_ids)",
        ],
    )
    require(
        producer["numerical_import_attempts"] == []
        and producer["raw_root"] == plan["raw_root"]
        and producer["normalized_root"] == plan["normalized_root"],
        "Actual source/API scope differs",
    )
    for key in (
        "normalization_HTTP_model_or_R_executed",
        "original_mass_or_manifest_constructor_recovered",
        "physical_core_chronology_denominator_rights_human_or_LRA_admitted",
    ):
        require(producer[key] is False, "Producer scope inflated")
    require(
        review["full_typed_and_canonical_series_equal"] is True
        and review["all_native_age_alternatives_and_raw_bounds_preserved"] is True
        and review["source_unit_zero_missing_fraction_and_noncount_refusals_preserved"]
        is True,
        "Full native source reconstruction absent",
    )
    for key in (
        "chronology_selection_or_support_hull_performed",
        "original_mass_or_manifest_construction_approval_recovered",
        "original_HTTP_capture_or_physical_core_identity_recovered",
        "country_attribution_independently_recomputed",
        "pollen_denominator_taxon_PPE_rights_human_model_or_LRA_admitted",
    ):
        require(review[key] is False, "Independent scientific scope inflated")
    same(review["actual_maintained_series"], producer["product"])
    same(
        [row["sample_id"] for row in review["current_source_count_mass_rows"]], selected
    )
    same([row["sample_id"] for row in review["selected_sample_identities"]], selected)
    domains = ["abbo-core-identity", "swedish-lake-core-identity"]
    require(
        [r["domain"] for r in review["retained_receipt_row_comparisons"]] == domains,
        "Exactly two retained count domains required",
    )
    for row in review["retained_receipt_row_comparisons"]:
        require(
            row["native_scientific_row_reconstruction_equal"] is True
            and row["original_mass_object_recovered"] is False
            and row["original_mass_or_manifest_construction_approval_recovered"]
            is False,
            "Historical construction promoted",
        )
    for row in review["current_source_count_mass_rows"]:
        require(
            row["known_compatible_pollen_denominator_status"] == "not_evaluated"
            and row["lra_admission_status"] == "refused",
            "Source-label partition promoted to denominator",
        )
    require(
        type(review["selected_denominators"]["samples"]) is int
        and review["selected_denominators"]["samples"]
        == review["selected_denominators"]["lra_refused_samples"]
        == 3,
        "Three refused selected samples required",
    )
    return {
        "source_candidate": candidate,
        "original_producer_native_exit": 0,
        "original_independent_native_exit": 0,
        "original_inner_and_outer": [0, 0],
        "selected_denominators": review["selected_denominators"],
        "current_source_count_mass_rows": review["current_source_count_mass_rows"],
        "historical_manifest_ownership_changed": False,
        "original_mass_or_manifest_construction_recovered": False,
        "scientific_chronology_or_LRA_admission": False,
    }


def source_join(plan: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    same(ledger["canonical_identity"], plan["canonical_identity_at_source_freeze"])
    require(
        ledger["bytecode_payloads_copied_or_executed"] is False
        and ledger["bytecode_source_equivalence_claimed"] is False,
        "Opaque sources promoted",
    )
    original, selected, copied, caches, generated = [
        indexed(ledger[k])
        for k in (
            "original_sources",
            "selected_execution_sources",
            "copied_sources",
            "omitted_unselected_cache_bytecode",
            "omitted_configured_generated_metadata",
        )
    ]
    require(
        tuple(map(len, (original, selected, copied, caches, generated)))
        == (6541, 2184, 2184, 4356, 1),
        "Original source ledger populations differ",
    )
    require(
        set(original) == set(selected) | set(caches) | set(generated)
        and len(original) == len(selected) + len(caches) + len(generated),
        "Source partition differs",
    )
    root, owned = (
        PurePosixPath(plan["repository"]),
        PurePosixPath(plan["owned_repository"]),
    )
    result: list[dict[str, Any]] = []
    for name, row in selected.items():
        relative = PurePosixPath(name).relative_to(root)
        path = str(owned / relative)
        allowed = (
            len(relative.parts) >= 4
            and relative.parts[0] == "packages"
            and relative.parts[1]
            in {
                "bijux-pollenomics",
                "bijux-pollenomics-lra",
                "bijux-pollenomics-dev",
                "pollenomics",
            }
            and relative.parts[2] == "src"
        ) or relative.as_posix() in {
            "packages/bijux-pollenomics-lra/pyproject.toml",
            "packages/bijux-pollenomics-lra/.gitignore",
        }
        require(
            allowed
            and relative.suffix not in {".pyc", ".pyo"}
            and path in copied
            and row == original[name]
            and all(copied[path][k] == row[k] for k in ("sha256", "bytes")),
            "Owned source join differs",
        )
        result.append(
            {
                "original": row,
                "execution_copy": copied[path],
                "role": "public_owned_source_resource",
            }
        )
    require(
        {v["execution_copy"]["path"] for v in result} == set(copied),
        "Extra copied sources",
    )
    for rows, key in (
        (caches, "omitted_unselected_cache_bytecode"),
        (generated, "omitted_configured_generated_metadata"),
    ):
        for item in ledger[key]:
            require(
                item["executed_or_copied"] is False
                and item["source_equivalence_claimed"] is False,
                "Omitted identity promoted",
            )
        for row in rows.values():
            result.append(
                {
                    "original": row,
                    "execution_copy": None,
                    "role": "bytecode_identity_only"
                    if rows is caches
                    else "configured_generated_metadata_identity_only",
                }
            )
    return result


def input_roles(
    plan: dict[str, Any],
    ledger: dict[str, Any],
    source: dict[str, Any],
    source_pin: dict[str, Any],
    peer_pin: dict[str, Any],
    runtime_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    groups = {
        "public_owned_source_resource": indexed(ledger["copied_sources"]),
        "public_source_ledger": indexed([plan["source_ledger"]]),
        "private_raw_normalized_identity_only": indexed(
            [
                {
                    **row,
                    "path": str(
                        PurePosixPath(plan["private_source_root"]) / row["path"]
                    ),
                }
                for row in plan["declared_inputs"]
            ]
        ),
        "public_original_count_manifest_report": indexed(
            [
                {
                    **row,
                    "path": str(
                        PurePosixPath(plan["private_source_root"]) / row["path"]
                    ),
                }
                for row in plan["source_declaration"]["public_retained_inputs"]
            ]
        ),
        "public_prior_input_identity_authority": indexed(
            [
                row
                for row in plan["input_pins"]
                if row["path"]
                in {
                    str(
                        PurePosixPath(plan["private_source_root"])
                        / plan["source_declaration"]["input_identity_authority"][
                            "capture_path"
                        ]
                    ),
                    str(
                        PurePosixPath(plan["private_source_root"])
                        / PurePosixPath(
                            plan["source_declaration"]["input_identity_authority"][
                                "capture_path"
                            ]
                        ).parent
                        / plan["source_declaration"]["input_identity_authority"][
                            "catalog_member"
                        ]
                    ),
                }
            ]
        ),
        "public_source_controller": indexed(source["files"] + [source_pin, peer_pin]),
        "runtime_identity_only": indexed(
            runtime_plan["input_pins"]
            + [
                plan["qualified_source_runtime"][k]
                for k in ("plan", "outer", "common", "independent_review")
            ]
        ),
    }
    require(
        len(groups["private_raw_normalized_identity_only"]) == 30
        and len(groups["public_original_count_manifest_report"]) == 6
        and len(groups["public_prior_input_identity_authority"]) == 2,
        "Original raw input identities differ",
    )
    originals = indexed(plan["input_pins"])
    result = []
    for index, row in enumerate(plan["input_pins"]):
        names = [name for name, rows in groups.items() if row["path"] in rows]
        require(
            bool(names), "Original input lacks finite declared role: " + row["path"]
        )
        for name in names:
            same(normalized(row), groups[name][row["path"]])
        result.append(
            {
                "original_index": index,
                "identity": normalized(row),
                "roles": names,
                "payload_member": blob(row)
                if any(name.startswith("public_") for name in names)
                else None,
            }
        )
    for name, rows in groups.items():
        if name != "runtime_identity_only":
            require(
                set(rows) <= set(originals),
                "Declared native role absent from original pins",
            )
    return result


def output_namespace(
    plan: dict[str, Any],
    catalogue: dict[str, Any],
    refs: dict[str, Any],
    outer: dict[str, Any],
) -> dict[str, Any]:
    root = PurePosixPath(plan["output"])
    names = {row["path"] for row in catalogue["files"]}
    names.update(refs[key]["path"] for key in ("catalogue", "inner", "outer"))
    names.update(outer[key]["path"] for key in ("stdout", "stderr"))
    entries: dict[str, dict[str, str]] = {}
    for name in names:
        path = PurePosixPath(name)
        require(path.is_relative_to(root), "Native output escapes original root")
        relative = path.relative_to(root)
        entries[relative.as_posix()] = {"kind": "file"}
        for parent in relative.parents:
            if parent != PurePosixPath("."):
                entries[parent.as_posix()] = {"kind": "directory"}
    for snapshot in plan["owned_namespace_snapshots"]:
        prefix = PurePosixPath(snapshot["root"]).relative_to(root)
        for name, row in snapshot["entries"].items():
            if row["kind"] == "directory":
                entries[(prefix / name).as_posix()] = {"kind": "directory"}
    for name in ("scratch", "cache", "cache/matplotlib"):
        entries[name] = {"kind": "directory"}
    return {"root": str(root), "excluded": [], "entries": dict(sorted(entries.items()))}


def exact_public_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = normalized(row)
        require(
            item["path"] not in result or result[item["path"]] == item,
            "Conflicting public role identity",
        )
        result[item["path"]] = item
    return result


def outer_stream_correspondence(
    catalogue: dict[str, Any], outer: dict[str, Any], inner_pin: dict[str, Any]
) -> dict[str, Any]:
    """The launcher writes PIPE buffers only after the inner catalogue is closed."""
    rows = indexed(catalogue["files"])
    stdout, stderr = normalized(outer["stdout"]), normalized(outer["stderr"])
    require(
        stdout["path"] != stderr["path"]
        and stdout["path"] not in rows
        and stderr["path"] not in rows,
        "Outer streams must be absent from the earlier inner catalogue",
    )
    tail = (
        json.dumps({"terminal": normalized(inner_pin), "actual_exit": 0}) + "\n"
    ).encode()
    require(
        stdout["bytes"] == len(tail)
        and stdout["sha256"] == hashlib.sha256(tail).hexdigest(),
        "Outer stdout must be the complete source-derived inner receipt line",
    )
    return {
        "stdout": stdout,
        "stderr": stderr,
        "outer_streams_absent_from_inner_catalogue": True,
        "streams_written_after_inner_catalogue": True,
        "stdout_is_exact_inner_receipt_print": True,
    }


def validate_packet(
    packet: dict[str, Any], read: Callable[[str], bytes]
) -> dict[str, Any]:
    require(
        set(packet)
        == {
            "schema_version",
            "native_references",
            "source_controller",
            "metadata_source_controller",
            "runtime_authority",
            "public_bindings",
            "members",
            "original_input_roles",
            "original_source_join",
            "original_output_namespace",
            "outer_stream_catalogue_correspondence",
            "receipt_scope",
            "scope",
        },
        "Closed capture schema required",
    )
    same(packet["scope"], SCOPE)
    require(packet["schema_version"] == SCHEMA, "Capture schema differs")
    members = packet["members"]
    require(list(members) == sorted(members), "Sorted packet members required")
    for name, row in members.items():
        member_name(name)
        raw = read(name)
        require(
            hashlib.sha256(raw).hexdigest() == row["sha256"] == name.split("/")[1]
            and len(raw) == row["bytes"],
            "Packet payload changed",
        )
    bindings = packet["public_bindings"]
    by_path = indexed([v["original"] for v in bindings])
    require(
        {v["member"] for v in bindings} == set(members),
        "Public payload coverage differs",
    )
    for binding in bindings:
        require(
            binding["member"] == blob(binding["original"])
            and members[binding["member"]]
            == {k: binding["original"][k] for k in ("sha256", "bytes")},
            "Public binding differs",
        )

    def object_at(row: dict[str, Any]) -> dict[str, Any]:
        same(by_path[row["path"]], normalized(row))
        return json_object(read(blob(row)))

    refs = packet["native_references"]
    require(
        refs["plan"]["sha256"] == PLAN_SHA
        and packet["source_controller"]["manifest"]["sha256"] == SOURCE_SHA,
        "Original plan/source manifest differs",
    )
    plan = object_at(refs["plan"])
    same(refs["source_ledger"], plan["source_ledger"])
    require(
        refs["source_ledger"]["sha256"]
        == "d2e2639682e73069fefdb09812b4c287c109090042fbbf2cd6d8ed84119358da",
        "Original source ledger differs",
    )
    ledger = object_at(refs["source_ledger"])
    same(packet["runtime_authority"], plan["qualified_source_runtime"])
    inner, outer, producer, review = [
        object_at(refs[key]) for key in ("inner", "outer", "producer", "review")
    ]
    same(packet["receipt_scope"], qualify_scope(plan, inner, outer, producer, review))
    source = object_at(packet["source_controller"]["manifest"])
    source_peer = object_at(packet["source_controller"]["review"])
    require(
        source["source_only"] is True
        and source_peer["approved"] is True
        and source_peer["source_manifest_sha256"] == SOURCE_SHA,
        "Original source approval differs",
    )
    runtime_plan = object_at(packet["runtime_authority"]["plan"])
    same(packet["original_source_join"], source_join(plan, ledger))
    same(
        packet["original_input_roles"],
        input_roles(
            plan,
            ledger,
            source,
            packet["source_controller"]["manifest"],
            packet["source_controller"]["review"],
            runtime_plan,
        ),
    )
    for row in packet["original_input_roles"]:
        if row["payload_member"] is not None:
            require(row["identity"]["path"] in by_path, "Declared public input missing")
    for row in source["files"] + [packet["source_controller"]["review"]]:
        same(by_path[row["path"]], normalized(row))
    same(refs["catalogue"], inner["products_manifest"])
    same(refs["inner"], outer["inner_terminal"])
    catalogue = object_at(refs["catalogue"])
    same(
        packet["original_output_namespace"],
        output_namespace(plan, catalogue, refs, outer),
    )
    require(
        len(catalogue["files"]) == inner["products_count_before_manifest"],
        "Complete catalogue size differs",
    )
    same(
        packet["outer_stream_catalogue_correspondence"],
        outer_stream_correspondence(catalogue, outer, refs["inner"]),
    )
    metadata_source = object_at(packet["metadata_source_controller"]["manifest"])
    metadata_peer = object_at(packet["metadata_source_controller"]["review"])
    require(
        metadata_source["source_only"] is True
        and metadata_peer["approved"] is True
        and metadata_peer["source_manifest_sha256"]
        == packet["metadata_source_controller"]["manifest"]["sha256"],
        "Metadata source approval differs",
    )
    wanted = exact_public_rows(
        catalogue["files"]
        + [
            row["identity"]
            for row in packet["original_input_roles"]
            if row["payload_member"] is not None
        ]
        + list(refs.values())
        + [outer["stdout"], outer["stderr"]]
        + source["files"]
        + list(packet["source_controller"].values())
        + [
            packet["runtime_authority"][k]
            for k in ("plan", "outer", "common", "independent_review")
        ]
        + metadata_source["files"]
        + list(packet["metadata_source_controller"].values())
    )
    require(set(by_path) == set(wanted), "Public role union has missing/extra payloads")
    for path in wanted:
        same(by_path[path], wanted[path])
    for row in catalogue["files"]:
        same(by_path[row["path"]], normalized(row))
    same(by_path[producer["product"]["path"]], normalized(producer["product"]))
    same(refs["inner"]["sha256"], INNER_SHA)
    same(refs["outer"]["sha256"], OUTER_SHA)
    same(refs["review"]["sha256"], REVIEW_SHA)
    for comparison in review["retained_receipt_row_comparisons"]:
        for key in (
            "actual_count_receipt",
            "saved_custody_manifest",
            "existing_report",
        ):
            row = comparison[key]
            same(by_path[row["path"]], normalized(row))
        receipt = object_at(comparison["actual_count_receipt"])
        manifest = object_at(comparison["saved_custody_manifest"])
        same(
            receipt["original_mass_sha256"],
            comparison["original_mass_sha256_historical_claim"],
        )
        same(
            manifest["historical_comparison"],
            comparison["historical_comparison_fields_retained"],
        )
        rows = (
            [receipt["sample_row"]]
            if comparison["domain"] == "abbo-core-identity"
            else receipt["sample_rows"]
        )
        expected = {r["sample_id"]: r for r in review["current_source_count_mass_rows"]}
        for row in rows:
            same_count_row(row, expected[row["sample_id"]])
    return dict(packet["receipt_scope"])
