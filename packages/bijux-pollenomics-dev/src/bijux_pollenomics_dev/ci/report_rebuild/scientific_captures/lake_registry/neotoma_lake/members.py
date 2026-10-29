"""Confine public source/metadata capsule members and preserve all omitted input identities."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from .execution import exact, require


def validate_members(root: Path, members: dict[str, Any]) -> None:
    """A capsule may contain physical directories, regular declared files and its capture only."""
    require(
        root == root.resolve()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "Capsule root has an alias ancestor",
    )
    actual = []
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Capsule alias or special member",
        )
        if path.is_file():
            actual.append(path.relative_to(root).as_posix())
    exact(sorted(actual), sorted(["capture.json", *members]))
    for name, expected in members.items():
        relative = PurePosixPath(name)
        require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and "\\" not in name
            and relative.as_posix() == name,
            "Member leaves capsule",
        )
        require(
            "__pycache__" not in relative.parts and relative.suffix != ".pyc",
            "Bytecode remains identity-only",
        )
        path = root / name
        require(
            not any(p.is_symlink() for p in (path, *path.parents)),
            "Member alias ancestor",
        )
        exact(
            {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            },
            expected,
        )


def validate_catalog(
    catalog: list[dict[str, Any]],
    original: list[dict[str, Any]],
    members: dict[str, Any],
    *,
    private_root: str,
    repository: str,
    public_paths: set[str],
    runtime_paths: set[str],
    raw_relational_paths: set[str] | None = None,
) -> dict[str, int]:
    """Classify original rows without treating omitted source/runtime bytes as newly observed."""
    exact(len(catalog), len(original))
    require(
        len({row["path"] for row in original}) == len(original),
        "Duplicate original identity",
    )
    counts: dict[str, int] = {}
    for index, (row, pin) in enumerate(zip(catalog, original, strict=True)):
        exact(row["original_index"], index)
        exact({key: row[key] for key in ("path", "sha256", "bytes")}, pin)
        role = row["retention_role"]
        name = row["retained_member"]
        path = Path(pin["path"])
        if role in {
            "public_first_party_source_or_resource",
            "public_control_or_declared_metadata",
        }:
            require(
                pin["path"] in public_paths
                and not path.is_relative_to(Path(private_root)),
                "Unreviewed retained public source",
            )
            require(
                type(name) is str and name in members,
                "Retained input lacks capsule member",
            )
            exact(members[name], {key: pin[key] for key in ("sha256", "bytes")})
        elif role == "private_source_identity_only":
            exact(name, None)
            require(
                path.is_relative_to(Path(private_root)),
                "Undeclared omitted private source",
            )
        elif role == "bytecode_identity_only":
            exact(name, None)
            require(
                path.is_relative_to(Path(repository) / "packages")
                and (path.suffix == ".pyc" or "__pycache__" in path.parts),
                "Omitted nonbytecode source",
            )
        elif role == "raw_relational_input_identity_only":
            exact(name, None)
            require(
                raw_relational_paths is not None
                and pin["path"] in raw_relational_paths
                and path.is_relative_to(Path(repository) / "data/neotoma"),
                "Unreviewed raw/relational omission",
            )
        elif role == "operational_tool_identity_only":
            exact(name, None)
            exact(
                pin,
                {
                    "path": "/Library/Developer/CommandLineTools/usr/bin/git",
                    "sha256": "a73bf622a2e470d5d57a4b1d5aef1e8680e67278018d4858a2f93825b7d595c7",
                    "bytes": 3837392,
                },
            )
        else:
            exact(role, "runtime_dependency_identity_only")
            exact(name, None)
            require(pin["path"] in runtime_paths, "Unqualified omitted runtime input")
        counts[role] = counts.get(role, 0) + 1
    return counts
