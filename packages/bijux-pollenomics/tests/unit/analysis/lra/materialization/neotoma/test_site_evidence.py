"""Native Neotoma site fields remain review evidence, never basin parameters."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization import (
    inspect_neotoma_lra_candidate_site_evidence,
)
from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.candidate_groups import (
    NeotomaCandidateGroups,
    summarize_neotoma_candidate_groups,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen import (
    assess_neotoma_pollen_screen,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence import (
    assess_neotoma_candidate_site_evidence,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from ..support import authorities


def _groups(value: dict[str, object]) -> NeotomaCandidateGroups:
    content = canonical_bytes(value)
    return NeotomaCandidateGroups(content, hashlib.sha256(content).hexdigest())


def test_site_review_retains_source_fields_without_basin_admission(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    result = inspect_neotoma_lra_candidate_site_evidence(
        raw_root=raw, normalized_root=normalized
    )
    report = result.as_dict()
    assert report["denominators"] == {
        "candidate_source_sites": 9,
        "candidate_collection_units": 9,
        "candidate_samples": 9,
        "lra_accepted_samples": 0,
    }
    assert (
        sum(
            value["candidate_source_sites"]
            for value in report["country_denominators"].values()
        )
        == 9
    )
    assert (
        sum(
            value["source_point_geometries"]
            for value in report["country_denominators"].values()
        )
        == 9
    )
    assert report["source_area_semantics"] == "not_verified_as_basin_area_or_dimension"
    assert report["lra_admission_status"] == "refused"
    assert all(
        row["basin_type_status"] == "not_reviewed" for row in report["site_rows"]
    )
    assert all(
        row["source_locator"]["surface"] == "sites" for row in report["site_rows"]
    )
    assert len(report["collection_unit_rows"]) == 9
    assert all(
        row["source_locator"]["surface"] == "collection_units"
        and row["source_depositional_environment"] is None
        and row["basin_type_status"] == "not_reviewed"
        for row in report["collection_unit_rows"]
    )
    assert hashlib.sha256(result.canonical_json).hexdigest() == result.result_digest


def test_source_binding_and_missing_candidate_site_are_refused(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    screen = assess_neotoma_pollen_screen(evidence)
    groups = summarize_neotoma_candidate_groups(screen)
    with pytest.raises(ValueError, match="digest"):
        assess_neotoma_candidate_site_evidence(
            evidence, NeotomaCandidateGroups(groups.canonical_json, "0" * 64)
        )
    payload = groups.as_dict()
    payload["site_rows"][0]["site_id"] = "neotoma:site:missing"
    with pytest.raises(ValueError, match="missing from authenticated surface"):
        assess_neotoma_candidate_site_evidence(evidence, _groups(payload))
    payload = groups.as_dict()
    payload["site_rows"][0]["collection_unit_ids"] = ["neotoma:collection-unit:missing"]
    with pytest.raises(ValueError, match="missing from authenticated surface"):
        assess_neotoma_candidate_site_evidence(evidence, _groups(payload))
