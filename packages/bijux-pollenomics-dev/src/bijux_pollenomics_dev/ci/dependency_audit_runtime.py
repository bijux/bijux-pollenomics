"""Require active public audit pins to match the invoking installed interpreter."""

from __future__ import annotations

import importlib.metadata as metadata
import json
import sys
from typing import TypedDict

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version


class InstalledAuditRuntime(TypedDict):
    """Authenticate the active package closure without auditing unrelated installers."""

    python_executable: str
    python_prefix: str
    marker_environment: dict[str, str]
    active_locked_public_versions: dict[str, str]
    actual_installed_public_versions: dict[str, str]
    scope: str


def installed_runtime(text: str) -> InstalledAuditRuntime:
    """Refuse missing, ambiguous or changed installed distributions before auditing."""
    environment: dict[str, str] = {}
    for key, value in default_environment().items():
        if not isinstance(value, str):
            raise ValueError("runtime marker environment is not text")
        environment[key] = value
    active: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        requirement = Requirement(line)
        if requirement.url is not None or requirement.extras:
            raise ValueError("runtime audit requires exact public distributions")
        specifiers = list(requirement.specifier)
        if len(specifiers) != 1 or specifiers[0].operator != "==":
            raise ValueError("runtime audit requires exact locked public versions")
        version = specifiers[0].version
        Version(version)
        if requirement.marker is not None and not requirement.marker.evaluate(
            environment
        ):
            continue
        normalized = canonicalize_name(requirement.name)
        if normalized in active and Version(active[normalized]) != Version(version):
            raise ValueError("conflicting active public versions: " + normalized)
        active[normalized] = version
    if not active:
        raise ValueError("runtime audit has no active locked public distributions")
    actual: dict[str, str] = {}
    mismatches: dict[str, dict[str, str | None]] = {}
    for name, expected in active.items():
        if len(list(metadata.distributions(name=name))) > 1:
            raise ValueError("ambiguous installed public distribution: " + name)
        try:
            found = metadata.version(name)
        except metadata.PackageNotFoundError:
            mismatches[name] = {"expected": expected, "actual": None}
            continue
        actual[name] = found
        if Version(found) != Version(expected):
            mismatches[name] = {"expected": expected, "actual": found}
    if mismatches:
        raise ValueError(
            "installed public versions differ from active audited lock pins: "
            + json.dumps(mismatches, sort_keys=True)
        )
    return {
        "python_executable": sys.executable,
        "python_prefix": sys.prefix,
        "marker_environment": environment,
        "active_locked_public_versions": active,
        "actual_installed_public_versions": actual,
        "scope": (
            "Exact active public package dependency closure in the invoking "
            "installed interpreter. Other installer/bootstrap distributions "
            "are outside this declared audit closure; workspace source custody "
            "and public vulnerability assessment remain separate."
        ),
    }
