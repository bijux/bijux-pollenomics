"""Execute the maintained frozen native reference and its original-vector comparison."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "plan.json"
plan = json.loads(PLAN.read_text())
if sys.argv[1:] != ["--registered-plan-sha256", hashlib.sha256(PLAN.read_bytes()).hexdigest()]:
    raise SystemExit("Registered plan identity required")
repository = Path(plan["repository"])
for name, row in plan["source_inventory"].items():
    if hashlib.sha256((repository / name).read_bytes()).hexdigest() != row["sha256"]:
        raise SystemExit("Changed frozen source: " + name)
for name, digest in plan["source_archives"].items():
    if hashlib.sha256((ROOT / "source-cache" / name).read_bytes()).hexdigest() != digest:
        raise SystemExit("Changed locked source archive: " + name)
for name in ("temporary", "logs"):
    (ROOT / name).mkdir(exist_ok=True)
os.environ.update(plan["environment"])
sys.path[:0] = [str(repository / "packages/bijux-pollenomics-dev/src"), str(repository / "packages/bijux-pollenomics-lra/src")]
from bijux_pollenomics_dev.lra_validation import live_reference
from bijux_pollenomics_dev.lra_validation.live_reference_comparison import summarize

assert Path(live_reference.__file__).resolve().is_relative_to(repository)
assert subprocess.check_output(("git", "rev-parse", "HEAD"),cwd=repository,text=True).strip() == plan["candidate"]
start = time.monotonic()
deadline = start + plan["resources"]["wall_seconds"]
original_bounded = live_reference.run_bounded_argv

def deadline_bounded(command, *, cwd, timeout_seconds, **kwargs):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Native reference aggregate deadline reached")
    return original_bounded(command,cwd=cwd,timeout_seconds=min(timeout_seconds, remaining),**kwargs)

live_reference.run_bounded_argv = deadline_bounded

def host_inventory():
    result = {}
    for package, directory in plan["host_package_paths"].items():
        base = Path(directory)
        for p in sorted(base.rglob("*")):
            if p.is_symlink():
                result[package + "/" + p.relative_to(base).as_posix()] = {"symlink": os.readlink(p), "resolved_sha256": hashlib.sha256(p.resolve().read_bytes()).hexdigest() if p.resolve().is_file() else None}
            elif p.is_file():
                result[package + "/" + p.relative_to(base).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in plan["runtime_files"]:
        result[p] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return result

before = host_inventory()
(ROOT / "host-before.json").write_text(json.dumps(before,indent=2)+"\n")
terminal = {"candidate":plan["candidate"],"plan_sha256":hashlib.sha256(PLAN.read_bytes()).hexdigest(),"status":"running","release_certificate":False}
code = 1
try:
    native = live_reference.execute(repository,ROOT / "native",Path(plan["r"]),Path(plan["rscript"]),Path(plan["fortran"]),ROOT / "source-cache")
    comparison = summarize(repository,ROOT / "native",repository / "docs/report/method-certification/original-r-reference/reference-bundle",ROOT / "comparison",ROOT / "source-cache")
    after = host_inventory()
    (ROOT / "host-after.json").write_text(json.dumps(after,indent=2)+"\n")
    if before != after:
        raise ValueError("Read-only native runtime/dependencies changed")
    for name,row in plan["source_inventory"].items():
        if hashlib.sha256((repository/name).read_bytes()).hexdigest()!=row["sha256"]:
            raise ValueError("Frozen native source changed")
    if comparison["current_core_passed"] != 43 or comparison["current_domains_passed"] != 23 or comparison["original_R_to_current_R_compared"] != 48:
        raise ValueError("Declared native comparison population differs")
    terminal.update(status="passed",exit_code=0,core_passed=43,domains_passed=23,original_vectors_compared=48,source_unchanged=True,host_unchanged=True)
    code = 0
except BaseException as error:
    terminal.update(status="failed",exit_code=1,error=type(error).__name__+": "+str(error))
finally:
    terminal["elapsed_seconds"] = time.monotonic()-start
    terminal["outputs_sha256"] = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for directory in (ROOT/"native",ROOT/"comparison") if directory.exists() for p in sorted(directory.rglob("*")) if p.is_file()}
    terminal["host_before_sha256"] = hashlib.sha256((ROOT/"host-before.json").read_bytes()).hexdigest()
    if (ROOT/"host-after.json").is_file():
        terminal["host_after_sha256"] = hashlib.sha256((ROOT/"host-after.json").read_bytes()).hexdigest()
    (ROOT/"terminal.json").write_text(json.dumps(terminal,indent=2)+"\n")
print(json.dumps({k:terminal[k] for k in ("status","exit_code","elapsed_seconds")},sort_keys=True))
raise SystemExit(code)
