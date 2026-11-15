"""Derived chronology support retains its scope, raw flags and paged readers."""

from __future__ import annotations

import json
from typing import Any

import pytest

from .test_source_chronology_review import paged_reader, review


def qualified_tabs(action: str = "") -> dict[str, Any]:
    return review(
        r"""
tabs.overview={source_family:'neotoma',site_id:'neotoma:site:20',country_code:'SE'};
tabs.provenance={source_snapshot_id:'source:one',build_id:'build:one',materialization_sha256:'a'.repeat(64)};
tabs.chronology.source_quality={
 schema_version:'neotoma-source-chronology-quality.v1',
 source_scope:{source_family:'neotoma',...tabs.provenance,site_id:tabs.overview.site_id,country_code:'SE'},
 source_profile:{eligibility_changed:false,chronology_selected:false},
 profiles:table(['profile_id','flags'],[['profile:one',['source_point_age_reversal_with_depth']]]),
 sample_flags:table(['sample_id','flags'],[['sample:one',['sample_has_no_source_age_claim']]]),
 claim_diagnostics:table(['chronology_claim_id','sample_id','profile_id','point_status','flags'],
  Array.from({length:30},(_,i)=>[`claim:${i}`,`sample:${i}`,'profile:one','finite_source_point_age',[]])),
 site_denominators:{profiles:1,samples:1,age_claims:30},
 claim_diagnostic_semantics:'Claim flags and shared profile context remain distinct.',
};
"""
        + action
    )


def test_current_quality_review_explains_descriptive_flags_without_admission() -> None:
    observed = qualified_tabs()
    assert observed["unchanged"] is True
    html = observed["html"]
    assert 'data-source-chronology-quality="available"' in html
    assert "1 source profile" in html and "30 age-claim diagnostics" in html
    assert "does not select a chronology" in html
    assert "source_point_age_reversal_with_depth" in html
    assert "sample_has_no_source_age_claim" in html


def test_quality_claims_use_actual_drawer_pager_without_opaque_duplicate() -> None:
    tabs = qualified_tabs()["tabs"]
    observed = paged_reader(
        tabs,
        ["next", "previous"],
        table_path="chronology.source_quality.claim_diagnostics",
    )
    first, second, returned = observed["snapshots"]
    assert "claim:0" in first and "claim:29" not in first
    assert "claim:29" in second and "claim:0" not in second
    assert first == returned and observed["unchanged"] is True
    assert "&quot;claim_diagnostics&quot;" not in first


@pytest.mark.parametrize(
    "field",
    [
        "source_family",
        "source_snapshot_id",
        "build_id",
        "materialization_sha256",
        "site_id",
        "country_code",
    ],
)
def test_foreign_quality_scope_cannot_be_presented_as_current_support(
    field: str,
) -> None:
    observed = qualified_tabs(
        "tabs.chronology.source_quality.source_scope["
        + json.dumps(field)
        + "]='foreign';"
    )
    assert 'data-source-chronology-quality="unavailable"' in observed["html"]
    assert "30 age-claim diagnostics" not in observed["html"]
    assert observed["unchanged"] is True


@pytest.mark.parametrize("surface", ["profiles", "sample_flags", "claim_diagnostics"])
def test_malformed_quality_tables_do_not_become_zero_diagnostics(surface: str) -> None:
    observed = qualified_tabs(
        "tabs.chronology.source_quality[" + json.dumps(surface) + "].record_count+=1;"
    )
    assert 'data-source-chronology-quality="unavailable"' in observed["html"]
    assert "1 source profile" not in observed["html"]


def test_legacy_quality_absence_does_not_establish_no_quality_issues() -> None:
    observed = review()
    assert 'data-source-chronology-quality="unavailable"' in observed["html"]
    assert (
        "does not establish that no chronology-quality issues exist" in observed["html"]
    )
