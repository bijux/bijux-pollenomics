"""Tests for the complete SEAD source-key table contract."""

from bijux_pollenomics.collection.sources.sead.evidence.source_keys import (
    sead_source_key_table_plans,
    source_key_table_contract_rows,
    source_key_table_contract_sha256,
)


def test_source_key_contract_includes_sites_and_all_planned_tables() -> None:
    plans = sead_source_key_table_plans()
    rows = source_key_table_contract_rows()

    assert len(plans) == len(rows) == 61
    assert plans[0].table == "tbl_sites"
    assert rows[0] == {
        "ordinal": 0,
        "table": "tbl_sites",
        "primary_key": "site_id",
        "projection_fields": [
            "site_id",
            "site_name",
            "national_site_identifier",
            "latitude_dd",
            "longitude_dd",
            "altitude",
            "site_description",
            "site_uuid",
        ],
        "filter_field": "site_id",
        "dependencies": [],
    }
    assert len({plan.table for plan in plans}) == 61
    assert source_key_table_contract_sha256(rows) == (
        "9a174f201d8b0d382e3fed339658d3a884a26b4413a20874d6491ba72f9250c5"
    )


def test_source_key_contract_digest_detects_plan_semantic_changes() -> None:
    rows = source_key_table_contract_rows()
    changed = [dict(row) for row in rows]
    changed[0]["primary_key"] = "changed_site_id"

    assert source_key_table_contract_sha256(changed) != (
        "9a174f201d8b0d382e3fed339658d3a884a26b4413a20874d6491ba72f9250c5"
    )
