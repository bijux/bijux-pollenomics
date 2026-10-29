"""Closed portable current-animal native and metadata execution evidence."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
from pathlib import Path
from typing import Any

from ...contracts import ReportRebuildError
from .animal_packet import json_object, member_name, validate_packet

CAPTURE = "data/source-custody/adna/animal-current-exports/capture.json"
CAPTURE_SHA = "1d03f47b264366da0acdc544e991bac38fdd7d1d403d3fd522f2c4e4ea37fd64"
PROOF_ROOT = "data/adna/current-animal-retention"
PROOF_IDENTITIES = {
    "plan.json": {
        "sha256": "02208621bd6c8f71f04adeeb55a04bca96887b81eeb2ffd1acf32eec63ba84bf",
        "bytes": 55828880,
    },
    "capture-terminal.json": {
        "sha256": "e8e3ed117da21f07c75a518be1f6a91cd2efc54508291487dd899fa5de9880f4",
        "bytes": 4846,
    },
    "capture-launch-terminal.json": {
        "sha256": "2010dc5a4981c858ad8e92ee648e87c28c2453474b81467f4b7ca9d3ecd06a8f",
        "bytes": 2470,
    },
    "assembly-result.json": {
        "sha256": "fb01c0e498f66007a35ea8d6f91763757d30b444eb307e27bc5859d38c41910d",
        "bytes": 555,
    },
    "independent-capture-review.json": {
        "sha256": "2fa8329a8645c010e41368a3d8401d9bc299d85f7146f3e1a22a612708ee31a6",
        "bytes": 1228,
    },
}


def same_metadata(left: object, right: object) -> None:
    require(type(left) is type(right), "Summary metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        require(set(left) == set(right), "Summary metadata fields differ")
        for key in left:
            same_metadata(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Summary ordered population differs")
        for a, b in zip(left, right, strict=True):
            same_metadata(a, b)
    elif isinstance(left, float) and isinstance(right, float):
        require(
            __import__("math").isfinite(left) and left.hex() == right.hex(),
            "Summary finite binary64 value differs",
        )
    else:
        require(left == right, "Summary metadata values differ")


def qualify_metadata(
    records: dict[str, Any], capture_sha: str, packet: dict[str, Any]
) -> None:
    plan, inner, outer, assembled, observed = [
        records[k] for k in ("plan", "inner", "outer", "assembly", "observer")
    ]
    require(
        inner["schema_version"] == "animal-current-export-metadata-capture-terminal.v1"
        and outer["schema_version"]
        == "animal-current-export-metadata-capture-watchdog.v1",
        "Correct current animal metadata receipt namespace required",
    )
    for value in (inner, outer):
        require(
            type(value["actual_exit"]) is int
            and value["actual_exit"] == 0
            and value["candidate"] == plan["candidate"]
            and value["plan_sha256"] == records["plan_identity"]["sha256"],
            "Actual successful metadata epoch required",
        )
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2, "Exact two metadata stages"
    )
    for expected, actual, name, action in zip(
        plan["stages"],
        inner["stages"],
        (
            "retained-animal-current-export-assembly",
            "independent-animal-current-export-capture-observer",
        ),
        ("assemble", "observer"),
        strict=True,
    ):
        require(
            expected["id"] == actual["id"] == name
            and expected["action"] == actual["action"] == action
            and expected["argv"] == actual["argv"]
            and type(expected["timeout_seconds"]) is int
            and expected["timeout_seconds"] == 180
            and type(actual["timeout_seconds"]) is int
            and actual["timeout_seconds"] == expected["timeout_seconds"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Metadata stage contract differs",
        )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and all(
            inner[k] is True
            for k in (
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_whole_wall_bound_pass",
            )
        ),
        "Metadata custody/resource failure",
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
        "Metadata outer failure",
    )
    for value in (assembled, observed):
        require(
            type(value["actual_exit"]) is int and value["actual_exit"] == 0,
            "Actual retained packet proof absent",
        )
    require(
        assembled["metadata_retention_only"] is True
        and assembled["raw_decode_or_source_consumer_repeated"] is False
        and assembled["original_owner_acceptance_changed"] is False
        and assembled["capture"] == observed["capture"]
        and assembled["capture"]["sha256"] == capture_sha,
        "Metadata capture/scope differs",
    )
    require(
        observed["metadata_only"] is True
        and observed["raw_or_selected_rows_decoded_or_consumer_repeated"] is False
        and observed["original_owner_acceptance_changed"] is False
        and type(observed["original_ordered_inputs"]) is int
        and observed["original_ordered_inputs"] == 62435
        and type(observed["original_source_join_count"]) is int
        and observed["original_source_join_count"] == 6710,
        "Ordered input/source proof differs",
    )

    require(
        plan["schema_version"] == "animal-current-export-metadata-capture-plan.v1",
        "Exact metadata plan schema required",
    )
    require(
        type(plan["input_pins"]) is list and len(plan["input_pins"]) == 62633,
        "Complete registered metadata input union required",
    )
    names = [row["path"] for row in plan["input_pins"]]
    require(len(names) == len(set(names)), "Unique registered metadata inputs required")
    same_metadata(plan["transport"]["packet"], packet)
    same_metadata(observed["receipt_scope"], packet["receipt_scope"])
    require(
        type(assembled["public_payload_count"]) is int
        and assembled["public_payload_count"]
        == observed["retained_payloads"]
        == len(packet["members"])
        == 2351
        and type(observed["retained_payloads"]) is int,
        "Exact public payload population required",
    )
    require(
        type(assembled["exact_packet_bytes"]) is int
        and type(observed["actual_packet_bytes"]) is int
        and assembled["exact_packet_bytes"]
        == observed["actual_packet_bytes"]
        == 126159750,
        "Exact public packet storage required",
    )
    require(
        type(assembled["capture"]["bytes"]) is int
        and assembled["capture"]["bytes"] == 32660595
        and assembled["public_capture_path"] == CAPTURE,
        "Exact retained capture identity required",
    )
    require(
        outer["inner_terminal"]["sha256"]
        == PROOF_IDENTITIES["capture-terminal.json"]["sha256"]
        and type(outer["inner_terminal"]["bytes"]) is int
        and outer["inner_terminal"]["bytes"] == 4846,
        "Exact inner terminal join required",
    )
    resources = {
        "overall_timeout_seconds": 420,
        "outer_timeout_seconds": 480,
        "declared_memory_bytes": 2147483648,
        "declared_storage_bytes": 536870912,
    }
    for document in (plan, inner, outer):
        same_metadata(document["resources"], resources)


def require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Current animal export evidence: " + reason)


def physical(repository: Path, name: str) -> Path:
    path = repository / name
    require(
        path.is_file()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular portable DNA member required",
    )
    return path


def checked(repository: Path, name: str, identity: dict[str, Any]) -> bytes:
    raw = physical(repository, name).read_bytes()
    require(
        type(identity["bytes"]) is int
        and len(raw) == identity["bytes"]
        and hashlib.sha256(raw).hexdigest() == identity["sha256"],
        "Portable DNA payload changed",
    )
    return raw


def exact_tree(root: Path, names: set[str], directories: set[str]) -> None:
    require(
        root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical DNA namespace required",
    )
    files: set[str] = set()
    dirs: set[str] = set()
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "DNA namespace alias/special member",
        )
        (files if path.is_file() else dirs).add(path.relative_to(root).as_posix())
    require(
        files == names and dirs == directories, "DNA namespace omitted/extra member"
    )


def animal_context(
    repository: Path,
) -> tuple[dict[str, Any], Callable[[str], bytes], dict[str, Any]]:
    raw = physical(repository, CAPTURE).read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == CAPTURE_SHA,
        "Exact genuine current animal capture required",
    )
    packet = json_object(raw)
    root = (repository / CAPTURE).parent
    exact_tree(root, set(packet["members"]) | {"capture.json"}, {"payloads"})

    def read(name: str) -> bytes:
        member_name(name)
        return checked(
            repository,
            (root / name).relative_to(repository).as_posix(),
            packet["members"][name],
        )

    native = validate_packet(packet, read)
    proof = repository / PROOF_ROOT
    exact_tree(proof, set(PROOF_IDENTITIES), set())
    roles = {
        "plan.json": "plan",
        "capture-terminal.json": "inner",
        "capture-launch-terminal.json": "outer",
        "assembly-result.json": "assembly",
        "independent-capture-review.json": "observer",
    }
    records: dict[str, Any] = {
        roles[name]: json_object(checked(repository, PROOF_ROOT + "/" + name, pin))
        for name, pin in PROOF_IDENTITIES.items()
    }
    records["plan_identity"] = PROOF_IDENTITIES["plan.json"]
    qualify_metadata(records, CAPTURE_SHA, packet)
    bindings = {row["original"]["path"]: row for row in packet["public_bindings"]}
    plan_ref = packet["native_references"]["plan"]
    original = json_object(read(bindings[plan_ref["path"]]["member"]))
    pins = {row["path"]: row for row in records["plan"]["input_pins"]}
    require(
        len(original["input_pins"]) == 62435,
        "Complete original animal input ledger required",
    )
    for pin in original["input_pins"]:
        require(pin["path"] in pins, "Original animal input missing from metadata plan")
        same_metadata(pin, pins[pin["path"]])
    exact_tree(root, set(packet["members"]) | {"capture.json"}, {"payloads"})
    exact_tree(proof, set(PROOF_IDENTITIES), set())
    return (
        packet,
        read,
        {
            "native": native,
            "metadata_stages_and_wholes_zero": True,
            "capture": {"path": CAPTURE, "sha256": CAPTURE_SHA},
            "metadata_proof": {"path": PROOF_ROOT, "files": PROOF_IDENTITIES},
            "all_original_ordered_inputs": 62435,
            "private_or_original_data_payloads_included": False,
        },
    )
