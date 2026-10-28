"""Validate the exact physical projection around Git-detached package members."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..contracts import require_relative_path
from .objects import hexadecimal, physical, require

MAX_PHYSICAL_MEMBERS = 8192
MAX_PHYSICAL_MEMBER_BYTES = 128 * 1024**2
MAX_PHYSICAL_BYTES = 512 * 1024**2


def validate_physical_capsule(
    repository: Path,
    prefix: str,
    members: dict[str, Any],
    detached: frozenset[str],
    descriptor_name: str,
    capture: dict[str, Any],
    capture_name: str = "capture.json",
) -> None:
    """Keep every original retained identity except explicitly Git-backed bodies physical."""
    physical(repository)
    require_relative_path(prefix, "capsule prefix")
    require_relative_path(descriptor_name, "source descriptor")
    require(
        descriptor_name not in members and descriptor_name != capture_name,
        "descriptor must be a distinct additional file",
    )
    require(
        len(members) <= MAX_PHYSICAL_MEMBERS and detached.issubset(members),
        "invalid original member population",
    )
    root = repository / prefix
    physical(root)
    require(root.is_dir(), "capsule root is not a directory")
    for name, row in members.items():
        require_relative_path(name, "original capsule member")
        require(
            type(row) is dict
            and set(row) == {"sha256", "bytes"}
            and hexadecimal(row["sha256"], 64)
            and type(row["bytes"]) is int
            and row["bytes"] >= 0,
            "original member identity schema differs",
        )
        require(
            "__pycache__" not in Path(name).parts
            and Path(name).suffix not in {".pyc", ".pyo"},
            "bytecode is not retained source payload",
        )
    expected = (set(members) - set(detached)) | {capture_name, descriptor_name}
    expected_dirs = {
        p.as_posix() for name in expected for p in Path(name).parents if p != Path(".")
    }
    files: set[str] = set()
    directories: set[str] = set()
    pending = [root]
    total = 0
    while pending:
        parent = pending.pop()
        for path in parent.iterdir():
            name = path.relative_to(root).as_posix()
            require(not path.is_symlink(), "capsule alias refused")
            if path.is_dir():
                require(name in expected_dirs, "unlisted capsule directory")
                directories.add(name)
                pending.append(path)
            else:
                require(
                    path.is_file() and path.stat().st_nlink == 1,
                    "special or linked capsule file",
                )
                require(name in expected, "unlisted capsule file")
                size = path.stat().st_size
                require(
                    size <= MAX_PHYSICAL_MEMBER_BYTES, "physical member exceeds bound"
                )
                total += size
                require(total <= MAX_PHYSICAL_BYTES, "physical capsule exceeds bound")
                files.add(name)
    require(
        files == expected and directories == expected_dirs,
        "physical capsule projection is incomplete",
    )
    require(
        type(capture) is dict
        and set(capture) == {"sha256", "bytes"}
        and hexadecimal(capture["sha256"], 64)
        and type(capture["bytes"]) is int,
        "capture identity schema differs",
    )
    for name, row in [
        (name, members[name]) for name in sorted(set(members) - set(detached))
    ] + [(capture_name, capture)]:
        path = root / name
        require(
            path.stat().st_size == row["bytes"],
            "original physical member length differs",
        )
        with path.open("rb") as stream:
            require(
                hashlib.file_digest(stream, "sha256").hexdigest() == row["sha256"],
                "original physical member SHA256 differs",
            )


def native_reference_members(capture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Project the pinned finite native packet without changing its original schema."""
    require(
        capture.get("schema_version") == "native-r-finite-covariance-capture.v1",
        "native source catalogue schema differs",
    )
    members: dict[str, dict[str, Any]] = {}

    def add(name: str, row: dict[str, Any]) -> None:
        require_relative_path(name, "native source catalogue member")
        require(
            name not in members
            and type(row.get("sha256")) is str
            and hexadecimal(row["sha256"], 64)
            and type(row.get("size")) is int
            and row["size"] >= 0,
            "native source catalogue identity differs",
        )
        members[name] = {"sha256": row["sha256"], "bytes": row["size"]}

    for name, row in capture["raw_members"].items():
        add("capture/" + name, row)
    add("capture/receipt.json", capture["execution_receipt"])
    review = capture["independent_terminal_review"]
    add(review["path"], review)
    for name, row in capture["source_context"]["evidence_members"].items():
        add(name, row)
    for row in capture["public_archives"].values():
        add(row["path"], row)
    acquisition = capture["public_acquisition"]
    add(acquisition["path"], acquisition)
    require(len(members) == 152, "complete native source catalogue required")
    return members


def native_oracle_members(capture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Project the original macOS native catalogues without editing native evidence."""
    require(
        capture.get("schema_version")
        in {
            "qualified-native-r-capture.v1",
            "qualified-native-r-annulus-capture.v1",
            "qualified-native-r-count-domain-capture.v1",
        },
        "native oracle catalogue schema differs",
    )
    members: dict[str, dict[str, Any]] = {}

    def add(name: str, row: dict[str, Any]) -> None:
        require_relative_path(name, "native oracle catalogue member")
        require(
            name not in members
            and type(row.get("sha256")) is str
            and hexadecimal(row["sha256"], 64)
            and type(row.get("size")) is int
            and row["size"] >= 0,
            "native oracle catalogue identity differs",
        )
        members[name] = {"sha256": row["sha256"], "bytes": row["size"]}

    require(
        type(capture["raw_members"]) is dict and len(capture["raw_members"]) == 138,
        "complete original native raw catalogue required",
    )
    for name, row in capture["raw_members"].items():
        add("capture/" + name, row)
    add("capture/receipt.json", capture["execution_receipt"])
    require(
        type(capture["public_archives"]) is dict
        and len(capture["public_archives"]) == 5,
        "exact native public archive catalogue required",
    )
    for row in capture["public_archives"].values():
        add(row["path"], row)
    public = capture["public_acquisition"]
    add(public["path"], public)
    require(len(members) == 145, "complete native oracle catalogue required")
    return members


def r_certificate_members(capture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Keep the original Linux certificate file catalogue as logical authority."""
    require(
        capture.get("schema_version") == "lra-live-r-certification.v2"
        and type(capture.get("files")) is dict
        and len(capture["files"]) == 142,
        "complete original Linux certificate catalogue required",
    )
    members = {}
    for name, row in capture["files"].items():
        require_relative_path(name, "Linux reference certificate member")
        require(
            type(row) is dict
            and set(row) == {"sha256", "byte_count"}
            and hexadecimal(row["sha256"], 64)
            and type(row["byte_count"]) is int
            and row["byte_count"] >= 0,
            "Linux reference certificate identity differs",
        )
        members[name] = {"sha256": row["sha256"], "bytes": row["byte_count"]}
    return members
