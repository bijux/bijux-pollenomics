"""Expose individual scientific facts without silently accepting changed evidence."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    authored_reader,
    parse_routes,
    render_route,
    verified_authored_reader,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    FIELDS,
    parse_qualification,
    validate_evidence,
)


def record(root: Path) -> tuple[bytes, dict[str, Any]]:
    source = b"# Paired development comparison\n\nOwn support is140/184 bins.\n"
    evidence = root / "docs/report/comparison/report.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"scored":140,"observed":184,"refused":44}\n')
    value: dict[str, Any] = {
        "reader_path": "docs/report/comparison/README.md",
        "scope_reason": "Previously exposed observed-pollen development comparison.",
        "canonical_accounts": [
            {"report_path": "reports/science/account.md", "source_sha256": "a" * 64}
        ],
        "qualification": {
            "authored_reader_sha256": hashlib.sha256(source).hexdigest(),
            "fields": {
                key: f"Reader-specific {label}: retained140/184 bins."
                for key, label in FIELDS
            },
            "evidence_pins": [
                {
                    "path": "docs/report/comparison/report.json",
                    "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                }
            ],
        },
    }
    return source, value


def test_individual_nine_fields_preserve_authored_reader_and_exact_pins(
    tmp_path: Path,
) -> None:
    source, value = record(tmp_path)
    routes = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))
    route = routes[value["reader_path"]]
    result = render_route(source, route)
    assert authored_reader(result) == source
    for _, label in FIELDS:
        assert f"**{label}.**".encode() in result
    assert result.count(b"140/184") == 10
    assert b"](report.json)" in result
    assert route.qualification is not None
    validate_evidence(tmp_path, route.qualification, portal=False)
    validate_evidence(tmp_path / "docs/report", route.qualification, portal=True)
    assert render_route(result, route) == result
    assert b"unreviewed" not in result


@pytest.mark.parametrize(
    "change",
    [
        "field_missing",
        "field_blank",
        "html_field",
        "duplicate_pin",
        "empty_pins",
        "escape_pin",
        "bad_hash",
    ],
)
def test_incomplete_or_unbound_qualification_refuses(
    tmp_path: Path, change: str
) -> None:
    _, value = record(tmp_path)
    qualification = copy.deepcopy(value["qualification"])
    if change == "field_missing":
        del qualification["fields"]["matched_denominator"]
    elif change == "field_blank":
        qualification["fields"]["negative_or_refused_result"] = " "
    elif change == "html_field":
        qualification["fields"]["supported_claim"] = "<script>promote claim</script>"
    elif change == "empty_pins":
        qualification["evidence_pins"] = []
    elif change == "duplicate_pin":
        qualification["evidence_pins"] *= 2
    elif change == "escape_pin":
        qualification["evidence_pins"][0]["path"] = "docs/report/../../secret"
    else:
        qualification["authored_reader_sha256"] = "unbound"
    with pytest.raises(ValueError):
        parse_qualification(qualification)


@pytest.mark.parametrize(
    "change",
    [
        "authored_denominator",
        "evidence_bytes",
        "evidence_symlink",
        "malformed_block",
        "trailing_html",
    ],
)
def test_changed_source_or_managed_boundary_refuses(
    tmp_path: Path, change: str
) -> None:
    source, value = record(tmp_path)
    route = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))[
        value["reader_path"]
    ]
    assert route.qualification is not None
    if change == "authored_denominator":
        with pytest.raises(ValueError):
            render_route(source.replace(b"140/184", b"184/184"), route)
    elif change.startswith("evidence"):
        path = tmp_path / "docs/report/comparison/report.json"
        if change == "evidence_bytes":
            path.write_text('{"scored":184}')
        else:
            other = tmp_path / "copy.json"
            other.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(other)
        with pytest.raises(ValueError):
            validate_evidence(tmp_path, route.qualification, portal=False)
    else:
        rendered = render_route(source, route)
        rendered = (
            rendered.replace(b"scientific-account-route:end", b"missing:end")
            if change == "malformed_block"
            else rendered + b"<script>arbitrary trailing markup</script>"
        )
        with pytest.raises(ValueError):
            render_route(rendered, route)


def test_unqualified_route_explicitly_preserves_unreviewed_scope(
    tmp_path: Path,
) -> None:
    source, value = record(tmp_path)
    value.pop("qualification")
    route = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))[
        value["reader_path"]
    ]
    result = render_route(source, route)
    assert b"Individual wrapper qualification remains unreviewed." in result
    assert b"**Matched denominator.**" not in result
    assert authored_reader(result) == source


def test_self_rendered_evidence_hash_refuses(tmp_path: Path) -> None:
    _, value = record(tmp_path)
    value["qualification"]["evidence_pins"][0]["path"] = value["reader_path"]
    with pytest.raises(ValueError, match="own rendered hash"):
        parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))


@pytest.mark.parametrize("change", ["denominator", "inside_html", "trailing_html"])
def test_comparison_refuses_tampered_managed_prose(tmp_path: Path, change: str) -> None:
    source, value = record(tmp_path)
    route = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))[
        value["reader_path"]
    ]
    rendered = render_route(source, route)
    assert verified_authored_reader(source, route) == source
    assert verified_authored_reader(rendered, route) == source
    if change == "denominator":
        rendered = rendered.replace(
            b"Reader-specific Supported claim: retained140/184 bins.",
            b"Reader-specific Supported claim: retained184/184 bins.",
        )
    elif change == "inside_html":
        rendered = rendered.replace(
            b"## Scientific verification and limits",
            b"<script>unsupported admission</script>\n## Scientific verification and limits",
        )
    else:
        rendered += b"<script>arbitrary trailing HTML</script>"
    with pytest.raises(ValueError):
        verified_authored_reader(rendered, route)


def test_cross_wrapper_rendered_evidence_hash_refuses(tmp_path: Path) -> None:
    _, value = record(tmp_path)
    second = copy.deepcopy(value)
    second["reader_path"] = "docs/report/comparison/SECOND.md"
    value["qualification"]["evidence_pins"][0]["path"] = second["reader_path"]
    with pytest.raises(ValueError, match="another rendered wrapper hash"):
        parse_routes(json.dumps({"schema_version": 1, "routes": [value, second]}))
