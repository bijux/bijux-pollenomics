"""Install only missing locked R dependencies and execute the original oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.request import urlopen

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv
from bijux_pollenomics_dev.ci.lra_reference.sources import verify_archive


def execute(
    repository: Path,
    output: Path,
    r: Path,
    rscript: Path,
    fortran: Path,
    source_cache: Path | None = None,
) -> dict[str, Any]:
    """Use exact package sources in an isolated library, recording native runtime."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Reference output must be absent")
    output.mkdir(parents=True)
    library = output / "library"
    library.mkdir()
    cache = output / "sources"
    cache.mkdir()
    lock_path = repository / "configs/ci/lra-r-source-lock.v1.json"
    lock = json.loads(lock_path.read_text())
    current_inputs = sorted(
        set((repository / "packages/bijux-pollenomics-lra/src").rglob("*.py"))
        | set(
            (
                repository / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle"
            ).rglob("*")
        )
        | {Path(__file__), lock_path, repository / lock["reference"]["repository_path"]}
    )
    input_hashes = {
        path.relative_to(repository).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in current_inputs
        if path.is_file() and "__pycache__" not in path.parts
    }
    report: dict[str, Any] = {
        "schema_version": "native-r-oracle-execution.1",
        "status": "running",
        "commands": [],
        "sources": [],
        "current_inputs_sha256": input_hashes,
    }
    environment = dict(
        R_LIBS_USER=str(library),
        R_LIBS_SITE="",
        R_ENVIRON_USER="/dev/null",
        R_PROFILE_USER="/dev/null",
        PYTHONDONTWRITEBYTECODE="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        NUMEXPR_NUM_THREADS="1",
        VECLIB_MAXIMUM_THREADS="1",
        TZ="UTC",
        LANG="C",
        LC_ALL="C",
        PATH=str(rscript.parent) + os.pathsep + os.environ.get("PATH", os.defpath),
    )

    def save() -> None:
        (output / "receipt.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )

    def command(name: str, argv: tuple[str, ...], timeout: int = 300) -> bytes:
        result = run_bounded_argv(
            ("/usr/bin/env", *(k + "=" + v for k, v in environment.items()), *argv),
            cwd=output,
            timeout_seconds=timeout,
        )
        (output / (name + ".stdout.log")).write_bytes(result.stdout)
        (output / (name + ".stderr.log")).write_bytes(result.stderr)
        report["commands"].append(
            {
                "name": name,
                "argv": list(result.command),
                "exit_code": result.returncode,
                "timed_out": result.timed_out,
                "duration_seconds": result.duration_seconds,
            }
        )
        save()
        if result.returncode or result.timed_out:
            raise RuntimeError("Native R reference command failed: " + name)
        return result.stdout

    try:
        inventory_code = 'p<-installed.packages();write.table(p[,c("Package","Version")],row.names=FALSE,col.names=FALSE,quote=FALSE,sep="\\t")'
        installed = dict(
            line.split("\t")
            for line in command(
                "initial-installed", (str(rscript), "--vanilla", "-e", inventory_code)
            )
            .decode()
            .strip()
            .splitlines()
        )
        version = (
            command(
                "runtime",
                (str(rscript), "--vanilla", "-e", "cat(as.character(getRversion()))"),
            )
            .decode()
            .strip()
        )
        if version != lock["runtime_policy"]["r_version"]:
            raise ValueError("Local R version differs from lock")
        for name, expected in lock["base_packages"].items():
            if installed.get(name) != expected:
                raise ValueError("Base R package differs: " + name)
        report.update(
            r_version=version,
            rscript_sha256=hashlib.sha256(rscript.resolve().read_bytes()).hexdigest(),
            lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
            initial_installed_versions=installed,
        )
        libfortran = Path(
            subprocess.check_output(
                (str(fortran), "-print-file-name=libgfortran.dylib"), text=True
            ).strip()
        ).resolve()
        if not libfortran.is_file():
            raise ValueError("Fortran runtime library absent")
        makevars = output / "Makevars"
        makevars.write_text(
            f"FC = {fortran}\nF77 = {fortran}\nFLIBS = -L{libfortran.parent} -lgfortran -lquadmath\n"
        )
        environment["R_MAKEVARS_USER"] = str(makevars)
        report["makevars_sha256"] = hashlib.sha256(makevars.read_bytes()).hexdigest()
        report["fortran_runtime_sha256"] = hashlib.sha256(
            libfortran.read_bytes()
        ).hexdigest()
        packages = {row["package"]: row for row in lock["packages"]}
        for name in lock["install_order"]:
            row = packages[name]
            if name in installed:
                if installed[name] != row["version"]:
                    raise ValueError("Installed R dependency differs: " + name)
                continue
            target = cache / row["archive_filename"]
            custody = (
                None if source_cache is None else source_cache / row["archive_filename"]
            )
            if custody is None:
                with urlopen(row["url"], timeout=60) as response:
                    data = response.read(row["byte_count"] + 1)
            else:
                data = custody.read_bytes()
            if (
                len(data) != row["byte_count"]
                or hashlib.sha256(data).hexdigest() != row["sha256"]
            ):
                raise ValueError("Locked source differs: " + name)
            target.write_bytes(data)
            verify_archive(target, name, row["version"])
            report["sources"].append(
                {
                    "package": name,
                    "version": row["version"],
                    "url": row["url"],
                    "sha256": row["sha256"],
                    "byte_count": len(data),
                    "origin": "exact_private_source_cache"
                    if custody
                    else "verified_provider_download",
                }
            )
            command(
                "install-" + name,
                (str(r), "CMD", "INSTALL", "--library=" + str(library), str(target)),
                timeout=600,
            )
        reference = lock["reference"]
        archive = repository / reference["repository_path"]
        if hashlib.sha256(archive.read_bytes()).hexdigest() != reference["sha256"]:
            raise ValueError("Original DISQOVER source differs")
        command(
            "install-disqover",
            (str(r), "CMD", "INSTALL", "--library=" + str(library), str(archive)),
        )
        (library / "disqover/SOURCE_SHA256").write_text(reference["sha256"] + "\n")
        loaded = dict(
            line.split("\t")
            for line in command(
                "final-installed", (str(rscript), "--vanilla", "-e", inventory_code)
            )
            .decode()
            .strip()
            .splitlines()
        )
        for row in lock["packages"]:
            if loaded.get(row["package"]) != row["version"]:
                raise ValueError("Final dependency differs: " + row["package"])
        report["final_locked_versions"] = {name: loaded[name] for name in packages}
        runner = (
            repository
            / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_live_r.py"
        )
        command(
            "oracle",
            (
                sys.executable,
                str(runner),
                "--library",
                str(library),
                "--output",
                str(output / "oracle"),
            ),
            timeout=300,
        )
        domain_runner = runner.with_name("run_source_domains.py")
        command(
            "source-domains",
            (
                sys.executable,
                str(domain_runner),
                "--library",
                str(library),
                "--output",
                str(output / "source-domains"),
            ),
            timeout=300,
        )
        if any(
            hashlib.sha256((repository / path).read_bytes()).hexdigest() != digest
            for path, digest in input_hashes.items()
        ):
            raise ValueError(
                "Original R or current Python input changed during execution"
            )
        report.update(status="passed", fresh_R_executed=True, release_certificate=False)
    except BaseException as error:
        report.update(status="failed", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        save()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--r", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, required=True)
    parser.add_argument("--fortran", type=Path, required=True)
    parser.add_argument("--source-cache", type=Path)
    args = parser.parse_args()
    execute(
        args.repository,
        args.output,
        args.r,
        args.rscript,
        args.fortran,
        args.source_cache,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
