"""Exact-command gate execution with durable, canonical evidence records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess  # nosec B404
import sys
import tempfile
import time

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

from ..governance.country_coverage import INPUT_PATHS as _COUNTRY_COVERAGE_INPUT_PATHS
from .release_evidence import ReleaseEvidenceError, hash_repository_object

__all__ = [
    "RecordedGateSpecification",
    "build_product_gate_specification",
    "run_recorded_gate",
]

_IDENTITY_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")
_PRODUCER_ID = "bijux-pollenomics.recorded-gate"
_PRODUCER_VERSION = "4"
_PRODUCER_MODULE = "bijux_pollenomics.provenance.gates"
_LOCAL_ATTESTATION = {
    "class": "local_self_attestation",
    "independent_execution_attested": False,
    "external_authority_id": None,
}


@dataclass(frozen=True)
class RecordedGateSpecification:
    """Trusted execution shape for one product-owned verification gate."""

    gate_id: str
    required: bool
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    input_paths: tuple[str, ...]
    artifacts_directory: str
    junit_path: str
    timeout_seconds: float | None = None
    runtime_identity: tuple[tuple[str, str], ...] = ()

    def as_record(self, repository_root: Path) -> dict[str, object]:
        """Return the canonical root-bound specification record."""
        root = _repository_root(repository_root)
        return {
            "gate_id": self.gate_id,
            "required": self.required,
            "argv": list(self.argv),
            "environment": dict(self.environment),
            "input_paths": list(self.input_paths),
            "artifacts_directory": self.artifacts_directory,
            "junit_path": self.junit_path,
            "timeout_seconds": self.timeout_seconds,
            "runtime_identity": dict(self.runtime_identity),
            "repository_root_digest": _digest_json(root.as_posix()),
            "producer": _producer_record(),
            "attestation": dict(_LOCAL_ATTESTATION),
        }


_GATE_TESTS: dict[str, tuple[str, ...]] = {
    "science": (
        "core/test_temporal_semantics.py",
        "collection/sources/sead/evidence/test_chronology.py",
        "analysis/classification/test_ecological_classification.py",
        "evidence/test_classification_audit_outputs.py",
        "analysis/classification/test_classification_events.py",
        "analysis/classification/test_harmonization.py",
        "core/test_temporal_overlap_consumers.py",
        "analysis/fieldwork/evidence_richness/test_report.py",
        "analysis/propagation/test_propagation_evidence_domains.py",
        "evidence/test_scientific_review.py",
        "collection/catalog/test_source_spatiotemporal_posture.py",
        "analysis/propagation/test_propagation_network.py",
    ),
    "data": (
        "adna/workflow/test_adna_normalization.py",
        "adna/species/test_adna_catalogs.py",
        "adna/projects/evidence/test_localities.py",
        "adna/workflow/test_adna_runtime.py",
        "adna/projects/test_adna_sample_master.py",
        "adna/projects/registry/test_sample_truth.py",
        "adna/sources/library",
        "adna/sources/test_adna_source_recovery.py",
        "adna/domain/test_adna_temporal_query.py",
        "collection/sources/sead/acquisition/test_full.py",
        "collection/sources/sead/acquisition/test_admission.py",
        "collection/sources/sead/evidence/test_claims.py",
        "collection/sources/sead/evidence/test_observations.py",
        "collection/sources/sead/acquisition/test_scoped.py",
        "collection/sources/neotoma/test_neotoma_data.py",
        "collection/sources/neotoma/test_neotoma_lineage_review.py",
        "collection/sources/neotoma/test_neotoma_relational.py",
        "collection/sources/neotoma/test_neotoma_materialization.py",
        "collection/sources/neotoma/test_neotoma_production.py",
        "collection/sources/landclim/test_landclim_data.py",
        "collection/sources/landclim/test_landclim_raw_receipt.py",
        "collection/sources/raa/test_raa_data.py",
        "collection/sources/raa/test_raa_authority.py",
        "collection/sources/svar/test_svar_data.py",
        "collection/sources/boundaries/test_boundaries.py",
        "collection/sources/boundaries/test_boundary_country_review.py",
        "collection/contracts/test_data_contract_surfaces.py",
        "collection/workflow/planning/test_layout.py",
        "collection/catalog/test_source_identity.py",
        "collection/contracts/test_source_family_contracts.py",
        "collection/contracts/test_source_layout_contract.py",
        "collection/catalog/test_source_provenance.py",
        "collection/catalog/test_source_traceability.py",
        "collection/catalog/test_source_validation.py",
    ),
    "map": (
        "reporting/map_document/evidence_projection",
        "reporting/atlas/test_map_publication.py",
        "reporting/atlas/test_static_atlas_assets.py",
        "reporting/atlas/test_publication_geography.py",
        "reporting/portal/test_reporting_artifacts.py",
        "reporting/portal/test_report_portal.py",
        "evidence/test_evidence_surface.py",
        "analysis/propagation/test_propagation_outputs.py",
        "governance/test_public_artifact_language.py",
    ),
    "provenance": (
        "provenance/test_release_evidence.py",
        "provenance/test_release_evidence_writer.py",
        "provenance/test_recorded_gates.py",
        "provenance/test_pollenomics_gate_runner.py",
    ),
    "doc-counts": (
        "governance/country_coverage",
        "governance/test_data_reference_docs.py",
        "collection/catalog/test_source_spatiotemporal_posture.py",
        "collection/workflow/materialization/test_repository_snapshot.py",
        "governance/repository_truth/test_assessments.py",
        "../regression/test_docs_breadth.py",
    ),
}

_GATE_TRUST_INPUTS = (
    "Makefile",
    "makes/pollenomics-verification.mk",
    "packages/bijux-pollenomics/pyproject.toml",
    "pyproject.toml",
    "uv.lock",
)

_GATE_FIXED_INPUTS: dict[str, tuple[str, ...]] = {
    "science": (
        *_GATE_TRUST_INPUTS,
        "configs/pytest.ini",
        "data/neotoma/raw",
        "data/sead/raw",
    ),
    "data": (
        *_GATE_TRUST_INPUTS,
        "configs/pytest.ini",
        "data/source_family_contracts.json",
        "data/source_spatiotemporal_posture_registry.json",
        "data/adna/final",
        "data/adna/governance",
        "data/neotoma",
        "data/sead",
        "data/landclim",
        "data/raa",
        "data/svar",
        "data/boundaries",
    ),
    "map": (*_GATE_TRUST_INPUTS, "configs/pytest.ini", "docs/report"),
    "provenance": (
        *_GATE_TRUST_INPUTS,
        "configs/pytest.ini",
        "configs/release_evidence_policy.json",
    ),
    "doc-counts": (
        *_GATE_TRUST_INPUTS,
        "configs/pytest.ini",
        "data/country_dimension_coverage.json",
        *_COUNTRY_COVERAGE_INPUT_PATHS,
        "data/evidence_artifact_contracts.json",
        "data/source_fact_ownership_registry.json",
        "data/source_family_contracts.json",
        "data/source_family_evidence_stage_matrix.json",
        "data/source_spatiotemporal_posture_registry.json",
        "docs/public/pollenomics-data",
    ),
}

_GATE_GLOBS: dict[str, tuple[str, ...]] = {
    "science": (
        "packages/bijux-pollenomics/src/bijux_pollenomics/core/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/*/*/*.py",
    ),
    "data": (
        "data/adna/species/*/manifests",
        "data/adna/species/*/normalized",
        "data/adna/species/*/reports",
        "data/adna/species/*/review",
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/*/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/*/*/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/adna/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/adna/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/adna/*/*/*.py",
    ),
    "map": (
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/*/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/*.py",
    ),
    "provenance": ("packages/bijux-pollenomics/src/bijux_pollenomics/provenance/*.py",),
    "doc-counts": (
        "packages/bijux-pollenomics/src/bijux_pollenomics/governance/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/governance/*/*.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/review/*.py",
    ),
}


def build_product_gate_specification(
    repository_root: Path, gate_id: str
) -> RecordedGateSpecification:
    """Return the repository-owned exact specification for a release gate."""
    root = _repository_root(repository_root)
    try:
        test_names = _GATE_TESTS[gate_id]
    except KeyError as error:
        raise ReleaseEvidenceError(
            f"unknown product verification gate: {gate_id}"
        ) from error
    test_root = "packages/bijux-pollenomics/tests/unit"
    tests = tuple(
        (
            "packages/bijux-pollenomics/tests/regression/test_docs_breadth.py"
            if name.startswith("../regression/")
            else f"{test_root}/{name}"
        )
        for name in test_names
    )
    inputs = set(_GATE_FIXED_INPUTS[gate_id])
    inputs.update(tests)
    for pattern in _GATE_GLOBS[gate_id]:
        inputs.update(path.relative_to(root).as_posix() for path in root.glob(pattern))
    artifacts_directory = "artifacts/execution-control/gates"
    junit_path = f"{artifacts_directory}/{gate_id}.junit.xml"
    pytest_path = root / "artifacts/root/check-venv/bin/pytest"
    argv = (
        str(pytest_path),
        "--rootdir",
        str(root),
        "-c",
        str(root / "configs/pytest.ini"),
        "-q",
        "-o",
        f"cache_dir={root}/{artifacts_directory}/pytest-cache/{gate_id}",
        f"--junitxml={root}/{junit_path}",
        *tests,
    )
    node_path = shutil.which("node")
    path_parts = [str(root / "artifacts/root/check-venv/bin")]
    if node_path is not None:
        path_parts.append(str(Path(node_path).parent))
    path_parts.extend(("/usr/bin", "/bin"))
    environment = {
        "PATH": ":".join(path_parts),
        "PYTHONPATH": str(root / "packages/bijux-pollenomics/src"),
        "PYTHONPYCACHEPREFIX": str(root / f"{artifacts_directory}/pycache/{gate_id}"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "HYPOTHESIS_DATABASE_DIRECTORY": str(
            root / f"{artifacts_directory}/hypothesis/{gate_id}"
        ),
        "LANG": "C",
        "LC_ALL": "C",
    }
    return RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=argv,
        environment=tuple(sorted(environment.items())),
        input_paths=tuple(sorted(inputs)),
        artifacts_directory=artifacts_directory,
        junit_path=junit_path,
        timeout_seconds=900.0,
        runtime_identity=_runtime_identity(str(pytest_path), node_path),
    )


def run_recorded_gate(
    repository_root: Path,
    *,
    gate_id: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    input_paths: Sequence[str],
    artifacts_directory: str,
    junit_path: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, object]:
    """Run exact argv without a shell and atomically publish its evidence record."""
    root = _repository_root(repository_root)
    _validate_gate_id(gate_id)
    command = _exact_argv(argv)
    execution_environment = _exact_environment(environment)
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool) or timeout_seconds <= 0
    ):
        raise ReleaseEvidenceError("timeout_seconds must be positive or null")
    directory = _prepare_artifacts_directory(root, artifacts_directory)
    junit = (
        _artifact_member(root, directory, junit_path, "JUnit path")
        if junit_path is not None
        else None
    )
    inputs = _input_records(root, input_paths)
    specification = RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=tuple(command),
        environment=tuple(execution_environment.items()),
        input_paths=tuple(sorted(input_paths)),
        artifacts_directory=artifacts_directory,
        junit_path=junit_path or "",
        timeout_seconds=timeout_seconds,
        runtime_identity=_runtime_identity(command[0], shutil.which("node")),
    )
    specification_record = specification.as_record(root)
    stdout_path = directory / f"{gate_id}.stdout.log"
    stderr_path = directory / f"{gate_id}.stderr.log"
    record_path = directory / f"{gate_id}.json"

    stdout_temporary = _temporary_path(directory, stdout_path.name)
    stderr_temporary = _temporary_path(directory, stderr_path.name)
    started = time.monotonic_ns()
    exit_code: int | None
    reason_code: str
    try:
        with (
            stdout_temporary.open("wb") as stdout_stream,
            stderr_temporary.open("wb") as stderr_stream,
        ):
            try:
                # Exact shell-free argv; product-spec binding is validated separately.
                completed = subprocess.run(  # nosec B603
                    command,
                    cwd=root,
                    env=execution_environment,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    check=False,
                    shell=False,
                    timeout=timeout_seconds,
                )
                exit_code = completed.returncode
                reason_code = "command_passed" if exit_code == 0 else "command_failed"
            except subprocess.TimeoutExpired:
                exit_code = None
                reason_code = "command_timed_out"
            except OSError as error:
                exit_code = None
                reason_code = "command_launch_failed"
                stderr_stream.write(f"{type(error).__name__}: {error}\n".encode())
            stdout_stream.flush()
            stderr_stream.flush()
            os.fsync(stdout_stream.fileno())
            os.fsync(stderr_stream.fileno())
        duration = time.monotonic_ns() - started
        os.replace(stdout_temporary, stdout_path)
        os.replace(stderr_temporary, stderr_path)
        _fsync_directory(directory)
    finally:
        for temporary in (stdout_temporary, stderr_temporary):
            if temporary.exists():
                temporary.unlink()

    stdout_record = _output_record(root, stdout_path)
    stderr_record = _output_record(root, stderr_path)
    junit_record: dict[str, object] | None = None
    if junit is not None:
        if junit.exists() or junit.is_symlink():
            junit_record = _output_record(root, junit)
            if reason_code == "command_passed":
                try:
                    _validate_passing_junit(junit)
                except ReleaseEvidenceError as error:
                    reason_code = str(error)
        else:
            junit_record = {
                "path": junit.relative_to(root).as_posix(),
                "status": "MISSING",
            }
            if reason_code == "command_passed":
                reason_code = "junit_missing"
    elif reason_code == "command_passed":
        reason_code = "junit_missing"
    try:
        current_inputs = _input_records(root, input_paths)
    except ReleaseEvidenceError:
        current_inputs = None
    if current_inputs != inputs:
        reason_code = "input_changed_during_gate"
    status = "PASS" if exit_code == 0 and reason_code == "command_passed" else "FAIL"
    record_content: dict[str, object] = {
        "schema_version": "recorded-gate.v4",
        "producer": specification_record["producer"],
        "attestation": specification_record["attestation"],
        "repository_root_digest": _digest_json(root.as_posix()),
        "gate_id": gate_id,
        "required": specification.required,
        "argv": command,
        "command_digest": _digest_json(command),
        "environment": execution_environment,
        "environment_digest": _digest_json(dict(sorted(execution_environment.items()))),
        "inputs": inputs,
        "input_digest": _digest_json(inputs),
        "artifacts_directory": artifacts_directory,
        "specification_digest": _digest_json(specification_record),
        "timeout_seconds": timeout_seconds,
        "duration_monotonic_ns": duration,
        "exit_code": exit_code,
        "status": status,
        "reason_code": reason_code,
        "stdout": stdout_record,
        "stderr": stderr_record,
        "junit": junit_record,
    }
    record = {"record_digest": _digest_json(record_content), **record_content}
    _atomic_replace(record_path, _canonical_bytes(record))
    return record


def _producer_record() -> dict[str, object]:
    source_bytes = _read_executing_source_bytes()
    source_files = [
        {
            "module": _PRODUCER_MODULE,
            "sha256": f"sha256:{hashlib.sha256(source_bytes).hexdigest()}",
            "byte_count": len(source_bytes),
        }
    ]
    source_digest = _digest_json(source_files)
    content: dict[str, object] = {
        "identity": _PRODUCER_ID,
        "version": _PRODUCER_VERSION,
        "source_files": source_files,
        "source_digest": source_digest,
    }
    return {**content, "digest": _digest_json(content)}


def _runtime_identity(
    executable: str, node_path: str | None
) -> tuple[tuple[str, str], ...]:
    path = Path(executable).resolve(strict=False)
    identity = {
        "command_executable_path": path.as_posix(),
        "command_executable_sha256": (
            f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
            if path.is_file()
            else "unavailable"
        ),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "runner_python": Path(sys.executable).resolve(strict=True).as_posix(),
    }
    if node_path is not None:
        node = Path(node_path).resolve(strict=True)
        identity["node_path"] = node.as_posix()
        identity["node_sha256"] = (
            f"sha256:{hashlib.sha256(node.read_bytes()).hexdigest()}"
        )
    return tuple(sorted(identity.items()))


def _read_executing_source_bytes() -> bytes:
    path = Path(__file__)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ReleaseEvidenceError("recorded gate producer source is unsafe") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReleaseEvidenceError(
                "recorded gate producer source is not a regular file"
            )
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ReleaseEvidenceError(
                "recorded gate producer source changed while reading"
            )
        return payload
    finally:
        os.close(descriptor)


def _validate_passing_junit(path: Path) -> None:
    try:
        root = ET.fromstring(path.read_bytes())
    except (OSError, ET.ParseError) as error:
        raise ReleaseEvidenceError("junit_invalid") from error
    tag = root.tag.rsplit("}", 1)[-1]
    if tag not in {"testsuite", "testsuites"}:
        raise ReleaseEvidenceError("junit_invalid")
    for element in root.iter():
        local_tag = element.tag.rsplit("}", 1)[-1]
        if local_tag in {"failure", "error", "skipped"}:
            raise ReleaseEvidenceError("junit_failed")
        if local_tag in {"testsuite", "testsuites"}:
            for attribute in ("failures", "errors", "skipped"):
                raw = element.attrib.get(attribute, "0")
                try:
                    count = int(raw)
                except ValueError as error:
                    raise ReleaseEvidenceError("junit_invalid") from error
                if count < 0:
                    raise ReleaseEvidenceError("junit_invalid")
                if count:
                    raise ReleaseEvidenceError("junit_failed")


def _input_records(root: Path, input_paths: Sequence[str]) -> list[dict[str, object]]:
    if any(not isinstance(path, str) for path in input_paths):
        raise ReleaseEvidenceError("input paths must be strings")
    paths = sorted(input_paths)
    if not paths:
        raise ReleaseEvidenceError("at least one gate input path is required")
    if len(paths) != len(set(paths)):
        raise ReleaseEvidenceError("duplicate gate input path")
    return [{"path": path, **hash_repository_object(root, path)} for path in paths]


def _output_record(root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    result = hash_repository_object(root, relative)
    return {"path": relative, **result}


def _exact_argv(argv: Sequence[str]) -> list[str]:
    if not argv or any(
        not isinstance(argument, str) or not argument or "\0" in argument
        for argument in argv
    ):
        raise ReleaseEvidenceError("argv must contain exact non-empty strings")
    return list(argv)


def _exact_environment(environment: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in environment.items():
        if (
            not isinstance(key, str)
            or not key
            or "=" in key
            or "\0" in key
            or not isinstance(value, str)
            or "\0" in value
        ):
            raise ReleaseEvidenceError("environment must contain valid string pairs")
        result[key] = value
    return dict(sorted(result.items()))


def _prepare_artifacts_directory(root: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path)
    if not parts or parts[0] != "artifacts":
        raise ReleaseEvidenceError("gate evidence must be under artifacts/")
    current = root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            with suppress(FileExistsError):
                current.mkdir(mode=0o755)
            mode = current.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(
                f"unsafe gate artifacts directory: {relative_path}"
            )
    return current


def _artifact_member(
    root: Path, directory: Path, relative_path: str, field: str
) -> Path:
    parts = _relative_parts(relative_path)
    path = root.joinpath(*parts)
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise ReleaseEvidenceError(
            f"{field} must be inside the gate artifacts directory"
        ) from error
    current = root
    for part in parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(f"{field} parent does not exist") from error
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(f"unsafe {field}")
    if path.exists() or path.is_symlink():
        raise ReleaseEvidenceError(f"{field} must not reuse existing evidence")
    return path


def _relative_parts(relative_path: str) -> tuple[str, ...]:
    if not relative_path or "\\" in relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or pure.as_posix() != relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ReleaseEvidenceError(f"path escapes repository root: {relative_path!r}")
    return pure.parts


def _temporary_path(directory: Path, name: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".writing", dir=directory
    )
    os.close(descriptor)
    return Path(temporary_name)


def _atomic_replace(destination: Path, payload: bytes) -> None:
    temporary = _temporary_path(destination.parent, destination.name)
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                dict(value),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error


def _digest_json(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_gate_id(gate_id: str) -> None:
    if not isinstance(gate_id, str) or _IDENTITY_PATTERN.fullmatch(gate_id) is None:
        raise ReleaseEvidenceError(f"invalid gate identity: {gate_id!r}")


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
