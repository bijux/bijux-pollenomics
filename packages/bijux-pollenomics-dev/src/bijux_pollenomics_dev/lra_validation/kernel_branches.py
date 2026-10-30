"""Compare two literal DISQOVER kernel branches without replaying old cohorts.

Thirty cases fix fall speed .03 m/s and wind speed 3 m/s across five methods.
Lake diameters 1999/2000/2001 m cross the source's 2 m/10 m integration step.
Peatland regionCutoff arguments 999999/1000000/1000001 m cross din-dout/din.
The latter argument is used literally, without resolving the source's differing
documentation and distance use. Source negatives, warnings and nonfinite return
values remain visible. Matching NaNs are source behavior, not finite success.
An explicit separate minimum-lake population checks one paired domain refusal
at diameter 5 m and two finite scalar comparisons at 6/7 m, without extending
the default 30-case population or counting a refusal as numerical success.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any
import warnings

import numpy as np
import scipy

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv
from bijux_pollenomics_dev.ci.lra_reference.sources import verify_archive
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra.dispersal import kernels, loess, rounding
from bijux_pollenomics_lra.models import errors, validation

METHODS = (
    "lsm unstable",
    "lsm unstable low",
    "gpm neutral",
    "gpm unstable",
    "1overd",
)
RTOL, ATOL = 1e-10, 3e-10
TIME_LIMIT = 60.0
OUTPUT_LIMIT = 1024 * 1024
LOCK = "configs/ci/lra-r-source-lock.v1.json"
DEFAULT_POPULATION = "kernel-boundaries"
MINIMUM_LAKE_POPULATION = "minimum-lake-diameter"
R_DOMAIN_ERROR = "wrong sign in 'by' argument"
PYTHON_DOMAIN_ERROR = "ValidationError: The source lake integration requires a basin diameter of at least 6 m"
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


@dataclass(frozen=True)
class KernelCase:
    case_id: str
    basin: str
    diameter_m: int
    region_cutoff_argument_m: int
    method: str
    fall_speed_m_s: float = 0.03
    wind_speed_m_s: int = 3


def cases(population: str = DEFAULT_POPULATION) -> tuple[KernelCase, ...]:
    """The source-derived matrix is fixed before any numerical evaluation."""
    if population == MINIMUM_LAKE_POPULATION:
        return tuple(
            KernelCase(
                f"lake-d{d}-c100000-gpm_neutral", "lake", d, 100000, "gpm neutral"
            )
            for d in (5, 6, 7)
        )
    if population != DEFAULT_POPULATION:
        raise ValueError("Unknown kernel population")
    return tuple(
        KernelCase(
            f"{basin}-d{diameter}-c{cutoff}-{method.replace(' ', '_')}",
            basin,
            diameter,
            cutoff,
            method,
        )
        for basin, settings in (
            ("lake", tuple((d, 100000) for d in (1999, 2000, 2001))),
            ("peatland", tuple((100, c) for c in (999999, 1000000, 1000001))),
        )
        for diameter, cutoff in settings
        for method in METHODS
    )


def _kind(value: float) -> str:
    return (
        "nan"
        if math.isnan(value)
        else "+inf"
        if value == math.inf
        else "-inf"
        if value == -math.inf
        else "finite"
    )


def compare(reference: str, actual: float) -> dict[str, Any]:
    """Convert original decimal tokens correctly; compare unchanged tolerances."""
    if reference not in {"NA", "NaN", "Inf", "-Inf"} and not _NUMBER.fullmatch(
        reference
    ):
        raise ValueError("Malformed R numeric token")
    expected = math.nan if reference in {"NA", "NaN"} else float(reference)
    if math.isinf(expected) and reference not in {"Inf", "-Inf"}:
        raise ValueError("Overflowing R decimal token")
    rk, pk = _kind(expected), _kind(actual)
    finite = rk == pk == "finite"
    residual = abs(expected - actual) if finite else 0.0
    return {
        "r_kind": rk,
        "python_kind": pk,
        "absolute_residual": residual if finite else "",
        "relative_residual_to_python": (
            residual / abs(actual) if finite and actual != 0 else ""
        ),
        "passed": rk == pk and (not finite or residual <= ATOL + RTOL * abs(actual)),
    }


def python_values(
    deadline: float, population: str = DEFAULT_POPULATION
) -> list[dict[str, Any]]:
    values = []
    for case in cases(population):
        if time.monotonic() >= deadline:
            raise TimeoutError("Kernel comparison exceeded its total deadline")
        row: dict[str, Any] = {"status": "error", "value": "", "error": ""}
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter("always")
            try:
                value = kernels.DispersalFactorK(
                    case.fall_speed_m_s,
                    case.basin,
                    case.diameter_m,
                    case.method,
                    case.region_cutoff_argument_m,
                    case.wind_speed_m_s,
                )
                if (
                    np.asarray(value).shape != ()
                    or np.asarray(value).dtype.kind not in "fi"
                ):
                    raise ValueError("Python kernel did not return one numeric scalar")
                row.update(status="returned", value=float(value))
            except (ValueError, ArithmeticError) as error:
                row["error"] = f"{type(error).__name__}: {error}"
        row["warnings"] = " | ".join(str(item.message) for item in observed)
        values.append(row)
    return values


def r_script(
    library: Path,
    output: Path,
    lock: dict[str, Any],
    population: str = DEFAULT_POPULATION,
) -> str:
    """Call the installed original function; never copy or redefine its body."""
    literal = json.dumps
    # DESCRIPTION versions are literal lock identities. numeric_version display
    # normalizes hyphens to dots and cannot authenticate those original strings.
    base = ";".join(
        f'stopifnot(packageDescription({literal(k)},fields="Version")=={literal(v)})'
        for k, v in lock["base_packages"].items()
    )
    deps = ";".join(
        f'stopifnot(packageDescription({literal(p["package"])},fields="Version")=={literal(p["version"])})'
        for p in lock["packages"]
    )
    calls = "\n".join(
        "run_case("
        + ",".join(
            (
                literal(c.case_id),
                literal(c.basin),
                str(c.diameter_m),
                str(c.region_cutoff_argument_m),
                literal(c.method),
            )
        )
        + ")"
        for c in cases(population)
    )
    native_contract = 'all(result$status=="returned")'
    if population == MINIMUM_LAKE_POPULATION:
        native_contract = (
            'identical(result$status,c("error","returned","returned")) && '
            'result$length[1]==0 && result$value[1]=="" && '
            f"result$error[1]=={literal(R_DOMAIN_ERROR)} && "
            "all(is.finite(as.numeric(result$value[2:3])))"
        )
    return f"""options(digits=17,warn=1)
