"""Closed metadata proof of the current source audit, without input-body admission."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

SCHEMA = "current-source-audit-execution-capture.v1"
PLAN_SHA = "1263d63a7e28abf920bb795f05e4fd1e2a6f53c35c7850470763447b15d576cc"
SOURCE_SHA = "12c0174869226108e30aaba1557f417be1ac90b692b292d386a74f315a88f0cf"
INNER_SHA = "343dabeebb2fe1bca86461b4207ab664b11cb5e54512e4c59852ea06344e783d"
OUTER_SHA = "700432409b3b881b42225fafb237e9d704744247ceb1c2ae155501c009b54008"
REVIEW_SHA = "639e7330af441072503920417b07c4b82ae8f6a95c73d6b7d9c882c44a3bbefc"
PRODUCER_SHA = "ec616ea82b560c0c34652e2825c481b197b1ae4e522e0962e3f750eed437bd96"
PRODUCTS = {
    "full-current-audit.json": {
        "sha256": "df746ca44d87016688d105b2448696b83d8e8267ceab4ac59b71af53fcc03d64",
        "bytes": 1770525,
    },
    "summary-current.json": {
        "sha256": "eaac246b596399e19f88a4730f84500d2aca654e5549ed7868255b8bf73bd85a",
        "bytes": 15490,
    },
}
CANDIDATE = "ad591c301bcadb6a3f963caa836a2e38a16d0de4"
SCOPE = {
    "current_mechanical_audit_only": True,
    "all599_input_bodies_identity_only": True,
    "original_live_data_bytes_required": True,
    "sealed_native_owned_data_copies_authenticated": True,
    "raw_or_private_payload_redistributed": False,
    "runtime_or_bytecode_payload_redistributed": False,
    "original26116f_recovered": False,
    "old_summary_construction_recovered": False,
    "original_owner_criterion_discharged": False,
    "live_provider_or_source_semantic_confirmation": False,
    "rights_human_ecological_or_LRA_admitted": False,
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


def data_identity_rows(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every declared repository/private input and its owned copy is identity-only."""
    require(
        set(plan["current_input_closure"]) == {"repository", "private"},
        "Exact repository/private source roles required",
    )
    require(
        len(plan["current_input_closure"]["repository"]["files"]) == 592
        and len(plan["current_input_closure"]["private"]["files"]) == 7,
        "Exact592 repository and7 private inputs required",
    )
    rows = []
    for key, projection in plan["current_input_closure"].items():
        require(key in {"repository", "private"}, "Unknown input projection")
        source = PurePosixPath(projection["root"])
        owned = PurePosixPath(
            plan["owned_repository"]
            if key == "repository"
            else plan["owned_private_root"]
        )
        for row in projection["files"]:
            original = normalized(row)
            path = PurePosixPath(original["path"])
            require(
                path.is_relative_to(source),
                "Declared source path escaped original root",
            )
            rows.extend(
                [original, {**original, "path": str(owned / path.relative_to(source))}]
            )
    result = indexed(rows)
    require(len(result) == 1198, "All599 original and599 copied input roles required")
    return result


def selected_catalogue_rows(
    plan: dict[str, Any], catalogue: dict[str, Any]
) -> list[dict[str, Any]]:
    omitted = data_identity_rows(plan)
    rows = indexed(catalogue["files"])
    omitted_copies = {
        name
        for name in omitted
        if PurePosixPath(name).is_relative_to(PurePosixPath(plan["output"]))
    }
    require(
        len(omitted_copies) == 599 and omitted_copies <= set(rows),
        "Complete599 copied-input catalogue omission required",
    )
    for name in omitted_copies:
        same(rows[name], omitted[name])
    return [normalized(row) for row in catalogue["files"] if row["path"] not in omitted]


