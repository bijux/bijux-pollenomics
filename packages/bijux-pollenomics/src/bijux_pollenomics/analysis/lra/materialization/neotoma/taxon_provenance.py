"""Retain Neotoma dataset attribution for source-screened taxon review."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, cast

from ..reading import NeotomaEvidence
from .accounting import source_accounting
from .series import source_element_status
from .taxon_priority import (
    _IDENTITY_FIELDS,
    _identity,
    prioritize_neotoma_candidate_taxa,
)


def _doi_status(value: object) -> str:
    if isinstance(value, list) and any(
        isinstance(item, str) and item.strip() for item in value
    ):
        return "source_doi_listed"
    return "source_doi_missing_or_unstructured"


def attribute_neotoma_priority_datasets(
    evidence: NeotomaEvidence,
    screen: dict[str, Any],
    review: dict[str, Any],
    priority: dict[str, Any],
) -> dict[str, Any]:
    """Link every candidate concept to source dataset IDs and native citations.

    Dataset DOI and contributor fields are source-native attribution leads.
    This does not resolve source rights, original publications or taxon review.
    """
    expected = prioritize_neotoma_candidate_taxa(evidence, screen, review)
    if {
        key: value for key, value in priority.items() if key != "input_file_sha256"
    } != expected:
        raise ValueError("Priority report differs from authenticated source projection")
    selected = frozenset(cast(list[str], screen["candidate_sample_ids"]))
    sample_datasets: dict[str, str] = {}
    for source in evidence.rows("samples"):
        sample = source.payload()
        sample_id = str(sample["sample_id"])
        if sample_id not in selected:
            continue
        if sample_id in sample_datasets:
            raise ValueError("Duplicate selected sample in source")
        sample_datasets[sample_id] = str(sample["dataset_id"])
    if set(sample_datasets) != set(selected):
        raise ValueError("Selected sample has no source dataset")

    datasets: dict[str, dict[str, Any]] = {}
    for source in evidence.rows("datasets"):
        dataset = source.payload()
        dataset_id = str(dataset["dataset_id"])
        if dataset_id in datasets:
            raise ValueError("Duplicate source dataset")
        datasets[dataset_id] = dataset
    if set(sample_datasets.values()) - datasets.keys():
        raise ValueError("Selected sample refers to a missing dataset")

    identities: dict[str, str] = {}
    for row in cast(list[dict[str, Any]], review["rows"]):
        if row.get("source_family") != "neotoma":
            continue
        source_identity = cast(dict[str, Any], row["supporting_evidence"])
        key = _identity(source_identity)
        if key in identities:
            raise ValueError("Duplicate source identity in full review")
        identities[key] = str(row["review_row_id"])

    accounting = source_accounting(evidence, sorted(selected))
    concept_datasets: dict[str, Counter[str]] = defaultdict(Counter)
    concept_samples: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    concept_mass: Counter[str] = Counter()
    dataset_samples: dict[str, set[str]] = defaultdict(set)
    dataset_observations: Counter[str] = Counter()
    for source in evidence.rows("observations"):
        observation = source.payload()
        sample_id = str(observation["sample_id"])
        if sample_id not in selected:
            continue
        dataset_id = str(observation["dataset_id"])
        if dataset_id != sample_datasets[sample_id]:
            raise ValueError("Observation dataset differs from selected sample")
        record = accounting.observation(source)
        if (
            record["count_status"] != "count_candidate"
            or source_element_status(
                observation.get("source_element"),
                observation.get("source_element_type"),
            )
            != "source_label_pollen"
        ):
            continue
        identity = {
            "source_family": "neotoma",
            "source_variable_id": observation["variable_id"],
            **{field: observation.get(field) for field in _IDENTITY_FIELDS[2:]},
        }
        concept_id = identities.get(_identity(identity))
        if concept_id is None:
            raise ValueError("Candidate pollen lacks full-review source identity")
        count = record.get("typed_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("Candidate pollen has no exact source count")
        concept_datasets[concept_id][dataset_id] += 1
        concept_samples[concept_id][dataset_id].add(sample_id)
        concept_mass[concept_id] += count
        dataset_samples[dataset_id].add(sample_id)
        dataset_observations[dataset_id] += 1

    rows = []
    for priority_row in cast(list[dict[str, Any]], priority["rows"]):
        concept_id = str(priority_row["review_row_id"])
        counts = concept_datasets[concept_id]
        if (
            sum(counts.values()) != priority_row["candidate_observation_count"]
            or concept_mass[concept_id] != priority_row["candidate_exact_count_sum"]
        ):
            raise ValueError("Dataset attribution differs from priority concept")
        rows.append(
            {
                "review_row_id": concept_id,
                "source_identity_sha256": priority_row["source_identity_sha256"],
                "source_reported_name": priority_row["source_reported_name"],
                "source_unit": priority_row["source_unit"],
                "review_state": priority_row["review_state"],
                "candidate_observation_count": sum(counts.values()),
                "candidate_dataset_count": len(counts),
                "source_datasets": [
                    {
                        "dataset_id": dataset_id,
                        "observation_count": counts[dataset_id],
                        "sample_count": len(concept_samples[concept_id][dataset_id]),
                    }
                    for dataset_id in sorted(counts)
                ],
            }
        )
    if (
        sum(dataset_observations.values())
        != priority["candidate_pollen_observation_count"]
    ):
        raise ValueError("Dataset observation attribution does not reconcile")
    dataset_rows = []
    for dataset_id in sorted(dataset_observations):
        dataset = datasets[dataset_id]
        payload = cast(dict[str, Any], dataset["source_payload"])
        dataset_rows.append(
            {
                "dataset_id": dataset_id,
                "source_dataset_id": dataset["source_dataset_id"],
                "source_country_code": dataset["country_code"],
                "source_constituent_database": payload.get("database"),
                "source_dataset_name": payload.get("datasetname"),
                "source_doi_values": payload.get("doi"),
                "source_dataset_pi": payload.get("datasetpi"),
                "source_dataset_notes": payload.get("datasetnotes"),
                "source_doi_status": _doi_status(payload.get("doi")),
                "candidate_sample_count": len(dataset_samples[dataset_id]),
                "candidate_pollen_observation_count": dataset_observations[dataset_id],
            }
        )
    evidence.assert_unchanged()
    return {
        "schema_version": "neotoma-candidate-taxon-attribution.v1",
        "source_snapshot_id": priority["source_snapshot_id"],
        "raw_manifest_sha256": priority["raw_manifest_sha256"],
        "normalized_manifest_sha256": priority["normalized_manifest_sha256"],
        "screen_candidate_ids_sha256": priority["screen_candidate_ids_sha256"],
        "review_bundle_sha256": priority["review_bundle_sha256"],
        "candidate_sample_count": priority["candidate_sample_count"],
        "candidate_pollen_observation_count": priority[
            "candidate_pollen_observation_count"
        ],
        "candidate_review_row_count": len(rows),
        "candidate_dataset_count": len(dataset_rows),
        "dataset_doi_status_counts": dict(
            sorted(Counter(row["source_doi_status"] for row in dataset_rows).items())
        ),
        "rows": rows,
        "dataset_rows": dataset_rows,
        "source_attribution_scope": "source-native_dataset_fields_only; original_publications_and_rights_not_verified",
        "lra_accepted_samples": 0,
        "publication_allowed": False,
    }
