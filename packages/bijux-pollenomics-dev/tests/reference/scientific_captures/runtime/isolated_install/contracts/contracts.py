"""Authenticate offline cached wheel payloads and confined runtime products."""

from __future__ import annotations

import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

BASE = Path(
    "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
BASE_SHA = "92019a8331209d7247702193bbdfbe359807d7ee1df92566fcf31935f6b273d4"
SELECTION_SHA = "54582ea7ac6ea354e5076ea4f07b57cdd40825748dd6cbbf65f006de678c5305"
CACHE = Path("/Users/bijan/.cache/uv/archive-v0")
ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
CORE = {
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "pyproj": "3.7.2",
    "pytest": "9.0.3",
    "mypy": "1.20.0",
    "ruff": "0.15.8",
}
OBSERVER_PROBES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "pyproj": "pyproj",
    "pytest": "pytest",
    "mypy.version": "mypy",
    "pydantic": "pydantic",
    "pandas": "pandas",
    "yaml": "pyyaml",
}
NATIVE_PROBES = {
    "numpy._core._multiarray_umath": "numpy",
    "scipy.linalg._fblas": "scipy",
    "pyproj._crs": "pyproj",
    "mypy.version": "mypy",
}
FIRST_PARTY = {
    "bijux-pollenomics",
    "bijux-pollenomics-dev",
    "bijux-pollenomics-lra",
    "pollenomics",
}
OPTIONAL_MISSING = {"python-discovery", "twine", "virtualenv"}


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, object]:
    require(path.is_file(), f"Missing regular input: {path}")
    return {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}


def verify_pin(row: dict[str, object]) -> None:
    path = Path(str(row["path"]))
    require(
        type(row["bytes"]) is int and row["bytes"] >= 0, "Input size is not an integer"
    )
    require(
        path.is_file()
        and path.stat().st_size == row["bytes"]
        and digest(path) == row["sha256"],
        f"Protected input changed: {path}",
    )


def json_value(path: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, object]]) -> dict[str, Any]:
        value = {}
        for key, item in rows:
            require(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    require(isinstance(value, dict), "Expected JSON object")
    assert isinstance(value, dict)
    json.dumps(value, allow_nan=False)
    return value


def member(value: object) -> str:
    require(
        isinstance(value, str) and bool(value) and value != ".",
        "Expected nonempty file member name",
    )
    assert isinstance(value, str)
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and path.as_posix() == value
        and ".." not in path.parts
        and "\\" not in value
        and not any(ord(c) < 32 for c in value),
        "Unconfined member",
    )
    return value


def no_aliases(path: Path) -> None:
    for node in (path, *path.parents):
        require(not node.is_symlink(), f"Input/output alias: {node}")


def confined_output(path: Path, *, absent: bool = False) -> Path:
    require(
        path.is_absolute()
        and ".." not in path.parts
        and path == Path(os.path.abspath(path)),
        "Output spelling is not canonical",
    )
    require(
        path.is_relative_to(ROOT / "artifacts") and path != ROOT / "artifacts",
        "Output must be below owned artifacts",
    )
    no_aliases(path)
    if absent:
        require(not path.exists(), "Output already exists")
    return path


