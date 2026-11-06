"""Project-locality coverage remains distinct from exact source-sample dates."""

from __future__ import annotations

import csv
from dataclasses import replace
import io
import json
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.adna.domain.locality import locality_sample_intervals
from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaLocalitySummary,
    AdnaSampleRecord,
)
from bijux_pollenomics.adna.projects.registry.localities import AdnaProjectLocalityLead
from bijux_pollenomics.adna.species.tracked_data.csv_exports.normalized import (
    _render_locality_summaries_csv,
)
from bijux_pollenomics.adna.species.tracked_data.payloads import (
    _locality_summaries_payload,
)
from bijux_pollenomics.adna.workflow.normalization import localities
from bijux_pollenomics.adna.workflow.normalization.models import (
    AdnaProjectSummary,
    AdnaSpeciesNormalizationBundle,
)
from bijux_pollenomics.core.temporal_semantics import (
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)
from tests.unit.adna.domain.test_adna_temporal_query import _sample_with_interval


def _samples(*, censored: bool = False) -> tuple[AdnaSampleRecord, ...]:
    result = []
    for owner, bounds in (
        ("young", (100, 110)),
        ("old", (300, 310)),
        ("missing", (None, None)),
    ):
        sample = _sample_with_interval(*bounds)
        chronology = replace(
            sample.chronology,
            original_text=(">500 BP" if censored else "")
            if owner == "missing"
            else f"{bounds[0]}-{bounds[1]} BP",
            time_mean_bp=None
            if owner == "missing"
            else sum(cast(tuple[int, int], bounds)) // 2,
            dating_basis="radiocarbon",
            evidence_class="unresolved"
            if owner == "missing"
            else "direct_radiocarbon_date",
            precision_posture="unresolved"
            if owner == "missing"
            else "sample_precise_interval",
        )
        result.append(
            replace(
                sample,
                identity=replace(sample.identity, stable_token=owner),
                master_id=owner,
                species_latin_name="Ovis aries",
                species_common_name="sheep",
                project_accession="PRJEB41594",
                chronology=chronology,
                chronology_strength="unresolved"
                if owner == "missing"
                else "sample_owned_interval",
                chronology_normalization_status="unresolved"
                if owner == "missing"
                else "normalized_interval",
                chronology_provenance_path=f"source/{owner}.json",
                chronology_provenance_locator=owner,
                chronology_provenance_kind="source_table",
                chronology_provenance_text=f"Exact source wording: {owner}",
                chronology_conflict_note="Source stratigraphic caution"
                if owner == "old"
                else "",
            )
        )
    return tuple(result)


def _construct(
    monkeypatch: pytest.MonkeyPatch,
    samples: tuple[AdnaSampleRecord, ...],
    *,
    aggregate: AdnaChronology | None = None,
) -> AdnaLocalitySummary:
    project = SimpleNamespace(
        project_accession="PRJEB41594",
        species_latin_name="Ovis aries",
        species_common_name="sheep",
        chronology_basis="radiocarbon",
        dating_basis="radiocarbon",
        source_family="test",
        source_release="source-release",
        record_modality="metadata_only",
        review_strength="source_bound",
        evidence_strength="source_bound",
        summary_token="source-project",
    )
    curated = tuple(
        SimpleNamespace(
            stable_sample_id=sample.master_id,
            project_accession="PRJEB41594",
            site_label="Test locality",
            political_entity="Sweden",
            sample_evidence_status="archive_native",
            sample_identity_resolution="final",
            time_start_bp=sample.time_start_bp,
            time_end_bp=sample.time_end_bp,
            dating_basis=sample.dating_basis,
        )
        for sample in samples
    )
    claims = tuple(
        SimpleNamespace(
            repo_stable_sample_id=sample.master_id,
            chronology_text=sample.time_label,
            time_start_bp=sample.time_start_bp,
            time_end_bp=sample.time_end_bp,
            chronology_evidence_class=sample.chronology.evidence_class,
            chronology_precision_posture=sample.chronology.precision_posture,
        )
        for sample in samples
    )
    lead = AdnaProjectLocalityLead(
        project_accession="PRJEB41594",
        locality_text="Test locality",
        political_entity="Sweden",
        latitude_text="",
        longitude_text="",
        coordinate_basis="",
        chronology_text="",
        time_start_bp=None,
        time_end_bp=None,
        interpretation_note="Source-owned locality",
    )
    monkeypatch.setattr(
        localities, "build_species_archive_projects", lambda *_: (project,)
    )
    monkeypatch.setattr(
        localities, "build_species_curated_sample_rows", lambda *_: curated
    )
    monkeypatch.setattr(
        localities, "build_project_sample_chronology_rows", lambda *_: claims
    )
    monkeypatch.setattr(
        localities, "build_species_project_locality_leads", lambda *_: (lead,)
    )
    monkeypatch.setattr(
        localities,
        "resolve_project_context",
        lambda *_: SimpleNamespace(nordic_relevance_reason="Source fixture"),
    )
    if aggregate is not None:
        monkeypatch.setattr(
            localities, "_aggregate_locality_chronology", lambda **_: aggregate
        )
    result, refusals = localities.build_species_project_locality_records(
        "Ovis aries",
        (cast(AdnaProjectSummary, project),),
        sample_records=samples,
    )
    assert refusals == ()
    assert len(result) == 1
    return result[0]


