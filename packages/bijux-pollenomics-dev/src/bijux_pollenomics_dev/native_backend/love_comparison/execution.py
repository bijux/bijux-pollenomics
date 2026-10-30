"""Frozen current-source R/Python LOVE fixture comparison and timing protocol.

One shared LOVEexample: one local/regional row, ten taxa, 36 rings, maximum
local ring ten, two deterministic repeats and 32 fixed candidates in each of
eight active calls. This is TEST-ONLY substituted R search, not RcppDE/SciPy
trajectory or convergence parity. Six source-undefined rings remain missing.
Use the established 3e-10 absolute + 1e-10 relative tolerance, exact labels,
parsed binary64 inputs, masks, selected indices and 256 search returns. Python
also performs eight mandatory solver certifications per public call.

Each engine performs one first and five warm complete wrapper calls in one
fresh process, with numerical threads one. Inputs are parsed before timings;
regional preparation, kernels, objective replay and summaries are inside them.
Report every sample, first/warm range/median, setup, export, whole worker wall
and whole-process peak RSS separately. The latter includes imports/setup and
is NOT an incremental allocation measurement; worker wall minus call time is
NOT a pure startup measurement. Source R uses millisecond elapsed resolution.
No isolated kernel speedup, C++ adoption, ecological or release claim follows.
Aggregate native deadline 120 seconds, output bound 16 MiB. Failed commands
and comparisons remain failed, with no retry, fallback or tolerance changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from statistics import median
import subprocess
import sys
import time
from typing import Any

from ...ci.atlas_media.process_execution import run_bounded_argv
from ...ci.report_rebuild.artifact_paths import require_absent_artifact_output
from ...ci.report_rebuild.source_paths import safe_source_file
from ..profiling import THREAD_VARIABLES
from . import comparison, inputs, worker

MODULE = "bijux_pollenomics_dev.native_backend.love_comparison"
PACKAGE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/love_comparison"
)
LRA = Path("packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra")
CONSUMED = (
    PACKAGE,
    LRA,
    inputs.REPLAY,
    inputs.SUPPORT,
    inputs.ARCHIVE,
    Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/profiling.py"
    ),
    Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/reference_replay.py"
    ),
)
MAX_BYTES = 16 * 1024**2
DEADLINE_SECONDS = 120


def revision(repository: Path) -> str:
    """Use Git for current code identity, never a historical whole-source pin."""
    from bijux_pollenomics_lra.api import run_love

    origin = Path(run_love.__code__.co_filename).resolve()
    if not origin.is_relative_to((repository / LRA).resolve()):
        raise ValueError("Current LOVE public function origin differs")
    for module in (sys.modules[__name__], inputs, comparison, worker):
        if module.__file__ is None:
            raise ValueError("Current LOVE comparison module has no origin")
        if (
            Path(module.__file__).resolve()
            != (repository / PACKAGE / Path(module.__file__).name).resolve()
        ):
            raise ValueError("Current LOVE comparison module origin differs")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=repository, text=True
        ).strip()

    for path in CONSUMED:
        if not git("ls-files", "--", path.as_posix()):
            raise ValueError("Current LOVE consumed source is untracked")
    paths = [str(path) for path in CONSUMED]
    if git("diff", "HEAD", "--name-only", "--", *paths) or git(
        "ls-files", "--others", "--exclude-standard", "--", *paths
    ):
        raise ValueError("Current LOVE consumed source must be committed and clean")
    return git("rev-parse", "HEAD")


def timing(samples: list[float]) -> dict[str, Any]:
    """Keep the first call distinct from the fixed five warm samples."""
    import math

    if len(samples) != 6 or any(not math.isfinite(v) or v < 0 for v in samples):
        raise ValueError("LOVE timing sample population differs")
    return {
        "samples_seconds": samples,
        "first_seconds": samples[0],
        "warm_median_seconds": median(samples[1:]),
        "warm_min_seconds": min(samples[1:]),
        "warm_max_seconds": max(samples[1:]),
    }


def peak_rss(stderr: str, system: str) -> int:
    """Native time reports bytes on Darwin and KiB on Linux."""
    pattern = (
        r"^\s*(\d+)\s+maximum resident set size\s*$"
        if system == "Darwin"
        else r"^\s*Maximum resident set size \(kbytes\):\s*(\d+)\s*$"
    )
    values = re.findall(pattern, stderr, re.MULTILINE)
    if system not in {"Darwin", "Linux"} or len(values) != 1:
        raise ValueError("Native process peak RSS is unavailable or ambiguous")
    return int(values[0]) * (1 if system == "Darwin" else 1024)


def unchanged(path: Path, digest: str) -> bool:
    """Missing evidence must fail integrity without erasing a native failure."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest() == digest
    except OSError:
        return False


