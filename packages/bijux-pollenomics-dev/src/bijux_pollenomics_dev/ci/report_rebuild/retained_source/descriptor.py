"""Decode compact pinned source transport metadata and exact grouped Git blob maps."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from ..contracts import require_relative_path
from . import objects
from .objects import MAX_MEMBERS, GitSourceMember, hexadecimal, physical, require

MAX_DESCRIPTOR_BYTES = 8 * 1024**2


def object_fields(value: object, keys: set[str]) -> dict[str, Any]:
    """Refuse ambiguous or extended authority schemas."""
    require(
        type(value) is dict and set(value) == keys, "source transport fields differ"
    )
    assert isinstance(value, dict)
    return value


def identity(value: object, name: str | None = None) -> dict[str, Any]:
    """Normalize the two existing identity shapes without dropping inconsistent paths."""
    require(type(value) is dict, "original member identity must be an object")
    assert isinstance(value, dict)
    require(
        set(value)
        in (
            {"sha256", "bytes"},
            {"path", "sha256", "bytes"},
            {"path", "sha256", "bytes", "kind"},
            {"path", "sha256", "bytes", "original", "role"},
        ),
        "original identity fields differ",
    )
    require(
        "path" not in value or value["path"] == name, "original identity path differs"
    )
    for field in ("kind", "role"):
        if field in value:
            require(
                type(value[field]) is str and bool(value[field]),
                "original member role metadata must be a nonempty string",
            )
    if "original" in value:
        original = object_fields(value["original"], {"path", "sha256", "bytes"})
        require(
            type(original["path"]) is str
            and bool(original["path"])
            and hexadecimal(original["sha256"], 64)
            and type(original["bytes"]) is int
            and original["bytes"] >= 0,
            "original input identity fields differ",
        )
    require(
        hexadecimal(value["sha256"], 64)
        and type(value["bytes"]) is int
        and value["bytes"] >= 0,
        "typed source identity required",
    )
    return {"sha256": value["sha256"], "bytes": value["bytes"]}


def normalize_members(value: Any) -> dict[str, dict[str, Any]]:
    """Accept existing dictionary or ordered path-row catalogues, preserving unique identities."""
    if type(value) is list:
        require(
            all(type(row) is dict and type(row.get("path")) is str for row in value),
            "member path rows required",
        )
        require(
            len({row["path"] for row in value}) == len(value),
            "duplicate original member path",
        )
        value = {row["path"]: row for row in value}
    require(type(value) is dict, "original member catalogue required")
    result = {}
    for name, row in value.items():
        require_relative_path(name, "original source member")
        result[name] = identity(row, name)
    return result


def json_object(raw: bytes) -> dict[str, Any]:
    """Decode one already-authenticated buffer with strict duplicate/nonfinite refusal."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            require(key not in result, "duplicate source JSON member")
            result[key] = value
        return result

    result = json.loads(raw, object_pairs_hook=pairs)
    json.dumps(result, allow_nan=False)
    require(type(result) is dict, "source metadata object required")
    assert isinstance(result, dict)
    return result


def pinned_bytes(path: Path, sha256: str, size: int, cap: int) -> bytes:
    """Read and authenticate the same bounded physical buffer before parsing."""
    physical(path)
    require(
        hexadecimal(sha256, 64) and type(size) is int and 0 < size <= cap,
        "pinned bounded metadata required",
    )
    require(
        path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size == size,
        "metadata absent, aliased or changed size",
    )
    raw = path.read_bytes()
    require(
        len(raw) == size and hashlib.sha256(raw).hexdigest() == sha256,
        "source metadata bytes changed",
    )
    return raw


@dataclass(frozen=True)
class Descriptor:
    """Immutable source transport metadata; original native predicates remain caller-owned."""

    capture_name: str
    capture: dict[str, Any]
    groups: tuple[dict[str, Any], ...]
    generated: tuple[dict[str, Any], ...]
    detached: frozenset[str]
    members: dict[str, dict[str, Any]]
    capsule_prefix: str | None = None

    def resolve(
        self, repository: Path, selected: frozenset[str] | None = None
    ) -> list[GitSourceMember]:
        """Verify every aggregate blob map; select body reads separately without broad fallback."""
        executable = objects.git_executable()
        deadline = time.monotonic() + objects.WHOLE_SECONDS
        result = []
        for group in self.groups:
            pairs = group["resolved_paths"]
            if selected is not None and not selected.intersection(
                name for name, _ in pairs
            ):
                continue
            entries: dict[str, str] = {}
            for start in range(0, len(pairs), 64):
                paths = sorted({path for _, path in pairs[start : start + 64]})
                raw = objects.query(
                    repository,
                    ["ls-tree", "-r", "-z", group["source_revision"], "--", *paths],
                    128 * 1024,
                    deadline,
                    executable,
                )
                chunk = {}
                for record in raw.split(b"\0"):
                    if record:
                        meta, raw_name = record.split(b"\t", 1)
                        mode, kind, blob = meta.decode("ascii").split()
                        name = raw_name.decode("utf-8")
                        require(
                            name not in chunk
                            and mode in {"100644", "100755"}
                            and kind == "blob"
                            and hexadecimal(blob, 40),
                            "linked, duplicate or non-blob Git source",
                        )
                        chunk[name] = blob
                require(set(chunk) == set(paths), "missing or extra Git source member")
                require(
                    all(
                        name not in entries or entries[name] == blob
                        for name, blob in chunk.items()
                    ),
                    "conflicting repeated Git source path",
                )
                entries.update(chunk)
            map_rows = sorted([[path, entries[path]] for _, path in pairs])
            raw_map = json.dumps(
                map_rows, separators=(",", ":"), ensure_ascii=True
            ).encode()
            require(
                hashlib.sha256(raw_map).hexdigest() == group["git_entries_sha256"],
                "grouped exact Git blob map differs",
            )
            for name, path in pairs:
                if selected is None or name in selected:
                    row = self.members[name]
                    result.append(
                        GitSourceMember(
                            name,
                            path,
                            group["source_revision"],
                            entries[path],
                            row["sha256"],
                            row["bytes"],
                            group.get("storage_role", "canonical_source"),
                            self.capsule_prefix
                            if group.get("storage_role") == "historical_code_witness"
                            else None,
                        )
                    )
        return result


