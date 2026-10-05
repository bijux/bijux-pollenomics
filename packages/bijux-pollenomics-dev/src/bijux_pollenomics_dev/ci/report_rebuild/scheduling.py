"""Derive CI owner selection from validated producer configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from . import configured_owner as owner_runner
from .configured_owner import (
    DEFAULT_CONFIGURATION,
    DEFAULT_INVENTORY,
    _configuration_owner,
    _read_object,
    _repository_relative,
    _safe_file,
    resolve_configured_owner,
)
from .contracts import ReportRebuildError
from .scheduling_custody.context import _owner_schedule_context

SCHEMA = "configured-report-owner-schedule.v1"
MAX_OWNERS = 139
IDENTITY = re.compile(r"[A-Za-z0-9_./-]+")


def configured_owner_schedule(
    repository: Path, *, source_root: Path | None = None
) -> dict[str, object]:
    """Validate every invocation and use full identities for scheduling."""
    repository = repository.resolve(strict=True)
    relative = _repository_relative(
        repository, DEFAULT_CONFIGURATION, "owner configuration"
    )
    configuration_path = _safe_file(repository, relative, "owner configuration")
    before = configuration_path.read_bytes()
    configuration = _read_object(repository, relative, "owner configuration")
    inventory_relative = _repository_relative(
        repository, DEFAULT_INVENTORY, "report ownership"
    )
    inventory_path = _safe_file(repository, inventory_relative, "report ownership")
    inventory_before = inventory_path.read_bytes()
    inventory = _read_object(repository, inventory_relative, "report ownership")
    rows = configuration.get("owners")
    if not isinstance(rows, list) or not rows:
        raise ReportRebuildError("configured owner list is empty")
    if len(rows) > MAX_OWNERS:
        raise ReportRebuildError(f"two-lane owner schedule exceeds {MAX_OWNERS} owners")
    with _owner_schedule_context(
        repository,
        Path(relative),
        Path(inventory_relative),
        configuration,
        inventory,
        check_ownership=owner_runner._schedule_ownership,
        safe_file=owner_runner._safe_file,
        relative_path=owner_runner._repository_relative,
        digest=owner_runner._digest,
    ):
        identities = []
        for row in rows:
            if not isinstance(row, dict):
                raise ReportRebuildError("configured owner must be an object")
            identity = row.get("owner_id")
            if (
                not isinstance(identity, str)
                or not IDENTITY.fullmatch(identity)
                or any(part.startswith(".") for part in identity.split("/"))
            ):
                raise ReportRebuildError("owner ID cannot be scheduled safely")
            _configuration_owner(configuration, identity)
            if source_root is None:
                resolve_configured_owner(repository, identity)
            else:
                resolve_configured_owner(repository, identity, source_root=source_root)
            identities.append(identity)
    identities.sort()
    selected = set(identities)
    # Scheduling requires complete coverage of generated ownership after
    # all public owner resolvers share one validated inventory.
    declarations = inventory.get("owners")
    if not isinstance(declarations, list):
        raise ReportRebuildError("report ownership owner list differs")
    generated = {
        row["owner_id"]
        for row in declarations
        if isinstance(row, dict) and row.get("role") == "generated_owner"
    }
    if selected != generated:
        missing = sorted(generated - selected)
        extra = sorted(selected - generated)
        raise ReportRebuildError(
            f"configured owner schedule differs from generated ownership: "
            f"missing={missing}, extra={extra}"
        )
    for identity in identities:
        parts = identity.split("/")
        if any("/".join(parts[:size]) in selected for size in range(1, len(parts))):
            raise ReportRebuildError("owner IDs overlap ancestor namespaces")
    matrix = [
        {"id": identity, "artifact": hashlib.sha256(identity.encode()).hexdigest()}
        for identity in identities
    ]
    if len({row["artifact"] for row in matrix}) != len(matrix):
        raise ReportRebuildError("owner artifact identities collide")
    if configuration_path.read_bytes() != before:
        raise ReportRebuildError("owner configuration changed during scheduling")
    if inventory_path.read_bytes() != inventory_before:
        raise ReportRebuildError("report ownership changed during scheduling")
    return {
        "schema_version": SCHEMA,
        "configuration_sha256": hashlib.sha256(before).hexdigest(),
        "owners": matrix,
        "owner_ids": " ".join(identities),
    }


def main(argv: list[str] | None = None) -> int:
    """Write the schedule and optional GitHub job outputs without producers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args(argv)
    try:
        repository = args.repository.resolve(strict=True)
        output = args.output.resolve()
        if (
            not output.is_relative_to(repository / "artifacts")
            or output.exists()
            or args.output.is_symlink()
        ):
            raise ReportRebuildError("absent repository artifact schedule required")
        report = configured_owner_schedule(repository, source_root=args.source_root)
        if args.check_only:
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.github_output is not None:
            with args.github_output.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"owners={json.dumps(report['owners'], separators=(',', ':'))}\n"
                )
                handle.write(f"owner_ids={report['owner_ids']}\n")
    except ReportRebuildError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
