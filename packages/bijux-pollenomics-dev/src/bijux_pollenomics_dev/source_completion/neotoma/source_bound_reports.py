"""Publish exact retained report bytes with independent source and artifact custody."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from bijux_pollenomics.core.owned_tree import publish_new_output_tree
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
    _object,
    _regular_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _write_reserved_file(
    directory: Path, name: str, payload: bytes, expected: tuple[int, int]
) -> None:
    """Never replace a competing file or follow a changed reserved output directory."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(directory, flags)
    try:
        if (
            _identity(os.fstat(descriptor)) != expected
            or _identity(_regular_path(directory, directory=True).stat()) != expected
        ):
            raise ReportRebuildError("reserved report directory identity changed")
        handle = os.open(
            name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o666,
            dir_fd=descriptor,
        )
        with os.fdopen(handle, "w+b") as stream:
            if _identity(_regular_path(directory, directory=True).stat()) != expected:
                raise ReportRebuildError(
                    "reserved report directory changed before write"
                )
            stream.write(payload)
            stream.flush()
            stream.seek(0)
            physical = os.fstat(stream.fileno())
            mapped = _regular_path(directory / name)
            if (
                physical.st_nlink != 1
                or _identity(mapped.stat()) != _identity(physical)
                or _identity(_regular_path(directory, directory=True).stat())
                != expected
                or stream.read() != payload
            ):
                raise ReportRebuildError(
                    "reserved report file identity or bytes changed"
                )
    finally:
        os.close(descriptor)


def publish(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    repository_inputs: tuple[Path, ...],
    qualify_selection: Callable[[QualifiedReportSources], None],
    produce: Callable[[QualifiedReportSources, Path], None],
    expected_members: frozenset[str],
    verify_report: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    """Retain every raw producer member and map only its freshly generated report."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(repository, source_root, descriptor)
    qualify_selection(qualified)
    inputs = {
        **qualified.inputs,
        **{p.as_posix(): _regular_path(repository / p) for p in repository_inputs},
    }

    def identity() -> dict[str, Any]:
        for path in inputs.values():
            _regular_path(path)
            if path.stat().st_nlink != 1:
                raise ReportRebuildError("retained source input has a physical alias")
        return producer_input_identity(inputs, repository)

    before = identity()
    # Raw correspondence tables stay in artifacts, outside the governed JSON mapping.
    retained_root = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}-retained-", dir=destination.parent
        )
    )
    raw = retained_root / "source-products"
    produce(qualified, raw)
    if frozenset(p.name for p in raw.iterdir()) != expected_members:
        raise ReportRebuildError("retained source report member population differs")
    for path in raw.iterdir():
        _regular_path(path)
        if path.stat().st_nlink != 1:
            raise ReportRebuildError("retained output has a physical alias")
    report_file = _regular_path(raw / "report.json")
    report_bytes = report_file.read_bytes()
    report = _object(report_bytes)
    verify_report(report)
    after = validated_external_report_sources(repository, source_root, descriptor)
    if after != qualified or identity() != before:
        raise ReportRebuildError(
            "retained report source inputs changed during publication"
        )
    require_absent_artifact_output(repository, destination)
    mapped = Path(tempfile.mkdtemp(prefix=".mapped-report-", dir=retained_root))
    mapped_identity = _identity(_regular_path(mapped, directory=True).stat())
    _write_reserved_file(mapped, "report.json", report_bytes, mapped_identity)
    custody_bytes = (
        json.dumps(
            {
                "inputs": before,
                "mapped_report": str(destination / "report.json"),
                "scope": "technical retained-report accounting; no new scientific admission",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()
    _write_reserved_file(
        retained_root,
        "source-custody.json",
        custody_bytes,
        _identity(retained_root.stat()),
    )
    require_absent_artifact_output(repository, destination)
    if _identity(_regular_path(mapped, directory=True).stat()) != mapped_identity:
        raise ReportRebuildError("reserved mapped directory changed before publication")
    publish_new_output_tree(final_output_root=destination, staging_output_root=mapped)
    if (
        _identity(_regular_path(destination, directory=True).stat()) != mapped_identity
        or {p.name for p in destination.iterdir()} != {"report.json"}
        or _regular_path(destination / "report.json").read_bytes() != report_bytes
    ):
        raise ReportRebuildError("published retained report identity or bytes changed")
    return report
