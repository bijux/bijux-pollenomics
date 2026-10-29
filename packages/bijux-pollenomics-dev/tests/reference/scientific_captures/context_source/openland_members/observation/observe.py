"""Independently bind OpenLand raw archive members, retained input copies and exact digest-only change."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from zipfile import ZipFile

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical controller entrypoint before helper imports")
_entry_directory = _entry_path.parent
_expected_python = {
    "contracts.py",
    "metadata.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller import")
sys.path.insert(0, str(_entry_directory))
from contracts import (  # noqa: E402
    INPUTS,
    PRODUCER,
    REPORT,
    ROOT,
    dump,
    exact,
    load,
    pin,
    require,
    sha,
    validate_source_bridge,
    verify_inputs,
)
from metadata import (  # noqa: E402
    CSV_MEMBERS,
    PDF_MEMBER,
    SCRIPT_MEMBER,
    SOURCE_BYTES,
    SOURCE_SHA,
    compare_products,
    expected_rows,
    safe_directory,
    upstream_blobs,
    validate_copies,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    verify_inputs(plan)
    output = Path(plan["output"])
    progress = load(output / "stage-progress.json")
    require(len(progress) == 1, "Exactly one actual producer stage required")
    stage = progress[0]
    require(
        stage["id"] == plan["stages"][0]["id"]
        and exact(stage["argv"], plan["stages"][0]["argv"])
        and type(stage["actual_exit"]) is int
        and stage["actual_exit"] == 0
        and stage["timed_out"] is False,
        "Original native producer stage differs",
    )
    for key in ("stdout", "stderr"):
        require(
            sha(Path(stage[key])) == stage[key + "_sha256"], "Actual source log differs"
        )
    execution = load(output / "source-execution.json")
    emitted = json.loads(Path(stage["stdout"]).read_text().splitlines()[-1])
    require(
        exact(emitted["source_execution"], pin(output / "source-execution.json")),
        "Actual stdout/receipt hash join differs",
    )
    require(
        execution["candidate"] == plan["candidate"]
        and exact(execution["plan"], pin(args.plan))
        and exact(execution["source"], plan["maintained_source"]),
        "Actual source/plan/candidate differs",
    )
    for key in ("source_exit", "metadata_exit"):
        require(
            type(execution[key]) is int and execution[key] == 0,
            "Actual source/metadata status differs",
        )
    expected_argv = [
        str(ROOT / PRODUCER),
        "--repository",
        str(ROOT),
        "--archive",
        str(INPUTS["archive"][0]),
        "--upstream-tree",
        str(INPUTS["upstream_tree"][0]),
        "--output",
        str(output / "producer"),
    ]
    require(
        exact(execution["executed_source_argv"], expected_argv)
        and execution["metadata_error"] is None,
        "Actual CLI scope differs",
    )
    expected_reads = {*CSV_MEMBERS, PDF_MEMBER, SCRIPT_MEMBER}
    require(
        set(execution["counters"]["member_content_reads"]) == expected_reads
        and len(execution["counters"]["member_content_reads"]) == 27
        and execution["counters"]["LRA_implementation_function_calls"] == 0,
        "Unsafe member/model execution",
    )
    protected = {r["path"]: r for r in plan["input_pins"]}
    for row in execution["first_party_origins"]:
        require(
            exact(
                protected.get(row["path"]),
                {key: row[key] for key in ("path", "sha256", "bytes")},
            ),
            "Actual source module origin not pinned",
        )
    bridge = plan["source_attribution_bridge"]
    validate_source_bridge(bridge)
    archive_path = INPUTS["archive"][0]
    require(
        sha(archive_path) == SOURCE_SHA and archive_path.stat().st_size == SOURCE_BYTES,
        "Complete private archive differs",
    )
    tree = load(INPUTS["upstream_tree"][0])
    blobs = upstream_blobs(tree)
    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
        safe_directory(infos)
        rows, reads = expected_rows(archive, infos, blobs)
    historical = load(ROOT / REPORT / "report.json")
    actual = load(output / "producer/report.json")
    expected_csv = compare_products(
        historical, actual, rows, (output / "producer/members.csv").read_bytes(), bridge
    )
    require(
        expected_csv == (ROOT / REPORT / "members.csv").read_bytes(),
        "Historical/source member CSV differs",
    )
    copied = execution["retained_input_copy_chain"]
    validate_copies(copied, plan["source_input_records"], output / "retained-inputs")
    verify_inputs(plan)
    dump(
        output / "independent-source-review.json",
        {
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "maintained_source": plan["maintained_source"],
            "native_source_execution": pin(output / "source-execution.json"),
            "produced_outputs": [
                pin(output / "producer" / name)
                for name in plan["produced_output_names"]
            ],
            "retained_declared_input_copies": copied,
            "independent_source_join_science_and_allowed_metadata_exit": 0,
            "tracked_members_CSV_byte_checker_exit": 0,
            "tracked_report_byte_checker_exit": 0
            if (output / "producer/report.json").read_bytes()
            == (ROOT / REPORT / "report.json").read_bytes()
            else 2,
            "source_attribution_bridge": bridge,
            "archive_entries": 51,
            "exact_upstream_blobs": 26,
            "member_payload_reads": sorted(reads),
            "local_GeoPackage_or_editor_payload_reads": 0,
            "public_member_admissions": 0,
            "independent_vegetation_benchmarks": 0,
            "new_HTTP_or_historical_tree_DOI_acquisition_claimed": False,
            "scope": plan["scope"],
        },
    )


if __name__ == "__main__":
    main()
