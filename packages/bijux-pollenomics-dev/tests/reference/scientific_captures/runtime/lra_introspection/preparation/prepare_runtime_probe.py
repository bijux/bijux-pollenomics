"""Freeze a metadata-only Darwin R namespace and DLL custody probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

from contracts import (
    FAMILIES,
    R_SHA,
    dump,
    original_library,
    pin,
    read,
    require,
    sha,
)
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
            f"Observed R core module framework alias differs: {alias}",
        )
        aliases[str(alias)] = str(target)
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
    failed = R / "artifacts/science/current-controlled-lra-numerical-certification"
    for relative in (
        "plan.json",
        "terminal.json",
        "controlled-numerical-terminal.json",
        "optimizer-solution-quality/same-process-runtime.json",
    ):
        files.add(failed / relative)
    require(
        sha(failed / "terminal.json")
        == "3e61e228806047291b388b3ffa52bae0eb6f8585944e2491bff775b11cf89543"
        and sha(failed / "controlled-numerical-terminal.json")
        == "042d74520771c4a6d6241d3496da05d53efda93423b0fec3dd3cd6d9956136ba",
        "Original registered failure epoch differs",
    )
    failed_terminal = read(failed / "terminal.json")
    require(
        failed_terminal["actual_exit"] == 1
        and len(failed_terminal["stages"]) == 1
        and failed_terminal["stages"][0]["actual_exit"] == 1,
        "Original native failure membership differs",
    )
    for row in failed_terminal["products"]:
        path = Path(row["path"])
        require(pin(path) == row, "Original failed execution product changed")
        files.add(path)
    failure = read(failed / "optimizer-solution-quality/same-process-runtime.json")
    require(
        failure["numerical_exit"] is None
        and failure["metadata_exit"] == 1
        and failure["before"] is None,
        "Original erased-DLL refusal differs",
    )
    failed_probe = R / "artifacts/science/current-controlled-lra-runtime-probe"
    require(
        sha(failed_probe / "terminal.json")
        == "e948e8f8c8b7ad0801172a96f326e3e042a0224f362f96fd89e8997307f6d083"
        and sha(failed_probe / "controlled-runtime-terminal.json")
        == "1e5adf2a790174cc51c46ad37010baa5ed6b146657bccddab8c4cc3f22dfa551",
        "Original introspection refusal epoch differs",
    )
    for row in read(failed_probe / "terminal.json")["products"]:
        path = Path(row["path"])
        require(pin(path) == row, "Original raw runtime failure product changed")
        files.add(path)
    files.update(
        [
            failed_probe / "terminal.json",
            failed_probe / "controlled-runtime-terminal.json",
        ]
    )
    out.mkdir()
    (out / "scratch").mkdir()
    (out / "home").mkdir()
    probe = out / "runtime-probe.R"
    report = out / "runtime-observation.json"
    probe.write_text(
        "source("
        + json.dumps(str(A / "oracle_metadata.R"))
        + ")\n"
        + "guarded_replay(NULL,"
        + json.dumps(str(report))
        + ","
        + json.dumps(str(r_home))
        + ","
        + json.dumps(str(library))
        + ",c("
        + ",".join(json.dumps(str(path)) for path in dependencies)
        + "),metadata_only=TRUE)\n"
    )
    files.add(probe)
    plan_path = out / "plan.json"
    stages = [
        {
            "id": "metadata-only-R-namespace-and-DLL-custody",
            "argv": [str(rscript), "--vanilla", str(probe)],
            "timeout_seconds": 30,
            "must_succeed": True,
        },
        {
            "id": "independent-R-runtime-and-input-observer",
            "argv": [
                str(PY),
                "-I",
                "-B",
                str(A / "observe_runtime_probe.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 20,
            "must_succeed": True,
        },
    ]
    require(identity() == before, "Canonical candidate changed during preparation")
    plan = {
        "id": "controlled-lra-runtime-probe-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "canonical_identity": before,
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "runtime_entry_targets": {
            str(PY): str(PY.resolve()),
            str(rscript): str(rscript.resolve()),
        },
        "runtime_aliases": aliases,
        "runtime_alias_links": {path: os.readlink(path) for path in aliases},
        "stdlib_alias_authority": alias_authority,
        "input_pins": [pin(p) for p in sorted(files)],
        "absent_input_paths": [
            str(out / "terminal.json"),
            str(out / "controlled-runtime-terminal.json"),
        ],
        "environment": {
            "PYTHONPATH": "",
            **requested_environment(out, library, r_home),
        },
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 65,
            "declared_memory_bytes": 1024**3,
            "declared_storage_bytes": 128 * 1024**2,
        },
        "original_Darwin_native_installation": original,
        "current_R_home": str(r_home),
        "native_Rscript": pin(rscript),
        "current_native_runtime_metadata": os_receipt,
        "native_dependency_files": [str(path) for path in dependencies],
        "native_seed_policy": "Exact six immediate installed package roots, DESCRIPTION/NAMESPACE and original913files authenticated, plus original41 host namespaces and freshjsonlite. Only actual useDynLib names select flat .so files; unused Cairo/debug bytes not selected.",
        "failed_original_replay": {
            "plan": pin(failed / "plan.json"),
            "terminal": pin(failed / "terminal.json"),
            "outer_terminal": pin(failed / "controlled-numerical-terminal.json"),
            "metadata": pin(
                failed / "optimizer-solution-quality/same-process-runtime.json"
            ),
            "first_offending_DLL_identity": "Unknown: original raw snapshot was not retained",
            "Python_fixture_ran": True,
            "R_numerical_source_ran": False,
        },
        "failed_introspection_probe": {
            "plan": pin(failed_probe / "plan.json"),
            "terminal": pin(failed_probe / "terminal.json"),
            "outer_terminal": pin(failed_probe / "controlled-runtime-terminal.json"),
            "raw_metadata": pin(failed_probe / "runtime-observation.json"),
            "observed_refused_DLL": "lapack",
            "R_numerical_source_ran": False,
        },
        "scope": "Actual metadata-only namespace loading/runtime observation; no original numerical R source, Python optimizer/fit, model, installation, source acquisition or ecological/release qualification. Complete raw before/after metadata retained before admission checks. Requested thread limits and completed resource postchecks only; no kernel network denial/full descendant RSS claim.",
    }
    dump(plan_path, plan)
    print(
        json.dumps(
            {
                "plan": pin(plan_path),
                "stages": 2,
                "native_seeds": len(native),
                "native_dependency_files": len(dependencies),
                "input_count": len(files),
                "actual_launch_argv": [
                    str(PY),
                    "-B",
                    str(A / "run.py"),
                    "--plan",
                    str(plan_path),
                    "--registered-plan-sha256",
                    sha(plan_path),
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
