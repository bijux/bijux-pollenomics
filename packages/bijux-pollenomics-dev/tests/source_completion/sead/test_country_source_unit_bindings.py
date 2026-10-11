"""Keep normalized country binding keys faithful to their native types."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead_country_source_units import account

COUNTRIES = (
    ("SE", "Sweden", 1925),
    ("DK", "Denmark", 59),
    ("NO", "Norway", 45),
    ("FI", "Finland", 40),
)


def _population() -> tuple[
    dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, Any]
]:
    sites: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    bindings: list[list[object]] = []
    site_id = 0
    for code_index, (code, name, count) in enumerate(COUNTRIES):
        for _ in range(count):
            site_id += 1
            uuid = f"site-{site_id}"
            sites.append({"site_id": site_id, "site_uuid": uuid})
            decisions.append(
                {
                    "site_id": site_id,
                    "site_uuid": uuid,
                    "governed_country_code": code,
                    "decision": {
                        "decision_status": "assigned",
                        "decision_method": "strict_boundary_containment",
                        "derived_country": name,
                    },
                }
            )
            bindings.append([site_id, uuid, code_index, 0])
    for status, count in (("review", 103), ("unassigned", 23)):
        for _ in range(count):
            site_id += 1
            decisions.append(
                {
                    "site_id": site_id,
                    "site_uuid": f"site-{site_id}",
                    "governed_country_code": "UNASSIGNED",
                    "decision": {"decision_status": status, "derived_country": None},
                }
            )
    tables: dict[str, list[dict[str, Any]]] = {
        "tbl_sites": sites,
        "tbl_sample_groups": [],
        "tbl_physical_samples": [],
        "tbl_analysis_entities": [],
        "tbl_datasets": [],
        "tbl_analysis_values": [],
    }
    contract: dict[str, Any] = {
        "fields": [
            "site_id",
            "site_uuid",
            "country_code_index",
            "assignment_method_index",
        ],
        "assignment_methods": ["strict_boundary_containment"],
        "country_codes": [row[0] for row in COUNTRIES],
        "rows": bindings,
    }
    return tables, decisions, contract


def test_valid_country_bindings_preserve_source_denominators() -> None:
    tables, decisions, contract = _population()
    rows, totals = account(tables, decisions, contract)
    assert len(rows) == 6
    assert totals["retrieved_site_count"] == 2069
    assert totals["decision_status_counts"] == {
        "assigned": 2069,
        "review": 103,
        "unassigned": 23,
    }
    assert sum(row["discovered_sites"] for row in rows[:4]) == 2069


@pytest.mark.parametrize(
    ("site_id", "field", "replacement"),
    [(1, 0, True), (1926, 2, True), (1, 3, False)],
)
def test_boolean_binding_fields_cannot_masquerade_as_integer_keys(
    site_id: int, field: int, replacement: bool
) -> None:
    tables, decisions, contract = _population()
    bindings = contract["rows"]
    assert isinstance(bindings, list)
    row = bindings[site_id - 1]
    assert isinstance(row, list)
    row[field] = replacement
    with pytest.raises(ValueError, match="normalized site country binding key changed"):
        account(tables, decisions, contract)