def run(repository: Path, output: Path, library: Path, rscript: Path) -> dict[str, Any]:
    """Execute each native worker once, preserving terminal failures and raw outputs."""
    repository, library = repository.resolve(strict=True), library.resolve(strict=True)
    if any(os.environ.get(name) != "1" for name in THREAD_VARIABLES):
        raise ValueError("All numerical thread variables must be one")
    output = require_absent_artifact_output(repository, output)
    if library.is_relative_to(output) or output.is_relative_to(library):
        raise ValueError("LOVE output overlaps installed R library")
    source = revision(repository)
    replay = safe_source_file(
        repository, inputs.REPLAY.as_posix(), "Original LOVE R replay"
    )
    support = safe_source_file(
        repository, inputs.SUPPORT.as_posix(), "Original R oracle support"
    )
    archive = safe_source_file(
        repository, inputs.ARCHIVE.as_posix(), "DISQOVER archive"
    )
    timed = safe_source_file(
        repository, (PACKAGE / "timed_replay.R").as_posix(), "LOVE timing entry"
    )
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    output.mkdir()
    started = time.perf_counter()
    input_started = time.perf_counter()
    identities = inputs.write(output / "input")
    export_seconds = time.perf_counter() - input_started
    report: dict[str, Any] = {
        "source_commit": source,
        "observed_python": sys.version,
        "observed_platform": platform.platform(),
        "observed_machine": platform.machine(),
        "observed_system": platform.system(),
        "rss_platform_units": "bytes"
        if platform.system() == "Darwin"
        else "KiB converted to bytes",
        "status": "running",
        "commands": [],
        "input_sha256": identities,
        "source_archive_sha256": archive_sha,
        "input_export_seconds": export_seconds,
        "thread_settings": {name: os.environ[name] for name in THREAD_VARIABLES},
    }
    system = platform.system()
    if system not in {"Darwin", "Linux"}:
        raise ValueError("LOVE comparison RSS requires Darwin or Linux")
    prefix = ("/usr/bin/time", "-l" if system == "Darwin" else "-v")
    commands = {
        "python": (
            sys.executable,
            "-B",
            "-m",
            MODULE + ".worker",
            "--input",
            str(output / "input"),
            "--output",
            str(output),
        ),
        "r": (
            str(rscript),
            "--vanilla",
            str(timed),
            str(output / "input"),
            str(output),
            str(library),
            archive_sha,
            str(support),
            str(replay),
        ),
    }
    try:
        for name, command in commands.items():
            remaining = DEADLINE_SECONDS - (time.perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("LOVE comparison aggregate deadline exceeded")
            result = run_bounded_argv(
                prefix + command,
                cwd=repository,
                timeout_seconds=remaining,
                max_output_bytes=4 * 1024**2,
            )
            (output / f"{name}-stdout.txt").write_bytes(result.stdout)
            (output / f"{name}-stderr.txt").write_bytes(result.stderr)
            report["commands"].append(
                {
                    "engine": name,
                    "argv": result.command,
                    "exit_code": result.returncode,
                    "timed_out": result.timed_out,
                    "whole_worker_seconds": result.duration_seconds,
                }
            )
            if result.returncode != 0 or result.timed_out:
                raise RuntimeError(f"Native LOVE {name} worker failed")
            report[name] = {
                "peak_process_rss_bytes": peak_rss(result.stderr.decode(), system),
                "whole_worker_seconds": result.duration_seconds,
            }
            if (
                sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
                > MAX_BYTES
            ):
                raise ValueError("LOVE comparison exceeds sixteen MiB")
        python = json.loads((output / "python-stdout.txt").read_bytes())
        report["python"].update(python, timing=timing(python["call_seconds"]))
        native_times = inputs.frame(output / "timings.csv")
        if native_times["call"].tolist() != list(range(1, 7)):
            raise ValueError("R complete-call timing identities differ")
        report["r"].update(
            timing=timing(native_times.seconds.tolist()),
            stages=inputs.frame(output / "stages.csv").to_dict(orient="records"),
        )
        if (
            output / "all-undefined-refusal.txt"
        ).read_text().strip() != "refused: all replay candidates invalid":
            raise ValueError("R all-undefined replay refusal differs")
        report["r"]["all_undefined_refusal"] = (
            (output / "all-undefined-refusal.txt").read_text().strip()
        )
        report["comparison"] = comparison.compare(output, output / "input")
        report["status"] = (
            "passed"
            if report["comparison"]["passed"]
            else "numerical_comparison_failed"
        )
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        try:
            report["source_stable"] = revision(repository) == source
        except (ValueError, subprocess.CalledProcessError) as exc:
            report["source_stable"] = False
            report["source_guard_error"] = str(exc)
        failed_inputs = [
            name
            for name, digest in identities.items()
            if not unchanged(output / "input" / name, digest)
        ]
        report["inputs_stable"] = not failed_inputs
        report["archive_stable"] = unchanged(archive, archive_sha)
        report["integrity_failures"] = ["input/" + name for name in failed_inputs]
        if not report["archive_stable"]:
            report["integrity_failures"].append(inputs.ARCHIVE.as_posix())
        if not all(
            report[key] for key in ("source_stable", "inputs_stable", "archive_stable")
        ):
            report["status"] = "source_or_input_changed"
        (output / "report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
    if report["status"] != "passed":
        raise ValueError("Current LOVE comparison did not pass")
    return report


def main() -> int:
    """Run the declared matched-wrapper comparison command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, default=Path("/usr/local/bin/Rscript"))
    args = parser.parse_args()
    report = run(args.repository, args.output, args.library, args.rscript)
    print(
        json.dumps(
            {"status": report["status"], "source_commit": report["source_commit"]}
        )
    )
    return 0
