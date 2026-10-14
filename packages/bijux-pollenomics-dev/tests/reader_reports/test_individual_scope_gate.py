"""Keep the ordinary claim gate stricter than legacy citation-route reading."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    parse_routes,
    render_route,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    FIELDS,
)
from bijux_pollenomics_dev.reader_reports import scientific_routes
from bijux_pollenomics_dev.reader_reports.scientific_limits import render_report

ROOT = Path(__file__).resolve().parents[4]


def verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "scientific_scope_gate", ROOT / "reports/needed/verify-claims.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ordinary_gate_requires_individual_fields_not_only_a_canonical_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = verifier()
    evidence = tmp_path / "reports/science/evidence.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b'{"fixture":true}\n')
    consumer = tmp_path / "reports/needed/consumer.py"
    consumer.parent.mkdir(parents=True)
    consumer.write_text('"""Source-free fixture consumer."""\n')
    (consumer.parent / "claim-account-sources.json").write_text(
        json.dumps({"schema_version": 1, "supplemental_report_paths": []})
    )
    (consumer.parent / "scientific-reader-sources.json").write_text(
        json.dumps({"schema_version": 1, "non_scientific_readers": []})
    )
    primary = tmp_path / "reports/science/account.md"
    original = b"# Conditional fixture\n\nNo scientific observations are used.\n"
    row: dict[str, str] = dict.fromkeys(module.FIELDS, "Declared source-free fixture.")
    row.update(
        report_path="reports/science/account.md",
        source_report_sha256=hashlib.sha256(original).hexdigest(),
        cause_categories="data",
        retained_evidence_paths="reports/science/evidence.json",
        existing_consumer_paths="reports/needed/consumer.py",
        packet_reference="none",
    )
    primary.write_bytes(render_report(original, row))
    row["source_report_sha256"] = hashlib.sha256(primary.read_bytes()).hexdigest()
    reader = tmp_path / "docs/report/fixture/README.md"
    reader.parent.mkdir(parents=True)
    authored = b"# Earlier citation\n\nThis pointer adds no new observations.\n"
    value: dict[str, Any] = {
        "reader_path": "docs/report/fixture/README.md",
        "scope_reason": "Source-free fixture citation with no new experiment.",
        "canonical_accounts": [
            {
                "report_path": row["report_path"],
                "source_sha256": row["source_report_sha256"],
            }
        ],
    }
    routes = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))
    reader.write_bytes(render_route(authored, routes[value["reader_path"]]))
    monkeypatch.setattr(scientific_routes, "load_routes", lambda: routes)
    legacy = scientific_routes.validate_reader_routes(tmp_path, [row])
    assert legacy["unreviewed_scientific_wrappers"] == 1
    with pytest.raises(ValueError, match="lack individual qualifications"):
        module.validate(tmp_path, [row], set())

    value["qualification"] = {
        "authored_reader_sha256": hashlib.sha256(authored).hexdigest(),
        "fields": {key: f"Source-free fixture {label}." for key, label in FIELDS},
        "evidence_pins": [
            {
                "path": "reports/science/evidence.json",
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
        ],
    }
    routes = parse_routes(json.dumps({"schema_version": 1, "routes": [value]}))
    reader.write_bytes(render_route(authored, routes[value["reader_path"]]))
    module.validate(tmp_path, [row], set())
