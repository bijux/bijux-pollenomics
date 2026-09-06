"""Atlas candidate evidence-accountability tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.atlas_accountability import (
    build_animal_atlas_candidate_accountability,
)
from bijux_pollenomics.adna.governance.audit_catalogs.rendering import (
    render_animal_atlas_candidate_accountability_markdown,
)

pytestmark = pytest.mark.generated_artifacts


def test_atlas_candidates_retain_complete_evidence_accountability(
    catalog_data_root: Path,
) -> None:
    accountability = build_animal_atlas_candidate_accountability(catalog_data_root)
    markdown = render_animal_atlas_candidate_accountability_markdown(accountability)

    assert accountability["candidate_row_count"] == 271
    assert accountability["passed_row_count"] == 271
    assert accountability["overall_ok"]
    assert all(row["fully_accountable"] for row in accountability["rows"])
    assert {
        (row["site_record_id"], tuple(row["sample_record_ids"]))
        for row in accountability["rows"]
        if row["project_accession"] == "PRJEB30282"
    } == {
        (
            "sus_scrofa_domesticus:locality:prjeb30282:bunds:denmark",
            ("sus_scrofa_domesticus:sample:prjeb30282:samea5160867",),
        ),
        (
            "sus_scrofa_domesticus:locality:prjeb30282:trelleborg:denmark",
            ("sus_scrofa_domesticus:sample:prjeb30282:samea5160868",),
        ),
    }
    assert "Overall ok: `true`" in markdown
