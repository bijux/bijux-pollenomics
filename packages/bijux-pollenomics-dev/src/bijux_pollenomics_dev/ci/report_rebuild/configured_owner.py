"""Run a configured report owner from its current ownership declaration."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    require_relative_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.execution import build_owner_output
from bijux_pollenomics_dev.ci.report_rebuild.ownership import (
    ReportOwnershipError,
    check_report_ownership,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

SCHEMA = "configured-report-owner-execution.v1"
DEFAULT_CONFIGURATION = Path("configs/ci/report-owner-execution.json")
DEFAULT_INVENTORY = Path("configs/ci/report-ownership.json")
DEFAULT_POLICY = Path("configs/ci/reproducible-report-build.json")
MODULE = re.compile(
    r"bijux_pollenomics_dev\.source_completion"
    r"(?:\.[a-z][a-z0-9_]*)+\Z"
)
SOURCE_RUNTIME = """import importlib.util
from pathlib import Path
import runpy
import sys
repository = Path(sys.argv[1]).resolve(strict=True)
module = sys.argv[2]
roots = ("packages/bijux-pollenomics-dev/src", "packages/bijux-pollenomics/src", "packages/bijux-pollenomics-lra/src")
for relative in reversed(roots):
    sys.path.insert(0, str(repository / relative))
expected = repository / roots[0] / (module.replace(".", "/") + ".py")
spec = importlib.util.find_spec(module)
if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected:
    raise SystemExit("configured owner producer module origin differs")
