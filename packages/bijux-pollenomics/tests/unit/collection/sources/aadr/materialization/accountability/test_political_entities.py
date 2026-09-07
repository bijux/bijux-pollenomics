"""AADR source-reported Political Entity reconciliation tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    reconcile_source_reported_political_entities,
    source_reported_political_entity_evidence,
)

from .support import reconciliation


def test_reconciliation_uses_only_exact_trimmed_source_values(tmp_path: Path) -> None:
    reconciled = reconcile_source_reported_political_entities(reconciliation(tmp_path))
    by_id = {record.genetic_id: record for record in reconciled}

    assert by_id["ID-DK"].disposition == "DK"
    assert by_id["ID-DK"].reconciliation_status == "exact"
    assert by_id["ID-DK"].evidence_groups[0].evidence.raw_value == " Denmark "
    assert by_id["ID-DK"].evidence_groups[0].evidence.trimmed_value == "Denmark"
    assert by_id["ID-FI"].disposition == "FI"
    assert by_id["ID-SE"].disposition == "SE"
    assert by_id["ID-OTHER"].disposition == "other"
    assert by_id["ID-MISSING"].disposition == "missing"
    assert by_id["ID-CONFLICT"].disposition == "conflict"
    assert by_id["ID-CONFLICT"].reconciliation_status == "conflict"
    assert by_id["ID-COMP"].disposition == "NO"
    assert by_id["ID-COMP"].reconciliation_status == "complementary"
    assert (
        sum(
            len(group.source_rows)
            for record in reconciled
            for group in record.evidence_groups
        )
        == 11
    )


def test_case_variant_is_other_and_never_inferred_as_target_country(
    tmp_path: Path,
) -> None:
    panel = reconciliation(tmp_path)
    record = next(record for record in panel.records if record.genetic_id == "ID-FI")
    changed_row = replace(
        record.source_evidence_rows[0],
        raw_tokens=tuple(
            "finland" if index == 1 else token
            for index, token in enumerate(record.source_evidence_rows[0].raw_tokens)
        ),
    )
    changed_record = replace(record, source_evidence_rows=(changed_row,))

    [result] = reconcile_source_reported_political_entities(
        replace(
            panel,
            records=(changed_record,),
            source_row_count=1,
            source_tables=(),
            unkeyed_rows=(),
        )
    )

    assert result.disposition == "other"
    assert result.evidence_groups[0].evidence.raw_value == "finland"


def test_evidence_distinguishes_blank_absent_token_and_absent_column(
    tmp_path: Path,
) -> None:
    panel = reconciliation(tmp_path)
    row = next(
        record.source_evidence_rows[0]
        for record in panel.records
        if record.genetic_id == "ID-MISSING"
    )

    blank = source_reported_political_entity_evidence(row)
    absent_token = source_reported_political_entity_evidence(
        replace(row, raw_tokens=(row.raw_tokens[0],))
    )
    without_column_names = tuple(
        name for name in row.column_names if name != "Political Entity"
    )
    absent_column = source_reported_political_entity_evidence(
        replace(row, column_names=without_column_names)
    )

    assert (blank.status, blank.raw_value, blank.trimmed_value) == (
        "value_missing",
        "",
        None,
    )
    assert (absent_token.status, absent_token.raw_value) == ("token_missing", None)
    assert (absent_column.status, absent_column.raw_value) == (
        "column_unavailable",
        None,
    )


def test_ambiguous_political_entity_columns_are_refused(tmp_path: Path) -> None:
    panel = reconciliation(tmp_path)
    row = panel.records[0].source_evidence_rows[0]
    ambiguous = replace(
        row,
        column_names=(*row.column_names, "Political Entity duplicate"),
        raw_tokens=(*row.raw_tokens, "Sweden"),
    )

    with pytest.raises(ValueError, match="Political Entity source columns"):
        source_reported_political_entity_evidence(ambiguous)
