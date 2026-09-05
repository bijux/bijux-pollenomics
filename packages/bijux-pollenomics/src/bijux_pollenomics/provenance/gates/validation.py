"""Fail-closed validation for recorded-gate requests and results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath, Path
import re

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

from ..release_evidence import ReleaseEvidenceError

_IDENTITY_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")


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


def _validate_gate_id(gate_id: str) -> None:
    if not isinstance(gate_id, str) or _IDENTITY_PATTERN.fullmatch(gate_id) is None:
        raise ReleaseEvidenceError(f"invalid gate identity: {gate_id!r}")


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
