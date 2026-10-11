"""The SEAD prerequisite frontier reconciles rows but never admits LRA input."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.sead import (
    assess_sead_lra_frontier,
)
from bijux_pollenomics.analysis.lra.materialization.sead.frontier import (
    _physical_sample_accounting,
    _selected_entities,
    _source_observation_flags,
)

from .support import admitted_fixture


def test_frontier_reconciles_complete_fixture_without_admission(tmp_path: Path) -> None:
    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    first = assess_sead_lra_frontier(
        raw_root=raw, normalized_root=normalized, expected_identity=expected
    )
    second = assess_sead_lra_frontier(
        raw_root=raw, normalized_root=normalized, expected_identity=expected
    )
    assert first.canonical_json == second.canonical_json
    assert hashlib.sha256(first.canonical_json).hexdigest() == first.result_digest
    report = first.as_dict()
    assert report["source_denominators"] == {
        "analysis_entities": 1,
        "observations": 4,
        "chronology_claims": 5,
        "source_physical_samples": 1,
        "analysis_entity_physical_sample_links": 1,
        "entity_linked_physical_samples": 1,
        "physical_sample_entity_multiplicity_counts": {"1": 1},
        "physical_samples_without_analysis_entity": 0,
    }
    assert report["selected_denominators"]["analysis_entities"] == 1
    assert report["selected_denominators"]["observations"] == 4
    assert (
        report["selected_denominators"][
            "entities_with_count_method_taxon_and_owned_comparable_claim"
        ]
        == 0
    )
    assert (
        report["selected_denominators"][
            "physical_samples_with_at_least_one_source_prerequisite_entity"
        ]
        == 0
    )
    assert report["lra_accepted_samples"] == 0
    assert report["executable_request"] is None
    assert report["frontier_status"] == "refused"
    assert report["palynology_lookup_present"] is False
    assert (
        report["selected_denominators"]["entities_with_observed_palynology_method"] == 0
    )
    assert (
        sum(report["selected_denominators"]["native_value_type_counts"].values())
        == report["selected_denominators"]["observations"]
    )
    assert report["country_denominators"]["SE"]["entity_linked_physical_samples"] == 1
    assert set(report["selected_entity_refusal_reason_counts"]) >= {
        "source_pollen_identity_not_accepted",
        "lra_chronology_decision_not_supplied",
    }


def test_physical_sample_ownership_counts_shared_entities_once() -> None:
    rows = [
        ("entity-a", "SE", 10),
        ("entity-b", "SE", 10),
        ("entity-c", "FI", 20),
        ("entity-d", "NO", None),
    ]
    result = _physical_sample_accounting(
        rows,
        {"entity-a", "entity-b", "entity-c", "entity-d"},
        {"entity-a"},
    )
    assert result.source_links == 3
    assert result.source_samples == 2
    assert result.source_multiplicity == {"1": 1, "2": 1}
    assert result.selected_country_links == {"FI": 1, "SE": 2}
    assert result.selected_country_samples == {"FI": 1, "SE": 1}
    assert result.prerequisite_samples == 1
    assert result.prerequisite_country_samples == {"SE": 1}


def test_physical_sample_country_conflict_refuses() -> None:
    with pytest.raises(ValueError, match="multiple countries"):
        _physical_sample_accounting(
            [("entity-a", "SE", 10), ("entity-b", "FI", 10)],
            {"entity-a", "entity-b"},
            set(),
        )


def test_selection_order_is_canonical() -> None:
    available = {"entity-a", "entity-b"}
    assert _selected_entities(available, ["entity-b", "entity-a"])[0] == [
        "entity-a",
        "entity-b",
    ]


def test_observation_intersection_requires_one_observed_relation() -> None:
    record = {
        "source_count_compatibility": "source_absolute_count_candidate",
        "source_pollen_method_candidate": True,
        "source_taxon_relation": {"taxon_id": 1},
        "palynology_lookup_present": True,
    }
    assert all(_source_observation_flags(record))
    record["source_pollen_method_candidate"] = False
    assert _source_observation_flags(record) == (True, False, True)


def test_explicit_selection_is_hash_bound_and_empty_selection_is_not_admission(
    tmp_path: Path,
) -> None:
    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    selected = assess_sead_lra_frontier(
        raw_root=raw,
        normalized_root=normalized,
        expected_identity=expected,
        selected_entity_ids=["sead-analysis-entity:1"],
    ).as_dict()
    assert selected["selection"]["mode"] == "explicit_entity_ids"
    assert selected["selection"]["entity_ids"] == ["sead-analysis-entity:1"]
    empty = assess_sead_lra_frontier(
        raw_root=raw,
        normalized_root=normalized,
        expected_identity=expected,
        selected_entity_ids=[],
    ).as_dict()
    assert empty["frontier_status"] == "empty_selection"
    assert empty["selected_denominators"]["analysis_entities"] == 0
    assert empty["lra_accepted_samples"] == 0


@pytest.mark.parametrize(
    "selection,match",
    (
        (["sead-analysis-entity:1", "sead-analysis-entity:1"], "duplicated"),
        (["missing"], "Unknown"),
        ([" sead-analysis-entity:1"], "exact nonempty"),
    ),
)
def test_invalid_entity_selections_refuse(
    tmp_path: Path, selection: list[str], match: str
) -> None:
    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    with pytest.raises(ValueError, match=match):
        assess_sead_lra_frontier(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=expected,
            selected_entity_ids=selection,
        )


def test_wrong_expected_identity_and_mid_read_mutation_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra.materialization.sead.reading import SeadEvidence

    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    with pytest.raises(ValueError):
        assess_sead_lra_frontier(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=replace(expected, build_id="sha256:" + "0" * 64),
        )

    original = SeadEvidence.assert_unchanged
    calls = 0

    def mutate_at_final_check(self: SeadEvidence) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            member = normalized / "source_native_observations.json"
            member.write_bytes(member.read_bytes() + b" ")
        original(self)

    monkeypatch.setattr(SeadEvidence, "assert_unchanged", mutate_at_final_check)
    with pytest.raises(ValueError, match="changed"):
        assess_sead_lra_frontier(
            raw_root=raw, normalized_root=normalized, expected_identity=expected
        )
