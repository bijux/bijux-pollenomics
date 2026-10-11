#!/usr/bin/env python3
"""Run the independent R/DISQOVER oracle.

Missing R, a missing reference installation, setup failure, or timeout is
reported as ``blocked`` and returns exit code 2. It is never converted into a
passing skip.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests/reference")]

from lra_oracle.cases import build_cases, r_literal  # noqa: E402
from lra_oracle.prospective import (  # noqa: E402
    load_prospective_optimized_declaration,
)
from lra_oracle.scope import R_COMPATIBLE_API  # noqa: E402

ARCHIVE = ROOT / "vendor" / "disqover_0.9.14.tar.gz"


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "live_r")
    parser.add_argument("--library", type=Path, default=ROOT / ".r-library")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args(argv)

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    setup, cases = build_cases(output / "inputs")
    prospective = load_prospective_optimized_declaration()
    source_hash = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    manifest = [
        {
            "id": f"C{index:04d}",
            "name": case.name,
            "api": case.api,
            "mode": case.mode,
            "rtol": case.rtol,
            "atol": case.atol,
            "exact_indices": list(case.exact_indices),
            "values": len(case.expected),
        }
        for index, case in enumerate(cases)
    ]
    expected_arrays: dict[str, Any] = {
        str(item["id"]): case.expected
        for item, case in zip(manifest, cases, strict=True)
    }
    np.savez_compressed(output / "python_expected_not_R_goldens.npz", **expected_arrays)
    _write_json(output / "case_manifest.json", manifest)

    script = [
        "options(digits=17,warn=1)",
        f".libPaths(c({r_literal(str(args.library.resolve()))},.libPaths()))",
        'if(!requireNamespace("disqover",quietly=TRUE))stop("Reference package not installed")',
        'stopifnot(as.character(packageVersion("disqover")) == "0.9.14")',
        f'stopifnot(readLines(system.file("SOURCE_SHA256",package="disqover"),warn=FALSE)[1] == {r_literal(source_hash)})',
        f"source({r_literal(str(ROOT / 'tests/reference/lra_oracle' / 'r_support.R'))})",
        f"outdir <- {r_literal(str(output))}",
        'writeLines(capture.output(sessionInfo()),file.path(outdir,"R_session_info.txt"))',
        "status <- data.frame(id=character(),status=character(),message=character())",
        """run_case <- function(id,expression) {
          tryCatch({
            value<-eval(expression,envir=.GlobalEnv)
            if(is.list(value))value<-flatten_numeric(value)
            if(is.character(value)){
              kind<-"character";val<-as.vector(value)
            }else{
              kind<-"numeric";val<-as.numeric(value)
              val<-ifelse(is.na(val),"NaN",sprintf("%.17g",val))
            }
            write.csv(data.frame(kind=rep(kind,length(val)),value=val),file.path(outdir,paste0(id,".csv")),row.names=FALSE,na="NaN")
            status[nrow(status)+1L,]<<-list(id,"completed","")
          },error=function(e){status[nrow(status)+1L,]<<-list(id,"error",conditionMessage(e))})
        }""",
        *setup,
    ]
    for item, case in zip(manifest, cases, strict=True):
        script.append(f"run_case({r_literal(item['id'])},quote({case.expression}))")
    script.extend(
        [
            'write.csv(status,file.path(outdir,"R_case_status.csv"),row.names=FALSE)',
            'quit(status=if(all(status$status=="completed"))0L else 1L)',
        ]
    )
    (output / "oracle.R").write_text("\n".join(script) + "\n", encoding="utf-8")

    report: dict[str, object] = {
        "schema_version": "1.0.0",
        "oracle": "disqover",
        "source_version": "0.9.14",
        "source_archive_sha256": source_hash,
        "python": platform.python_version(),
        "prepared_cases": len(cases),
        "source_compatible_api": list(R_COMPATIBLE_API),
        "prospective_optimized_love": {
            "declaration_id": prospective.declaration_id,
            "declaration_sha256": prospective.declaration_sha256,
            "case_input_sha256": {
                case.case_id: case.input_sha256 for case in prospective.cases
            },
            "rtol": prospective.rtol,
            "atol": prospective.atol,
            "stochastic_optimizer_trajectory": "excluded",
        },
        "api_covered_by_prepared_cases": sorted({case.api for case in cases}),
        "live_R_executed": False,
        "passed_cases": 0,
        "failed_cases": 0,
        "scope_notes": [
            "Supplied draws isolate stochastic wrapper mathematics from RNG-stream differences.",
            "Candidate replay isolates LOVE objective/wrapper parity from optimizer trajectories.",
            "A pass does not establish ecological validity against held-out observations.",
        ],
    }

    def save_report() -> None:
        _write_json(output / "report.json", report)

    if args.prepare_only:
        report["status"] = "prepared_not_executed"
        save_report()
        print(f"Prepared {len(cases)} cases; R was not executed.")
        return 0

    rscript = shutil.which("Rscript")
    if rscript is None:
        report.update(
            status="blocked",
            reason="Rscript is not installed; no live R parity is established.",
        )
        save_report()
        print(report["reason"])
        return 2

    for old in [
        *output.glob("C[0-9][0-9][0-9][0-9].csv"),
        output / "R_case_status.csv",
        output / "R_session_info.txt",
        output / "R_stdout.log",
        output / "R_stderr.log",
    ]:
        old.unlink(missing_ok=True)

    start = time.monotonic()
    try:
        completed = subprocess.run(
            [rscript, "--vanilla", str(output / "oracle.R")],
            env=dict(os.environ, R_LIBS_USER=str(args.library.resolve())),
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        report.update(status="blocked", reason=str(error))
        save_report()
        return 2

    (output / "R_stdout.log").write_text(completed.stdout, encoding="utf-8")
    (output / "R_stderr.log").write_text(completed.stderr, encoding="utf-8")
    report.update(
        live_R_executed=True,
        elapsed_seconds=time.monotonic() - start,
        R_exit_code=completed.returncode,
    )
    status_path = output / "R_case_status.csv"
    if not status_path.exists():
        report.update(
            status="blocked",
            reason="R did not finish oracle setup; inspect R_stderr.log.",
        )
        save_report()
        return 2

    status = pd.read_csv(status_path, keep_default_na=False).set_index("id")
    results: list[dict[str, object]] = []
    passed_cases = 0
    failed_cases = 0
    for item, case in zip(manifest, cases, strict=True):
        case_result: dict[str, object] = {
            "id": item["id"],
            "name": case.name,
            "api": case.api,
            "mode": case.mode,
        }
        try:
            case_id = str(item["id"])
            if (
                case_id not in status.index
                or status.loc[case_id, "status"] != "completed"
            ):
                message = (
                    status.loc[case_id, "message"]
                    if case_id in status.index
                    else "R output missing"
                )
                raise AssertionError(message)
            raw = pd.read_csv(
                output / f"{case_id}.csv", keep_default_na=False, dtype=str
            )
            if case.expected.dtype.kind in "USO":
                actual = raw["value"].astype(str).to_numpy()
                np.testing.assert_array_equal(actual, case.expected.astype(str))
            else:
                actual = pd.to_numeric(
                    raw["value"].replace({"NaN": np.nan, "NA": np.nan}),
                    errors="raise",
                ).to_numpy(float)
                expected = case.expected.astype(float)
                if actual.shape != expected.shape:
                    raise AssertionError(
                        f"shape mismatch: actual {actual.shape}, expected {expected.shape}"
                    )
                exact = np.asarray(case.exact_indices, dtype=int)
                if exact.size:
                    if np.any(exact < 0) or np.any(exact >= len(expected)):
                        raise AssertionError("Exact comparison index is out of bounds")
                    np.testing.assert_array_equal(actual[exact], expected[exact])
                approximate = np.ones(len(expected), dtype=bool)
                approximate[exact] = False
                if approximate.any():
                    np.testing.assert_allclose(
                        actual[approximate],
                        expected[approximate],
                        rtol=case.rtol,
                        atol=case.atol,
                        equal_nan=True,
                    )
                finite = np.isfinite(actual) & np.isfinite(case.expected)
                errors = np.abs(actual[finite] - case.expected[finite])
                case_result["max_abs_error"] = (
                    float(errors.max()) if errors.size else 0.0
                )
            case_result["status"] = "passed"
            passed_cases += 1
        except (AssertionError, ValueError, KeyError, OSError) as error:
            case_result.update(status="failed", reason=str(error))
            failed_cases += 1
        results.append(case_result)

    report.update(
        status="passed"
        if failed_cases == 0 and completed.returncode == 0
        else "failed",
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        cases=results,
    )
    save_report()
    print(
        f"Live R: {report['passed_cases']} passed, {report['failed_cases']} failed; "
        f"{report['status']}."
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
