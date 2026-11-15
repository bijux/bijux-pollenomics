"""Complete downloads retain derived support tables and their separate source scope."""

from __future__ import annotations

import json
from typing import Any

import pytest

from .test_source_chronology_issue_export import export_issues


def export_quality(action: str = "") -> dict[str, Any]:
    return export_issues(
        r"""
tabs.chronology.source_quality={
 schema_version:'neotoma-source-chronology-quality.v1',
 source_scope:{source_family:'neotoma',site_id:'neotoma:site:12',source_snapshot_id:'source:one'},
 source_profile:{eligibility_changed:false,chronology_selected:false},
 profiles:{...table(['profile_id','depth_unit','flags'],[['profile:one','cm',['source_point_age_reversal_with_depth']]]),source_locator_contract:'profile#{profile_id}'},
 sample_flags:table(['sample_id','flags'],[['sample:one',['sample_has_no_source_age_claim']]]),
 claim_diagnostics:table(['chronology_claim_id','profile_id','point_status','flags'],[['claim:one',null,'missing_source_point_age',[]]]),
 site_denominators:{profiles:1,samples:1,age_claims:1},
};
"""
        + action
    )


def test_download_decodes_all_quality_tables_without_changing_scope_or_nulls() -> None:
    observed = export_quality()
    result = observed["quality"]
    assert observed["unchanged"] is True
    assert result["source_scope"]["source_snapshot_id"] == "source:one"
    assert result["source_profile"] == {
        "eligibility_changed": False,
        "chronology_selected": False,
    }
    profile = result["profiles"]["records"][0]
    assert profile["depth_unit"] == "cm"
    assert profile["flags"] == ["source_point_age_reversal_with_depth"]
    assert result["profiles"]["source_locator_contract"] == "profile#{profile_id}"
    assert result["claim_diagnostics"]["records"][0]["profile_id"] is None
    assert result["sample_flags"]["records"][0]["flags"] == [
        "sample_has_no_source_age_claim"
    ]


@pytest.mark.parametrize("surface", ["profiles", "sample_flags", "claim_diagnostics"])
def test_download_refuses_inconsistent_quality_table_counts(surface: str) -> None:
    observed = export_quality(
        "tabs.chronology.source_quality[" + json.dumps(surface) + "].record_count+=1;"
    )
    assert "table" in observed["error"]


def test_legacy_download_does_not_invent_quality_results() -> None:
    observed = export_issues()
    assert observed["quality"] == {
        "status": "unavailable",
        "reason_code": "source_chronology_quality_not_available",
    }
