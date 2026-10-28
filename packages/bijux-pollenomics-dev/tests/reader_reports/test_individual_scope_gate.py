"""Require individual qualifications through caller-supplied reader authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    parse_routes,
    render_route,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    FIELDS,
)
from bijux_pollenomics_dev.reader_reports.scientific_routes import (
    validate_reader_routes,
)


def test_individual_gate_preserves_unreviewed_and_exact_structured_evidence(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "reports/science/account.md"
    primary.parent.mkdir(parents=True)
    primary.write_text("# Source-free conditional account\n")
    reader = tmp_path / "docs/report/fixture/README.md"
    reader.parent.mkdir(parents=True)
    evidence = reader.parent / "result.json"
    evidence.write_text('{"scored":3,"requested":4,"refused":1}\n')
    authored = b"# Source-free fixture\n\nNo field observations.\n"
    record: dict[str, Any] = {
        "reader_path": "docs/report/fixture/README.md",
        "canonical_accounts": [{"report_path": "reports/science/account.md"}],
        "scope_reason": "Source-free conditional fixture; no scientific admission.",
    }
    claims = [{"report_path": "reports/science/account.md"}]
    dispositions = {"schema_version": 1, "non_scientific_readers": []}
    routes = parse_routes(json.dumps({"schema_version": 2, "routes": [record]}))
    reader.write_bytes(render_route(authored, routes[record["reader_path"]]))
    result = validate_reader_routes(
        tmp_path, claims, routes, reader_dispositions=dispositions
    )
    assert result["unreviewed_scientific_wrappers"] == 1
    with pytest.raises(ValueError, match="lack individual qualifications"):
        validate_reader_routes(
            tmp_path,
            claims,
            routes,
            reader_dispositions=dispositions,
            require_individual_qualifications=True,
        )
    record["qualification"] = {
        "fields": {key: f"Source-free {label}; retained3of4." for key, label in FIELDS},
        "evidence_pins": [
            {
                "path": "docs/report/fixture/result.json",
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
        ],
    }
    routes = parse_routes(json.dumps({"schema_version": 2, "routes": [record]}))
    reader.write_bytes(render_route(authored, routes[record["reader_path"]]))
    result = validate_reader_routes(
        tmp_path,
        claims,
        routes,
        reader_dispositions=dispositions,
        require_individual_qualifications=True,
    )
    assert result["individually_qualified_wrappers"] == 1
    assert result["unreviewed_scientific_wrappers"] == 0
    evidence.write_text('{"scored":4,"requested":4,"refused":0}\n')
    with pytest.raises(ValueError, match="evidence changed"):
        validate_reader_routes(
            tmp_path,
            claims,
            routes,
            reader_dispositions=dispositions,
            require_individual_qualifications=True,
        )
