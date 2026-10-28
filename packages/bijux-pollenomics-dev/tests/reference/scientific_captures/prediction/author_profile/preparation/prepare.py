"""Freeze a source-owned author replay in explicit upstream publication order."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

from custody import document_inputs, successful_uncertainty

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
PRIVATE = R.parent / "-bijux-pollenomics-data/landclim/author-reference"
NAMES = ("author-site-uncertainty", "author-site-profile-comparison")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular(path):
    assert (
        path.is_absolute()
        and ".." not in path.parts
        and path.resolve() == path
        and path.is_file()
        and not any(x.is_symlink() for x in (path, *path.parents))
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner", choices=NAMES, required=True)
    parser.add_argument("--uncertainty-plan", type=Path)
    parser.add_argument("--uncertainty-plan-sha256")
    parser.add_argument("--uncertainty-terminal", type=Path)
    parser.add_argument("--uncertainty-terminal-sha256")
    parser.add_argument("--check-inputs-only", action="store_true")
    args = parser.parse_args()
    assert (
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix).absolute() == PY.parent.parent
        and sys.version_info[:2] == (3, 11)
    )
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    output = args.output.absolute()
    assert (
        not output.exists()
        and output.resolve() == output
        and ".." not in output.parts
        and output.is_relative_to(R / "artifacts")
        and not any(p.is_symlink() for p in (output, *output.parents))
    )
    manifest = A / "prepared-source-manifest.json"
    frozen = json.loads(manifest.read_bytes())
    for row in frozen["files"]:
        path = A / row["path"]
        assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
    source_proposal = json.loads((A / "qualified-source-proposal.json").read_bytes())
    for row in source_proposal["paths"]:
        assert sha(R / row["path"]) == row["proposed_sha256"]
    dev_root = R / "packages/bijux-pollenomics-dev/src"
    sys.path.insert(0, str(dev_root))
    snapshot_module = importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.author_snapshot"
    )
    assert (
        Path(snapshot_module.__file__).absolute()
        == dev_root / "bijux_pollenomics_dev/ci/report_rebuild/author_snapshot.py"
    )
    descriptor = Path(
        "configs/ci/qualified-report-sources/landclim-author-snapshot.json"
    )
    qualified_snapshot = snapshot_module.validated_author_snapshot(
        R, PRIVATE.parents[1], descriptor
    )
    assert (
        qualified_snapshot.directory == PRIVATE
        and len(qualified_snapshot.inputs) == 195
    )
    snapshot = PRIVATE / "snapshot-manifest.json"
    assert (
        sha(snapshot)
        == "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
    )
    source = json.loads(snapshot.read_bytes())
    assert source["file_count"] == len(source["files"]) == 193
    pins = {
        snapshot,
        manifest,
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        R / "artifacts/science/runtime/receipt.json",
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
    }
    pins.update(A / row["path"] for row in frozen["files"])
    pins.update(qualified_snapshot.inputs.values())
    for name, digest in source["files"].items():
        path = PRIVATE / name
        regular(path)
        assert sha(path) == digest
        pins.add(path)
    root = R / "packages/bijux-pollenomics-lra/src"
    for path in root.rglob("*"):
        if (
            path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in (".pyc", ".pyo")
        ):
            pins.add(path)
    current_code = {}
    old_products = {}
    original_reports = {}
    private_members = {}
    stages = []
    for name in (args.owner,):
        directory = R / "docs/report/method-certification" / name
        script = directory / "replay.py"
        report_path = directory / "report.json"
        report = json.loads(report_path.read_bytes())
        rows = report.get("repository_code_inputs") or [
            r for r in report["input_identities"] if r["path"].endswith(".py")
        ]
        names = [
            r["path"].replace(
                "/reconstruction/joint_site_draws.py",
                "/reconstruction/uncertainty/joint_site_draws.py",
            )
            for r in rows
        ]
        current_code[name] = [
            {"path": n, "sha256": sha(R / n), "bytes": (R / n).stat().st_size}
            for n in names
        ]
        pins.update(R / n for n in names)
        private_rows = report.get("private_source_inputs") or [
            r for r in report["input_identities"] if r["path"].startswith("author/")
        ]
        for row in private_rows:
            path = PRIVATE / row["path"]
            assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
        private_members[name] = private_rows
        original_reports[name] = str(report_path)
        old_products[name] = {
            n: str(directory / n)
            for n in (
                ("report.json", "draws.json", "cover-draws.csv")
                if name == NAMES[0]
                else ("report.json",)
            )
        }
        pins.update(Path(p) for p in old_products[name].values())
        pins.add(script)
        if name == NAMES[0]:
            row = report["author_prepared_lineage"]
            path = R / row["path"]
            assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
            pins.add(path)
        stages.append(
            {
                "id": "current-original-source-" + name,
                "argv": [
                    str(PY),
                    "-B",
                    str(script),
                    "--repository",
                    str(R),
                    "--source-root",
                    str(PRIVATE),
                    "--output",
                    str(output / name),
                ],
                "timeout_seconds": 60,
                "must_succeed": True,
            }
        )
    # Every canonical documentation input is physically authenticated now. The
    # historical profile recorded an earlier metadata epoch, not different draws.
    documents, bridge = document_inputs(R, A)
    pins.update(Path(row["absolute_path"]) for row in documents)
    pins.add(A / "retained-original-uncertainty-report.json")
    prerequisite = None
    if args.owner == NAMES[1]:
        assert all(
            (
                args.uncertainty_plan,
                args.uncertainty_plan_sha256,
                args.uncertainty_terminal,
                args.uncertainty_terminal_sha256,
            )
        )
        prerequisite, inherited = successful_uncertainty(
            R,
            args.uncertainty_plan,
            args.uncertainty_plan_sha256,
            args.uncertainty_terminal,
            args.uncertainty_terminal_sha256,
        )
        pins.update(inherited)
    else:
        assert not any(
            (
                args.uncertainty_plan,
                args.uncertainty_plan_sha256,
                args.uncertainty_terminal,
                args.uncertainty_terminal_sha256,
            )
        )
    sys.path.insert(0, str(root))
    lra_api = importlib.import_module("bijux_pollenomics_lra.api")
    assert (
        Path(lra_api.joint_site_cover_draws.__code__.co_filename).resolve()
        == root / "bijux_pollenomics_lra/reconstruction/uncertainty/joint_site_draws.py"
    )
    imported = []
    for name, module in sorted(sys.modules.items()):
        value = getattr(module, "__file__", None)
        if value and Path(value).is_file():
            pins.add(Path(value).resolve())
            imported.append({"module": name, **regular(Path(value).resolve())})
    records = [regular(path) for path in sorted(pins)]
    assert identity() == before
    if args.check_inputs_only:
        print(
            json.dumps(
                {
                    "input_check_only": True,
                    "candidate": args.candidate,
                    "owner": args.owner,
                    "physical_doc_inputs": documents,
                    "epoch_bridge": bridge,
                    "pins": len(records),
                    "source_snapshot_members": 193,
                }
            )
        )
        return
    output.mkdir()
    (output / "scratch").mkdir()
    stages.append(
        {
            "id": "independent-original-source-numerical-output-review",
            "argv": [
                str(PY),
                "-I",
                "-B",
                str(A / "observe.py"),
                "--plan",
                str(output / "plan.json"),
            ],
            "timeout_seconds": 60,
            "must_succeed": True,
        }
    )
    environment = {
        "PYTHONPATH": str(root),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": str(output / "pycache"),
        "TMPDIR": str(output / "scratch"),
        "PROJ_NETWORK": "OFF",
        **dict.fromkeys(
            (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            ),
            "1",
        ),
    }
    plan = {
        "id": "original-author-site-source-replay-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "canonical_identity": before,
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "private_root": str(PRIVATE),
        "private_manifest": regular(snapshot),
        "private_members": private_members,
        "source_snapshot_members": 193,
        "qualified_author_snapshot": {
            "descriptor": str(R / descriptor),
            "descriptor_sha256": qualified_snapshot.descriptor_sha256,
            "source_root": str(PRIVATE.parents[1]),
            "source_id": "landclim/author-reference",
            "input_count": len(qualified_snapshot.inputs),
            "scientific_or_rights_admission": False,
        },
        "owner": args.owner,
        "profile_document_inputs": [
            {k: v for k, v in row.items() if k != "absolute_path"} for row in documents
        ],
        "historical_document_epoch_bridge": bridge,
        "successful_uncertainty_prerequisite": prerequisite,
        "current_code_inputs": current_code,
        "original_reports": original_reports,
        "original_products": old_products,
        "module_origins": imported,
        "input_pins": records,
        "absent_input_paths": [],
        "environment": environment,
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 180,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 67108864,
            "sequential_stage_count": 2,
            "numerical_threads": 1,
        },
        "scope": "One genuine maintained current Python author-site replay on exact original193-member private prior-exposed author capsule. Uncertainty owns three products and1024 conditional joint draws; profile runs only after those genuine successful outputs are adopted at canonical input paths and owns one report using1000 identical retained paired draws. Exact original typed scientific values, six sites/ten positive taxa, source/chronology/geometry/PPE/rights caveats preserved. Only authenticated actual code provenance and exact actual upstream documentation input identities may change. No R/optimizer/ecological validation, private redistribution or human/scientific release claim. Separate candidate epochs remain explicit.",
        "actual_launch_argv": [
            str(PY),
            "-B",
            str(A / "run.py"),
            "--plan",
            str(output / "plan.json"),
            "--registered-plan-sha256",
            "PLAN_SHA256",
        ],
    }
    path = output / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "plan": str(path),
                "sha256": sha(path),
                "candidate": args.candidate,
                "pins": len(records),
                "private_members": 193,
                "private_inputs": [len(rows) for rows in private_members.values()],
                "stages": 2,
                "actual_launch_argv": plan["actual_launch_argv"],
            }
        )
    )


if __name__ == "__main__":
    main()