def data_copy_correspondence(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Join historical original identities to the sealed native execution copies."""
    identities = data_identity_rows(plan)
    result = []
    for key, projection in plan["current_input_closure"].items():
        original_root = PurePosixPath(projection["root"])
        owned = PurePosixPath(
            plan["owned_repository"]
            if key == "repository"
            else plan["owned_private_root"]
        )
        for row in projection["files"]:
            original = normalized(row)
            copy = identities[
                str(owned / PurePosixPath(original["path"]).relative_to(original_root))
            ]
            require(
                original["sha256"] == copy["sha256"]
                and original["bytes"] == copy["bytes"],
                "Sealed original/copy identity differs",
            )
            result.append(
                {
                    "original": original,
                    "sealed_execution_copy": copy,
                    "original_and_sealed_copy_inputs_required": True,
                    "payload_member": None,
                }
            )
    require(len(result) == 599, "Complete historical copy correspondence required")
    return result


def retention_input_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Retain every original native physical input with no historical substitution."""
    original = indexed(plan["input_pins"])
    joins = data_copy_correspondence(plan)
    for row in joins:
        same(original[row["original"]["path"]], row["original"])
        same(
            original[row["sealed_execution_copy"]["path"]], row["sealed_execution_copy"]
        )
    require(
        len(original) == 63315,
        "Exact complete original physical input population required",
    )
    return [normalized(row) for row in plan["input_pins"]]


def source_join(plan: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    same(ledger["canonical_identity"], plan["canonical_identity_at_source_freeze"])
    require(
        ledger["bytecode_payloads_copied_or_executed"] is False
        and ledger["bytecode_source_equivalence_claimed"] is False,
        "Opaque source promotion",
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
        == (7142, 2785, 2785, 4356, 1),
        "Exact source ledger populations differ",
    )
    require(
        set(original) == set(selected) | set(caches) | set(generated)
        and len(original) == sum(map(len, (selected, caches, generated))),
        "Source partition differs",
    )
    identity_only = data_identity_rows(plan)
    private_root = PurePosixPath(plan["owned_private_root"])
    private_copies = indexed(ledger["private_copies"])
    expected_private = {
        name: row
        for name, row in identity_only.items()
        if PurePosixPath(name).is_relative_to(private_root)
    }
    require(
        len(private_copies) == 7 and private_copies == expected_private,
        "Complete seven owned private input identities differ",
    )
    root, owned = (
        PurePosixPath(plan["repository"]),
        PurePosixPath(plan["owned_repository"]),
    )
    omissions = {
        row["path"]: row
        for key in (
            "omitted_unselected_cache_bytecode",
            "omitted_configured_generated_metadata",
        )
        for row in ledger[key]
    }
    result: list[dict[str, Any]] = []
    for row in ledger["original_sources"]:
        old = normalized(row)
        name = old["path"]
        if name in selected:
            relative = PurePosixPath(name).relative_to(root)
            copy = str(owned / relative)
            require(
                copy in copied
                and all(copied[copy][k] == old[k] for k in ("sha256", "bytes")),
                "Execution source copy changed",
            )
            if name in identity_only:
                same(old, identity_only[name])
                same(copied[copy], identity_only[copy])
                role = "declared_input_body_identity_only"
            else:
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
                    "pyproject.toml",
                    "packages/bijux-pollenomics/pyproject.toml",
                    "packages/bijux-pollenomics-lra/pyproject.toml",
                    "packages/bijux-pollenomics-lra/.gitignore",
                }
                require(
                    allowed and relative.suffix not in {".pyc", ".pyo"},
                    "Public source escaped complete four-package resource scope",
                )
                role = "public_owned_source_resource"
            same(old, selected[name])
            result.append(
                {"original": old, "execution_copy": copied[copy], "role": role}
            )
        else:
            omission = omissions[name]
            require(
                omission["executed_or_copied"] is False
                and omission["source_equivalence_claimed"] is False,
                "Omitted source role promoted",
            )
            same(old, normalized(omission))
            result.append(
                {
                    "original": old,
                    "execution_copy": None,
                    "role": "bytecode_identity_only"
                    if name in caches
                    else "configured_generated_metadata_identity_only",
                }
            )
    require(
        {r["execution_copy"]["path"] for r in result if r["execution_copy"] is not None}
        == set(copied),
        "Copied source population differs",
    )
    require(
        sum(r["role"] == "public_owned_source_resource" for r in result) == 2193,
        "Exact2193 public source/resource copies required",
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
    joins = source_join(plan, ledger)
    authority = plan["qualified_source_runtime"]
    groups = {
        "declared_input_body_identity_only": data_identity_rows(plan),
        "public_owned_source_resource": indexed(
            [
                row["execution_copy"]
                for row in joins
                if row["role"] == "public_owned_source_resource"
            ]
        ),
        "public_source_ledger": indexed([plan["source_ledger"]]),
        "public_native_source_controller": indexed(
            source["files"] + [source_pin, peer_pin]
        ),
        "public_runtime_authority_metadata": indexed(
            [authority[k] for k in ("plan", "outer", "common", "independent_review")]
        ),
        "runtime_identity_only": indexed(runtime_plan["input_pins"]),
    }
    originals = indexed(plan["input_pins"])
    result = []
    require(
        len(originals) == 63315 and len(groups["runtime_identity_only"]) == 59882,
        "Exact63315 original/59882 runtime identity populations required",
    )
    for index, row in enumerate(plan["input_pins"]):
        roles = [key for key, group in groups.items() if row["path"] in group]
        require(
            len(roles) == 1,
            "Exactly one closed original input role required: " + row["path"],
        )
        same(normalized(row), groups[roles[0]][row["path"]])
        result.append(
            {
                "original_index": index,
                "identity": normalized(row),
                "roles": roles,
                "payload_member": blob(row) if roles[0].startswith("public_") else None,
            }
        )
    require(
        set().union(*(set(rows) for rows in groups.values())) == set(originals),
        "Original input role population differs",
    )
    return result


def qualify_scope(
    plan: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    producer: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    require(
        plan["schema_version"] == "current-source-audit-owned-plan.v1"
        and plan["candidate"] == CANDIDATE,
        "Exact native source epoch required",
    )
    for value in (inner, outer, producer, review):
        require(
            type(value["actual_exit"]) is int
            and value["actual_exit"] == 0
            and value["candidate"] == CANDIDATE,
            "Genuine native stage/whole0 required",
        )
    require(
        inner["schema_version"] == "current-source-audit-terminal.v1"
        and outer["schema_version"]
        == "current-source-audit-owned-child-watchdog-terminal.v1",
        "Exact original native schemas required",
    )
    for value in (inner, outer):
        require(
            value["plan_sha256"] == PLAN_SHA
            and value["memory_bound_pass"] is True
            and value["inclusive_storage_bound_pass"] is True,
            "Native custody/resource failure",
        )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["completed_whole_wall_bound_pass"] is True,
        "Native failure or wall refusal",
    )
    require(
        outer["child_native_exit"] == 0
        and type(outer["child_native_exit"]) is int
        and outer["child_timed_out"] is False
        and outer["registered_plan_unchanged"] is True
        and outer["completed_outer_wall_bound_pass"] is True,
        "Owned watchdog refusal",
    )
    require(
        inner["live_canonical_equality_claimed"] is False
        and inner["OS_quota_or_full_descendant_RSS_claimed"] is False,
        "Historical/runtime scope inflated",
    )
    expected = [
        ("maintained-current-source-audit", "producer", 360),
        ("independent-current-source-audit-observer", "observer", 240),
    ]
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2,
        "Exact two original native roles required",
    )
    python = plan["runtime_entry_lexical_paths"][0]
    native_source = str(PurePosixPath(plan["stages"][0]["argv"][3]).parent)
    for declaration, actual, (name, action, seconds) in zip(
        plan["stages"], inner["stages"], expected, strict=True
    ):
        argv = [
            python,
            "-I",
            "-B",
            native_source + "/entry.py",
            action,
            "--plan",
            plan["output"] + "/plan.json",
        ]
        same(
            declaration,
            {"id": name, "action": action, "timeout_seconds": seconds, "argv": argv},
        )
        for key in declaration:
            same(actual[key], declaration[key])
        require(
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Native stage refused",
        )
    same(producer["actual_argv"][1:], plan["stages"][0]["argv"][1:])
    require(
        producer["actual_executable"] == python,
        "Actual producer lexical interpreter differs",
    )
    same(
        producer["owned_package_search_roots"],
        [
            plan["owned_repository"] + "/packages/" + name + "/src"
            for name in (
                "bijux-pollenomics",
                "bijux-pollenomics-lra",
                "bijux-pollenomics-dev",
                "pollenomics",
            )
        ],
    )
    same(
        producer["maintained_public_calls"],
        [
            {"call": "build_source_audit", "root": plan["owned_repository"]},
            {
                "call": "build_intake_custody_report",
                "repository": plan["owned_repository"],
                "private_source_root": plan["owned_private_root"],
            },
            {
                "call": "summarize_source_audit",
                "input": "complete_current_audit_with_intake_custody",
            },
            {
                "call": "publish_json_outputs",
                "outputs": [plan["output"] + "/" + name for name in PRODUCTS],
            },
        ],
    )
    protected = indexed(plan["input_pins"])
    modules = set()
    for row in producer["first_party_origins"]:
        require(
            row["module"] not in modules
            and PurePosixPath(row["path"]).is_relative_to(
                PurePosixPath(plan["owned_repository"])
            ),
            "Actual module origin mixed or escaped",
        )
        modules.add(row["module"])
        same(normalized(row), protected[row["path"]])
    require(
        {
            "bijux_pollenomics_dev.source_completion.audit",
            "bijux_pollenomics_dev.source_completion.intake_custody",
            "bijux_pollenomics_dev.source_completion.publication.json_outputs",
        }
        <= modules,
        "Actual maintained module identities incomplete",
    )
    for key in (
        "historical_full_audit_recovered",
        "old_summary_byte_equality_claimed",
        "live_provider_completeness_or_scientific_admission",
    ):
        require(producer[key] is False, "Producer scope promotion")
    require(
        producer["native_exit_means_API_execution_not_zero_accounting_findings"] is True
        and producer["numerical_import_attempts"] == producer["network_attempts"] == [],
        "Producer scope differs",
    )
    require(
        review["complete_typed_and_byte_reconstruction"] is True
        and review["historical_full_audit_recovered"] is False
        and review["old_summary_reproduced"] is False
        and review["full_source_confirmation"] is False,
        "Independent scope promotion",
    )
    require(
        producer["schema_version"] == "current-source-audit-execution.v1"
        and review["schema_version"] == "independent-current-source-audit-review.v1",
        "Original scientific witness schemas differ",
    )
    require(
        review["source_execution_sha256"] == PRODUCER_SHA,
        "Independent original producer join differs",
    )
    same(producer["products"], review["products"])
    for row, name in zip(producer["products"], PRODUCTS, strict=True):
        same(normalized(row), {"path": plan["output"] + "/" + name, **PRODUCTS[name]})
    require(
        review["source_count"] == 11
        and type(review["source_count"]) is int
        and review["current_consumed_input_count"] == 321
        and type(review["current_consumed_input_count"]) is int,
        "Exact current source/reader denominator differs",
    )
    require(
        review["accounting_checks_pass"] is True
        and review["accounting_findings"] == []
        and producer["accounting_checks_pass"] is True
        and type(producer["accounting_finding_count"]) is int
        and producer["accounting_finding_count"] == 0,
        "Actual current mechanical finding changed",
    )
    return {
        "native_source_candidate": CANDIDATE,
        "native_stage_exits": [0, 0],
        "native_inner_and_outer_exits": [0, 0],
        "source_families": 11,
        "country_cells": 198,
        "capability_cells": 187,
        "input_records": 321,
        "present": 284,
        "native_missing": 37,
        "native_missing_absent": 35,
        "native_directory_as_file": 2,
        "mechanical_findings": 0,
        "full_source_confirmation": False,
        "original_owner_remains_unresolved": True,
    }


def validate_packet(
    packet: dict[str, Any], read: Callable[[str], bytes]
) -> dict[str, Any]:
    require(
        packet["schema_version"] == SCHEMA,
        "Exact current-audit capture schema required",
    )
    same(packet["scope"], SCOPE)
    members = packet["members"]
    used = set()
    for name, row in members.items():
        member_name(name)
        require(
            set(row) == {"sha256", "bytes"},
            "Exact public payload identity fields required",
        )
        normalized({"path": "/controlled/payload", **row})
        raw = read(name)
        require(
            hashlib.sha256(raw).hexdigest() == row["sha256"]
            and len(raw) == row["bytes"],
            "Public member content mismatch",
        )
    bindings = exact_public_rows([row["original"] for row in packet["public_bindings"]])
    for row in packet["public_bindings"]:
        name = blob(row["original"])
        require(
            row["member"] == name
            and members[name] == {k: row["original"][k] for k in ("sha256", "bytes")},
            "Public binding differs",
        )
        used.add(name)
    require(used == set(members), "Unknown/unreferenced public member")

    def document(row: dict[str, Any]) -> dict[str, Any]:
        same(bindings[row["path"]], normalized(row))
        return json_object(read(blob(row)))

    refs = packet["native_references"]
    for key, checksum in (
        ("plan", PLAN_SHA),
        ("inner", INNER_SHA),
        ("outer", OUTER_SHA),
        ("review", REVIEW_SHA),
        ("producer", PRODUCER_SHA),
    ):
        require(refs[key]["sha256"] == checksum, "Native authority differs")
    plan, ledger, inner, outer, producer, review = [
        document(refs[k])
        for k in ("plan", "source_ledger", "inner", "outer", "producer", "review")
    ]
    same(plan["source_ledger"], refs["source_ledger"])
    same(outer["inner_terminal"], refs["inner"])
    same(inner["products_manifest"], refs["catalogue"])
    result = qualify_scope(plan, inner, outer, producer, review)
    same(packet["receipt_scope"], result)
    catalogue = document(refs["catalogue"])
    require(
        len(catalogue["files"]) == inner["products_count_before_manifest"] == 2803,
        "Complete original output catalogue differs",
    )
    same(
        packet["outer_stream_catalogue_correspondence"],
        outer_stream_correspondence(catalogue, outer, refs["inner"]),
    )
    stream = (
        json.dumps({"terminal": normalized(refs["inner"]), "actual_exit": 0}) + "\n"
    ).encode()
    require(
        read(blob(outer["stdout"])) == stream,
        "Complete later outer PIPE stdout differs",
    )
    original_source = packet["source_controller"]
    require(
        original_source["manifest"]["sha256"] == SOURCE_SHA,
        "Original reviewed source manifest differs",
    )
    source = document(original_source["manifest"])
    peer = document(original_source["review"])
    require(
        peer["approved"] is True and peer["source_manifest_sha256"] == SOURCE_SHA,
        "Original source peer not bound",
    )
    same(packet["runtime_authority"], plan["qualified_source_runtime"])
    runtime_plan = document(plan["qualified_source_runtime"]["plan"])
    roles = input_roles(
        plan,
        ledger,
        source,
        original_source["manifest"],
        original_source["review"],
        runtime_plan,
    )
    same(packet["original_input_roles"], roles)
    same(packet["original_data_copy_correspondence"], data_copy_correspondence(plan))
    same(packet["original_source_join"], source_join(plan, ledger))
    same(
        packet["original_output_namespace"],
        output_namespace(plan, catalogue, refs, outer),
    )
    metadata_source = packet["metadata_source_controller"]
    manifest = document(metadata_source["manifest"])
    admission = document(metadata_source["review"])
    require(
        manifest["source_only"] is True
        and admission["approved"] is True
        and admission["source_manifest_sha256"]
        == metadata_source["manifest"]["sha256"],
        "Metadata source approval differs",
    )
    expected = exact_public_rows(
        selected_catalogue_rows(plan, catalogue)
        + [row["identity"] for row in roles if row["payload_member"] is not None]
        + list(refs.values())
        + [outer["stdout"], outer["stderr"]]
        + source["files"]
        + list(original_source.values())
        + [
            plan["qualified_source_runtime"][k]
            for k in ("plan", "outer", "common", "independent_review")
        ]
        + manifest["files"]
        + list(metadata_source.values())
    )
    require(bindings == expected, "Exact finite portable public role partition differs")
    require(
        not set(data_identity_rows(plan)).intersection(bindings),
        "A declared input body entered public payloads",
    )
    full, summary = [document(row) for row in producer["products"]]
    require(
        full["full_source_confirmation"] is False
        and summary["full_source_confirmation"] is False
        and full["external_intake_custody"]["scientific_admission"]
        == "not_established_by_custody",
        "Audit science/rights scope promoted",
    )

    def digest(value: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    require(
        full["audit_sha256"]
        == digest({k: v for k, v in full.items() if k != "audit_sha256"})
        and summary["summary_sha256"]
        == digest({k: v for k, v in summary.items() if k != "summary_sha256"})
        and summary["full_audit_sha256"] == full["audit_sha256"],
        "Derived metadata digest joins differ",
    )
    require(
        len(full["input_files"]) == 321
        and sum(row["presence"] == "present" for row in full["input_files"]) == 284
        and full["accounting_checks_pass"] is True
        and full["accounting_findings"] == [],
        "Literal current input/finding result differs",
    )
    return result