def decode(
    raw: bytes, original_members: Any, *, capsule_prefix: str | None = None
) -> Descriptor:
    """Derive compact source groups from unchanged original logical identities."""
    members = normalize_members(original_members)
    row = object_fields(
        json_object(raw),
        {
            "schema_version",
            "capture",
            "historical_native_epochs",
            "source_revision_correspondence",
            "git_groups",
            "generated_members",
            "rewritten_source_epoch_executed",
        },
    )
    require(
        row["schema_version"] == "git-retained-source.v1"
        and row["rewritten_source_epoch_executed"] is False,
        "source transport cannot relabel native execution",
    )
    native = row["historical_native_epochs"]
    require(
        type(native) is list
        and native == sorted(set(native))
        and all(hexadecimal(value, 40) for value in native),
        "literal original native epochs required",
    )
    capture = object_fields(row["capture"], {"name", "sha256", "bytes"})
    capture_name = require_relative_path(capture["name"], "original capture name")
    capture_pin = identity({key: capture[key] for key in ("sha256", "bytes")})
    epochs = {}
    require(
        type(row["source_revision_correspondence"]) is list
        and len(row["source_revision_correspondence"]) <= 256,
        "bounded source correspondence required",
    )
    for item in row["source_revision_correspondence"]:
        item = object_fields(item, {"historical_source_commit", "source_revision"})
        old, new = item["historical_source_commit"], item["source_revision"]
        require(
            hexadecimal(old, 40) and hexadecimal(new, 40) and old not in epochs,
            "duplicate or invalid source correspondence",
        )
        epochs[old] = new
    require(type(row["generated_members"]) is list, "generated metadata rows required")
    generated = []
    names = []
    for item in row["generated_members"]:
        item = object_fields(
            item,
            {
                "member",
                "generator",
                "scalars",
                "original_generator_execution_claimed",
                "original_version_derivation_claimed",
            },
        )
        name = require_relative_path(item["member"], "generated source member")
        require(
            name in members
            and item["original_generator_execution_claimed"] is False
            and item["original_version_derivation_claimed"] is False,
            "generated metadata is not original genesis",
        )
        generated.append(item)
        names.append(name)
    groups = []
    used = set()
    require(
        type(row["git_groups"]) is list and len(row["git_groups"]) <= 256,
        "bounded source groups required",
    )
    for item in row["git_groups"]:
        require(type(item) is dict, "source group object required")
        selector = "prefixes" if "prefixes" in item else "paths"
        storage_role = item.get("storage_role", "canonical_source")
        if "storage_role" in item:
            require(
                storage_role == "historical_code_witness"
                and selector == "paths"
                and capsule_prefix is not None,
                "historical witnesses require explicit paths and capsule authority",
            )
        object_fields(
            item,
            {
                "historical_source_commit",
                "source_revision",
                "member_count",
                "git_entries_sha256",
                selector,
            }
            | ({"storage_role"} if "storage_role" in item else set()),
        )
        old = item["historical_source_commit"]
        require(
            old in epochs and item["source_revision"] == epochs[old],
            "source group has no exact epoch correspondence",
        )
        require(
            hexadecimal(item["git_entries_sha256"], 64),
            "group Git map fingerprint required",
        )
        if selector == "prefixes":
            prefixes = object_fields(
                item["prefixes"], {"member_prefix", "repository_prefix"}
            )
            for prefix in prefixes.values():
                require(
                    type(prefix) is str and prefix.endswith("/"),
                    "literal source prefix required",
                )
                require_relative_path(prefix[:-1], "source prefix")
            prefix = prefixes["member_prefix"]
            pairs = [
                [name, prefixes["repository_prefix"] + name[len(prefix) :]]
                for name in sorted(members)
                if name.startswith(prefix) and name not in names
            ]
        else:
            pairs = item["paths"]
            require(
                type(pairs) is list
                and all(type(pair) is list and len(pair) == 2 for pair in pairs),
                "explicit source path pairs required",
            )
        require(
            type(item["member_count"]) is int
            and 0 < item["member_count"] == len(pairs),
            "source group count differs",
        )
        require(
            pairs == sorted(pairs),
            "source path pairs must preserve canonical string order",
        )
        for name, path in pairs:
            require(
                name in members, "source group refers to an unlisted original member"
            )
            GitSourceMember(
                name,
                path,
                item["source_revision"],
                "0" * 40,
                members[name]["sha256"],
                members[name]["bytes"],
                storage_role,
                capsule_prefix if storage_role == "historical_code_witness" else None,
            ).validate()
            names.append(name)
        used.add(old)
        groups.append({**item, "resolved_paths": pairs})
    require(
        len(names) <= MAX_MEMBERS
        and len(names) == len(set(names))
        and used == set(epochs),
        "duplicate source member or unused epoch correspondence",
    )
    return Descriptor(
        capture_name,
        capture_pin,
        tuple(groups),
        tuple(generated),
        frozenset(names),
        members,
        capsule_prefix,
    )
