"""Validate exact tracked report ownership declarations without replay claims."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from graphlib import CycleError, TopologicalSorter
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

SCHEMA = "report-output-ownership.v1"
REPORT_ROOT = "docs/report"
INVENTORY_SCOPE = (
    "tracked report paths; ownership declarations do not certify reproduction"
)
DEFAULT_INVENTORY = Path("configs/ci/report-ownership.json")
ROLES = frozenset(
    {
        "publisher_partition",
        "generated_owner",
        "retained_source",
        "maintained_editorial",
        "maintained_code",
        "maintained_configuration",
        "unresolved",
    }
)
OWNER_ID = re.compile(
    r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*(?:/[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*)*\Z"
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
OWNER_FIELDS: frozenset[str] = frozenset(
    {"owner_id", "role", "paths", "producer_paths", "producer_inputs", "verification"}
)
INVENTORY_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "root",
        "inventory_scope",
        "path_count",
        "paths_sha256",
        "owners",
    }
)


class ReportOwnershipError(ValueError):
    """An ownership declaration differs from the tracked report namespace."""


@dataclass(frozen=True)
class OwnershipCheckResult:
    """Path accounting only; no producer or source certificate is authenticated."""

    path_count: int
    owner_count: int
    role_counts: dict[str, int]
    unresolved_owner_ids: list[str]
    unresolved_path_count: int
    verification_scope: str = "tracked membership and declaration structure only"


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportOwnershipError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _relative_path(value: object, label: str, *, report: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ReportOwnershipError(f"{label} must be a nonempty repository path")
    parts = value.split("/")
    if (
        value.startswith("/")
        or "\\" in value
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ReportOwnershipError(
            f"{label} is not a canonical repository path: {value}"
        )
    if report and (len(parts) < 3 or parts[:2] != ["docs", "report"]):
        raise ReportOwnershipError(f"{label} is outside docs/report: {value}")
    return value


def _paths(
    value: object, label: str, *, report: bool = False, required: bool = False
) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(path, str) for path in value):
        raise ReportOwnershipError(f"{label} must be a path list")
    paths = [_relative_path(path, label, report=report) for path in value]
    if required and not paths:
        raise ReportOwnershipError(f"{label} must be nonempty")
    if paths != sorted(set(paths)):
        raise ReportOwnershipError(f"{label} must be sorted and unique")
    return paths


def _regular_confined_file(repository: Path, relative: str, label: str) -> Path:
    """Reject symlinked ancestors as well as symlinked or missing file leaves."""
    parts = _relative_path(relative, label).split("/")
    path = repository
    try:
        for part in parts[:-1]:
            path /= part
            if not stat.S_ISDIR(path.lstat().st_mode):
                raise ReportOwnershipError(f"{label} has a non-real directory: {path}")
        path /= parts[-1]
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ReportOwnershipError(f"{label} is not a real regular file: {path}")
    except OSError as error:
        raise ReportOwnershipError(
            f"{label} is missing or unreadable: {path}"
        ) from error
    if not path.resolve().is_relative_to(repository):
        raise ReportOwnershipError(f"{label} escapes repository: {path}")
    return path


def _tracked_report_paths(repository: Path) -> list[str]:
    try:
        root = (
            subprocess.run(
                ["git", "-C", str(repository), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                timeout=30,
            )
            .stdout.decode("utf-8")
            .strip()
        )
        if Path(root).resolve() != repository:
            raise ReportOwnershipError("--repository must be the Git worktree root")
        output = subprocess.run(
            ["git", "-C", str(repository), "ls-files", "-z", "--", REPORT_ROOT],
            check=True,
            capture_output=True,
            timeout=30,
        ).stdout
        paths = [item.decode("utf-8") for item in output.split(b"\0") if item]
    except (OSError, UnicodeError, subprocess.SubprocessError) as error:
        raise ReportOwnershipError(
            f"cannot enumerate tracked report paths: {error}"
        ) from error
    if len(paths) != len(set(paths)):
        raise ReportOwnershipError("Git report path population is not unique")
    paths.sort()
    for path in paths:
        _relative_path(path, "tracked report path", report=True)
        _regular_confined_file(repository, path, "tracked report path")
    return paths


def _load_inventory(repository: Path, inventory: Path) -> dict[str, Any]:
    if inventory.is_absolute():
        try:
            relative = inventory.relative_to(repository).as_posix()
        except ValueError as error:
            raise ReportOwnershipError("inventory is outside repository") from error
    else:
        relative = inventory.as_posix()
    path = _regular_confined_file(repository, relative, "ownership inventory")
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportOwnershipError(
            f"cannot read ownership inventory: {error}"
        ) from error
    if not isinstance(payload, dict) or frozenset(payload) != INVENTORY_FIELDS:
        raise ReportOwnershipError("ownership inventory fields are not exact")
    return payload


def check_report_ownership(
    repository: Path,
    inventory_path: Path | None = None,
    *,
    require_resolved: bool = False,
) -> OwnershipCheckResult:
    """Check declared roles against every current Git-tracked report file."""
    repository = repository.resolve()
    tracked = _tracked_report_paths(repository)
    payload = _load_inventory(
        repository, inventory_path if inventory_path is not None else DEFAULT_INVENTORY
    )
    if payload["schema_version"] != SCHEMA or payload["root"] != REPORT_ROOT:
        raise ReportOwnershipError("ownership inventory schema or root differs")
    if payload["inventory_scope"] != INVENTORY_SCOPE:
        raise ReportOwnershipError("ownership inventory scope differs")
    if type(payload["path_count"]) is not int or payload["path_count"] != len(tracked):
        raise ReportOwnershipError("ownership path_count differs from tracked paths")
    expected_digest = hashlib.sha256(
        json.dumps(sorted(tracked), separators=(",", ":")).encode()
    ).hexdigest()
    digest = payload["paths_sha256"]
    if (
        not isinstance(digest, str)
        or SHA256.fullmatch(digest) is None
        or digest != expected_digest
    ):
        raise ReportOwnershipError("ownership paths_sha256 differs from tracked paths")

    owners = payload["owners"]
    if not isinstance(owners, list) or not owners:
        raise ReportOwnershipError("ownership owners must be a nonempty list")
    owner_ids: set[str] = set()
    assigned: dict[str, str] = {}
    role_counts: Counter[str] = Counter()
    unresolved_ids: list[str] = []
    for index, raw in enumerate(owners):
        if not isinstance(raw, dict) or frozenset(raw) != OWNER_FIELDS:
            raise ReportOwnershipError(f"owner {index} fields are not exact")
        owner_id = raw["owner_id"]
        if not isinstance(owner_id, str) or OWNER_ID.fullmatch(owner_id) is None:
            raise ReportOwnershipError(f"owner {index} id is not a stable domain name")
        if owner_id in owner_ids:
            raise ReportOwnershipError(f"duplicate owner_id: {owner_id}")
        owner_ids.add(owner_id)
        role = raw["role"]
        if not isinstance(role, str) or role not in ROLES:
            raise ReportOwnershipError(f"owner {owner_id} has invalid role")
        owned = _paths(
            raw["paths"], f"owner {owner_id} paths", report=True, required=True
        )
        producer_paths = _paths(
            raw["producer_paths"], f"owner {owner_id} producer_paths"
        )
        producer_inputs = _paths(
            raw["producer_inputs"], f"owner {owner_id} producer_inputs"
        )
        verification = raw["verification"]
        if not isinstance(verification, str) or not verification.strip():
            raise ReportOwnershipError(f"owner {owner_id} verification is missing")
        if role == "generated_owner":
            if not producer_paths or not producer_inputs:
                raise ReportOwnershipError(
                    f"generated owner {owner_id} needs producer paths and inputs"
                )
            if (set(producer_paths) | set(producer_inputs)) & set(owned):
                raise ReportOwnershipError(
                    f"generated owner {owner_id} feeds its own output"
                )
        if role == "maintained_code" and any(
            Path(path).suffix not in {".py", ".R", ".sh"} for path in owned
        ):
            raise ReportOwnershipError(
                f"maintained code owner {owner_id} has non-code path"
            )
        if role == "maintained_editorial" and any(
            Path(path).suffix != ".md" for path in owned
        ):
            raise ReportOwnershipError(
                f"maintained editorial owner {owner_id} has non-Markdown path"
            )
        if role == "maintained_configuration" and any(
            Path(path).suffix != ".json" for path in owned
        ):
            raise ReportOwnershipError(
                f"maintained configuration owner {owner_id} has non-JSON path"
            )
        for path in (*producer_paths, *producer_inputs):
            _regular_confined_file(repository, path, f"owner {owner_id} source")
        for path in owned:
            if path in assigned:
                raise ReportOwnershipError(
                    f"report path has overlapping owners: {path}"
                )
            assigned[path] = owner_id
            role_counts[role] += 1
        if role == "unresolved":
            unresolved_ids.append(owner_id)

    missing = sorted(set(tracked) - assigned.keys())
    extra = sorted(assigned.keys() - set(tracked))
    if missing or extra:
        raise ReportOwnershipError(
            f"ownership population differs: missing={missing}, extra={extra}"
        )
    _require_acyclic_generated_owners(owners, assigned)
    if require_resolved and unresolved_ids:
        raise ReportOwnershipError(
            f"unresolved report owners remain: {', '.join(sorted(unresolved_ids))}"
        )
    return OwnershipCheckResult(
        path_count=len(tracked),
        owner_count=len(owner_ids),
        role_counts=dict(sorted(role_counts.items())),
        unresolved_owner_ids=sorted(unresolved_ids),
        unresolved_path_count=role_counts["unresolved"],
    )


def _require_acyclic_generated_owners(
    owners: list[dict[str, Any]], assigned: dict[str, str]
) -> None:
    """An owner cannot reconstruct its inputs through its own downstream output."""
    generated = {
        owner["owner_id"]: owner
        for owner in owners
        if owner["role"] == "generated_owner"
    }
    dependencies = {
        owner_id: {
            assigned[path]
            for path in (*owner["producer_paths"], *owner["producer_inputs"])
            if path in assigned and assigned[path] in generated
        }
        for owner_id, owner in generated.items()
    }
    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as error:
        raise ReportOwnershipError(
            "generated owner dependency cycle: " + " -> ".join(error.args[1])
        ) from error


def main(argv: list[str] | None = None) -> int:
    """Validate exact tracked report ownership declarations without replay claims."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[6],
        help="Git worktree root containing docs/report",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY,
        help="repository-relative ownership inventory",
    )
    parser.add_argument("--require-resolved", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check_report_ownership(
            args.repository, args.inventory, require_resolved=args.require_resolved
        )
    except ReportOwnershipError as error:
        print(f"report ownership check failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
