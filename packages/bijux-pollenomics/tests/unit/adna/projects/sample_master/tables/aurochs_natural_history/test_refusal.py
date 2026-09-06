"""Tests for the explicit paper-only Fre1 sequencing refusal."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    _reconcile_aurochs_natural_history,
)

from .support import governed_inputs

pytestmark = pytest.mark.generated_artifacts


def test_fre1_is_preserved_without_a_fabricated_accession() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    row = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )[-1]

    assert row.workbook.sample_label == "Fre1"
    assert row.archive is None
    assert row.sequencing_status == "archive_sequence_identity_not_evidenced"
    assert row.workbook.udg_treatment == "No"
    assert row.workbook.coverage_text == "0.0"
    assert "no Fre1 filename or BioSample identity" in row.refusal_reason
    assert "accession is not inferred" in row.refusal_reason
