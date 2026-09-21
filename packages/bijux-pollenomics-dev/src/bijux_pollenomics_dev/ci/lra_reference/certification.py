"""Run the existing oracle and publish a self-contained, source-bound certificate."""

from __future__ import annotations

from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv

from .contracts import ReferenceRefusal, load_lock, read_json
from .evidence import (
    SCHEMA,
    file_inventory,
    validate_bundle,
    validate_oracle,
)
from .paths import exclusive_outputs, local_path
from .source_identity import inspect_source_identity, selected_engine_version
from .sources import (
    SOURCE_STATUS_ARGUMENTS,
    SOURCE_TREE_ARGUMENTS,
    sha256,
    source_inventory,
)


def certify(
    *,
    lock_path: Path,
    repository: Path,
    library: Path,
    rscript: Path,
    provision_receipt: Path,
    output: Path,
) -> dict[str, Any]:
    """Run the locked R oracle and write a source-bound certificate bundle."""
    lock_path, repository, library, provision_receipt, output = (
        local_path(path)
        for path in (lock_path, repository, library, provision_receipt, output)
    )
    exclusive_outputs((output,), (lock_path, library, provision_receipt))
    lock = load_lock(lock_path)
    lock_hash = sha256(lock_path)
    provision = read_json(provision_receipt.read_bytes())
    if provision.get("status") != "passed" or provision.get("lock_sha256") != lock_hash:
        raise ReferenceRefusal("Successful matching provisioning is required")
    if provision.get("library") != str(library):
        raise ReferenceRefusal("Provisioned library path differs")
    runtime_build = provision.get("runtime_build")
    if (
        runtime_build is not None
        and file_inventory(Path(runtime_build["prefix"]))
        != runtime_build["runtime_files"]
    ):
        raise ReferenceRefusal("Built R runtime bytes changed after provisioning")
    before_library = file_inventory(library)
    if {path: row["sha256"] for path, row in before_library.items()} != provision.get(
        "library_files"
    ):
        raise ReferenceRefusal("Installed library bytes changed after provisioning")
    if sha256(rscript.resolve(strict=True)) != provision["r_runtime"]["Rscript_sha256"]:
        raise ReferenceRefusal("Rscript bytes changed after provisioning")
    output.mkdir(parents=True)
    report: dict[str, Any] = {"schema_version": SCHEMA, "status": "incomplete"}
    commands = []

    def command(
        name: str, argv: tuple[str, ...], cwd: Path, timeout: int = 120
    ) -> bytes:
        result = run_bounded_argv(argv, cwd=cwd, timeout_seconds=timeout)
        (output / (name + ".stdout.log")).write_bytes(result.stdout)
        (output / (name + ".stderr.log")).write_bytes(result.stderr)
        commands.append(
            {
                "step": name,
                "argv": list(result.command),
                "cwd": str(cwd),
                "exit_code": result.returncode,
                "timed_out": result.timed_out,
                "duration_seconds": result.duration_seconds,
            }
        )
        (output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode or result.timed_out:
            raise ReferenceRefusal(f"Certification command failed: {name}")
        return result.stdout

    try:
        commit = (
            command("git-head", ("git", "rev-parse", "HEAD"), repository)
            .decode()
            .strip()
        )
        tree = (
            command("git-tree", ("git", "rev-parse", "HEAD^{tree}"), repository)
            .decode()
            .strip()
        )
        identity = inspect_source_identity(
            repository,
            command("git-tree-files", ("git", *SOURCE_TREE_ARGUMENTS), repository),
        )
        sources = identity.tracked_files
        engine_version_identity = selected_engine_version(identity)
        changed = (
            command(
                "git-status",
                ("git", *SOURCE_STATUS_ARGUMENTS),
                repository,
            )
            .decode()
            .strip()
        )
        canonical = (
            repository
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference"
        )
        committed_source = not changed and Path(__file__).resolve().is_relative_to(
            canonical
        )
        implementation = {
            path.relative_to(Path(__file__).parent).as_posix(): sha256(path)
            for path in Path(__file__).parent.rglob("*.py")
        }
        runtime_root = Path(provision["r_runtime"]["home"])
        runtime_files = {
            str(path): sha256(path)
            for relative in (
                "bin/exec/R",
                "lib/libR.dylib",
                "lib/libR.so",
                "lib/libRblas.dylib",
                "lib/libRlapack.dylib",
                "etc/Makeconf",
            )
            if (path := runtime_root / relative).is_file()
        }
        python_runtime = {
            "version": sys.version,
            "executable": sys.executable,
            "executable_sha256": sha256(Path(sys.executable).resolve()),
            "distributions": sorted(
                (
                    {"name": item.metadata["Name"], "version": item.version}
                    for item in metadata.distributions()
                ),
                key=lambda row: row["name"].lower(),
            ),
        }
        ci = None
        if "GITHUB_RUN_ID" in os.environ:
            ci = {
                "repository": os.environ["GITHUB_REPOSITORY"],
                "run_id": int(os.environ["GITHUB_RUN_ID"]),
                "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
            }
        runner = (
            repository
            / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_live_r.py"
        )
        process_environment = {
            "PATH": str(rscript.parent)
            + os.pathsep
            + os.environ.get("PATH", os.defpath),
            "R_LIBS_USER": str(library),
            "R_LIBS_SITE": "",
            "R_ENVIRON_USER": "/dev/null",
            "R_PROFILE_USER": "/dev/null",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "TZ": "UTC",
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        command(
            "oracle",
            (
                "/usr/bin/env",
                *(name + "=" + value for name, value in process_environment.items()),
                sys.executable,
                str(runner),
                "--library",
                str(library),
                "--output",
                str(output / "oracle"),
            ),
            output,
            timeout=1900,
        )
        oracle = read_json((output / "oracle/report.json").read_bytes())
        manifest = read_json((output / "oracle/case_manifest.json").read_bytes())
        validate_oracle(oracle, manifest, lock.payload["reference"]["sha256"])
        domain_runner = (
            repository
            / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_source_domains.py"
        )
        command(
            "source-domains",
            (
                "/usr/bin/env",
                *(name + "=" + value for name, value in process_environment.items()),
                sys.executable,
                str(domain_runner),
                "--library",
                str(library),
                "--output",
                str(output / "source-domains"),
            ),
            output,
            timeout=1900,
        )
        from .profiles import validate_source_domains

        validate_source_domains(
            output / "source-domains", lock.payload["reference"]["sha256"]
        )
        if (
            identity.executed_files != source_inventory(repository)
            or selected_engine_version(identity) != engine_version_identity
            or before_library != file_inventory(library)
            or sha256(lock_path) != lock_hash
            or any(
                sha256(Path(path)) != digest for path, digest in runtime_files.items()
            )
            or implementation
            != {
                path.relative_to(Path(__file__).parent).as_posix(): sha256(path)
                for path in Path(__file__).parent.rglob("*.py")
            }
        ):
            raise ReferenceRefusal(
                "Source, runtime, library or implementation changed during execution"
            )
        if (
            command("git-head-after", ("git", "rev-parse", "HEAD"), repository)
            .decode()
            .strip()
            != commit
        ):
            raise ReferenceRefusal("Source HEAD changed during execution")
        if (
            command("git-status-after", ("git", *SOURCE_STATUS_ARGUMENTS), repository)
            .decode()
            .strip()
            != changed
        ):
            raise ReferenceRefusal("Relevant source checkout changed during execution")
        if (
            runtime_build is not None
            and file_inventory(Path(runtime_build["prefix"]))
            != runtime_build["runtime_files"]
        ):
            raise ReferenceRefusal("Built R runtime changed during certification")
        bundle = output / "bundle"
        bundle.mkdir()
        shutil.copytree(output / "oracle", bundle / "oracle")
        shutil.copytree(output / "source-domains", bundle / "source-domains")
        for relative in identity.generated_files:
            target = bundle / "generated-sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repository / relative, target)
        shutil.copy2(lock_path, bundle / "source-lock.json")
        shutil.copy2(provision_receipt, bundle / "provision.json")
        shutil.copy2(output / "commands.json", bundle / "commands.json")
        report.update(
            status="passed",
            source_commit=commit,
            source_tree=tree,
            committed_source=committed_source,
            source_files=sources,
            tracked_git_blobs=identity.tracked_git_blobs,
            generated_source_files=identity.generated_files,
            engine_version_identity=engine_version_identity,
            source_unchanged=True,
            required_profiles={
                "core_source_compatibility": 25,
                "source_domains_corrected_forward": 23,
            },
            shared_input_representation="executed-oracle.R-inline-literals-v1",
            lock_sha256=lock_hash,
            profile_id=lock.payload["profile_id"],
            r_runtime=provision["r_runtime"],
            runtime_files=runtime_files,
            library_files=provision["library_files"],
            python_runtime=python_runtime,
            implementation_files=implementation,
            github=ci,
            files=file_inventory(bundle),
        )
        (bundle / "certificate.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
        validate_bundle(bundle, target_sha=commit, expected_lock_sha256=lock_hash)
    except BaseException as error:
        report.update(status="failed", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        (output / "result.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
    return report
