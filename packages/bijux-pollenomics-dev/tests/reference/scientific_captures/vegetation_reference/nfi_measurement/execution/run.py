"""Apply completed resource admission to the unchanged maintained bounded report runner."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_custody import aliases_unchanged


def sha(p: Path) -> str:
    with p.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--registered-plan-sha256", required=True)
    a = p.parse_args()
    assert sha(a.plan) == a.registered_plan_sha256
    plan = json.loads(a.plan.read_bytes())
    assert aliases_unchanged(
        plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
    )
    out = Path(plan["output"])
    assert all(
        Path(entry).resolve() == Path(target)
        for entry, target in plan["runtime_entry_targets"].items()
    )
    terminal = out / "nfi-metadata-terminal.json"
    assert not terminal.exists()
    command = [
        plan["qualified_python"],
        "-B",
        plan["common_runner"],
        "--plan",
        str(a.plan),
        "--registered-plan-sha256",
        a.registered_plan_sha256,
    ]
    completed = subprocess.run(
        command,
        cwd=plan["repository"],
        timeout=plan["resources"]["overall_timeout_seconds"] + 20,
        check=False,
    )
    common = out / "terminal.json"
    actual = json.loads(common.read_bytes())
    assert aliases_unchanged(
        plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
    )
    assert all(
        Path(entry).resolve() == Path(target)
        for entry, target in plan["runtime_entry_targets"].items()
    )
    assert actual["actual_exit"] == completed.returncode
    rss = max(
        (
            r["observed_cumulative_completed_child_peak_rss_bytes_macos"]
            for r in actual["stages"]
        ),
        default=0,
    )
    for row in plan["input_pins"]:
        path = Path(row["path"])
        assert (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size == row["bytes"]
            and sha(path) == row["sha256"]
        )
    records: list[dict[str, Any]] = []
    for path in sorted(out.rglob("*")):
        assert not path.is_symlink()
        if path.is_file():
            records.append(
                {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}
            )
    total = sum(r["bytes"] for r in records)
    budget = plan["resources"]["declared_storage_bytes"]
    passed = (
        completed.returncode == 0
        and rss <= plan["resources"]["declared_memory_bytes"]
        and total + 16384 <= budget
    )
    receipt = {
        "candidate": plan["candidate"],
        "plan_sha256": a.registered_plan_sha256,
        "common_terminal": {"path": str(common), "sha256": sha(common)},
        "common_actual_exit": completed.returncode,
        "completed_child_peak_rss_bytes_macos": rss,
        "output_bytes_before_receipt": total,
        "storage_receipt_reserved_bytes": 16384,
        "memory_bound_pass": rss <= plan["resources"]["declared_memory_bytes"],
        "storage_bound_pass": total + 16384 <= budget,
        "actual_exit": 0 if passed else 1,
        "scope": "Completed-child RSS and regular logical output bytes qualify declared bounds; 16KiB own receipt reserve included. Unchanged common runner controls exact candidate/input before-after and each actual stage, plus process-group timeouts. No OS quota or full descendant process census.",
    }
    raw = (json.dumps(receipt, indent=2) + "\n").encode()
    assert len(raw) <= 16384
    terminal.write_bytes(raw)
    print(
        json.dumps(
            {
                "terminal": str(terminal),
                "sha256": sha(terminal),
                "actual_exit": receipt["actual_exit"],
            }
        )
    )
    raise SystemExit(receipt["actual_exit"])


if __name__ == "__main__":
    main()
