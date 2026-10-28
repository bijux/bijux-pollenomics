"""Independently derive complete workbook/source findings without producer imports."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

# Authenticate the physical helper namespace before Python can select local imports.
_entrypoint_path = Path(__file__).absolute()
_source_directory = _entrypoint_path.parent
if _entrypoint_path != _entrypoint_path.resolve() or any(
    _ancestor.is_symlink()
    for _ancestor in (_entrypoint_path, *_entrypoint_path.parents)
):
    raise ValueError("Controller entrypoint or ancestor is an alias")
_source_modules = {
    "observe.py",
    "common_runner.py",
    "prepare.py",
    "cache_contract.py",
    "runtime.py",
    "contracts.py",
    "run.py",
    "execute_source.py",
    "independent.py",
    "check_contracts.py",
}
for _entry in _source_directory.iterdir():
    if _entry.is_symlink() or (not _entry.is_file() and not _entry.is_dir()):
        raise ValueError("Controller namespace contains an alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller import directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _source_modules:
        raise ValueError("Unexpected controller import member")
sys.path.insert(0, str(_source_directory))
from cache_contract import (  # noqa: E402 — authenticate local imports first.
    validate_cache,
)
from contracts import (  # noqa: E402 — authenticate local imports first.
    CACHE,
    LANES,
    LEDGER,
    PRIVATE,
    RAW,
    ROOT,
    SOURCE,
    dump,
    exact,
    load,
    physical_pin,
    pin,
    require,
    sha,
    source_namespace,
    verify_frozen_pins,
)
from independent import (  # noqa: E402 — authenticate local imports first.
    AGE_INTERPRETATION,
    WITNESS_INTERPRETATION,
    neotoma_findings,
    workbook_age_findings,
)
from runtime import (  # noqa: E402 — authenticate local imports first.
    enable_xlrd,
    profile_guard,
    qualify_process_snapshot,
    raw_process_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--lane", choices=LANES, required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    plan = load(args.plan)
    output = Path(plan["output"])
    lane = plan["lanes"][args.lane]
    verify_frozen_pins(plan["input_pins"])
    enable_xlrd()
    before = raw_process_snapshot()
    qualify_process_snapshot(before, plan["input_pins"], SOURCE)
    stages = load(output / "stage-progress.json")
    needed = 1 if args.lane == "neotoma" else 3
    require(len(stages) == needed, "Missing or extra prior native stages")
    for expected, actual in zip(plan["stages"][:needed], stages, strict=True):
        require(
            exact(actual["argv"], expected["argv"])
            and actual["id"] == expected["id"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Genuine earlier native stage zero required",
        )
    with (ROOT / LEDGER).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    sequences = (
        ("FLINK", "STAV")
        if args.lane == "neotoma"
        else ("FLINK", "HOLK", "RANV", "STAV")
    )
    ledger: dict[str, dict[str, str]] = {}
    sheets = {}
    workbook_pins = []
    xlrd = __import__("xlrd")
    for seq in sequences:
        selected = [row for row in rows if row["publication_sequence"] == seq]
        require(len(selected) == 1, "Exact selected source ledger row required")
        row = selected[0]
        ledger[seq] = row
        require(
            row["per_sequence_rights"] == "unresolved"
            and row["independent_ground_truth"] == "refused_candidate_overlap",
            "Rights/independent truth boundary differs",
        )
        workbook = PRIVATE / row["typed_workbook_member"]
        item = physical_pin(workbook)
        require(
            item["sha256"] == row["typed_workbook_sha256"],
            "Actual workbook identity differs",
        )
        workbook_pins.append(item)
        sheets[seq] = xlrd.open_workbook(str(workbook)).sheet_by_index(0)
    if args.lane == "neotoma":
        findings, joins = neotoma_findings(sheets, ledger, load(ROOT / RAW))
        expected = {
            "schema_version": "rootsi-neotoma-chronology-witness.v1",
            "overlap_ledger_sha256": sha(ROOT / LEDGER),
            "neotoma_raw_part_sha256": sha(ROOT / RAW),
            "findings": findings,
            "interpretation": WITNESS_INTERPRETATION,
        }
    else:
        findings = workbook_age_findings(sheets, ledger)
        joins = {
            row["sequence"]: {
                "sample_rows": row["sample_rows"],
                "source_age_column": row["source_age_basis"],
                "dated_event_admitted": False,
            }
            for row in findings
        }
        expected = {
            "schema_version": "rootsi-workbook-chronology-audit.v1",
            "overlap_ledger_sha256": sha(ROOT / LEDGER),
            "sequence_count": 4,
            "source_age_column_sequences": ["FLINK", "HOLK"],
            "no_source_age_column_sequences": ["RANV", "STAV"],
            "findings": findings,
            "interpretation": AGE_INTERPRETATION,
        }
    generated = Path(lane["source_argv"][-1])
    retained = Path(lane["historical_report"]["path"])
    result = load(generated)
    require(
        exact(result, expected),
        "Complete independent typed workbook/source finding differs",
    )
    require(
        exact(result, load(retained))
        and generated.read_bytes() == retained.read_bytes(),
        "Tracked typed/byte checker refused",
    )
    runtime = load(output / (args.lane + "-source-runtime.json"))
    require(
        runtime["candidate"] == plan["candidate"]
        and exact(runtime["plan"], pin(args.plan))
        and exact(runtime["source"], lane["source"])
        and exact(runtime["executed_source_argv"], lane["source_argv"])
        and exact(runtime["interpreter_flags"], ["-I", "-S", "-B"]),
        "Producer runtime/source binding differs",
    )
    require(
        type(runtime["source_exit"]) is int
        and runtime["source_exit"] == 0
        and type(runtime["metadata_exit"]) is int
        and runtime["metadata_exit"] == 0
        and runtime["metadata_error"] is None,
        "Producer or runtime native failure",
    )
    require(
        type(runtime["before"]["pid"]) is int
        and runtime["before"]["pid"] > 0
        and runtime["before"]["pid"] == runtime["after"]["pid"],
        "Same producer process snapshots required",
    )
    for side in ("before", "after"):
        qualify_process_snapshot(runtime[side], plan["input_pins"], SOURCE)
    stdout = Path(stages[-1]["stdout"])
    require(
        sha(stdout) == stages[-1]["stdout_sha256"], "Actual producer stdout differs"
    )
    native = __import__("json").loads(stdout.read_text().splitlines()[-1])
    require(
        exact(
            native["source_runtime"], pin(output / (args.lane + "-source-runtime.json"))
        )
        and exact(native["generated_report"], pin(generated))
        and type(native["source_exit"]) is int
        and native["source_exit"] == 0
        and type(native["metadata_exit"]) is int
        and native["metadata_exit"] == 0,
        "Native stdout/product/runtime join differs",
    )
    verify_frozen_pins(plan["input_pins"])
    validate_cache(CACHE, load(SOURCE / "xlrd-cache-contract.json"))
    after = raw_process_snapshot()
    qualify_process_snapshot(after, plan["input_pins"], SOURCE)
    target = output / (args.lane + "-independent-review.json")
    record = {
        "actual_exit": 0,
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "lane": args.lane,
        "producer_stage": stages[-1],
        "complete_independent_typed_report_exact": True,
        "tracked_byte_checker_exit": 0,
        "generated": pin(generated),
        "canonical": pin(retained),
        "workbooks": workbook_pins,
        "ledger": pin(ROOT / LEDGER),
        "native_source_joins": joins,
        "source_runtime": pin(output / (args.lane + "-source-runtime.json")),
        "observer_before": before,
        "observer_after": after,
        "raw_workbooks_redistributed": False,
        "calendar_conversion_or_age_correction_claimed": False,
        "dated_event_or_LRA_admission_claimed": False,
        "rights_or_human_acceptance_claimed": False,
    }
    dump(target, record)
    if args.lane == "workbook":
        first = load(output / "neotoma-independent-review.json")
        require(
            type(first["actual_exit"]) is int
            and first["actual_exit"] == 0
            and first["plan"] == pin(args.plan),
            "First independent observer zero required",
        )
        dump(
            output / "independent-source-review.json",
            {
                "actual_exit": 0,
                "candidate": plan["candidate"],
                "plan": pin(args.plan),
                "tracked_byte_checker_exit": 0,
                "two_independent_reviews": [
                    pin(output / "neotoma-independent-review.json"),
                    pin(target),
                ],
                "complete_both_typed_reports_and_bytes_exact": True,
                "source_cache_profile": "source-bound isolated base/pure-xlrd; no observed147 or installed-distribution authority",
                "scope": plan["scope"],
            },
        )


if __name__ == "__main__":
    main()
