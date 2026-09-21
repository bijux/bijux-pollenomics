"""Install verified local source archives into an exclusive private R library."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
from typing import Any

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv

from ..contracts import ReferenceRefusal, load_lock, read_json
from ..evidence import file_inventory
from ..paths import exclusive_outputs, local_path
from ..sources import sha256, verify_sources


def provision(
    *,
    lock_path: Path,
    source_cache: Path,
    repository: Path,
    library: Path,
    output: Path,
    r: Path,
    rscript: Path,
    pkg_config_path: Path | None = None,
    makevars: Path | None = None,
    runtime_receipt: Path | None = None,
) -> dict[str, Any]:
    """Install verified R sources into a private library and record their bytes."""
    lock_path, source_cache, repository, library, output = (
        local_path(path)
        for path in (lock_path, source_cache, repository, library, output)
    )
    lock = load_lock(lock_path)
    if lock.payload["runtime_policy"].get("package_configure_args") != {
        "stringi": ["--disable-icu-bundle", "--with-extra-cxxflags=-std=gnu++17"]
    }:
        raise ReferenceRefusal(
            "Source provisioning requires explicit offline package configuration"
        )
    sources = verify_sources(lock, source_cache, repository)
    if makevars is not None:
        sources["compiler_makevars"] = local_path(makevars)
    runtime_build = None
    if runtime_receipt is not None:
        sources["runtime_build_receipt"] = local_path(runtime_receipt)
        runtime_build = read_json(sources["runtime_build_receipt"].read_bytes())
        if (
            runtime_build.get("schema_version") != "lra-r-runtime.v1"
            or runtime_build.get("status") != "passed"
            or runtime_build.get("lock_sha256") != sha256(lock_path)
        ):
            raise ReferenceRefusal(
                "Successful matching R source-build receipt is required"
            )
        runtime_prefix = local_path(Path(runtime_build["prefix"]))
        if rscript != runtime_prefix / "bin/Rscript" or runtime_build.get(
            "runtime_files"
        ) != file_inventory(runtime_prefix):
            raise ReferenceRefusal("Built R runtime location or bytes differ")
    exclusive_outputs(
        (output, library),
        (
            lock_path,
            source_cache,
            *sources.values(),
        ),
    )
    output.mkdir(parents=True)
    steps: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema_version": "lra-r-provision.v1",
        "status": "incomplete",
        "lock_sha256": sha256(lock_path),
        "source_files": {
            name: {"path": str(path), "sha256": sha256(path)}
            for name, path in sources.items()
        },
        "library": str(library),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "steps": steps,
    }

    report["runtime_build"] = runtime_build

    def command(name: str, argv: tuple[str, ...], timeout: int = 600) -> bytes:
        completed = run_bounded_argv(argv, cwd=output, timeout_seconds=timeout)
        (output / (name + ".stdout.log")).write_bytes(completed.stdout)
        (output / (name + ".stderr.log")).write_bytes(completed.stderr)
        steps.append(
            {
                "step": name,
                "argv": list(completed.command),
                "exit_code": completed.returncode,
                "timed_out": completed.timed_out,
                "duration_seconds": completed.duration_seconds,
            }
        )
        (output / "progress.json").write_text(json.dumps(report, indent=2))
        if completed.timed_out or completed.returncode:
            raise ReferenceRefusal(f"{name} failed; inspect retained command logs")
        return completed.stdout

    try:
        identity = (
            command(
                "runtime",
                (
                    str(rscript),
                    "--vanilla",
                    "-e",
                    'cat(as.character(getRversion()),"\\n",R.version$platform,"\\n",R.home(),"\\n",sep="")',
                ),
            )
            .decode()
            .splitlines()
        )
        if identity[0] != lock.payload["runtime_policy"]["r_version"]:
            raise ReferenceRefusal("Installed R version differs from the source lock")
        report["r_runtime"] = {
            "version": identity[0],
            "platform": identity[1],
            "home": identity[2],
            "R": str(r),
            "Rscript": str(rscript),
            "R_resolved": str(r.resolve()),
            "Rscript_resolved": str(rscript.resolve()),
            "R_launcher_sha256": sha256(r.resolve()),
            "Rscript_sha256": sha256(rscript.resolve()),
            "origin": "existing-system-runtime-version-checked; not claimed built by this invocation",
        }
        if runtime_build is not None:
            report["r_runtime"]["origin"] = "source-built-verified"
        command("compiler-config", (str(r), "CMD", "config", "--all"))
        for tool in ("cc", "c++", "gfortran", "make", "pkg-config"):
            executable = shutil.which(tool)
            if executable:
                command("tool-" + tool.replace("+", "x"), (executable, "--version"))
        library.mkdir(parents=True)
        private_home = output / "home"
        private_home.mkdir()
        config_path = (
            str(pkg_config_path.resolve(strict=True))
            if pkg_config_path is not None
            else ""
        )
        prefix = (
            "/usr/bin/env",
            "-i",
            f"HOME={private_home}",
            f"PATH={os.environ.get('PATH', os.defpath)}",
            f"PKG_CONFIG_PATH={config_path}",
            "LANG=" + lock.payload["runtime_policy"]["locale"],
            "LC_ALL=" + lock.payload["runtime_policy"]["locale"],
            f"R_LIBS_USER={library}",
            "R_LIBS_SITE=",
            "R_ENVIRON_USER=/dev/null",
            "R_PROFILE_USER=/dev/null",
            f"R_MAKEVARS_USER={sources.get('compiler_makevars', '/dev/null')}",
            "R_MAKEVARS_SITE=/dev/null",
            "MAKEFLAGS=-j1",
            "OMP_NUM_THREADS=1",
            "OPENBLAS_NUM_THREADS=1",
            "MKL_NUM_THREADS=1",
            "TZ=UTC",
        )
        report["build_environment"] = {
            item.split("=", 1)[0]: item.split("=", 1)[1] for item in prefix[2:]
        }
        if pkg_config_path is not None:
            command(
                "system-icu",
                (
                    *prefix,
                    shutil.which("pkg-config") or "pkg-config",
                    "--modversion",
                    "icu-uc",
                ),
            )
        for name in (*lock.install_order, "disqover"):
            # Prevent stringi from acquiring an unpinned ICU source archive.
            configure_args = (
                lock.payload["runtime_policy"]
                .get("package_configure_args", {})
                .get(name, [])
            )
            configure = (
                ("--configure-args=" + " ".join(configure_args),)
                if configure_args
                else ()
            )
            command(
                "install-" + name,
                (
                    *prefix,
                    str(r),
                    "CMD",
                    "INSTALL",
                    "--library=" + str(library),
                    *configure,
                    str(sources[name]),
                ),
                1800,
            )
            (library / name / "SOURCE_SHA256").write_text(sha256(sources[name]) + "\n")
        names = [*lock.install_order, "disqover"]
        code = (
            "names<-"
            + ("c(" + ",".join(json.dumps(name) for name in names) + ")")
            + ";rows<-do.call(rbind,lapply(names,function(n){d<-packageDescription(n);data.frame(package=n,version=d$Version,library=normalizePath(find.package(n)),stringsAsFactors=FALSE)}));write.csv(rows,stdout(),row.names=FALSE)"
        )
        rows = list(
            csv.DictReader(
                io.StringIO(
                    command(
                        "installed-identity",
                        (*prefix, str(rscript), "--vanilla", "-e", code),
                    ).decode()
                )
            )
        )
        expected = {source.package: source.version for source in lock.sources}
        expected["disqover"] = lock.payload["reference"]["version"]
        if {row["package"] for row in rows} != set(names):
            raise ReferenceRefusal("Installed dependency inventory is incomplete")
        for row in rows:
            if (
                row["version"] != expected[row["package"]]
                or Path(row["library"]) != (library / row["package"]).resolve()
            ):
                raise ReferenceRefusal(
                    "A dependency came from an unpinned library/version"
                )
        report["installed_packages"] = rows
        report["library_files"] = {
            path.relative_to(library).as_posix(): sha256(path)
            for path in sorted(library.rglob("*"))
            if path.is_file()
        }
        if sha256(lock_path) != report["lock_sha256"] or any(
            sha256(path) != report["source_files"][name]["sha256"]
            for name, path in sources.items()
        ):
            raise ReferenceRefusal("Source or lock changed during provisioning")
        if (
            runtime_build is not None
            and file_inventory(runtime_prefix) != runtime_build["runtime_files"]
        ):
            raise ReferenceRefusal("Built R runtime changed during provisioning")
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    """Provision the locked R library from command-line paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--source-cache", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--r", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, required=True)
    parser.add_argument("--pkg-config-path", type=Path)
    parser.add_argument("--makevars", type=Path)
    parser.add_argument("--runtime-receipt", type=Path)
    args = parser.parse_args()
    provision(
        lock_path=args.lock,
        source_cache=args.source_cache,
        repository=args.repository,
        library=args.library,
        output=args.output,
        r=args.r,
        rscript=args.rscript,
        pkg_config_path=args.pkg_config_path,
        makevars=args.makevars,
        runtime_receipt=args.runtime_receipt,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