print("report-owner-producer-origin: " + str(expected), file=sys.stderr, flush=True)
sys.argv = sys.argv[2:]
runpy.run_module(module, run_name="__main__")
"""

SOURCE_FLAGS = frozenset(
    {
        "--screen",
        "--raw-part",
        "--raw-manifest",
        "--workbook",
        "--workbook-receipt",
        "--count-mass",
        "--projection",
        "--receipt",
        "--sites",
    }
)
OWNER_FIELDS: frozenset[str] = frozenset(
    {
        "owner_id",
        "module",
        "source_paths",
        "source_arguments",
        "output_mode",
        "timeout_seconds",
    }
)
OPTIONAL_OWNER_FIELDS: frozenset[str] = frozenset(
    {"include_repository_argument", "output_subdirectory", "external_source_descriptor"}
)


@dataclass(frozen=True)
class ConfiguredOwner:
    """One validated producer invocation, bound to declared source paths."""

    owner_id: str
    command: tuple[str, ...]
    inputs: dict[str, Path]
    source_paths: dict[str, str]
    expected_outputs: dict[str, str]
    timeout_seconds: int
    external_source_descriptor: Path | None
    external_source_root: Path | None
    external_inputs: dict[str, Path]
    external_descriptor_sha256: str | None


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportRebuildError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _safe_file(repository: Path, relative: str, label: str) -> Path:
    """Require a regular repository file reached only through real directories."""
    parts = require_relative_path(relative, label).split("/")
    path = repository
    try:
        for component in parts[:-1]:
            path /= component
            if not stat.S_ISDIR(path.lstat().st_mode):
                raise ReportRebuildError(f"{label} has a non-real ancestor: {path}")
        path /= parts[-1]
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ReportRebuildError(f"{label} is not a regular file: {path}")
    except OSError as error:
        raise ReportRebuildError(f"{label} is unreadable: {path}") from error
    if not path.resolve().is_relative_to(repository):
        raise ReportRebuildError(f"{label} escapes the repository")
    return path


def _repository_relative(repository: Path, supplied: Path, label: str) -> str:
    if supplied.is_absolute():
        try:
            supplied = supplied.relative_to(repository)
        except ValueError as error:
            raise ReportRebuildError(f"{label} is outside the repository") from error
    return require_relative_path(supplied.as_posix(), label)


def _read_object(repository: Path, relative: str, label: str) -> dict[str, Any]:
    path = _safe_file(repository, relative, label)
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportRebuildError(f"cannot read {label}: {path}") from error
    if not isinstance(value, dict):
        raise ReportRebuildError(f"{label} must be an object")
    return value


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _configuration_owner(
    configuration: dict[str, Any], owner_id: str
) -> dict[str, Any]:
    if (
        set(configuration) != {"schema_version", "owners"}
        or configuration["schema_version"] != SCHEMA
    ):
        raise ReportRebuildError("configured owner schema or fields differ")
    rows = configuration["owners"]
    if not isinstance(rows, list) or not rows:
        raise ReportRebuildError("configured owner list is empty")
    found: dict[str, Any] | None = None
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ReportRebuildError("configured owner must be an object")
        if not row.keys() >= OWNER_FIELDS or not row.keys() <= (
            OWNER_FIELDS | OPTIONAL_OWNER_FIELDS
        ):
            raise ReportRebuildError("configured owner fields differ")
        if (
            "include_repository_argument" in row
            and type(row["include_repository_argument"]) is not bool
        ):
            raise ReportRebuildError("include_repository_argument must be a boolean")
        if "output_subdirectory" in row:
            require_relative_path(row["output_subdirectory"], "output subdirectory")
        if "external_source_descriptor" in row:
            require_relative_path(
                row["external_source_descriptor"], "external source descriptor"
            )
        identity = require_relative_path(row["owner_id"], "configured owner ID")
        if identity in seen:
            raise ReportRebuildError(f"duplicate configured owner: {identity}")
        seen.add(identity)
        if identity == owner_id:
            found = row
    if found is None:
        raise ReportRebuildError(f"unknown configured owner: {owner_id}")
    return found


def resolve_configured_owner(
    repository: Path,
    owner_id: str,
    *,
    source_root: Path | None = None,
    configuration_path: Path = DEFAULT_CONFIGURATION,
    inventory_path: Path = DEFAULT_INVENTORY,
) -> ConfiguredOwner:
    """Resolve one allowed invocation without running its producer."""
    repository = repository.resolve(strict=True)
    owner_id = require_relative_path(owner_id, "owner ID")
    try:
        check_report_ownership(repository, inventory_path)
    except ReportOwnershipError as error:
        raise ReportRebuildError(f"report ownership is invalid: {error}") from error
    configuration = _read_object(
        repository,
        _repository_relative(repository, configuration_path, "owner configuration"),
        "owner configuration",
    )
    row = _configuration_owner(configuration, owner_id)
    inventory = _read_object(
        repository,
        _repository_relative(repository, inventory_path, "report ownership"),
        "report ownership",
    )
    declarations = [
        item for item in inventory.get("owners", []) if item["owner_id"] == owner_id
    ]
    if len(declarations) != 1 or declarations[0]["role"] != "generated_owner":
        raise ReportRebuildError(f"owner is not declared generated: {owner_id}")
    declaration = declarations[0]
    owned = declaration["paths"]
    raw_sources = row["source_paths"]
    if not isinstance(raw_sources, dict) or not raw_sources:
        raise ReportRebuildError("configured owner needs a nonempty output mapping")
    paths: dict[str, str] = {}
    for source, target in raw_sources.items():
        source = require_relative_path(source, "produced file")
        target = require_relative_path(target, "owned report")
        if not target.startswith("docs/report/"):
            raise ReportRebuildError("configured owner output is outside docs/report")
        paths[source] = target.removeprefix("docs/report/")
    if len(set(raw_sources.values())) != len(raw_sources):
        raise ReportRebuildError("configured owner has duplicate output targets")
    if sorted(raw_sources.values()) != owned:
        raise ReportRebuildError("configured output map differs from owner declaration")
    if set(declaration["producer_paths"]) & set(owned) or set(
        declaration["producer_inputs"]
    ) & set(owned):
        raise ReportRebuildError("configured owner feeds its output")
    input_names = sorted(
        set(declaration["producer_paths"]) | set(declaration["producer_inputs"])
    )
    if len(input_names) != len(declaration["producer_paths"]) + len(
        declaration["producer_inputs"]
    ):
        raise ReportRebuildError("owner producer and data paths overlap")
    inputs = {
        name: _safe_file(repository, name, "declared producer input")
        for name in input_names
    }
    external_descriptor: Path | None = None
    external_inputs: dict[str, Path] = {}
    external_digest: str | None = None
    declared_external = row.get("external_source_descriptor")
    if declared_external is not None:
        descriptor = require_relative_path(
            declared_external, "external source descriptor"
        )
        if descriptor not in declaration["producer_inputs"]:
            raise ReportRebuildError(
                "external descriptor is not a declared repository input"
            )
        if source_root is None:
            raise ReportRebuildError("configured external owner requires --source-root")
        qualified = validated_external_report_sources(
            repository, source_root, Path(descriptor)
        )
        if qualified.inputs.get(descriptor) != inputs[descriptor]:
            raise ReportRebuildError("external descriptor differs from declared input")
        external_descriptor = Path(descriptor)
        external_inputs = qualified.inputs
        external_digest = qualified.descriptor_sha256
        for label, external_path in qualified.inputs.items():
            if label == descriptor:
                continue
            if label in inputs:
                raise ReportRebuildError(
                    "external input overlaps repository declaration"
                )
            inputs[label] = external_path
    module = row["module"]
    if not isinstance(module, str) or MODULE.fullmatch(module) is None:
        raise ReportRebuildError(
            "configured module is outside maintained source completion"
        )
    module_path = f"packages/bijux-pollenomics-dev/src/{module.replace('.', '/')}.py"
    if module_path not in declaration["producer_paths"]:
        raise ReportRebuildError("configured module is absent from producer paths")
    source_arguments = row["source_arguments"]
    if not isinstance(source_arguments, list):
        raise ReportRebuildError("source arguments must be a list")
    arguments: list[str] = []
    used_flags: set[str] = set()
    for argument in source_arguments:
        if not isinstance(argument, dict) or set(argument) != {"flag", "path"}:
            raise ReportRebuildError("source argument fields differ")
        flag = argument["flag"]
        path = require_relative_path(argument["path"], "source argument path")
        if (
            not isinstance(flag, str)
            or flag not in SOURCE_FLAGS
            or flag in used_flags
            or path not in declaration["producer_inputs"]
        ):
            raise ReportRebuildError("source argument differs from declared input")
        used_flags.add(flag)
        arguments.extend((flag, str(inputs[path])))
    mode = row["output_mode"]
    if not isinstance(mode, str) or mode not in {"directory", "single_file"}:
        raise ReportRebuildError("configured output mode is invalid")
    if mode == "single_file" and len(paths) != 1:
        raise ReportRebuildError(
            "single-file configured owner needs one output mapping"
        )
    output_subdirectory = row.get("output_subdirectory")
    if output_subdirectory is not None:
        if mode != "directory":
            raise ReportRebuildError(
                "output subdirectory requires directory output mode"
            )
        if any(not source.startswith(f"{output_subdirectory}/") for source in paths):
            raise ReportRebuildError(
                "produced file lies outside configured output subdirectory"
            )
    timeout = row["timeout_seconds"]
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ReportRebuildError("configured timeout must be between 1 and 600 seconds")
    output_argument = "{output_root}"
    if mode == "single_file":
        output_argument = f"{{output_root}}/{next(iter(paths))}"
    elif output_subdirectory is not None:
        output_argument = f"{{output_root}}/{output_subdirectory}"
    repository_arguments = (
        ("--repository", str(repository))
        if row.get("include_repository_argument", True)
        else ()
    )
    external_arguments = (
        (
            "--source-descriptor",
            str(external_descriptor),
            "--source-root",
            str(source_root.absolute()),
        )
        if source_root is not None and external_descriptor is not None
        else ()
    )
    command = (
        sys.executable,
        "-c",
        SOURCE_RUNTIME,
        str(repository),
        module,
        *repository_arguments,
        *arguments,
        *external_arguments,
        "--output",
        output_argument,
    )
    return ConfiguredOwner(
        owner_id=owner_id,
        command=command,
        inputs=inputs,
        source_paths=paths,
        expected_outputs={
            target: _digest(_safe_file(repository, target, "tracked owner output"))
            for target in owned
        },
        timeout_seconds=timeout,
        external_source_descriptor=external_descriptor,
        external_source_root=source_root,
        external_inputs=external_inputs,
        external_descriptor_sha256=external_digest,
    )


def build_configured_owner(
    *,
    repository: Path,
    plan_path: Path,
    lane: str,
    owner_id: str,
    evidence_root: Path,
    source_root: Path | None = None,
    policy_path: Path = DEFAULT_POLICY,
    configuration_path: Path = DEFAULT_CONFIGURATION,
    inventory_path: Path = DEFAULT_INVENTORY,
) -> JsonObject:
    """Build one independently bound owner and require tracked byte identity."""
    repository = repository.resolve(strict=True)
    selected = resolve_configured_owner(
        repository,
        owner_id,
        source_root=source_root,
        configuration_path=configuration_path,
        inventory_path=inventory_path,
    )
    manifest = build_owner_output(
        repo_root=repository,
        policy_path=_safe_file(
            repository,
            _repository_relative(repository, policy_path, "rebuild policy"),
            "rebuild policy",
        ),
        plan_path=plan_path,
        lane=lane,
        owner_id=selected.owner_id,
        producer_command=selected.command,
        producer_inputs=selected.inputs,
        source_paths=selected.source_paths,
        evidence_root=evidence_root,
        timeout_seconds=selected.timeout_seconds,
    )
    if selected.external_source_descriptor is not None:
        if selected.external_source_root is None:
            raise ReportRebuildError("external source root disappeared")
        after = validated_external_report_sources(
            repository,
            selected.external_source_root,
            selected.external_source_descriptor,
        )
        if (
            after.inputs != selected.external_inputs
            or after.descriptor_sha256 != selected.external_descriptor_sha256
        ):
            raise ReportRebuildError(
                "external source declaration changed during owner build"
            )
    output_root = (evidence_root / "output").resolve(strict=True)
    for target, expected_sha256 in selected.expected_outputs.items():
        produced = _safe_file(
            output_root,
            target.removeprefix("docs/report/"),
            "generated owner output",
        )
        tracked = _safe_file(repository, target, "tracked owner output")
        if _digest(tracked) != expected_sha256 or _digest(produced) != expected_sha256:
            raise ReportRebuildError(
                f"generated owner bytes differ from tracked report: {target}"
            )
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Run one configured owner in an existing bound rebuild plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--lane", choices=("reference", "replay"), required=True)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--configuration", type=Path, default=DEFAULT_CONFIGURATION)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    args = parser.parse_args(argv)
    try:
        result = build_configured_owner(
            repository=args.repository,
            plan_path=args.plan,
            lane=args.lane,
            owner_id=args.owner_id,
            evidence_root=args.evidence_root,
            source_root=args.source_root,
            policy_path=args.policy,
            configuration_path=args.configuration,
            inventory_path=args.inventory,
        )
    except ReportRebuildError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "owner_id": result["owner_id"],
                "lane": result["lane"],
                "manifest": str(args.evidence_root / "manifest.json"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
