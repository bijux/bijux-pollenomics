"""Freeze exact historical comparison and source-bound development preparation."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
PRIVATE = R.parent / "-bijux-pollenomics-data/landclim/author-reference"
P = "docs/report/method-certification/petrkunes-r-comparison"
C = "docs/report/pollen-reconstruction/author-lra-constrained"
F = "docs/report/pollen-reconstruction/author-lra-optimized-feasibility"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path):
    assert path.is_absolute() and path.resolve() == path and path.is_file()
    assert ".." not in path.parts and not any(
        p.is_symlink() for p in (path, *path.parents)
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
    args = parser.parse_args()
    assert Path(sys.executable).absolute() == PY
    assert Path(sys.prefix).absolute() == PY.parent.parent
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    out = args.output.absolute()
    assert not out.exists() and out.resolve() == out and ".." not in out.parts
    assert out.is_relative_to(R / "artifacts") and not any(
        p.is_symlink() for p in (out, *out.parents)
    )
    manifest = A / "prepared-source-manifest.json"
    source = json.loads(manifest.read_bytes())
    for row in source["files"]:
        assert pin(A / row["path"]) == {**row, "path": str(A / row["path"])}
    peer = json.loads((A / "independent-preparation-review.json").read_bytes())
    assert peer["approved"] is True and peer["source_manifest_sha256"] == sha(manifest)
    roots = [
        R / "packages" / n / "src"
        for n in (
            "bijux-pollenomics-dev",
            "bijux-pollenomics",
            "bijux-pollenomics-lra",
            "pollenomics",
        )
    ]
    sys.path[:0] = list(map(str, roots))
    module = importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.author_snapshot"
    )
    qualified = module.validated_author_snapshot(
        R,
        PRIVATE.parents[1],
        Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json"),
    )
    assert qualified.directory == PRIVATE and len(qualified.inputs) == 195
    retained = json.loads((R / P / "native-report.json").read_bytes())
    assert (
        len(retained["private_inputs"]),
        len(retained["reference_inputs"]),
        len(retained["code_inputs"]),
    ) == (14, 2, 5)
    pins = {
        manifest,
        A / "independent-preparation-review.json",
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        R / "artifacts/science/runtime/receipt.json",
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
    }
    pins.update(A / row["path"] for row in source["files"])
    pins.update(qualified.inputs.values())
    for field, base in (
        ("private_inputs", PRIVATE),
        ("reference_inputs", R),
        ("code_inputs", R),
    ):
        for row in retained[field]:
            path = base / row["path"]
            assert sha(path) == row["sha256"] and path.stat().st_size == row["bytes"]
            pins.add(path)
    for family in (P, C, F):
        pins.update(
            p
            for p in (R / family).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        )
    for root in roots:
        pins.update(
            p
            for p in root.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".pyo")
        )
    for name in (
        "bijux_pollenomics_dev.essd_reproduction.author_lra_development",
        "bijux_pollenomics.analysis.lra_validation.experiments.configuration",
        "bijux_pollenomics.analysis.lra.execution.service",
    ):
        imported = importlib.import_module(name)
        assert any(
            Path(imported.__file__).resolve().is_relative_to(root) for root in roots
        )
    for imported in sys.modules.values():
        name = getattr(imported, "__file__", None)
        if name and Path(name).is_file():
            pins.add(Path(name).resolve())
    records = [pin(p) for p in sorted(pins)]
    assert identity() == before
    out.mkdir()
    (out / "scratch").mkdir()

    def stage(name, argv, timeout):
        return {
            "id": name,
            "argv": [str(PY), "-B", *argv],
            "timeout_seconds": timeout,
            "must_succeed": True,
        }

    stages = [
        stage(
            "historical-python-full-grid-comparison",
            [
                str(R / P / "native_comparison.py"),
                "--repository",
                str(R),
                "--private-root",
                str(PRIVATE),
                "--output",
                str(out / "comparison"),
            ],
            120,
        ),
        stage(
            "source-bound-author-development-inputs",
            [
                "-m",
                "bijux_pollenomics_dev.essd_reproduction.author_lra_development",
                "--author-source-root",
                str(PRIVATE),
                "--output",
                str(out / "source-inputs"),
            ],
            60,
        ),
        stage(
            "constrained-love-closed-composition-inputs",
            [
                str(R / C / "prepare.py"),
                "--source",
                str(out / "source-inputs"),
                "--destination",
                str(out / "constrained-inputs"),
            ],
            60,
        ),
        stage(
            "bounded-feasibility-request-inputs",
            [
                str(R / F / "prepare.py"),
                "--author-source-root",
                str(PRIVATE),
                "--output",
                str(out / "feasibility"),
            ],
            60,
        ),
        stage(
            "independent-original-science-and-request-identities",
            [str(A / "observe.py"), "--plan", str(out / "plan.json")],
            60,
        ),
    ]
    env = {
        "PYTHONPATH": ":".join(map(str, roots)),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMPDIR": str(out / "scratch"),
        "PROJ_NETWORK": "OFF",
    }
    env.update(
        dict.fromkeys(
            (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            ),
            "1",
        )
    )
    plan = {
        "id": "author-development-source-inputs-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "canonical_identity": before,
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "private_root": str(PRIVATE),
        "input_pins": records,
        "absent_input_paths": [],
        "environment": env,
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 420,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 67108864,
            "sequential_stage_count": 5,
            "numerical_threads": 1,
        },
        "scope": "One actual current Python historical nine-site31-taxon grid comparison on original tagged-R retained draws, plus deterministic original15site author input preparation and exact30taxon constrained/feasibility request identities. No optimizer/fit/newR or new prediction/scoring/frozen outcome. Prior-exposed English development only; no Nordic/independent vegetation/geometry/rights/human/release admission.",
    }
    plan["actual_launch_argv"] = [
        str(PY),
        "-B",
        str(A / "run.py"),
        "--plan",
        str(out / "plan.json"),
        "--registered-plan-sha256",
        "PLAN_SHA256",
    ]
    assert identity() == before
    p = out / "plan.json"
    p.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "plan": str(p),
                "sha256": sha(p),
                "pins": len(records),
                "stages": len(stages),
                "actual_launch_argv": plan["actual_launch_argv"],
            }
        )
    )


if __name__ == "__main__":
    main()
