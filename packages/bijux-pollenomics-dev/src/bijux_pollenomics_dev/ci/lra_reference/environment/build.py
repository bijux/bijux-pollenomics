"""Build the exact locked R runtime locally; package sources are installed separately."""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import tarfile
from typing import Any

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv

from ..contracts import ReferenceRefusal, load_lock
from ..evidence import file_inventory
from ..paths import exclusive_outputs, local_path
from ..sources import sha256, verify_sources


def build_runtime(
    *, lock_path: Path, source_cache: Path, repository: Path, prefix: Path, output: Path
) -> dict[str, Any]:
    """Build the pinned R source into an exclusive local runtime prefix."""
    lock_path, source_cache, repository, prefix, output = (
        local_path(path)
        for path in (lock_path, source_cache, repository, prefix, output)
    )
    lock = load_lock(lock_path)
    sources = verify_sources(lock, source_cache, repository)
    exclusive_outputs(
        (prefix, output),
        (
            lock_path,
            source_cache,
            repository / lock.payload["reference"]["repository_path"],
        ),
    )
    output.mkdir(parents=True)
    home = output / "home"
    home.mkdir()
    receipt: dict[str, Any] = {
        "schema_version": "lra-r-runtime.v1",
        "status": "incomplete",
        "lock_sha256": sha256(lock_path),
        "source_archive_sha256": sha256(sources["R"]),
        "source_version": lock.payload["r"]["version"],
        "prefix": str(prefix),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "steps": [],
    }
    environment = (
        "/usr/bin/env",
        "-i",
        f"HOME={home}",
        f"PATH={os.environ.get('PATH', os.defpath)}",
        "MAKEFLAGS=-j1",
        "OMP_NUM_THREADS=1",
        "OPENBLAS_NUM_THREADS=1",
        "MKL_NUM_THREADS=1",
        "TZ=UTC",
        "LANG=C",
        "LC_ALL=C",
    )

    def command(
        name: str, argv: tuple[str, ...], cwd: Path, timeout: int = 3600
    ) -> bytes:
        result = run_bounded_argv(
            (*environment, *argv), cwd=cwd, timeout_seconds=timeout
        )
        (output / (name + ".stdout.log")).write_bytes(result.stdout)
        (output / (name + ".stderr.log")).write_bytes(result.stderr)
        receipt["steps"].append(
            {
                "step": name,
                "argv": list(result.command),
                "cwd": str(cwd),
                "exit_code": result.returncode,
                "timed_out": result.timed_out,
                "duration_seconds": result.duration_seconds,
            }
        )
        (output / "progress.json").write_text(json.dumps(receipt, indent=2) + "\n")
        if result.returncode or result.timed_out:
            raise ReferenceRefusal("R source build failed: " + name)
        return result.stdout

    try:
        for tool in ("cc", "c++", "gfortran", "make", "pkg-config"):
            executable = shutil.which(tool)
            if executable is None:
                raise ReferenceRefusal(
                    "Required runtime build tool is missing: " + tool
                )
            command(
                "tool-" + tool.replace("+", "x"), (executable, "--version"), output, 30
            )
        extracted = output / "source"
        extracted.mkdir()
        with tarfile.open(sources["R"]) as archive:
            archive.extractall(extracted, filter="data")
        source = extracted / ("R-" + lock.payload["r"]["version"])
        work = output / "build"
        work.mkdir()
        command(
            "configure",
            (
                str(source / "configure"),
                "--prefix=" + str(prefix),
                *lock.payload["runtime_policy"]["r_configure_args"],
            ),
            work,
        )
        command("build", ("make", "-j1"), work)
        command("install", ("make", "-j1", "install"), work)
        actual = (
            command(
                "runtime",
                (
                    str(prefix / "bin/Rscript"),
                    "--vanilla",
                    "-e",
                    "cat(as.character(getRversion()))",
                ),
                output,
                30,
            )
            .decode()
            .strip()
        )
        if actual != lock.payload["r"]["version"]:
            raise ReferenceRefusal("Built R version differs from the source lock")
        command(
            "compiler-config",
            (str(prefix / "bin/R"), "CMD", "config", "--all"),
            output,
            30,
        )
        if (
            sha256(lock_path) != receipt["lock_sha256"]
            or sha256(sources["R"]) != receipt["source_archive_sha256"]
        ):
            raise ReferenceRefusal("R build inputs changed during execution")
        receipt["runtime_files"] = file_inventory(prefix)
        receipt["Rscript_sha256"] = sha256(prefix / "bin/Rscript")
        receipt["status"] = "passed"
    except BaseException as error:
        receipt.update(status="failed", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
