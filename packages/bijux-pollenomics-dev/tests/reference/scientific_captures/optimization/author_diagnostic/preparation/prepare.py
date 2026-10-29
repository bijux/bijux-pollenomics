"""Freeze original-author bounded diagnostics without executing their solvers."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
PRIVATE = R.parent / "-bijux-pollenomics-data/landclim/author-reference"
PACKAGES = (
    "bijux-pollenomics",
    "bijux-pollenomics-dev",
    "bijux-pollenomics-lra",
    "pollenomics",
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path):
    assert path.is_absolute() and path.resolve() == path and path.is_file()
    assert not any(p.is_symlink() for p in (path, *path.parents))
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def identity():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    assert git("branch", "--show-current").strip() == b"main"
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
    parser.add_argument("--check-inputs-only", action="store_true")
    args = parser.parse_args()
    assert (
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix).absolute() == PY.parent.parent
        and sys.version_info[:2] == (3, 11)
    )
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    out = args.output.absolute()
    assert not out.exists() and out.resolve() == out and ".." not in out.parts
    assert out.is_relative_to(R / "artifacts") and not any(
        p.is_symlink() for p in (out, *out.parents)
    )
    manifest = A / "prepared-source-manifest.json"
    document = json.loads(manifest.read_bytes())
    for row in document["files"]:
        assert pin(A / row["path"]) == {**row, "path": str(A / row["path"])}
    peer = A / "independent-preparation-review.json"
    review = json.loads(peer.read_bytes())
    assert review["approved"] is True and review["source_manifest_sha256"] == sha(
        manifest
    )
    roots = [R / "packages" / n / "src" for n in PACKAGES]
    sys.path[:0] = list(map(str, roots))
    from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
        validated_author_snapshot,
    )

    qualified = validated_author_snapshot(
        R,
        PRIVATE.parents[1],
        Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json"),
    )
    assert qualified.directory == PRIVATE and len(qualified.inputs) == 195
    pins = {
        manifest,
        peer,
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        R / "artifacts/science/runtime/receipt.json",
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
    }
    pins.update(qualified.inputs.values())
    pins.update(A / row["path"] for row in document["files"])
    qualified_root = R / "artifacts/science/current-author-development-inputs"
    outer = qualified_root / "author-site-terminal.json"
    assert (
        sha(outer) == "11e284eb7c4280fc2cb04fbb4bea2979acd7bfb4c964f8c4c222fd68ea903ab4"
    )
    actual = json.loads(outer.read_bytes())
    original_plan = qualified_root / "plan.json"
    assert (
        sha(original_plan)
        == actual["plan_sha256"]
        == "a8d5006746679caede8c332d6cf1307a6878bed73245db37772b1e9912b936b0"
    )
    terminal = Path(actual["common_terminal"]["path"])
    assert sha(terminal) == actual["common_terminal"]["sha256"]
    native = json.loads(terminal.read_bytes())
    assert (
        type(actual["actual_exit"]) is int
        and actual["actual_exit"] == actual["common_actual_exit"] == 0
    )
    assert len(native["stages"]) == 5 and all(
        type(r["actual_exit"]) is int and r["actual_exit"] == 0
        for r in native["stages"]
    )
    observer = qualified_root / "independent-author-development-input-review.json"
    assert (
        sha(observer)
        == "bb46e0feb51b08fbc5bbb22a4bc48316a6fed23b36c73dc6dcc4f6fe2bef2e94"
    )
    witness = json.loads(observer.read_bytes())
    assert witness["historical_native_comparison_byte_exact"] is True
    assert witness["optimizer_R_or_new_prediction_executed"] is False
    input_roots = (
        qualified_root / "constrained-inputs",
        qualified_root / "feasibility/extended/inputs",
    )
    expected = {
        row["path"]: row
        for row in witness["products_before_observer"]
        if row["path"].startswith(
            ("constrained-inputs/", "feasibility/extended/inputs/")
        )
    }
    seen = set()
    for directory in input_roots:
        for path in directory.rglob("*"):
            assert not path.is_symlink()
            if path.is_file():
                name = path.relative_to(qualified_root).as_posix()
                row = expected[name]
                assert pin(path) == {**row, "path": str(path)}
                seen.add(name)
                pins.add(path)
    assert seen == set(expected)
    assert (
        sha(input_roots[0] / "experiment.json")
        == "aba70474156edfd1e03ac777ddb1083b8f396f3e3a21a03d104a3b3713a544b4"
    )
    assert (
        sha(input_roots[1] / "request.json")
        == "bf99b6d8add47095749b1770a0e62a575c1f90217af2c477f36525ddd0a5d69c"
    )
    pins.update({outer, original_plan, terminal, observer})
    qualified_epoch = {
        "candidate": actual["candidate"],
        "plan": pin(original_plan),
        "outer_terminal": pin(outer),
        "observer": pin(observer),
        "scope": "Actual source commit cacf5c5d956f379cf21b94b64791e1daf7650f1a five-stage input preparation; no assertion its whole old source tree is the present candidate. Only exact authenticated derived input files are reused.",
    }
    original_reports = {}
    for label, relative in (
        (
            "gradient",
            "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json",
        ),
        (
            "finite",
            "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite-candidate.json",
        ),
    ):
        path = R / relative
        original_reports[label] = pin(path)
        pins.add(path)
    baseline = (
        R
        / "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json"
    )
    pins.add(baseline)
    for relative in (
        "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py",
        "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite_candidate.py",
    ):
        pins.add(R / relative)
    for relative, expected_sha in {
        "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py": "6383372379623ced187c8b8b5dd43f813dd5ec384a467f872bb99b579e2d1e38",
        "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite_candidate.py": "508cbe3471633d1738d6f2528d12d583d24f1fa2b36a642bb528aa6eb0979e9e",
        "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json": "68afb09419754130f482783397f58b12c7c06ee041430b24d264dc7f9c30e009",
        "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json": "8ce87d7083b0dde01d9030bb82bbd6ea9d3193dc4c52fc0ad7c9346894d8774d",
        "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite-candidate.json": "0de8b9f2558c60c8dd405c01a31cae6542f908e225aa28b698e7c645a2cc2cf1",
    }.items():
        assert sha(R / relative) == expected_sha
    modules = {}
    for name, source in zip(
        (
            "bijux_pollenomics",
            "bijux_pollenomics_dev",
            "bijux_pollenomics_lra",
            "pollenomics",
        ),
        roots,
        strict=True,
    ):
        path = Path(importlib.import_module(name).__file__).absolute()
        assert path.is_relative_to(source)
        modules[name] = pin(path)
    for source in roots:
        pins.update(
            p
            for p in source.rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in (".pyc", ".pyo")
        )
    aliases = {str(PY): str(PY.resolve())}
    standard_library = Path(sysconfig.get_path("stdlib"))
    for runtime_root in (PY.parent.parent, standard_library):
        for path in runtime_root.rglob("*"):
            if runtime_root == standard_library and "site-packages" in path.parts:
                continue
            if path.is_symlink():
                assert path.resolve().exists()
                aliases[str(path)] = str(path.resolve())
            if path.is_file() and path.suffix not in (".pyc", ".pyo"):
                pins.add(path.resolve())
    assert identity() == before
    if args.check_inputs_only:
        print(
            json.dumps(
                {
                    "all_physical_inputs_pass": True,
                    "candidate": args.candidate,
                    "qualified_inputs": len(qualified.inputs),
                    "qualified_input_epoch": qualified_epoch,
                    "pins": len(pins),
                    "actual_public_calls_or_plan": False,
                }
            )
        )
        return
    out.mkdir()
    (out / "scratch").mkdir()
    stages = [
        {
            "id": "source-bound-three-training-item-gradient-diagnostic",
            "argv": [
                str(PY),
                "-B",
                str(
                    R
                    / "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py"
                ),
                "--prepared",
                str(input_roots[0]),
                "--output",
                str(out / "gradient.json"),
            ],
            "timeout_seconds": 240,
            "must_succeed": True,
        },
        {
            "id": "source-bound-finite-best-candidate-diagnostic",
            "argv": [
                str(PY),
                "-B",
                str(
                    R
                    / "docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite_candidate.py"
                ),
                "--inputs",
                str(input_roots[1]),
                "--output",
                str(out / "finite.json"),
            ],
            "timeout_seconds": 240,
            "must_succeed": True,
        },
        {
            "id": "independent-complete-original-science-and-refusal-comparison",
            "argv": [
                str(PY),
                "-B",
                str(A / "observe.py"),
                "--plan",
                str(out / "plan.json"),
            ],
            "timeout_seconds": 60,
            "must_succeed": True,
        },
    ]
    env = {
        "PYTHONPATH": os.pathsep.join(map(str, roots)),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMPDIR": str(out / "scratch"),
        "PYTHONPYCACHEPREFIX": str(out / "pycache"),
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
                "BLIS_NUM_THREADS",
            ),
            "1",
        )
    )
    plan = {
        "id": "author-optimizer-diagnostics-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "private_root": str(PRIVATE),
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "canonical_identity": before,
        "runtime_entry_targets": aliases,
        "input_pins": [pin(p) for p in sorted(pins)],
        "absent_input_paths": [],
        "packages": PACKAGES,
        "module_origins": modules,
        "qualified_input_epoch": qualified_epoch,
        "original_reports": original_reports,
        "gradient_baseline": pin(baseline),
        "environment": env,
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 600,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 67108864,
            "maximum_parallel_workers": 1,
            "numerical_threads_per_worker": 1,
        },
        "scope": "Two unchanged bounded prior-exposed English author development diagnostics, using exact genuine114 derived inputs and complete193member private authority. Three declared problematic training items/two rings and one finite best-candidate pair. Maintained diagnostic optimizer bodies genuinely run; no full15fold/195fit/newR/newheldoutprediction. Complete typed outputs must equal governed historical reports; any scalar/count/type/convergence delta is retained as refusal rather than updating expectations. No ecological/Nordic/rights/human or official release admission.",
    }
    path = out / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "plan": str(path),
                "sha256": sha(path),
                "stages": len(stages),
                "pins": len(pins),
            }
        )
    )


if __name__ == "__main__":
    main()
