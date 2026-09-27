"""Source-qualified first-observed refusal using authenticated Neotoma rows."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.neotoma_first_observed import (
    _reader_snapshot,
    build_neotoma_first_observed,
)

JsonObject = dict[str, object]
ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return build_neotoma_first_observed(ROOT)


def test_native_reader_and_export_identities_are_bound(report: JsonObject) -> None:
    identity = cast(JsonObject, report["source_identity"])
    assert identity["source_family"] == "neotoma"
    assert cast(str, identity["source_snapshot_id"]).startswith("sha256:")
    surfaces = cast(list[JsonObject], identity["verified_native_surfaces"])
    assert {row["surface"] for row in surfaces} == {
        "sites",
        "samples",
        "age_claims",
        "observations",
        "variables",
        "collection_units",
        "datasets",
    }
    assert (
        next(row for row in surfaces if row["surface"] == "observations")[
            "selected_native_rows"
        ]
        == 3103
    )
    assert (
        len(
            cast(
                list[JsonObject],
                next(row for row in surfaces if row["surface"] == "observations")[
                    "verified_parts"
                ],
            )
        )
        == 8
    )


def test_native_site_closure_rejects_an_omitted_export_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_read_text = Path.read_text

    def omitted_observation(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        content = original_read_text(path, encoding=encoding, errors=errors)
        if path.name == "neotoma-site-12.pollen-series.json":
            export = json.loads(content)
            export["pollen_observations"]["records"].pop()
            return json.dumps(export)
        return content

    monkeypatch.setattr(Path, "read_text", omitted_observation)
    with pytest.raises(
        ValueError, match="Export/native observation_id identity mismatch"
    ):
        _reader_snapshot(ROOT)


def test_complete_feature_profile_denominators_and_refusals(report: JsonObject) -> None:
    counts = cast(JsonObject, report["denominators"])
    assert {
        key: counts[key]
        for key in (
            "sites",
            "variables",
            "attempts",
            "full_coverage_attempts",
            "refused",
            "events",
            "estimator_invocations",
        )
    } == {
        "sites": 2,
        "variables": 128,
        "attempts": 256,
        "full_coverage_attempts": 14,
        "refused": 256,
        "events": 0,
        "estimator_invocations": 0,
    }
    attempts = cast(list[JsonObject], report["attempts"])
    assert Counter(row["chronology_profile"] for row in attempts) == {
        "native_default": 128,
        "named_calibrated_alternative": 128,
    }
    assert all(row["status"] == "refused" and row["event"] is None for row in attempts)
    assert all(
        "accepted_taxon_mapping_not_available" in cast(list[str], row["blocker_codes"])
        for row in attempts
    )


def test_all_sample_cells_and_literal_native_units_remain_visible(
    report: JsonObject,
) -> None:
    for site in cast(list[JsonObject], report["sites"]):
        universe = cast(list[JsonObject], site["sample_universe"])
        assert len(universe) == site["sample_count"]
        expected = {row["sample_id"] for row in universe}
        inventories = cast(list[JsonObject], site["feature_sample_inventories"])
        assert len(inventories) == site["variable_count"]
        for inventory in inventories:
            rows = cast(list[JsonObject], inventory["rows"])
            assert {row["sample_id"] for row in rows} == expected
            assert len(rows) == len(universe)
            for row in rows:
                observation = row["observation"]
                if observation is None:
                    continue
                o = cast(JsonObject, observation)
                assert cast(float, o["source_value"]) > 0
                assert o["source_unit"] == "NISP" and o["unit_family"] == "count"
                assert o["source_denominator"] is None


def test_both_real_chronology_profiles_keep_missingness_and_overlap(
    report: JsonObject,
) -> None:
    sites = {row["site_id"]: row for row in cast(list[JsonObject], report["sites"])}
    assert sites["neotoma:site:12"]["default_claim_statuses"] == {"context_only": 135}
    assert sites["neotoma:site:12"]["alternative_claim_statuses"] == {
        "comparable": 131,
        "refused": 4,
    }
    assert sites["neotoma:site:3009"]["alternative_claim_statuses"] == {
        "comparable": 28
    }
    attempts = cast(list[JsonObject], report["attempts"])
    full = [row for row in attempts if row["complete_sample_observation_coverage"]]
    assert len(full) == 14
    assert all(
        row["governed_sample_inputs_count"] == 131
        for row in full
        if row["site_id"] == "neotoma:site:12"
        and row["chronology_profile"] == "named_calibrated_alternative"
    )
    assert all(
        row["governed_sample_inputs_count"] == 28
        for row in full
        if row["site_id"] == "neotoma:site:3009"
        and row["chronology_profile"] == "named_calibrated_alternative"
    )
    assert all(
        "selected_chronology_not_comparable" in cast(list[str], row["blocker_codes"])
        for row in full
        if row["chronology_profile"] == "native_default"
    )
    assert all(
        "chronology_order_indeterminate" in cast(list[str], row["blocker_codes"])
        for row in full
        if row["chronology_profile"] == "named_calibrated_alternative"
    )
    default_first = next(
        row
        for row in cast(
            list[JsonObject], sites["neotoma:site:12"]["chronology_claim_ledger"]
        )
        if cast(JsonObject, row["claim"])["is_default_chronology"]
        and cast(JsonObject, row["claim"])["source_age_value"] == 0
    )
    assert (
        cast(JsonObject, default_first["claim"])["comparability_status"]
        == "context_only"
    )
    assert cast(JsonObject, default_first["claim"])["younger_bp"] is None


def test_retained_readiness_matches_replay_without_event_promotion(
    report: JsonObject,
) -> None:
    retained = json.loads(
        (ROOT / "docs/report/propagation/source-first-observed/report.json").read_text()
    )
    assert retained == json.loads(json.dumps(report))
    claims = cast(JsonObject, report["claims"])
    assert claims["real_source_rows_consumed"] is True
    assert claims["alternate_chronology_selected_for_publication"] is False
    assert claims["unreviewed_taxon_concept_promoted"] is False
    assert claims["first_observed_events_admitted"] is False
