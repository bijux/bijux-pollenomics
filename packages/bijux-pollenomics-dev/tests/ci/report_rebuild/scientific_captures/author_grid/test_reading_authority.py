"""Keep sealed historical grid authority distinct from current rendered readers."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    authored_reader,
    parse_routes,
    render_route,
    verified_authored_reader,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid import (
    admission,
)

READER = "docs/report/constructed/REPORT.md"
FIELD_NAMES = (
    "supported_claim",
    "unsupported_claim",
    "actual_verification_performed",
    "remaining_input_or_review",
    "cause_category",
    "consequence",
    "precise_next_acceptance_route",
    "negative_or_refused_result",
    "matched_denominator",
)


def authority() -> dict[str, Any]:
    """Return a single constructed route with prose and machine evidence roles."""
    return {
        "schema_version": 1,
        "routes": [
            {
                "reader_path": READER,
                "canonical_accounts": [
                    {
                        "report_path": "reports/science/constructed.md",
                        "source_sha256": "a" * 64,
                    }
                ],
                "scope_reason": "Current source-Python control; not installed-distribution execution.",
                "qualification": {
                    "authored_reader_sha256": "b" * 64,
                    "fields": {
                        name: "Constructed " + name + "." for name in FIELD_NAMES
                    },
                    "evidence_pins": [
                        {
                            "path": "reports/science/constructed.json",
                            "sha256": "c" * 64,
                        },
                        {
                            "path": "docs/report/constructed/rows.csv",
                            "sha256": "d" * 64,
                        },
                        {
                            "path": "docs/report/constructed/notes.md",
                            "sha256": "e" * 64,
                        },
                        {
                            "path": "docs/report/constructed/reader.py",
                            "sha256": "f" * 64,
                        },
                        {
                            "path": "docs/report/constructed/formula.tex",
                            "sha256": "0" * 64,
                        },
                    ],
                },
            }
        ],
    }


def test_legacy_projection_preserves_all_fields_paths_and_machine_hashes() -> None:
    original = authority()
    routes = admission._captured_reading_routes(json.dumps(original))
    projected = deepcopy(original)
    projected["schema_version"] = 2
    route = projected["routes"][0]
    del route["canonical_accounts"][0]["source_sha256"]
    del route["qualification"]["authored_reader_sha256"]
    for pin in route["qualification"]["evidence_pins"][2:]:
        del pin["sha256"]
    assert routes == parse_routes(json.dumps(projected))
    assert original == authority()
    evidence = routes[READER].qualification
    assert evidence is not None
    assert [pin.sha256 for pin in evidence.evidence] == [
        "c" * 64,
        "d" * 64,
        None,
        None,
        None,
    ]


def test_changed_raw_machine_pin_remains_a_distinct_authority() -> None:
    original = authority()
    changed = deepcopy(original)
    changed["routes"][0]["qualification"]["evidence_pins"][0]["sha256"] = "9" * 64
    assert admission._captured_reading_routes(
        json.dumps(original)
    ) != admission._captured_reading_routes(json.dumps(changed))


@pytest.mark.parametrize(
    "where", ["root", "route", "account", "qualification", "evidence"]
)
def test_unknown_legacy_fields_refuse(where: str) -> None:
    value = authority()
    route = value["routes"][0]
    selected = {
        "root": value,
        "route": route,
        "account": route["canonical_accounts"][0],
        "qualification": route["qualification"],
        "evidence": route["qualification"]["evidence_pins"][0],
    }[where]
    selected["unknown"] = True
    with pytest.raises((ValueError, KeyError, TypeError)):
        admission._captured_reading_routes(json.dumps(value))


@pytest.mark.parametrize(
    "kind",
    [
        "schema",
        "boolean_schema",
        "duplicate_reader",
        "missing_field",
        "escape_reader",
        "self_account",
        "bad_raw_hash",
        "missing_raw_hash",
        "bad_prose_hash",
    ],
)
def test_malformed_legacy_authority_does_not_become_a_current_route(kind: str) -> None:
    value = authority()
    row = value["routes"][0]
    if kind == "schema":
        value["schema_version"] = 2
    elif kind == "boolean_schema":
        value["schema_version"] = True
    elif kind == "duplicate_reader":
        value["routes"].append(deepcopy(row))
    elif kind == "missing_field":
        del row["qualification"]["fields"]["supported_claim"]
    elif kind == "escape_reader":
        row["reader_path"] = "../REPORT.md"
    elif kind == "self_account":
        row["canonical_accounts"][0]["report_path"] = READER
    elif kind == "bad_raw_hash":
        row["qualification"]["evidence_pins"][0]["sha256"] = "bad"
    elif kind == "missing_raw_hash":
        del row["qualification"]["evidence_pins"][0]["sha256"]
    else:
        row["qualification"]["authored_reader_sha256"] = "bad"
    with pytest.raises((ValueError, KeyError, TypeError)):
        admission._captured_reading_routes(json.dumps(value))


def test_duplicate_json_fields_refuse_before_projection() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        admission._captured_reading_routes(
            '{"schema_version":1,"schema_version":1,"routes":[]}'
        )


def test_current_footer_is_verified_while_old_capsule_bytes_are_not_relabelled() -> (
    None
):
    route = admission._captured_reading_routes(json.dumps(authority()))[READER]
    raw = b"# Constructed raw writer text\n"
    current = render_route(raw, route)
    assert verified_authored_reader(current, route) == raw
    assert authored_reader(current) == raw
    changed = current.replace(
        b"Constructed supported_claim.", b"Promoted unsupported claim."
    )
    with pytest.raises(ValueError, match="differs"):
        verified_authored_reader(changed, route)
    with pytest.raises(ValueError, match="must be terminal"):
        authored_reader(current + b"tail")
