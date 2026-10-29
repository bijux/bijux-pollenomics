"""Freeze public-call profiling on admitted source inputs without executing it."""

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
    retained_review = (
        R
        / "artifacts/science/representative-performance-input-custody/retained-source-review.json"
    )
    assert (
        sha(retained_review)
        == "0f39df9c5c01f0bd2e9d74966445507d92a16f24cacb4103a9cd2a6166f9aed5"
    )
    pins.add(retained_review)
    for retained in json.loads(retained_review.read_bytes())["rows"]:
        path = Path(retained["retained_path"])
        assert sha(path) == retained["actual_sha256"] == retained["expected_sha256"]
        pins.add(path)
    prerequisites = []
    for job, family, terminal_sha, product_sha in (
        (
            "current-landclim-author-uncertainty",
            "author-site-uncertainty",
            "5d219a86ff4b052594c388f77391866d1e5930fd151a19876826f2f20c09127c",
            "7da46aa0ca1c17b6915f6ee99e51c4911632472a244aefdc1a62828f1d4c41d4",
        ),
        (
            "current-landclim-author-profile",
            "author-site-profile-comparison",
            "d1310069079fd00f411e588e0551e7f0bb6311530b9872ab29f52bf1de613ea4",
            "73649b9d5e5c3b4699840148140b4b0edab8fd939e82b357852e2e162792dde4",
        ),
    ):
        directory = R / "artifacts/science" / job
        terminal = directory / "author-site-terminal.json"
        assert sha(terminal) == terminal_sha
        actual = json.loads(terminal.read_bytes())
        common = Path(actual["common_terminal"]["path"])
        original_plan = directory / "plan.json"
        assert (
            sha(common) == actual["common_terminal"]["sha256"]
            and sha(original_plan) == actual["plan_sha256"]
        )
        assert (
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == actual["common_actual_exit"] == 0
        )
        states = json.loads(common.read_bytes())
        assert len(states["stages"]) == 2 and all(
            type(s["actual_exit"]) is int and s["actual_exit"] == 0
            for s in states["stages"]
        )
        observer = directory / "independent-author-review.json"
        assert (
            sha(observer)
            == {
                "current-landclim-author-uncertainty": "bdde25827b73ea9077e3a2e462098c92824f7b6c86a4a60f8210bf57a63b44a0",
                "current-landclim-author-profile": "baee780d11c9dd4beaf0a68330c46f7bcafdcbec2002c3c52652dd238003961c",
            }[job]
        )
        observed = json.loads(observer.read_bytes())
        assert (
            observed["scientific_typed_values_exact_to_original"] is True
            and observed["source_private_members_exact"] is True
        )
        report = R / "docs/report/method-certification" / family / "report.json"
        produced = directory / family / "report.json"
        assert sha(report) == sha(produced) == product_sha
        pins.update({terminal, common, original_plan, observer, report, produced})
        prerequisites.append(
            {
                "family": family,
                "terminal": pin(terminal),
                "report": pin(report),
                "execution_candidate": actual["candidate"],
            }
        )
    uncertainty = R / "docs/report/method-certification/author-site-uncertainty"
    for name, expected in (
        (
            "draws.json",
            "84da401dc862452bc329d11df074d2c6d7353b3e34b223892b5fd6702fae4390",
        ),
        (
            "cover-draws.csv",
            "dffe151e3b4aa177cbe17332ba9c10f73fa0119f9dbc9c607b4d060f935f6885",
        ),
    ):
        assert sha(uncertainty / name) == expected
        pins.add(uncertainty / name)
    report = json.loads((uncertainty / "report.json").read_bytes())
    for row in report["private_source_inputs"]:
        assert pin(PRIVATE / row["path"]) == {**row, "path": str(PRIVATE / row["path"])}
    for row in report["repository_code_inputs"]:
        assert pin(R / row["path"]) == {**row, "path": str(R / row["path"])}
        pins.add(R / row["path"])
    lineage = R / report["author_prepared_lineage"]["path"]
    assert sha(lineage) == report["author_prepared_lineage"]["sha256"]
    pins.add(lineage)
    for name in (
        "python-baseline",
        "python-isolated",
        "native-forward",
        "native-memory",
        "love-source-profile",
        "love-source-comparison",
    ):
        pins.add(R / "docs/report/numerical-performance" / name / "report.json")
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
                    "source_prerequisites": prerequisites,
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
            "id": name + "-worker-" + str(i),
            "argv": [
                str(PY),
                "-B",
                str(A / "measure.py"),
                "--plan",
                str(out / "plan.json"),
                "--worker",
                str(i),
                "--workload",
                name,
            ],
            "timeout_seconds": 60 if name == "author-conditional-joint-draws" else 180,
            "must_succeed": True,
        }
        for name in (
            "author-conditional-joint-draws",
            "love-larger-fixed-candidate-batch",
        )
        for i in range(3)
    ]
    stages.extend(
        [
            {
                "id": "equal-total-work-process-scaling",
                "argv": [
                    str(PY),
                    "-B",
                    str(A / "scaling.py"),
                    "--plan",
                    str(out / "plan.json"),
                ],
                "timeout_seconds": 180,
                "must_succeed": True,
            },
            {
                "id": "independent-source-output-timing-review",
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
    )
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
        "id": "representative-source-profile-"
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
        "source_prerequisites": prerequisites,
        "workloads": [
            "author-conditional-joint-draws",
            "love-larger-fixed-candidate-batch",
        ],
        "environment": env,
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 1200,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 268435456,
            "maximum_parallel_workers": 2,
            "numerical_threads_per_worker": 1,
        },
        "scope": "Source-qualified actual six-site/ten-taxon/1024stored conditional joint draw public calls and128synthetic computational LOVEexample repetitions, never128independent sites. Three isolated first+sevenwarm calls each, separate diagnostic profile and unprofiled one-boundary measurements, equal-total1vs2workers. No sourceR execution, optimizer search, newC++compiler/kernel, ecological/rights/human or release admission; old seven-workload/64replica timings retain historical scope. Confirmed measured hotspot alone cannot authorize compilation: same-input currentR/Python and separately reviewed prospective spike remain required.",
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
