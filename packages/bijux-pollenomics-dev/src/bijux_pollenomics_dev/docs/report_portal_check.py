"""Check the published report portal's file inventory and Markdown structure."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any

from bijux_pollenomics.reporting.presentation.report_portal.narrative_quality import (
    _build_quality_row,
)
from bijux_pollenomics.reporting.presentation.report_portal.pages import (
    _render_portal_pages,
)

REPORT_ROOT = Path("docs/report")
REGISTRY = REPORT_ROOT / "report_surface_registry.json"
QUALITY = REPORT_ROOT / "report_narrative_quality_review.json"
EXCLUDED = frozenset(
    {
        "docs/report/report_narrative_quality_review.json",
        "docs/report/report_narrative_quality_review.md",
        "docs/report/report_surface_registry.json",
        "docs/report/report_surface_registry.md",
    }
)
_NAVIGATION_PATHS = frozenset(
    {
        "index.md",
        "how-to-read.md",
        "maps/index.md",
        "scopes/index.md",
        "reviews/index.md",
        "caveats/index.md",
        "maintenance/index.md",
    }
)


class ReportPortalCheckError(ValueError):
    """The report portal is stale or its inventory cannot be trusted."""


@dataclass(frozen=True)
class ReportPortalCheckResult:
    """Counts from the exact checked filesystem population."""

    report_file_count: int
    excluded_metadata_count: int
    registered_surface_count: int
    markdown_page_count: int


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportPortalCheckError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportPortalCheckError(f"cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ReportPortalCheckError(f"{path} must contain a JSON object")
    return payload


def _count(payload: dict[str, Any], key: str, owner: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ReportPortalCheckError(f"{owner}.{key} must be a non-negative integer")
    return value


def _rows(payload: dict[str, Any], owner: str) -> list[dict[str, Any]]:
    value = payload.get("rows")
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ReportPortalCheckError(f"{owner}.rows must be a list of objects")
    return value


def _repository_path(row: dict[str, Any], owner: str) -> str:
    value = row.get("repository_path")
    if not isinstance(value, str) or not value.startswith("docs/report/"):
        raise ReportPortalCheckError(f"{owner}.repository_path is outside docs/report")
    path = PurePosixPath(value)
    if str(path) != value or ".." in path.parts or "\\" in value or len(path.parts) < 3:
        raise ReportPortalCheckError(
            f"{owner}.repository_path is not canonical: {value}"
        )
    return value


def _regular_files(report_root: Path) -> dict[str, Path]:
    if report_root.is_symlink() or not report_root.is_dir():
        raise ReportPortalCheckError(
            f"report root must be a real directory: {report_root}"
        )
    files: dict[str, Path] = {}
    for directory, names, filenames in os.walk(report_root, followlinks=False):
        parent = Path(directory)
        for name in names:
            path = parent / name
            if not stat.S_ISDIR(path.lstat().st_mode):
                raise ReportPortalCheckError(f"report directory is not real: {path}")
        for name in filenames:
            path = parent / name
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ReportPortalCheckError(f"report file is not regular: {path}")
            relative = path.relative_to(report_root).as_posix()
            files[f"docs/report/{relative}"] = path
    return files


def _confined_report_root(repository: Path) -> Path:
    report_root = repository / REPORT_ROOT
    try:
        resolved = report_root.resolve(strict=True)
    except OSError as error:
        raise ReportPortalCheckError(f"cannot resolve report root: {error}") from error
    if not resolved.is_relative_to(repository):
        raise ReportPortalCheckError(f"report root escapes repository: {report_root}")
    for ancestor in (repository / "docs", report_root):
        if not stat.S_ISDIR(ancestor.lstat().st_mode):
            raise ReportPortalCheckError(
                f"report ancestor is not a real directory: {ancestor}"
            )
    return report_root


def _count_map(payload: dict[str, Any], key: str) -> dict[str, int]:
    declared = payload.get(key)
    if not isinstance(declared, dict) or any(
        not isinstance(label, str)
        or not label
        or not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for label, value in declared.items()
    ):
        raise ReportPortalCheckError(f"{key} must be a string-to-count object")
    return declared


def _counter_matches(
    payload: dict[str, Any], key: str, rows: list[dict[str, Any]], field: str
) -> None:
    declared = _count_map(payload, key)
    actual: Counter[str] = Counter()
    for row in rows:
        label = row.get(field)
        if not isinstance(label, str) or not label:
            raise ReportPortalCheckError(f"registry row has invalid {field}")
        actual[label] += 1
    if declared != dict(actual):
        raise ReportPortalCheckError(f"{key} does not match registry rows")


def _markdown_structure(text: str) -> tuple[list[str], list[str]]:
    """Compare rendered navigation headings and destinations without prose pins."""
    headings = [line.strip() for line in text.splitlines() if line.startswith("#")]
    destinations = re.findall(r"\[[^]\n]+\]\(([^)\n]+)\)", text)
    return headings, destinations


def check_report_portal(repository: Path) -> ReportPortalCheckResult:
    """Reconcile portal metadata with real files and current Markdown structure.

    Machine-output content remains governed by its domain manifests. The
    narrative-quality inventory checks page paths and layout coverage; it
    does not assert human or scientific review.
    """
    repository = repository.resolve()
    report_root = _confined_report_root(repository)
    files = _regular_files(report_root)
    registry = _load_object(files.get(REGISTRY.as_posix(), repository / REGISTRY))
    quality = _load_object(files.get(QUALITY.as_posix(), repository / QUALITY))

    if registry.get("schema_version") != "report-surface-registry.v2":
        raise ReportPortalCheckError("unsupported report surface registry schema")
    if registry.get("inventory_scope") != (
        "all input files plus generated navigation pages; registry metadata excluded"
    ):
        raise ReportPortalCheckError("registry inventory scope has changed")
    if registry.get("validation_scope") != (
        "path inventory and Markdown structure; machine outputs retain their domain manifests"
    ):
        raise ReportPortalCheckError("registry validation scope has changed")
    if quality.get("schema_version") != "report-narrative-quality-review.v2":
        raise ReportPortalCheckError("unsupported narrative quality schema")
    if quality.get("review_scope") != (
        "automated layout signals; no human or scientific review"
    ):
        raise ReportPortalCheckError("narrative quality review scope has changed")

    excluded = registry.get("excluded_metadata_paths")
    if (
        not isinstance(excluded, list)
        or len(excluded) != len(EXCLUDED)
        or any(not isinstance(path, str) for path in excluded)
        or frozenset(excluded) != EXCLUDED
    ):
        raise ReportPortalCheckError(
            "registry must exclude the four exact portal metadata files"
        )
    if not files.keys() >= EXCLUDED:
        raise ReportPortalCheckError("an excluded portal metadata file is missing")

    registry_rows = _rows(registry, "registry")
    registry_paths: dict[str, dict[str, Any]] = {}
    markdown_paths: set[str] = set()
    for row in registry_rows:
        path = _repository_path(row, "registry row")
        if path in registry_paths:
            raise ReportPortalCheckError(f"duplicate registry path: {path}")
        registry_paths[path] = row
        actual_file = files.get(path)
        if actual_file is None:
            raise ReportPortalCheckError(f"registry path is missing: {path}")
        expected_format = actual_file.suffix.lstrip(".") or "none"
        if row.get("format") != expected_format:
            raise ReportPortalCheckError(f"registry format diverges: {path}")
        if "content_sha256" in row:
            raise ReportPortalCheckError(
                f"registry row owns generic content hash: {path}"
            )
        if expected_format == "md":
            markdown_paths.add(path)

    actual_paths = files.keys() - EXCLUDED
    if registry_paths.keys() != actual_paths:
        missing = sorted(actual_paths - registry_paths.keys())
        extra = sorted(registry_paths.keys() - actual_paths)
        raise ReportPortalCheckError(
            f"registry population differs: missing={missing}, extra={extra}"
        )
    if _count(registry, "surface_count", "registry") != len(registry_rows):
        raise ReportPortalCheckError("registry surface_count diverges")
    for count_key, field in (
        ("family_counts", "family"),
        ("audience_counts", "audience"),
        ("geography_counts", "geography"),
    ):
        _counter_matches(registry, count_key, registry_rows, field)

    quality_rows = _rows(quality, "quality")
    quality_paths: set[str] = set()
    quality_postures: Counter[str] = Counter()
    for row in quality_rows:
        path = _repository_path(row, "quality row")
        if path in quality_paths:
            raise ReportPortalCheckError(f"duplicate quality path: {path}")
        quality_paths.add(path)
        if path not in markdown_paths:
            raise ReportPortalCheckError(
                f"quality path is not registered Markdown: {path}"
            )
        if "content_sha256" in row:
            raise ReportPortalCheckError(
                f"quality row owns generic content hash: {path}"
            )
        for field in (
            "prose_paragraph_count",
            "link_bullet_count",
            "bullet_sentence_count",
            "heading_count",
            "table_line_count",
        ):
            _count(row, field, f"quality row {path}")
        expected = _build_quality_row(
            path.removeprefix("docs/report/"), files[path].read_text(encoding="utf-8")
        )
        if row != expected:
            raise ReportPortalCheckError(f"quality layout signals are stale: {path}")
        posture = row.get("quality_posture")
        if not isinstance(posture, str) or not posture:
            raise ReportPortalCheckError(f"quality posture is missing: {path}")
        quality_postures[posture] += 1
    if quality_paths != markdown_paths:
        missing = sorted(markdown_paths - quality_paths)
        raise ReportPortalCheckError(
            f"quality Markdown coverage is incomplete: {missing}"
        )
    if _count(quality, "page_count", "quality") != len(quality_rows):
        raise ReportPortalCheckError("quality page_count diverges")
    if _count_map(quality, "quality_posture_counts") != dict(quality_postures):
        raise ReportPortalCheckError("quality posture counts diverge")

    existing_rows = [
        row
        for path, row in registry_paths.items()
        if path.removeprefix("docs/report/") not in _NAVIGATION_PATHS
    ]
    for relative_path, expected_text in _render_portal_pages(
        report_root, existing_rows
    ).items():
        actual = files[f"docs/report/{relative_path}"].read_text(encoding="utf-8")
        if _markdown_structure(actual) != _markdown_structure(expected_text):
            raise ReportPortalCheckError(
                f"portal navigation structure is stale: {relative_path}"
            )

    return ReportPortalCheckResult(
        report_file_count=len(files),
        excluded_metadata_count=len(EXCLUDED),
        registered_surface_count=len(registry_rows),
        markdown_page_count=len(markdown_paths),
    )


def main(argv: list[str] | None = None) -> int:
    """Check the published report portal's file inventory and Markdown structure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[5],
        help="repository root containing docs/report",
    )
    args = parser.parse_args(argv)
    try:
        result = check_report_portal(args.repository)
    except (OSError, ReportPortalCheckError) as error:
        print(f"report portal check failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