def test_project_constructor_keeps_disjoint_and_missing_owned_supports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    samples = _samples()
    before = [sample.as_dict() for sample in samples]
    locality = _construct(monkeypatch, samples)
    assert (locality.time_start_bp, locality.time_end_bp, locality.time_mean_bp) == (
        100,
        310,
        205,
    )
    assert locality.dating_basis == "locality_sample_coverage"
    assert locality.chronology.evidence_class == "locality_sample_coverage_hull"
    assert locality.chronology.precision_posture == "display_coverage_only"
    assert locality.sample_ids == tuple(sample.master_id for sample in samples)
    assert locality.sample_count == 3
    for sample, support in zip(samples, locality.sample_chronologies, strict=True):
        assert support.sample_id == sample.master_id
        assert support.chronology == sample.chronology
        assert support.source_release == sample.source_release
        assert support.provenance_path == sample.chronology_provenance_path
        assert support.provenance_locator == sample.chronology_provenance_locator
        assert support.provenance_excerpt == sample.chronology_provenance_text
        assert support.provenance_kind == sample.chronology_provenance_kind
        assert support.chronology_strength == sample.chronology_strength
        assert support.normalization_status == sample.chronology_normalization_status
        assert support.conflict_note == sample.chronology_conflict_note
    assert [sample.as_dict() for sample in samples] == before
    gap = canonical_bp_interval(200, 200)
    assert gap is not None
    assert not any(
        closed_bp_intervals_overlap(interval, gap)
        for _, interval in locality_sample_intervals(locality)
    )
    assert len(locality_sample_intervals(locality)) == 2


def test_censored_source_support_does_not_gain_a_finite_hull(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality = _construct(monkeypatch, _samples(censored=True))
    assert locality.time_start_bp is None
    assert locality.time_end_bp is None
    assert locality.time_mean_bp is None
    assert ">500 BP" in locality.time_label
    assert locality.sample_chronologies[-1].chronology.original_text == ">500 BP"
    assert locality.sample_chronologies[-1].chronology.time_start_bp is None
    assert locality.chronology.precision_posture == "display_coverage_only"


@pytest.mark.parametrize("numeric", [True, False])
def test_project_boundary_changes_only_the_three_hull_labels(
    monkeypatch: pytest.MonkeyPatch, numeric: bool
) -> None:
    aggregate = AdnaChronology(
        original_text="Exact aggregate source text",
        time_start_bp=100 if numeric else None,
        time_end_bp=310 if numeric else None,
        time_mean_bp=205 if numeric else None,
        date_stddev_bp="17.25",
        source_mean_bp_text="205",
        dating_basis="radiocarbon",
        evidence_class="direct_radiocarbon_date",
        precision_posture="sample_precise_interval",
        refusal_reason_code="source_refusal_retained",
    )
    locality = _construct(monkeypatch, _samples(), aggregate=aggregate)
    assert locality.chronology == replace(
        aggregate,
        dating_basis="locality_sample_coverage",
        evidence_class="locality_sample_coverage_hull",
        precision_posture="display_coverage_only",
    )


def test_maintained_locality_json_and_csv_keep_exact_owned_supports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality = _construct(monkeypatch, _samples())
    bundle = cast(
        AdnaSpeciesNormalizationBundle,
        SimpleNamespace(
            species=SimpleNamespace(latin_name="Ovis aries"),
            locality_records=(locality,),
        ),
    )
    payload = _locality_summaries_payload(bundle)
    assert payload["schema_version"] == "adna-locality-summary-export.v2"
    assert payload["localities"] == [locality.as_dict()]
    reader = csv.DictReader(io.StringIO(_render_locality_summaries_csv(bundle)))
    row = next(reader)
    assert reader.fieldnames is not None
    assert reader.fieldnames[:4] == [
        "schema_version",
        "chronology_role",
        "sample_ids",
        "sample_chronologies",
    ]
    assert row["schema_version"] == "adna-locality-summary-export.v2"
    assert row["chronology_role"] == "locality_sample_coverage_hull"
    assert row["sample_ids"].split(";") == list(locality.sample_ids)
    assert json.loads(row["sample_chronologies"]) == [
        support.as_dict() for support in locality.sample_chronologies
    ]
    assert row["dating_basis"] == "locality_sample_coverage"
    assert row["chronology_evidence_class"] == "locality_sample_coverage_hull"
    assert row["chronology_precision_posture"] == "display_coverage_only"
    assert next(reader, None) is None