library_path <- {literal(str(library))}
out <- {literal(str(output))}
.libPaths(c(library_path,.libPaths()))
stopifnot(as.character(getRversion())=={literal(lock["runtime_policy"]["r_version"])})
{base}
{deps}
loadNamespace("disqover",lib.loc=library_path)
package_path <- getNamespaceInfo(asNamespace("disqover"),"path")
stopifnot(normalizePath(package_path)==normalizePath(file.path(library_path,"disqover")))
stopifnot(packageDescription("disqover",lib.loc=library_path,fields="Version")=="0.9.14")
stopifnot(readLines(file.path(package_path,"SOURCE_SHA256"),warn=FALSE)[1]=={literal(lock["reference"]["sha256"])})
cat("R_VERSION=",as.character(getRversion()),"\\nPACKAGE_PATH=",package_path,"\\n",sep="")
writeLines(capture.output(sessionInfo()),file.path(out,"r-session.txt"))
rows <- list()
run_case <- function(id,basin,diameter,cutoff,method) {{
  messages <- character(); error <- ""; value <- NULL
  value <- tryCatch(withCallingHandlers(
    disqover::DispersalFactorK(.03,basin,diameter,method,cutoff,3),
    warning=function(w){{messages <<- c(messages,conditionMessage(w));invokeRestart("muffleWarning")}}),
    error=function(e){{error <<- conditionMessage(e);NULL}})
  ok <- error=="" && is.null(dim(value)) && (is.double(value)||is.integer(value)) && length(value)==1
  if(!ok && error=="")error <- "Kernel did not return one numeric scalar"
  token <- if(!ok)"" else if(is.nan(value))"NaN" else if(is.na(value))"NA" else sprintf("%.17g",value)
  rows[[length(rows)+1]] <<- data.frame(case_id=id,status=if(ok)"returned" else "error",
    length=length(value),value=token,warnings=paste(messages,collapse=" | "),error=error)
}}
{calls}
result <- do.call(rbind,rows)
write.csv(result,file.path(out,"r-values.csv"),row.names=FALSE,na="NA")
quit(status=if({native_contract})0L else 1L)
"""


def read_r(path: Path, population: str = DEFAULT_POPULATION) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != [
            "case_id",
            "status",
            "length",
            "value",
            "warnings",
            "error",
        ]:
            raise ValueError("R output columns differ")
        rows = list(reader)
    if [row["case_id"] for row in rows] != [case.case_id for case in cases(population)]:
        raise ValueError("R output population/order differs")
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("R output row shape differs")
    return rows


def comparison_rows(
    raw: list[dict[str, str]],
    python: list[dict[str, Any]],
    population: str = DEFAULT_POPULATION,
) -> list[dict[str, Any]]:
    result = []
    for case, r, p in zip(cases(population), raw, python, strict=True):
        row = asdict(case) | {
            "r_value": r["value"],
            "python_value": repr(p["value"]),
            "r_status": r["status"],
            "r_length": r["length"],
            "python_status": p["status"],
            "r_warnings": r["warnings"],
            "python_warnings": p["warnings"],
            "r_error": r["error"],
            "python_error": p["error"],
            "r_kind": "",
            "python_kind": "",
            "absolute_residual": "",
            "relative_residual_to_python": "",
            "passed": False,
        }
        if r["case_id"] != case.case_id:
            raise ValueError("R case identity differs")
        refusal = population == MINIMUM_LAKE_POPULATION and case.diameter_m == 5
        if refusal:
            row["passed"] = (
                r["status"] == p["status"] == "error"
                and r["length"] == "0"
                and r["value"] == p["value"] == ""
                and r["error"] == R_DOMAIN_ERROR
                and p["error"] == PYTHON_DOMAIN_ERROR
            )
        elif (
            r["status"] == p["status"] == "returned"
            and r["length"] == "1"
            and not r["error"]
        ):
            row.update(compare(r["value"], p["value"]))
        if population == MINIMUM_LAKE_POPULATION:
            if not refusal:
                row["passed"] = (
                    row["passed"] and row["r_kind"] == row["python_kind"] == "finite"
                )
            expected = "paired_refusal" if refusal else "finite_comparison"
            row.update(
                expected_outcome=expected,
                outcome=expected if row["passed"] else "failed",
            )
        result.append(row)
    return result


def _source(repository: Path) -> tuple[str, dict[str, Any]]:
    root = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
    modules = (
        (
            sys.modules[__name__],
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/kernel_branches.py",
        ),
        (kernels, root + "dispersal/kernels.py"),
        (loess, root + "dispersal/loess.py"),
        (rounding, root + "dispersal/rounding.py"),
        (errors, root + "models/errors.py"),
        (validation, root + "models/validation.py"),
    )
    paths = [LOCK, root + "resources/data/lsm_models.npz"]
    for module, relative in modules:
        path = repository / relative
        if path.resolve(strict=True) != path or Path(module.__file__ or "") != path:
            raise ValueError("Canonical consumed kernel source required")
        paths.append(relative)
    lock = json.loads((repository / LOCK).read_text())
    ref = lock["reference"]
    if ref["package"] != "disqover" or ref["version"] != "0.9.14":
        raise ValueError("Original DISQOVER source profile required")
    archive = repository / ref["repository_path"]
    if (
        archive.resolve(strict=True) != archive
        or hashlib.sha256(archive.read_bytes()).hexdigest() != ref["sha256"]
    ):
        raise ValueError("Original source archive differs")
    verify_archive(archive, "disqover", "0.9.14")
    paths.append(ref["repository_path"])
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    subprocess.check_call(
        [*command, "ls-files", "--error-unmatch", "--", *paths],
        stdout=subprocess.DEVNULL,
        timeout=10,
    )
    subprocess.check_call(
        [*command, "diff", "--exit-code", revision, "--", *paths], timeout=10
    )
    return revision, lock


def execute(
    repository: Path,
    library: Path,
    rscript: Path,
    output: Path,
    population: str = DEFAULT_POPULATION,
) -> int:
    """Use one existing library/batch; preserve raw failures and guard actual source."""
    started = time.monotonic()
    deadline = started + TIME_LIMIT
    revision, lock = _source(repository)
    require_absent_artifact_output(repository, output)
    if library.resolve(strict=True) != library or not library.is_dir():
        raise ValueError("Physical shared R library required")
    output.mkdir()
    print(f"source_commit={revision} command={sys.orig_argv!r}", flush=True)
    print(
        f"python={platform.python_version()} numpy={np.__version__} scipy={scipy.__version__} platform={platform.platform()}",
        flush=True,
    )
    terminal = 1
    try:
        python = python_values(deadline, population)
        script = output / "oracle-command.R"
        script.write_text(r_script(library, output, lock, population))
        environment = {
            "R_LIBS_USER": str(library),
            "R_LIBS_SITE": "",
            "R_ENVIRON_USER": "/dev/null",
            "R_PROFILE_USER": "/dev/null",
            "TZ": "UTC",
            "LANG": "C",
            "LC_ALL": "C",
        }
        completed = run_bounded_argv(
            (
                "/usr/bin/env",
                *(f"{k}={v}" for k, v in environment.items()),
                str(rscript),
                "--vanilla",
                str(script),
            ),
            cwd=output,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
            max_output_bytes=OUTPUT_LIMIT // 4,
        )
        (output / "r-stdout.txt").write_bytes(completed.stdout)
        (output / "r-stderr.txt").write_bytes(completed.stderr)
        print(
            f"r_exit={completed.returncode} timed_out={completed.timed_out} r_seconds={completed.duration_seconds}",
            flush=True,
        )
        rows = comparison_rows(
            read_r(output / "r-values.csv", population), python, population
        )
        with (output / "comparison.csv").open("x", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(rows[0]), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        terminal = int(
            completed.returncode != 0
            or completed.timed_out
            or not all(row["passed"] for row in rows)
        )
        print(
            f"cases={len(rows)} passed={sum(row['passed'] for row in rows)} rtol={RTOL} atol={ATOL}",
            flush=True,
        )
        if population == MINIMUM_LAKE_POPULATION:
            print(
                f"population={population} numerical_matches={sum(r['outcome'] == 'finite_comparison' for r in rows)} "
                f"paired_refusals={sum(r['outcome'] == 'paired_refusal' for r in rows)}",
                flush=True,
            )
    except (ValueError, OSError, TimeoutError, RuntimeError) as error:
        print(f"failure={type(error).__name__}: {error}", flush=True)
    finally:
        try:
            if _source(repository) != (revision, lock):
                raise ValueError("Consumed source or raw reference changed")
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            terminal = 1
            print(f"source_stable=false failure={error}", flush=True)
        total_bytes = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        if total_bytes >= OUTPUT_LIMIT or time.monotonic() > deadline:
            terminal = 1
            print("failure=total output or time budget exceeded", flush=True)
        print(
            f"exit_code={terminal} elapsed_seconds={time.monotonic() - started} output_bytes={total_bytes}",
            flush=True,
        )
    return terminal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("repository", "library", "rscript", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument(
        "--population",
        choices=(DEFAULT_POPULATION, MINIMUM_LAKE_POPULATION),
        default=DEFAULT_POPULATION,
    )
    args = parser.parse_args()
    if args.repository.absolute().resolve(strict=True) != args.repository.absolute():
        raise ValueError("Physical repository required")
    raise SystemExit(
        execute(
            args.repository.absolute(),
            args.library.absolute(),
            args.rscript.absolute(),
            args.output.absolute(),
            args.population,
        )
    )


if __name__ == "__main__":
    main()
