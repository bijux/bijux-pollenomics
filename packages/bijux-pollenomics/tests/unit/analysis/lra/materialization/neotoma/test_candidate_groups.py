"""Source grouping counts never promote sample candidates to independent sites."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization import (
    inspect_neotoma_lra_candidate_groups,
)
from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.candidate_groups import (
    summarize_neotoma_candidate_groups,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen import (
    NeotomaPollenScreen,
    assess_neotoma_pollen_screen,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from ..support import authorities


def _screen(value: dict[str, object]) -> NeotomaPollenScreen:
    content = canonical_bytes(value)
    return NeotomaPollenScreen(content, hashlib.sha256(content).hexdigest())


def test_source_group_denominators_bind_screen_without_site_admission(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    result = inspect_neotoma_lra_candidate_groups(
        raw_root=raw, normalized_root=normalized
    )
    report = result.as_dict()
    assert report["denominators"] == {
        "candidate_samples": 9,
        "source_sites": 9,
        "source_collection_units": 9,
        "source_datasets": 9,
        "lra_accepted_samples": 0,
    }
    assert (
        sum(row["candidate_samples"] for row in report["country_denominators"].values())
        == 9
    )
    assert (
        report["independence_status"] == "source_site_aliases_and_basins_not_reviewed"
    )
    assert report["lra_admission_status"] == "refused"
    assert len(report["site_rows"]) == 9
    assert hashlib.sha256(result.canonical_json).hexdigest() == result.result_digest


def test_multiple_candidate_samples_at_one_source_site_count_once(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    screen = assess_neotoma_pollen_screen(read_neotoma_evidence(raw, normalized))
    payload = screen.as_dict()
    candidates = [
        row
        for row in payload["sample_decisions"]
        if row["screen_status"] == "necessary_candidate"
    ]
    candidates[1]["site_id"] = candidates[0]["site_id"]
    groups = summarize_neotoma_candidate_groups(_screen(payload)).as_dict()
    assert groups["denominators"]["candidate_samples"] == 9
    assert groups["denominators"]["source_sites"] == 8
    shared = next(
        row for row in groups["site_rows"] if row["site_id"] == candidates[0]["site_id"]
    )
    assert shared["candidate_sample_count"] == 2
    assert shared["sample_ids"] == sorted(
        [candidates[0]["sample_id"], candidates[1]["sample_id"]]
    )


def test_tampered_candidate_partition_or_country_refuses(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    screen = assess_neotoma_pollen_screen(read_neotoma_evidence(raw, normalized))
    with pytest.raises(ValueError, match="digest"):
        summarize_neotoma_candidate_groups(
            NeotomaPollenScreen(screen.canonical_json, "0" * 64)
        )
    payload = screen.as_dict()
    candidate = next(
        row
        for row in payload["sample_decisions"]
        if row["screen_status"] == "necessary_candidate"
    )
    candidate["screen_status"] = "refused"
    with pytest.raises(ValueError, match="Candidate IDs"):
        summarize_neotoma_candidate_groups(_screen(payload))
    candidate["screen_status"] = "necessary_candidate"
    candidate["country_code"] = "DK"
    with pytest.raises(ValueError, match="Country sample groups"):
        summarize_neotoma_candidate_groups(_screen(payload))
