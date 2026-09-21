"""Source-locked R dependency inputs; never a runtime host dependency."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


class ReferenceRefusal(ValueError):
    """A missing or inconsistent reference prerequisite cannot certify parity."""


@dataclass(frozen=True)
class Source:
    """Identity and exact archive bytes for one locked R source package."""

    package: str
    version: str
    url: str
    sha256: str
    byte_count: int
    archive_filename: str


@dataclass(frozen=True)
class ReferenceLock:
    """Validated source lock with its ordered package installation plan."""

    path: Path
    payload: dict[str, Any]
    sources: tuple[Source, ...]
    install_order: tuple[str, ...]


def _load_lock(path: Path) -> ReferenceLock:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ReferenceRefusal(f"Duplicate lock field: {key}")
            value[key] = item
        return value

    value = json.loads(path.read_bytes(), object_pairs_hook=unique)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "lra-r-source-lock.v1"
    ):
        raise ReferenceRefusal("Unsupported R source lock")
    records = [value["r"], *value["packages"]]
    sources = []
    for row in records:
        for name in ("package", "version", "url", "sha256", "archive_filename"):
            if not isinstance(row.get(name), str) or not row[name]:
                raise ReferenceRefusal(f"Invalid source field: {name}")
        if not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9.]*", row["package"]
        ) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise ReferenceRefusal("Invalid package identity/digest")
        if (
            "/" in row["archive_filename"]
            or "\\" in row["archive_filename"]
            or row["archive_filename"] in {".", ".."}
        ):
            raise ReferenceRefusal("Unsafe source archive filename")
        if not row["url"].startswith("https://cran.r-project.org/src/") or not row[
            "url"
        ].endswith("/" + row["archive_filename"]):
            raise ReferenceRefusal(
                "Source must be an exact authoritative CRAN archive URL"
            )
        if (
            isinstance(row["byte_count"], bool)
            or not isinstance(row["byte_count"], int)
            or row["byte_count"] < 1
        ):
            raise ReferenceRefusal("Invalid archive byte count")
        sources.append(Source(**{key: row[key] for key in Source.__dataclass_fields__}))
    names = [row.package for row in sources]
    order = value["install_order"]
    if (
        len(names) != len(set(names))
        or not isinstance(order, list)
        or any(not isinstance(v, str) for v in order)
        or len(order) != len(set(order))
        or set(order) != set(names) - {"R"}
    ):
        raise ReferenceRefusal("Incomplete or duplicate install order")
    observed = {"R", *value["base_packages"]}
    by_name = {row["package"]: row for row in records}
    for name in order:
        if any(
            edge["package"] not in observed for edge in by_name[name]["dependencies"]
        ):
            raise ReferenceRefusal("Dependency order is not closed")
        observed.add(name)
    if (
        value["runtime_policy"]["r_version"] != value["r"]["version"]
        or value["runtime_policy"]["numerical_threads"] != 1
    ):
        raise ReferenceRefusal("Runtime policy disagrees with the R source lock")
    return ReferenceLock(path, value, tuple(sources), tuple(order))


def load_lock(path: Path) -> ReferenceLock:
    """Malformed or unsupported lock content is always a typed refusal."""
    try:
        result = _load_lock(path)
        reference = result.payload["reference"]
        if (
            reference["package"] != "disqover"
            or reference["version"] != "0.9.14"
            or reference["sha256"]
            != "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
        ):
            raise ReferenceRefusal("Unsupported reference source identity")
        if result.sources[0].package != "R" or result.sources[0].version != "4.6.0":
            raise ReferenceRefusal("Unsupported reference R source profile")
        base_names = {
            "base",
            "compiler",
            "datasets",
            "graphics",
            "grDevices",
            "grid",
            "methods",
            "parallel",
            "splines",
            "stats",
            "stats4",
            "tcltk",
            "tools",
            "utils",
        }
        if not set(result.payload["base_packages"]) <= base_names or any(
            version != result.sources[0].version
            for version in result.payload["base_packages"].values()
        ):
            raise ReferenceRefusal(
                "Base-package declarations disagree with the locked R runtime"
            )
        policy = result.payload["runtime_policy"]
        if (
            type(policy.get("numerical_threads")) is not int
            or policy["numerical_threads"] != 1
            or policy.get("python_minor") != "3.11"
            or policy.get("locale") not in {"C", "C.UTF-8"}
            or policy.get("r_configure_args")
            != ["--with-x=no", "--enable-R-shlib", "--without-recommended-packages"]
        ):
            raise ReferenceRefusal("Unsupported or malformed reference runtime policy")
        configuration = policy.get("package_configure_args")
        if configuration is not None and configuration != {
            "stringi": ["--disable-icu-bundle", "--with-extra-cxxflags=-std=gnu++17"]
        }:
            raise ReferenceRefusal("Unsupported reference package configuration")
        for source in result.sources:
            if any(ord(char) < 32 for char in source.archive_filename + source.url):
                raise ReferenceRefusal("Control characters in archive identity")
        return result
    except ReferenceRefusal:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ReferenceRefusal("Malformed or unreadable R source lock") from error


def read_json(data: bytes) -> Any:
    """Decode evidence JSON while refusing duplicate keys and nonfinite numbers."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ReferenceRefusal("Duplicate evidence JSON field")
            result[key] = value
        return result

    def nonfinite(value: str) -> None:
        raise ReferenceRefusal("Nonfinite evidence JSON number")

    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, TypeError, UnicodeError) as error:
        raise ReferenceRefusal("Malformed evidence JSON") from error
