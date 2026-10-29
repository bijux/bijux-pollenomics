"""Freeze two unchanged controlled numerical replays on authenticated Darwin R."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig

from contracts import (
    FAMILIES,
    PRODUCTS,
    R_SHA,
    dump,
    original_library,
    pin,
    read,
    require,
    sha,
)
from probe_custody import qualify_runtime_probe
from runtime_custody import (
    native_closure,
    native_seeds,
    requested_environment,
    stdlib_alias_contract,
    tree,
)

A = Path(__file__).resolve().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    require(git("branch", "--show-current").strip() == b"main", "Local main required")
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix).absolute() == PY.parent.parent
        and sys.version_info[:2] == (3, 11),
        "Qualified lexical Python3.11 required",
    )
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    out = args.output.absolute()
    require(
        out.resolve() == out
        and out.is_relative_to(R / "artifacts")
        and not out.exists()
        and not any(p.is_symlink() for p in (out, *out.parents)),
        "Fresh nonsymlink artifact destination required",
    )
    manifest = A / "prepared-source-manifest.json"
    held = read(manifest)
    for row in held["files"]:
        require(
            pin(A / row["path"]) == {**row, "path": str(A / row["path"])},
            "Held source changed",
        )
    review = A / "independent-source-review.json"
    peer = read(review)
    require(
        peer["approved"] is True and peer["source_manifest_sha256"] == sha(manifest),
        "Independent held source review required",
    )
    qualified_probe_root = (
        R / "artifacts/science/current-controlled-lra-introspection-probe"
    )
    runtime_probe_reference, prerequisite_files = qualify_runtime_probe(
        qualified_probe_root
    )
    original = original_library(R)
    library = Path(original["root"])
    r_home = Path("/Library/Frameworks/R.framework/Versions/4.6/Resources")
    rscript = r_home / "bin/Rscript"
    require(sha(rscript) == R_SHA, "Qualified Darwin Rscript differs")
    makeconf = (r_home / "etc/Makeconf").read_text()
    require(
        "R_ARCH = \n" in makeconf and "SHLIB_EXT = .so\n" in makeconf,
        "Flat .so R loader layout differs",
    )
    for name, version in [("jsonlite", "2.0.0")]:
        text = (r_home / "library" / name / "DESCRIPTION").read_text()
        require(
            f"Package: {name}\n" in text and f"Version: {version}\n" in text,
            "Current installed JSON namespace differs",
        )
    files = {
        Path(__file__).resolve(),
        manifest,
        review,
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
        R / "artifacts/science/runtime/receipt.json",
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        Path("/usr/bin/otool"),
        Path("/usr/bin/sw_vers"),
    }
    aliases = {str(PY): str(PY.resolve())}
    roots = [
        R / "packages" / name / "src"
        for name in [
            "bijux-pollenomics",
            "bijux-pollenomics-dev",
            "bijux-pollenomics-lra",
            "pollenomics",
        ]
    ]
    roots += [
        Path(sysconfig.get_path("stdlib")).resolve(),
        PY.parent.parent / "lib/python3.11/site-packages",
        r_home,
        library,
    ]
    stdlib = Path(sysconfig.get_path("stdlib")).resolve()
    external_files, unused_aliases, alias_authority = stdlib_alias_contract(
        stdlib, PY.parent.parent, list(sys.path)
    )
    for root in roots:
        paths, links = tree(
            root.resolve(),
            external_files=external_files if root.resolve() == stdlib else None,
            unused_directory_aliases=unused_aliases
            if root.resolve() == stdlib
            else None,
        )
        files.update(paths)
        aliases.update(links)
    for row in held["files"]:
        files.add(A / row["path"])
    for family in FAMILIES:
        directory = R / "docs/report/method-certification" / family
        files.update(p for p in directory.iterdir() if p.is_file())
    files.add(Path(original["public_native_capture"]["path"]))
    files.update(Path(row["path"]) for row in original["public_execution_evidence"])
    files.update(
        [
            R / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R",
            R / "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz",
            Path(original["receipt"]["path"]),
            Path(original["terminal"]["path"]),
        ]
    )
    framework = r_home.parents[2]
    for alias, target in (
        (framework / "Resources", r_home),
        (framework / "Versions/Current", r_home.parent),
    ):
        require(
            alias.is_symlink() and alias.resolve(strict=True) == target,
            f"Qualified R core module framework alias differs: {alias}",
        )
        aliases[str(alias)] = str(target)
    files.update(prerequisite_files)
    native = native_seeds(R, r_home, library)
    dependencies, loader = native_closure(native)
    files.update(dependencies)
    os_receipt = {
        "platform": sys.platform,
        "os_build": subprocess.check_output(
            ["/usr/bin/sw_vers"], text=True, timeout=10
        ),
        "native_dependencies": loader,
    }
    out.mkdir()
    (out / "scratch").mkdir()
    (out / "home").mkdir()
    stages = []
    origins = {}
    wrappers = {}
    plan_path = out / "plan.json"
    for family in FAMILIES:
        source = R / "docs/report/method-certification" / family
        owned = out / "owned-replays" / family
        owned.mkdir(parents=True)
        py = owned / "replay.py"
        shutil.copyfile(source / "replay.py", py)
        require(sha(py) == sha(source / "replay.py"), "Maintained Python copy differs")
        if family == "optimizer-solution-quality":
            shutil.copyfile(source / "cases.json", owned / "cases.json")
            files.add(owned / "cases.json")
        r_name = "solver.R" if family == "optimizer-solution-quality" else "replay.R"
        wrapper = owned / r_name
        process = out / family / "same-process-runtime.json"
        wrapper.write_text(
            "source("
            + json.dumps(str(A / "oracle_metadata.R"))
            + ")\nguarded_replay("
            + ",".join(
                json.dumps(str(x)) for x in [source / r_name, process, r_home, library]
            )
            + ",c("
            + ",".join(json.dumps(str(path)) for path in dependencies)
            + "))\n"
        )
        files.update([py, wrapper])
        origins[family] = {
            "canonical_python": pin(source / "replay.py"),
            "owned_python": pin(py),
            "canonical_R": pin(source / r_name),
            "R_wrapper": pin(wrapper),
            "same_process_runtime": str(process),
        }
        wrappers[family] = str(owned)
        stages.append(
            {
                "id": family + "-current-native-replay",
                "argv": [
                    str(PY),
                    "-B",
                    str(py),
                    "--repository",
                    str(R),
                    "--library",
                    str(library),
                    "--rscript",
                    str(rscript),
                    "--output",
                    str(out / family),
                ],
                "timeout_seconds": 75,
                "must_succeed": True,
            }
        )
    stages.append(
        {
            "id": "independent-ordered-values-objectives-and-runtime",
            "argv": [
                str(PY),
                "-I",
                "-B",
                str(A / "observe_numerical.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 30,
            "must_succeed": True,
        }
    )
    require(identity() == before, "Candidate changed during source preparation")
    plan = {
        "id": "controlled-lra-current-numerical-certification-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:10],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "canonical_identity": before,
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "runtime_aliases": aliases,
        "runtime_alias_links": {path: os.readlink(path) for path in aliases},
        "stdlib_alias_authority": alias_authority,
        "input_pins": [pin(p) for p in sorted(files)],
        "absent_input_paths": [
            str(out / "terminal.json"),
            str(out / "controlled-numerical-terminal.json"),
        ],
        "environment": {
            "PYTHONPATH": os.pathsep.join(str(p) for p in roots[:4]),
            **requested_environment(out, library, r_home),
        },
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 210,
            "declared_memory_bytes": 1024**3,
            "declared_storage_bytes": 128 * 1024**2,
        },
        "qualified_runtime_probe": runtime_probe_reference,
        "qualified_runtime_probe_root": str(qualified_probe_root),
        "original_Darwin_native_installation": original,
        "current_R_home": str(r_home),
        "native_Rscript": pin(rscript),
        "current_native_runtime_metadata": os_receipt,
        "native_dependency_files": [str(path) for path in dependencies],
        "native_seed_policy": "Rscript/exec plus NAMESPACE useDynLib declarations from the original41 disqover namespace families, six exact immediate installed package DESCRIPTION/NAMESPACE roots, freshjsonlite and authenticated named R core lapack module required by sessionInfo introspection. Other complete R_HOME files are pinned, not all utilities or Cairo devices claimed loaded. Before/after R metadata refuses any other DLL path.",
        "maintained_replays": origins,
        "expected_public_products": {k: list(v) for k, v in PRODUCTS.items()},
        "scope": "New controlled current Python/Darwin-R certification of two declared fixtures; unchanged numerical scripts/tolerances, real artifact wrappers in report source hashes, before/after same-process namespaces/DLLs. Old reports/candidates/timing and original unpinned-jsonlite limit remain historical. No ecological, human, platform matrix or release acceptance. Numerical thread variables requested only; host network access not kernel-denied, no network/source/install operation in declared commands.",
    }
    dump(plan_path, plan)
    print(
        json.dumps(
            {
                "plan": pin(plan_path),
                "actual_launch_argv": [
                    str(PY),
                    "-B",
                    str(A / "run.py"),
                    "--plan",
                    str(plan_path),
                    "--registered-plan-sha256",
                    sha(plan_path),
                ],
                "stages": 3,
                "original_library_files": 913,
                "input_count": len(files),
                "resources": plan["resources"],
            }
        )
    )


if __name__ == "__main__":
    main()