def create_root(path: Path) -> None:
    confined_output(path, absent=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    no_aliases(path.parent)
    path.mkdir()


def write_json(path: Path, value: object) -> None:
    confined_output(path)
    require(path.parent.is_dir(), "Output parent must already exist")
    with path.open("xb") as stream:
        stream.write((json.dumps(value, indent=2) + "\n").encode())


def normalize(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def wheel_name(distribution: str, tags: list[str]) -> str:
    require(
        distribution.endswith(".dist-info") and "/" not in distribution,
        "Wheel metadata directory differs",
    )
    stem = distribution.removesuffix(".dist-info")
    require(
        "-" in stem and re.fullmatch(r"[A-Za-z0-9_.+!-]+", stem),
        "Wheel name/version is invalid",
    )
    require(
        tags and len(tags) == len(set(tags)), "Wheel tags must be complete and unique"
    )
    split = [tag.split("-") for tag in tags]
    require(
        all(
            len(x) == 3 and all(re.fullmatch(r"[A-Za-z0-9_]+", p) for p in x)
            for x in split
        ),
        "Malformed wheel tag",
    )
    axes = [sorted({row[i] for row in split}) for i in range(3)]
    expected = {f"{p}-{a}-{t}" for p in axes[0] for a in axes[1] for t in axes[2]}
    require(
        expected == set(tags),
        "Compressed filename would advertise undeclared wheel tags",
    )
    return stem + "-" + "-".join(".".join(axis) for axis in axes) + ".whl"


def record_rows(raw: bytes, record_name: str) -> list[dict[str, str]]:
    rows = []
    seen = set()
    for values in csv.reader(io.StringIO(raw.decode(), newline="")):
        require(len(values) == 3, "RECORD row shape differs")
        name, hash_value, size = values
        member(name)
        require(name not in seen, "Duplicate RECORD member")
        seen.add(name)
        if name == record_name:
            require(hash_value == size == "", "Original RECORD self-entry differs")
        else:
            require(
                hash_value.startswith("sha256=")
                and bool(size)
                and size.isascii()
                and size.isdecimal(),
                "Original RECORD must have SHA256 and integer size",
            )
            encoded = hash_value.removeprefix("sha256=")
            require(
                re.fullmatch(r"[A-Za-z0-9_-]{43}", encoded) is not None,
                "Malformed RECORD digest",
            )
            require(
                len(base64.urlsafe_b64decode(encoded + "=")) == 32,
                "Invalid RECORD SHA256",
            )
        rows.append({"name": name, "record_hash": hash_value, "record_size": size})
    require(record_name in seen and bool(rows), "Original RECORD is absent")
    return rows


def validate_payload(row: dict[str, Any]) -> dict[str, Any]:
    archive = Path(row["archive"])
    require(
        archive.is_absolute() and archive.parent == CACHE and archive.is_dir(),
        "Cached archive is not the selected physical cache",
    )
    no_aliases(archive)
    distribution = member(row["distribution"])
    require(distribution.endswith(".dist-info"), "Cached distribution metadata differs")
    root = archive / distribution
    no_aliases(root)
    require(root.is_dir(), "Cached distribution directory is absent")
    metadata, wheel, record = (root / name for name in ("METADATA", "WHEEL", "RECORD"))
    for path in (metadata, wheel, record):
        no_aliases(path)
    require(
        digest(metadata) == row["metadata_sha256"]
        and digest(wheel) == row["wheel_sha256"],
        "Original metadata/WHEEL identity differs",
    )
    message = BytesParser().parsebytes(metadata.read_bytes())
    name, version = message["Name"], message["Version"]
    require(
        isinstance(name, str)
        and isinstance(version, str)
        and normalize(name) not in FIRST_PARTY | OPTIONAL_MISSING,
        "Unselected or first-party installed metadata",
    )
    selected_name, selected_version = distribution.removesuffix(".dist-info").rsplit(
        "-", 1
    )
    require(
        normalize(selected_name) == normalize(name) and selected_version == version,
        "Selected distribution Name/Version differs",
    )
    wheel_metadata = BytesParser().parsebytes(wheel.read_bytes())
    tags = wheel_metadata.get_all("Tag", [])
    require(tags == row["complete_wheel_tags"], "Complete original WHEEL tags differ")
    filename = wheel_name(distribution, tags)
    records = record_rows(record.read_bytes(), distribution + "/RECORD")
    by_name = {item["name"]: item for item in records}
    physical = {}
    entries: dict[str, str] = {}
    for path in archive.rglob("*"):
        mode = path.lstat().st_mode
        require(
            not stat.S_ISLNK(mode) and (stat.S_ISREG(mode) or stat.S_ISDIR(mode)),
            "Cache alias or special file",
        )
        entries[path.relative_to(archive).as_posix()] = (
            "file" if stat.S_ISREG(mode) else "directory"
        )
        if stat.S_ISREG(mode):
            relative = path.relative_to(archive).as_posix()
            require(relative in by_name, "Unlisted original cache file")
            record_row = by_name[relative]
            data = path.read_bytes()
            if record_row["record_hash"]:
                encoded = (
                    base64.urlsafe_b64encode(hashlib.sha256(data).digest())
                    .decode()
                    .rstrip("=")
                )
                require(
                    "sha256=" + encoded == record_row["record_hash"]
                    and len(data) == int(record_row["record_size"]),
                    "Original cached RECORD hash/size differs",
                )
            physical[relative] = {
                **pin(path),
                "name": relative,
                "mode": stat.S_IMODE(mode),
            }
    require(
        set(physical) == set(by_name), "Original cache RECORD/member closure differs"
    )
    return {
        **row,
        "name": name,
        "version": version,
        "wheel_filename": filename,
        "record_sha256": digest(record),
        "members": [physical[k] for k in sorted(physical)],
        "archive_entries": {key: entries[key] for key in sorted(entries)},
    }


def validate_selection(value: dict[str, Any]) -> None:
    selected = value.get("selected")
    require(
        isinstance(selected, list) and len(selected) == 147,
        "Expected exact 147 selected distributions",
    )
    assert isinstance(selected, list)
    require(
        len({r["distribution"] for r in selected})
        == len({r["archive"] for r in selected})
        == 147,
        "Duplicate selected distribution/archive",
    )
    require(
        {
            r["distribution"].split("-", 1)[0].replace("_", "-")
            for r in value["missing_optional_release_distributions"]
        }
        == OPTIONAL_MISSING,
        "Optional missing release scope differs",
    )
    require(
        len(value["excluded_current_first_party_installations"]) == 5,
        "Original first-party exclusions differ",
    )


def aliases(paths: list[Path]) -> list[dict[str, str]]:
    result = {}
    for path in paths:
        for node in (path, *path.parents):
            if node.is_symlink():
                result[str(node)] = {
                    "path": str(node),
                    "raw_link": os.readlink(node),
                    "resolved_target": str(node.resolve(strict=True)),
                }
    return [result[key] for key in sorted(result)]


def verify_aliases(rows: list[dict[str, Any]]) -> None:
    require(len(rows) == len({r["path"] for r in rows}), "Duplicate runtime alias")
    for row in rows:
        path = Path(row["path"])
        require(
            path.is_symlink()
            and os.readlink(path) == row["raw_link"]
            and str(path.resolve(strict=True)) == row["resolved_target"],
            "Original runtime lexical alias changed",
        )


def validate_probe_dependencies(
    payloads: list[dict[str, Any]], probes: dict[str, str] | None = None
) -> None:
    selected = {normalize(row["name"]): row["version"] for row in payloads}
    require(len(selected) == len(payloads), "Duplicate probe-distribution namespace")
    declared = {**OBSERVER_PROBES, **NATIVE_PROBES} if probes is None else probes
    require(
        all(normalize(distribution) in selected for distribution in declared.values()),
        "Observer probe requires an unselected distribution",
    )
    require(
        all(selected.get(name) == version for name, version in CORE.items()),
        "Observer core version is not selected",
    )


def verify_cache_membership(payloads: list[dict[str, Any]]) -> None:
    for row in payloads:
        root = Path(row["archive"])
        no_aliases(root)
        require(root.is_dir(), "Selected cache archive disappeared")
        actual = {}
        for child in root.rglob("*"):
            require(
                not child.is_symlink() and (child.is_file() or child.is_dir()),
                "Cache namespace alias/special entry",
            )
            actual[child.relative_to(root).as_posix()] = (
                "file" if child.is_file() else "directory"
            )
        require(
            actual == row["archive_entries"],
            "Complete cached namespace membership changed",
        )


def verify_unused_namespaces(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        path = Path(row["path"])
        require(
            path.is_symlink() == row["is_symlink"]
            and (str(path.resolve(strict=False)) == row["resolved_target"]),
            "Unused no-site namespace spelling changed",
        )
        if path.is_symlink():
            require(os.readlink(path) == row["raw_link"], "Unused no-site link changed")


def namespace_snapshot(root: Path, excluded: list[str]) -> dict[str, Any]:
    """Bind every lexical entry while omitting only explicitly unused subtrees."""
    require(root.is_dir() and not root.is_symlink(), "Namespace root is not physical")
    entries: dict[str, Any] = {}
    pending = [root]
    while pending:
        parent = pending.pop()
        for path in parent.iterdir():
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[relative] = {
                    "kind": "symlink",
                    "raw_link": os.readlink(path),
                    "resolved_target": str(path.resolve(strict=False)),
                }
            elif path.is_dir():
                entries[relative] = {"kind": "directory"}
                if str(path) not in excluded:
                    pending.append(path)
            elif path.is_file():
                entries[relative] = {"kind": "file"}
            else:
                raise ValueError("Special runtime namespace entry")
    return {"root": str(root), "excluded": excluded, "entries": entries}


def verify_base_namespaces(rows: list[dict[str, Any]]) -> None:
    require(len(rows) == len({row["root"] for row in rows}), "Duplicate base namespace")
    for row in rows:
        require(
            namespace_snapshot(Path(row["root"]), row["excluded"]) == row,
            "Complete base runtime namespace changed",
        )


def verify_absences(paths: list[str]) -> None:
    require(len(paths) == len(set(paths)), "Duplicate absent input")
    for name in paths:
        path = Path(name)
        require(not path.exists() and not path.is_symlink(), "Absent input appeared")


FORBIDDEN_RUNTIME_KEYS = {
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "_PYTHON_HOST_PLATFORM",
    "__PYVENV_LAUNCHER__",
}


def runtime_override_key(key: str) -> bool:
    return key.startswith("DYLD_") or key in FORBIDDEN_RUNTIME_KEYS


def require_runtime_environment(environment: dict[str, str]) -> dict[str, Any]:
    present = sorted(key for key in environment if runtime_override_key(key))
    require(
        not present, "Loader/build environment override present: " + ", ".join(present)
    )
    return {
        "forbidden_key_prefixes": ["DYLD_"],
        "forbidden_exact_keys": sorted(FORBIDDEN_RUNTIME_KEYS),
        "present_forbidden_key_names": present,
        "environment_values_disclosed": False,
    }
