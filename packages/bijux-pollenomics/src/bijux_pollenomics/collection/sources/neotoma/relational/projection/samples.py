"""Sample and sample-age relational projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import copy

from ..chronology import build_age_claim
from ..diagnostics import add_orphan, register_record, required_source_id
from ..identifiers import digest
from ..source_payloads import copy_source_payload_excluding
from ..state import RelationalBuildState
from .observations import project_observations


def project_samples(
    state: RelationalBuildState,
    *,
    dataset: Mapping[str, object],
    dataset_id: str,
    unit_id: str,
    site_id: str,
    country_code: str,
    default_source_id: str | None,
    chronology_ids_by_source: Mapping[str, str],
) -> None:
    samples = dataset.get("samples")
    if not isinstance(samples, list):
        samples = []
    state.source_counts["sample_rows"] += len(samples)
    state.country_counts[country_code]["sample_rows"] += len(samples)
    for sample in samples:
        if not isinstance(sample, Mapping):
            add_orphan(state.orphans, "dataset", dataset_id, "invalid_sample_row")
            continue
        sample_source_id = required_source_id(
            sample.get("sampleid"), "sample", state.orphans, parent_id=dataset_id
        )
        if sample_source_id is None:
            continue
        sample_id = f"neotoma:sample:{sample_source_id}"
        register_record(
            state.tables["samples"],
            {
                "sample_id": sample_id,
                "source_sample_id": sample.get("sampleid"),
                "source_analysis_unit_id": sample.get("analysisunitid"),
                "source_analysis_unit_name": copy.deepcopy(
                    sample.get("analysisunitname")
                ),
                "source_sample_name": copy.deepcopy(sample.get("samplename")),
                "source_igsn": copy.deepcopy(sample.get("igsn")),
                "source_depth": copy.deepcopy(sample.get("depth")),
                "source_thickness": copy.deepcopy(sample.get("thickness")),
                "source_sample_analysts": copy.deepcopy(
                    sample.get("sampleanalyst")
                ),
                "dataset_id": dataset_id,
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "country_code": country_code,
                "source_payload": copy_source_payload_excluding(
                    sample, "ages", "datum"
                ),
                "source_snapshot_id": state.source_snapshot_id,
                "build_id": state.build_id,
            },
            id_field="sample_id",
            conflicts=state.conflicts,
            conflict_kind="sample_payload_conflict",
        )
        project_age_claims(
            state,
            sample=sample,
            sample_id=sample_id,
            dataset_id=dataset_id,
            unit_id=unit_id,
            site_id=site_id,
            country_code=country_code,
            default_source_id=default_source_id,
            chronology_ids_by_source=chronology_ids_by_source,
        )
        project_observations(
            state,
            sample=sample,
            sample_source_id=sample_source_id,
            sample_id=sample_id,
            dataset_id=dataset_id,
            unit_id=unit_id,
            site_id=site_id,
            country_code=country_code,
        )


def project_age_claims(
    state: RelationalBuildState,
    *,
    sample: Mapping[str, object],
    sample_id: str,
    dataset_id: str,
    unit_id: str,
    site_id: str,
    country_code: str,
    default_source_id: str | None,
    chronology_ids_by_source: Mapping[str, str],
) -> None:
    ages = sample.get("ages")
    if not isinstance(ages, list):
        ages = []
    state.source_counts["age_claim_rows"] += len(ages)
    state.country_counts[country_code]["age_claim_rows"] += len(ages)
    age_occurrence_counts: Counter[str] = Counter()
    for age in ages:
        if not isinstance(age, Mapping):
            add_orphan(state.orphans, "sample", sample_id, "invalid_age_row")
            continue
        age_digest = digest(dict(age))
        age_occurrence_counts[age_digest] += 1
        age_record = build_age_claim(
            age,
            occurrence=age_occurrence_counts[age_digest],
            sample_id=sample_id,
            dataset_id=dataset_id,
            collection_unit_id=unit_id,
            site_id=site_id,
            country_code=country_code,
            default_source_id=default_source_id,
            chronology_ids_by_source=chronology_ids_by_source,
            source_snapshot_id=state.source_snapshot_id,
            build_id=state.build_id,
            orphans=state.orphans,
        )
        state.age_postures[str(age_record["comparability_status"])] += 1
        state.country_counts[country_code][
            f"age_{age_record['comparability_status']}"
        ] += 1
        admission_reason = age_record.get("admission_reason")
        if admission_reason is not None:
            state.age_reasons[str(admission_reason)] += 1
        register_record(
            state.tables["age_claims"],
            age_record,
            id_field="chronology_claim_id",
            conflicts=state.conflicts,
            conflict_kind="age_claim_identity_conflict",
        )
