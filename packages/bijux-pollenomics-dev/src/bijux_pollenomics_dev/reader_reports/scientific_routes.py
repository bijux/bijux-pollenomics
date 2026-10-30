"""Verify every scientific prose surface has a source-bound reading authority."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    Route,
    load_routes,
    render_route,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    validate_evidence,
)

from .source import repository_file


def validate_reader_routes(
    root: Path,
    claims: list[dict[str, str]],
    routes: Mapping[str, Route] | None = None,
    *,
    require_individual_qualifications: bool = False,
) -> dict[str, int]:
    """Refuse missing dispositions, unknown accounts and altered generated routes."""
    routes = load_routes() if routes is None else routes
    if require_individual_qualifications and any(
        route.qualification is None for route in routes.values()
    ):
        raise ValueError("Scientific wrappers still lack individual qualifications")
    primary = {row["report_path"] for row in claims}
    path = repository_file(root, "reports/needed/scientific-reader-sources.json")
    authority: Any = json.loads(path.read_text())
    if (
        not isinstance(authority, dict)
        or authority.get("schema_version") != 1
        or not isinstance(authority.get("non_scientific_readers"), list)
    ):
        raise ValueError("Scientific reader disposition authority is invalid")
    excluded: set[str] = set()
    for row in authority["non_scientific_readers"]:
        if (
            not isinstance(row, dict)
            or row.get("classification")
            not in {"engineering_reader", "navigation_or_governance"}
            or not isinstance(row.get("scope_reason"), str)
            or not row["scope_reason"].strip()
        ):
            raise ValueError("Scientific reader exclusion lacks a concrete disposition")
        relative = row.get("reader_path")
        if (
            not isinstance(relative, str)
            or PurePosixPath(relative).parts[:2] != ("docs", "report")
            or PurePosixPath(relative).suffix != ".md"
            or relative in excluded
        ):
            raise ValueError("Scientific reader exclusion is malformed or duplicated")
        repository_file(root, relative)
        excluded.add(relative)
    routed = set(routes)
    if excluded & routed or excluded & set(primary) or routed & set(primary):
        raise ValueError("Scientific reader dispositions overlap")
    physical = {
        p.relative_to(root).as_posix() for p in (root / "docs/report").rglob("*.md")
    }
    expected = routed | excluded | {p for p in primary if p.startswith("docs/report/")}
    if physical != expected:
        raise ValueError(
            f"Scientific reader coverage differs: unclassified={sorted(physical - expected)}, missing={sorted(expected - physical)}"
        )
    for relative, route in routes.items():
        source = repository_file(root, relative)
        raw = source.read_bytes()
        if raw != render_route(raw, route):
            raise ValueError(f"Scientific reader route missing or changed: {relative}")
        if route.qualification is not None:
            validate_evidence(root, route.qualification, portal=False)
        for account in route.accounts:
            if account.report_path not in primary:
                raise ValueError(
                    f"Scientific reader account authority changed: {relative}"
                )
            repository_file(root, account.report_path)
    return {
        "primary_accounts": len(primary),
        "scientific_wrappers": len(routed),
        "individually_qualified_wrappers": sum(
            route.qualification is not None for route in routes.values()
        ),
        "unreviewed_scientific_wrappers": sum(
            route.qualification is None for route in routes.values()
        ),
        "non_scientific_readers": len(excluded),
        "physical_docs_report_markdown": len(physical),
    }
