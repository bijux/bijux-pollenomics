"""Validate a closed public capsule and complete ordered, explicitly omitted input identities."""

from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from .execution import exact, require


def validate_members(root: Path, members: dict[str, Any]) -> None:
    require(
        root == root.resolve()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "Capsule root alias",
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
            "Member path escapes capsule",
        )
        require(
            relative.suffix != ".pyc" and "__pycache__" not in relative.parts,
            "Bytecode payload is not public source",
        )
        path = root / name
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
    original_roles: dict[str, dict[str, Any]],
    runtime_paths: set[str],
    repository: str,
    retained_aliases: dict[str, str],
) -> dict[str, int]:
    """No omitted input is silently converted into a fresh source or runtime-equivalence claim."""
    exact(len(catalog), len(original))
    require(
        len({row["path"] for row in original}) == len(original),
        "Duplicate original pin",
    )
    counts: Counter[str] = Counter()
    for index, (row, pin) in enumerate(zip(catalog, original, strict=True)):
        exact(row["original_index"], index)
        exact({key: row[key] for key in ("path", "sha256", "bytes")}, pin)
        role, member = row["retention_role"], row["retained_member"]
        name = pin["path"]
        if role == "retained_original_public_source":
            if name in original_roles:
                exact(original_roles[name]["retained_member"], member)
                require(member is not None, "Original private/runtime payload promoted")
            else:
                require(name in retained_aliases, "Unreviewed original source copy")
                exact(retained_aliases[name], member)
            exact(members[member], {key: pin[key] for key in ("sha256", "bytes")})
        elif role == "retained_observer_control_or_public_metadata":
            path = Path(name)
            require(
                path.is_relative_to(Path(repository) / "artifacts/science")
                or path.is_relative_to(Path(repository) / "packages"),
                "Undeclared retained observer input",
            )
            require(
                type(member) is str and member in members,
                "Missing observer input member",
            )
            exact(members[member], {key: pin[key] for key in ("sha256", "bytes")})
        else:
            exact(member, None)
            require(
                role
                in {
                    "private_source_identity_only",
                    "runtime_dependency_identity_only",
                    "bytecode_identity_only",
                },
                "Unknown omission role",
            )
            if name in original_roles:
                expected = {
                    "omitted_private_capture_payload_identity_only": "private_source_identity_only",
                    "omitted_runtime_or_dependency_identity_only": "runtime_dependency_identity_only",
                    "omitted_first_party_bytecode_identity_only": "bytecode_identity_only",
                }
                require(
                    original_roles[name]["retention_role"] in expected,
                    "Original public input omitted",
                )
                exact(role, expected[original_roles[name]["retention_role"]])
            else:
                exact(role, "runtime_dependency_identity_only")
                require(name in runtime_paths, "Unreviewed omitted runtime input")
        counts[role] += 1
    return dict(sorted(counts.items()))
