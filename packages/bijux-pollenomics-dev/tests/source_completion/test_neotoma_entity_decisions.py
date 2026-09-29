"""Dataset inclusion in the pollen study is separate from LRA readiness."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_dev.source_completion.neotoma_entity_decisions import build


REPOSITORY = Path(__file__).resolve().parents[4]


def test_source_bound_dataset_decisions_replay_governed_result() -> None:
    result = build(REPOSITORY)
    governed = json.loads(
        (
            REPOSITORY
            / "docs/report/regions/nordic/source-capability/neotoma-entities/report.json"
        ).read_text()
    )
    assert result == governed
    assert result["dataset_count"] == 209
    assert result["sample_count"] == 12388
    assert result["direct_pollen_included_datasets"] == 85
    assert result["direct_pollen_excluded_datasets"] == 124
    assert (
        sum(
            row["count_and_comparable_age_candidate_samples"]
            for row in result["decisions"]
        )
        == 10637
    )
    assert all(
        row["lra_disposition"] == "unresolved_source_requirements"
        for row in result["decisions"]
    )
    assert result["country_denominators"]["SE"]["direct_pollen_included"] == 3
    assert result["country_denominators"]["DK"]["direct_pollen_included"] == 2
    assert result["country_denominators"]["NO"]["direct_pollen_included"] == 52
    assert result["country_denominators"]["FI"]["direct_pollen_included"] == 28
