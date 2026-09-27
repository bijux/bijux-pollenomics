"""Replay the locked R oracle in a recorded local Linux container."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, cast

from bijux_pollenomics_dev.ci.lra_reference.contracts import (
    ReferenceRefusal,
    load_lock,
)
from bijux_pollenomics_dev.ci.lra_reference.evidence import (
    file_inventory,
    validate_oracle,
)
from bijux_pollenomics_dev.ci.lra_reference.profiles import validate_source_domains
from bijux_pollenomics_dev.ci.lra_reference.sources import (
    sha256,
    source_inventory,
    verify_sources,
)

_BASE_DIGEST = "sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84"
_PYTHON_VERSIONS = {"numpy": "2.4.6", "pandas": "2.3.3", "scipy": "1.17.1"}
_CONTAINER_CODE = """
import json
from pathlib import Path
import subprocess
import sys
import numpy
import pandas
import scipy

output = Path('/run')
identity = {
    'python': sys.version,
    'numpy': numpy.__version__,
    'pandas': pandas.__version__,
    'scipy': scipy.__version__,
    'r_version': subprocess.check_output(
        ['Rscript', '--vanilla', '-e', 'cat(as.character(getRversion()))'], text=True
    ).strip(),
    'r_platform': subprocess.check_output(
        ['Rscript', '--vanilla', '-e', 'cat(R.version$platform)'], text=True
    ).strip(),
}
(output / 'environment.json').write_text(json.dumps(identity, indent=2) + '\\n')
for runner, directory in (
    ('run_live_r.py', 'oracle'),
    ('run_source_domains.py', 'source-domains'),
):
    command = [
        sys.executable,
        '/repo/packages/bijux-pollenomics-lra/tests/reference/lra_oracle/' + runner,
        '--library', '/provision/library',
        '--output', str(output / directory),
    ]
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)
"""


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ReferenceRefusal(f"Expected object: {path}")
    return value


def _inventory_hash(files: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _verify_reused_runtime(
    repository: Path,
    source_cache: Path,
    runtime_tree: Path,
    provision_tree: Path,
) -> dict[str, Any]:
    lock_path = repository / "configs/ci/lra-r-source-lock.v1.json"
    lock = load_lock(lock_path)
    archives = verify_sources(lock, source_cache, repository)
    runtime_receipt = _json(runtime_tree / "receipt/report.json")
    provision_receipt = _json(provision_tree / "receipt/report.json")
    lock_hash = sha256(lock_path)
    reference_hash = cast(str, lock.payload["reference"]["sha256"])
    if (
        runtime_receipt.get("status") != "passed"
        or runtime_receipt.get("lock_sha256") != lock_hash
        or runtime_receipt.get("source_archive_sha256") != lock.payload["r"]["sha256"]
        or runtime_receipt.get("prefix") != "/output/runtime"
        or provision_receipt.get("status") != "passed"
        or provision_receipt.get("lock_sha256") != lock_hash
        or provision_receipt.get("library") != "/provision/library"
        or provision_receipt.get("runtime_build") != runtime_receipt
        or cast(dict[str, Any], provision_receipt.get("r_runtime", {})).get("origin")
        != "source-built-verified"
    ):
        raise ReferenceRefusal("Reused R build or provision receipt differs from lock")
    runtime_files = file_inventory(runtime_tree / "runtime")
    library_files = file_inventory(provision_tree / "library")
    if (
        runtime_files != runtime_receipt.get("runtime_files")
        or {name: row["sha256"] for name, row in library_files.items()}
        != provision_receipt.get("library_files")
        or sha256(runtime_tree / "runtime/bin/Rscript")
        != runtime_receipt.get("Rscript_sha256")
    ):
        raise ReferenceRefusal("Reused R runtime or private library bytes differ")
    expected_versions = {
        row.package: row.version for row in lock.sources if row.package != "R"
    }
    expected_versions["disqover"] = cast(str, lock.payload["reference"]["version"])
    installed = cast(
        list[dict[str, Any]], provision_receipt.get("installed_packages", [])
    )
    if (
        len(installed) != len(expected_versions)
        or {row["package"]: row["version"] for row in installed} != expected_versions
    ):
        raise ReferenceRefusal("Reused private R package version closure differs")
    return {
        "lock_sha256": lock_hash,
        "reference_sha256": reference_hash,
        "archive_sha256": {name: sha256(path) for name, path in archives.items()},
        "runtime_receipt_sha256": sha256(runtime_tree / "receipt/report.json"),
        "provision_receipt_sha256": sha256(provision_tree / "receipt/report.json"),
        "runtime_files": runtime_files,
        "library_files": provision_receipt["library_files"],
        "installed_packages": installed,
    }


def _validate_core_raw(root: Path, reference_hash: str) -> dict[str, Any]:
    report = _json(root / "report.json")
    manifest = json.loads((root / "case_manifest.json").read_text())
    validate_oracle(report, manifest, reference_hash, expected_core_cases=43)
    with (root / "R_case_status.csv").open(newline="") as stream:
        statuses = list(csv.DictReader(stream))
    ids = {cast(str, row["id"]) for row in manifest}
    if (
        len(statuses) != 43
        or {row.get("id") for row in statuses} != ids
        or any(row.get("status") != "completed" for row in statuses)
    ):
        raise ReferenceRefusal("Linux R core raw completion denominator differs")
    for case in manifest:
        raw_path = root / f"{case['id']}.csv"
        if not raw_path.is_file():
            raise ReferenceRefusal("Linux R core raw vector is missing")
        with raw_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != case["values"] or any(
            set(row) != {"kind", "value"} or row["kind"] not in {"numeric", "character"}
            for row in rows
        ):
            raise ReferenceRefusal("Linux R core raw vector denominator differs")
        for row in rows:
            if row["kind"] == "numeric":
                try:
                    float(row["value"])
                except (TypeError, ValueError) as error:
                    raise ReferenceRefusal(
                        "Linux R core raw number is invalid"
                    ) from error
    return report


def _container_command(
    repository: Path,
    output: Path,
    runtime_tree: Path,
    provision_tree: Path,
    image_id: str,
) -> list[str]:
    name = "bijux-pollenomics-linux-r-oracle-" + image_id.split(":")[-1][:12]
    environment = {
        "PATH": "/output/runtime/bin:/usr/local/bin:/usr/bin:/bin",
        "PYTHONPATH": ":".join(
            f"/repo/packages/{package}/src"
            for package in (
                "bijux-pollenomics",
                "bijux-pollenomics-dev",
                "bijux-pollenomics-lra",
            )
        ),
        "R_LIBS_USER": "/provision/library",
        "R_LIBS_SITE": "",
        "R_ENVIRON_USER": "/dev/null",
        "R_PROFILE_USER": "/dev/null",
        "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "TZ": "UTC",
        "LANG": "C",
        "LC_ALL": "C",
    }
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--platform",
        "linux/arm64",
        "--cpus",
        "1",
        "--memory",
        "4g",
        "--network",
        "none",
    ]
    for source, target, readonly in (
        (repository, "/repo", True),
        (runtime_tree, "/output", True),
        (provision_tree, "/provision", True),
        (output, "/run", False),
    ):
        command += [
            "--mount",
            f"type=bind,source={source},target={target}"
            + (",readonly" if readonly else ""),
        ]
    for key, value in environment.items():
        command += ["--env", f"{key}={value}"]
    return [*command, image_id, "python", "-c", _CONTAINER_CODE]


def execute(
    *,
    repository: Path,
    output: Path,
    retained: Path,
    runtime_tree: Path,
    provision_tree: Path,
    source_cache: Path,
    image_id_path: Path,
    dockerfile: Path,
    timeout_seconds: int = 1200,
) -> dict[str, Any]:
    """Retain actual Linux R vectors and refuse every release-CI implication."""
    repository = repository.resolve(strict=True)
    output = output.resolve()
    retained = retained.resolve()
    runtime_tree = runtime_tree.resolve(strict=True)
    provision_tree = provision_tree.resolve(strict=True)
    source_cache = source_cache.resolve(strict=True)
    if output.exists() or retained.exists():
        raise ValueError("Linux oracle output and retained destination must be absent")
    output.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema_version": "linux-r-oracle-evidence.v1",
        "status": "incomplete",
        "release_certificate": False,
        "release_refusal_codes": [
            "local_linux_arm_is_not_locked_ubuntu_x86_64_ci",
            "github_run_attempt_and_artifact_absent",
        ],
    }
    started = time.monotonic()
    try:
        provenance = _verify_reused_runtime(
            repository, source_cache, runtime_tree, provision_tree
        )
        report["source_lock"] = provenance
        before = source_inventory(repository)
        report["executed_source_files"] = before
        image_id = image_id_path.read_text().strip()
        if not image_id.startswith("sha256:") or len(image_id) != 71:
            raise ReferenceRefusal("Docker image content ID is invalid")
        docker_text = dockerfile.read_text()
        if not docker_text.startswith("FROM python@" + _BASE_DIGEST + "\n"):
            raise ReferenceRefusal("Recorded Linux Python base digest differs")
        image = json.loads(
            subprocess.check_output(
                ["docker", "image", "inspect", image_id, "--format", "{{json .}}"],
                text=True,
                timeout=30,
            )
        )
        if (
            image.get("Id") != image_id
            or image.get("Architecture") != "arm64"
            or image.get("Os") != "linux"
        ):
            raise ReferenceRefusal("Linux container image identity differs")
        report["container"] = {
            "image_id": image_id,
            "base_digest": _BASE_DIGEST,
            "dockerfile_sha256": sha256(dockerfile),
            "architecture": image["Architecture"],
            "os": image["Os"],
            "numerical_python_versions": _PYTHON_VERSIONS,
            "network": "none during execution",
            "cpu_limit": 1,
            "memory_limit_bytes": 4 * 1024**3,
        }
        command = _container_command(
            repository, output, runtime_tree, provision_tree, image_id
        )
        report["command"] = command
        with (
            (output / "container.stdout.log").open("wb") as stdout,
            (output / "container.stderr.log").open("wb") as stderr,
        ):
            try:
                process = subprocess.run(
                    command,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout_seconds,
                    check=False,
                )
                report["container_exit_code"] = process.returncode
                report["container_timed_out"] = False
            except subprocess.TimeoutExpired:
                report["container_exit_code"] = None
                report["container_timed_out"] = True
                subprocess.run(
                    ["docker", "stop", "--time", "10", command[4]],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
        if report["container_exit_code"] != 0:
            raise ReferenceRefusal("Linux R oracle container failed or timed out")
        environment = _json(output / "environment.json")
        if (
            environment.get("r_version") != "4.6.0"
            or environment.get("r_platform") != "aarch64-unknown-linux-gnu"
            or any(
                environment.get(name) != version
                for name, version in _PYTHON_VERSIONS.items()
            )
        ):
            raise ReferenceRefusal("Executed Linux R/Python runtime identity differs")
        core = _validate_core_raw(output / "oracle", provenance["reference_sha256"])
        domains = validate_source_domains(
            output / "source-domains", provenance["reference_sha256"]
        )
        raw = {
            name: file_inventory(output / name) for name in ("oracle", "source-domains")
        }
        report.update(
            linux_r_executed=True,
            environment=environment,
            core_cases={
                "attempted": core["prepared_cases"],
                "passed": core["passed_cases"],
            },
            source_domain_cases={
                "attempted": domains["prepared_cases"],
                "passed": domains["passed_cases"],
            },
            raw_files=raw,
            raw_inventory_sha256=_inventory_hash(raw),
        )
        if before != source_inventory(repository):
            raise ReferenceRefusal("Executed source bytes changed during Linux R run")
        retained.mkdir(parents=True)
        for name in raw:
            shutil.copytree(output / name, retained / name)
            if file_inventory(retained / name) != raw[name]:
                raise ReferenceRefusal("Retained Linux R raw outputs differ")
        report["status"] = "passed_local_linux_oracle"
    except BaseException as error:
        report.update(
            status="refused",
            error=type(error).__name__ + ": " + str(error),
            linux_r_executed=(output / "oracle/R_session_info.txt").is_file(),
        )
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        (output / "receipt.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
        retained.mkdir(parents=True, exist_ok=True)
        (retained / "report.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n"
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in (
        "repository",
        "output",
        "retained",
        "runtime-tree",
        "provision-tree",
        "source-cache",
        "image-id-path",
        "dockerfile",
    ):
        parser.add_argument("--" + option, required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    args = parser.parse_args()
    report = execute(
        repository=args.repository,
        output=args.output,
        retained=args.retained,
        runtime_tree=args.runtime_tree,
        provision_tree=args.provision_tree,
        source_cache=args.source_cache,
        image_id_path=args.image_id_path,
        dockerfile=args.dockerfile,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        json.dumps(
            {
                key: report.get(key)
                for key in ("status", "core_cases", "source_domain_cases", "error")
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed_local_linux_oracle" else 2


if __name__ == "__main__":
    raise SystemExit(main())
