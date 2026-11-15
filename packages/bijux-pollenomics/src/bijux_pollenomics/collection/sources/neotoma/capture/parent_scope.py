"""Shared native roster identity and exposure declarations for bounded source scopes."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ..client import positive_native_id
from .receipts import _object, _read
from .resources.models import EXPOSURE_ROLES


def _pinned(path: Path, digest: str, bound: int) -> dict[str, Any]:
    content = _read(path, bound)
    if sha256(content).hexdigest() != digest:
        raise ValueError("Neotoma unit source identity differs")
    return _object(content)


def _roster(path: Path, digest: str) -> dict[str, Any]:
    roster = _pinned(path, digest, 16 * 1024 * 1024)
    rows = roster.get("resources")
    if (
        not isinstance(rows, list)
        or not rows
        or type(roster.get("resource_count")) is not int
        or roster["resource_count"] != len(rows)
        or not isinstance(roster.get("policy_sources"), list)
        or not roster["policy_sources"]
        or any(
            not isinstance(value, str) or not value.startswith("https://")
            for value in roster["policy_sources"]
        )
    ):
        raise ValueError("Neotoma unit roster population or policy differs")
    seen = set()
    parents: dict[int, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Neotoma unit roster row is malformed")
        ids = [
            positive_native_id(row.get(key))
            for key in ("dataset_id", "site_id", "collection_unit_id")
        ]
        if ids[0] in seen or (ids[2] in parents and parents[ids[2]] != ids[1]):
            raise ValueError("Neotoma unit roster identity or parent is ambiguous")
        seen.add(ids[0])
        parents[ids[2]] = ids[1]
        roles = row.get("exposure_roles")
        if (
            not isinstance(roles, dict)
            or set(roles) != {"current", "doi_frozen"}
            or any(
                not isinstance(role, str) or role not in EXPOSURE_ROLES
                for role in roles.values()
            )
        ):
            raise ValueError("Neotoma unit roster exposure roles are invalid")
        if (
            not isinstance(row.get("dataset_type"), str)
            or not row["dataset_type"].strip()
            or "database" not in row
            or row["database"] is not None
            and (not isinstance(row["database"], str) or not row["database"].strip())
        ):
            raise ValueError("Neotoma unit roster native type/database is invalid")
    return roster
