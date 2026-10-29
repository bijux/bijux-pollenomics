"""Reconstruct a closed AADR execution packet from literal sealed metadata only."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

SCHEMA = "aadr-current-default-export-capture.v1"
PLAN_SHA = "86618be564ff435074e2518a383e0bd1066e9e479bf397296edf6bd8d944d7bc"
SOURCE_SHA = "3fc43e79c612e350faae43042a5f9139fac1e9121732e513b235a87394f92626"
COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
SCOPE = {
    "metadata_retention_only": True,
    "raw_ANNO_or_exporter_reexecuted": False,
    "publisher_ownership_changed": False,
    "old_v1_products_or_lifecycle_relabelled": False,
    "runtime_raw_bytecode_generated_payloads_included": False,
    "scientific_chronology_genotype_rights_human_ecology_pollen_LRA_admitted": False,
}


def require(value: object, text: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ValueError(text)


def json_object(raw: bytes) -> dict[str, Any]:
    """Decode a retained JSON object while rejecting duplicate member names."""

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
    """Validate the declared source path, byte length and digest."""
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
    """Index declared members while refusing duplicate source paths."""
    result = {}
    for row in rows:
        value = normalized(row)
        require(value["path"] not in result, "Duplicate identity path")
        result[value["path"]] = value
    return result


def member_name(name: object) -> str:
    """Validate a literal confined member name."""
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
    """Return the content-addressed member name for the declared identity."""
    return member_name("payloads/" + normalized(row)["sha256"])


def same(left: object, right: object) -> None:
    """Require exact nested values, native types and source membership."""
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


def qualify_scope(
    plan: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    producer: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Check declared scope against captured execution and data roles."""
    candidate = plan["candidate"]
    require(
        isinstance(candidate, str)
        and len(candidate) == 40
        and all(c in "0123456789abcdef" for c in candidate),
        "Source epoch required",
    )
    require(
        plan["schema_version"] == "adna-owned-sample-export-plan.v1"
        and plan["canonical_identity_at_source_freeze"]["candidate"] == candidate
        and plan["canonical_identity_at_source_freeze"]["status"] == "",
        "Original source-freeze epoch differs",
    )
    require(
        plan["countries"] == list(COUNTRIES) and len(plan["input_pins"]) == 62114,
        "Original fixed input/country population differs",
    )
    for obj in (inner, outer):
        require(
            obj["candidate"] == candidate
            and obj["plan_sha256"] == PLAN_SHA
            and type(obj["actual_exit"]) is int
            and obj["actual_exit"] == 0,
            "No successful original receipt for exact plan",
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
        "Exactly both native stages required",
    )
    for declared, actual, name, action in zip(
        plan["stages"],
        inner["stages"],
        ("maintained-sample-producer", "independent-source-sample-observer"),
        ("producer", "observer"),
        strict=True,
    ):
        require(
            declared["id"] == actual["id"] == name
            and declared["action"] == actual["action"] == action
            and type(declared["timeout_seconds"]) is int
            and declared["timeout_seconds"] == 180
            and type(actual["timeout_seconds"]) is int
            and actual["timeout_seconds"] == 180
            and declared["argv"] == actual["argv"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Native stage role/argv/time/exit mismatch",
        )
    for obj in (producer, review):
        require(
            obj["candidate"] == candidate
            and type(obj["actual_exit"]) is int
            and obj["actual_exit"] == 0,
            "Actual native product witness missing",
        )
    require(
        producer["numerical_import_attempts"] == []
        and producer["new_current_source_contract"] is True
        and producer["legacy_v1_inverse_or_historical_reproduction_claimed"] is False
        and producer[
            "rich_native_provenance_recovered_or_genotype_rights_ecology_human_LRA_admitted"
        ]
        is False,
        "Producer scope inflated",
    )
    require(
        review["full_typed_metadata_and_both_default_v2_transports_verified"] is True
        and review["historical_byte_equality_required_or_assumed"] is False
        and review["old_v1_inverse_or_original_missing_receipt_recovery"] is False
        and review["genotype_biology_ecology_rights_calibration_or_LRA_acceptance"]
        is False
        and review["independent_observer_calls_public_loader_or_exporter"] is False
        and review[
            "software_interval_hull_does_not_validate_disjoint_scientific_support"
        ]
        is True
        and review["disjoint_support_gaps_remain_scientifically_refused"] is True,
        "Independent scope inflated",
    )
    require(
        [r["country_query"] for r in review["countries"]]
        == list(COUNTRIES)
        == [r["country_query"] for r in producer["countries"]],
        "Country witnesses differ",
    )
    for actual, observed in zip(
        producer["countries"], review["countries"], strict=True
    ):
        require(
            type(actual["sample_count"]) is int
            and actual["sample_count"] == observed["current_unique_samples"]
            and observed["full_typed_and_v2_CSV_GeoJSON_equal"] is True,
            "Full native typed result differs",
        )
        same(actual["dataset_row_counts"], observed["current_dataset_row_counts"])
        audit = observed["duplicate_native_chronology_support_audit"]
        require(
            audit["original_supports_preserved"] is True
            and audit["calibration_or_chronology_scientifically_validated"] is False,
            "Native support evidence lost or inflated",
        )
        require(
            audit["counts"]["duplicate_ids"] == len(audit["duplicates"]),
            "Duplicate witness count differs",
        )
        for row in audit["duplicates"]:
            require(
                row["software_merge_match_is_scientific_chronology_validation"] is False
                and row["scientific_support_refusal"]
                == (
                    "disjoint_native_support_hull"
                    if row["open_gaps_introduced_by_hull"]
                    else ""
                ),
                "Support gaps promoted",
            )
    return {
        "source_candidate": candidate,
        "original_producer_native_exit": 0,
        "original_independent_native_exit": 0,
        "original_inner_and_outer": [0, 0],
        "publisher_ownership_changed": False,
        "scientific_chronology_admission": False,
    }


def source_join(plan: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    """Join the source ledger to its declared frozen input identities."""
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
    """Classify inputs through their recorded source-role correspondence."""
    groups = {
        "public_owned_source_resource": indexed(ledger["copied_sources"]),
        "public_source_ledger": indexed([plan["source_ledger"]]),
        "raw_or_historical_seven_identity_only": indexed(
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
        len(groups["raw_or_historical_seven_identity_only"]) == 7,
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
    """Validate the native output namespace against its declared plan."""
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
    """Select only source rows explicitly declared public by the capture."""
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
    """Validate retained packet roles and recorded native execution."""
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
        == "f843170a28d30104b7416b9a0b0b2c7c940ce87349315eb864d2320a14d1ec70",
        "Original source ledger differs",
    )
    ledger = object_at(refs["source_ledger"])
    same(packet["runtime_authority"], plan["qualified_source_runtime"])
    inner, outer, producer, review = [
        object_at(refs[key]) for key in ("inner", "outer", "producer", "review")
    ]
    same(packet["receipt_scope"], qualify_scope(plan, inner, outer, producer, review))
    source = object_at(packet["source_controller"]["manifest"])
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
    require(len(producer["countries"]) == 4, "Four native country outputs required")
    for country in producer["countries"]:
        require(
            set(country["products"]) == {"csv", "geojson", "typed"},
            "Exact three public output roles required",
        )
        for row in country["products"].values():
            same(by_path[row["path"]], normalized(row))
    return dict(packet["receipt_scope"])
