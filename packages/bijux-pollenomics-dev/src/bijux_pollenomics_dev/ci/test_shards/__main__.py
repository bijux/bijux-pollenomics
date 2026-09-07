"""Refuse incomplete, overlapping, failed, or revision-mismatched test shards."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from . import shard_for


def verify_receipts(
    paths: list[Path],
    *,
    count: int,
    revision: str,
    expected_universe_file: Path | None = None,
) -> int:
    """Require exact partition coverage and completed execution of every test."""
    if count < 1 or len(paths) != count:
        raise ValueError("test shard receipt count does not match the expected matrix")
    receipts = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if {row["index"] for row in receipts} != set(range(count)):
        raise ValueError("missing or duplicate test shard index")
    universe = receipts[0]["universe"]
    if not universe or universe != sorted(set(universe)):
        raise ValueError("test universe must be nonempty, sorted, and unique")
    if expected_universe_file is not None:
        plan = json.loads(expected_universe_file.read_text(encoding="utf-8"))
        if (
            plan.get("schema_version") != "pytest-shard-receipt.v1"
            or plan.get("revision") != revision
            or plan.get("index") != 0
            or plan.get("count") != 1
            or plan.get("exit_code") != 0
            or plan.get("collection_only") is not True
            or plan.get("completed") != []
            or plan.get("selected") != universe
            or plan.get("universe") != universe
        ):
            raise ValueError("test shards differ from the independent collection plan")
    completed: list[str] = []
    for row in receipts:
        if row["schema_version"] != "pytest-shard-receipt.v1":
            raise ValueError("unsupported shard receipt schema")
        if row.get("collection_only") is not False:
            raise ValueError("test shard must execute rather than only collect tests")
        if row["count"] != count or row["revision"] != revision:
            raise ValueError("shard receipt identity mismatch")
        if row["universe"] != universe:
            raise ValueError("test collection differs between shards")
        expected = [node for node in universe if shard_for(node, count) == row["index"]]
        if row["selected"] != expected or row["completed"] != expected:
            raise ValueError(
                "test shard execution does not match its exact selected partition"
            )
        if row["exit_code"] != 0:
            raise ValueError("test shard did not pass")
        completed.extend(row["completed"])
    if sorted(completed) != universe:
        raise ValueError("test shard union does not equal the selected test universe")
    return len(universe)


def _write_junit(destination: Path, *, total: int, count: int) -> None:
    """Atomically attest successful reconciliation beneath repository artifacts."""
    destination = destination.resolve()
    if not destination.is_relative_to(Path.cwd().resolve() / "artifacts"):
        raise ValueError("reconciliation JUnit must be beneath repository artifacts")
    suite = ET.Element(
        "testsuite", name="test-shard-reconciliation", tests="1", failures="0"
    )
    case = ET.SubElement(suite, "testcase", name="exact-selected-universe")
    ET.SubElement(
        case, "system-out"
    ).text = (
        f"{total} selected tests accounted exactly once across {count} passing shards."
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        staged = Path(stream.name)
        stream.write(ET.tostring(suite, encoding="utf-8", xml_declaration=True))
    try:
        os.replace(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    """Verify the current workflow's downloaded compact receipts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--junit-output", type=Path)
    parser.add_argument("--expected-universe-file", type=Path)
    args = parser.parse_args()
    paths = sorted(args.receipt_root.rglob("shard-receipt.json"))
    total = verify_receipts(
        paths,
        count=args.count,
        revision=args.revision,
        expected_universe_file=args.expected_universe_file,
    )
    if args.junit_output is not None:
        _write_junit(args.junit_output, total=total, count=args.count)
    print(
        f"All {args.count} test shards passed; {total} selected tests accounted exactly once."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
