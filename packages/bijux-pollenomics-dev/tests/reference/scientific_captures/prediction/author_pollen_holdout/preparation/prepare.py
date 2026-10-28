"""Freeze the maintained source-bound pollen baseline and exact reader observer."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

from input_custody import qualify, row, sha

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
PRIVATE = R.parent / "-bijux-pollenomics-data/landclim/author-reference"


def identity():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    assert git("branch", "--show-current").decode().strip() == "main"
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--check-inputs-only", action="store_true")
    args = p.parse_args()
    assert Path(sys.executable).absolute() == PY and sys.version_info[:2] == (3, 11)
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    source_proposal = (
        R
        / "artifacts/science/author-pollen-replay-reader-contract/guarded-source-proposal.json"
    )
    assert (
        sha(source_proposal)
        == "cdbd3a326d148f67ede3d537b4b2e560b75935bd30d1586a90d989a41563e526"
    )
    proposed = json.loads(source_proposal.read_bytes())
    wrapper = (
        R
        / "docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py"
    )
    declared = next(r for r in proposed["paths"] if R / r["path"] == wrapper)
    assert sha(wrapper) == declared["proposed_sha256"]
    output = args.output.absolute()
    assert (
        not output.exists() and output.resolve() == output and ".." not in output.parts
    )
    assert output.is_relative_to(R / "artifacts")
    assert not any(p.is_symlink() for p in (output, *output.parents))
    frozen = A / "prepared-source-manifest.json"
    document = json.loads(frozen.read_bytes())
    for item in document["files"]:
        assert row(A / item["path"])["sha256"] == item["sha256"]
        assert (A / item["path"]).stat().st_size == item["bytes"]
    roots = [
        R / f"packages/{p}/src"
        for p in (
            "bijux-pollenomics",
            "bijux-pollenomics-dev",
            "bijux-pollenomics-lra",
            "pollenomics",
        )
    ]
    sys.path[:0] = [str(p) for p in roots]
    authority = importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.author_snapshot"
    )
    descriptor = Path(
        "configs/ci/qualified-report-sources/landclim-author-snapshot.json"
    )
    source = authority.validated_author_snapshot(R, PRIVATE.parents[1], descriptor)
    assert source.directory == PRIVATE and len(source.inputs) == 195
    complete = qualify(R, PRIVATE)
    accounts = importlib.import_module(
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts"
    )
    family = R / "docs/report/pollen-reconstruction/author-example-site-mean-holdout"
    route_name = (
        "docs/report/pollen-reconstruction/author-example-site-mean-holdout/REPORT.md"
    )
    route = accounts.load_routes()[route_name]
    raw = (family / "REPORT.md").read_bytes()
    authored = accounts.verified_authored_reader(raw, route)
    assert accounts.render_route(authored, route) == raw
    producer = importlib.import_module(
        "bijux_pollenomics_dev.essd_reproduction.observed_pollen_baseline"
    )
    assert (
        Path(producer.__file__).absolute()
        == roots[1]
        / "bijux_pollenomics_dev/essd_reproduction/observed_pollen_baseline.py"
    )
    common = R / "artifacts/science/current-report-custody/run_account_qualification.py"
    pins = {Path(r["path"]) for r in complete["inputs"]}
    pins.update(source.inputs.values())
    pins.update({wrapper, source_proposal})
    pins.update(
        {
            frozen,
            common,
            PY.resolve(),
            PY.parent.parent / "pyvenv.cfg",
            R / "artifacts/science/runtime/receipt.json",
        }
    )
    pins.update(A / r["path"] for r in document["files"])
    pins.update(
        family / n
        for n in ("report.json", "scores.csv", "predictions.csv", "REPORT.md")
    )
    for root in roots:
        pins.update(
            p
            for p in root.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".pyo")
        )
    modules = []
    for name, module in sorted(sys.modules.items()):
        value = getattr(module, "__file__", None)
        if value and Path(value).is_file():
            path = Path(value).resolve()
            pins.add(path)
            modules.append({"module": name, **row(path)})
    records = [row(p) for p in sorted(pins)]
    assert identity() == before
    if args.check_inputs_only:
        print(
            json.dumps(
                {
                    "all_physical_inputs_pass": True,
                    "source_members": 193,
                    "qualified_inputs": 195,
                    "named_inputs": len(complete["inputs"]),
                    "sites": 17,
                    "taxa": 31,
                    "grids": 2,
                    "candidate": args.candidate,
                    "reader_authored_sha256": hashlib.sha256(authored).hexdigest(),
                    "complete": complete,
                    "pins": len(records),
                }
            )
        )
        return
    output.mkdir()
    (output / "scratch").mkdir()
    plan = {
        "id": "source-author-pollen-family-replay-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "qualified_python": str(PY),
        "common_runner": str(common),
        "canonical_identity": before,
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "private_root": str(PRIVATE),
        "complete_source_inputs": complete,
        "original_family": str(family),
        "reader_path": route_name,
        "input_pins": records,
        "module_origins": modules,
        "absent_input_paths": [],
        "environment": {
            "PYTHONPATH": ":".join(str(p) for p in roots),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "scratch"),
            "PROJ_NETWORK": "OFF",
            **dict.fromkeys(
                (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                    "BLIS_NUM_THREADS",
                    "RAYON_NUM_THREADS",
                ),
                "1",
            ),
        },
        "stages": [
            {
                "id": "maintained-managed-reader-family-replay",
                "argv": [
                    str(PY),
                    "-B",
                    str(wrapper),
                    "--source-root",
                    str(PRIVATE),
                    "--output",
                    str(output / "products"),
                ],
                "timeout_seconds": 120,
                "must_succeed": True,
            },
            {
                "id": "independent-complete-source-numerical-reader-observer",
                "argv": [
                    str(PY),
                    "-B",
                    str(A / "observe.py"),
                    "--plan",
                    str(output / "plan.json"),
                ],
                "timeout_seconds": 60,
                "must_succeed": True,
            },
        ],
        "resources": {
            "overall_timeout_seconds": 240,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 67108864,
            "concurrency": 1,
            "numerical_threads": 1,
        },
        "scope": "Actual maintained family replay CLI wrapping the unchanged observed-pollen site-ID holdout on original193-member prior-exposed English author capsule;17sites/2grids/31taxa. Reuses original authenticated reference receipts without newR. All four final family outputs must be byte-exact, including the fully rendered managed REPORT and normalized CSV. Source count/zero-unavailable/site-denominator/refusal limits unchanged. No vegetation accuracy/Nordic cohort/rights or human/scientific release acceptance. Source-qualified replay is not itself complete same-candidate mixedreport gate.",
    }
    plan["actual_launch_argv"] = [
        str(PY),
        "-B",
        str(A / "run.py"),
        "--plan",
        str(output / "plan.json"),
        "--registered-plan-sha256",
        "PLAN_SHA256",
    ]
    path = output / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "plan": str(path),
                "sha256": sha(path),
                "pins": len(records),
                "actual_launch_argv": plan["actual_launch_argv"],
            }
        )
    )


if __name__ == "__main__":
    main()
