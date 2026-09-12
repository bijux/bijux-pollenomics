"""Publish exact SEAD accounting without scientific approval or numerical imports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from ..models import AdmissionReport, canonical_bytes, producer_identity
from ..paths import checked_output_directory
from ..reading import json_object
from .chronology import ChronologyAccounting
from .observations import sead_accounting
from .reading import read_sead_evidence

_COUNTRIES = ("DK", "FI", "NO", "SE", "UNASSIGNED")
_RELATION_FIELDS = (
    "dataset_semantics",
    "value_semantics",
    "taxon_relations",
    "dimension_semantics",
    "dimension_relations",
)


def _write_rows(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("xb") as stream:
        for row in rows:
            stream.write(canonical_bytes(row))
        stream.flush()
        os.fsync(stream.fileno())


def run_audit(
    *,
    raw_root: Path,
    normalized_root: Path,
    expected_identity: SeadAdmissionExpectedIdentity,
    output_directory: Path,
) -> AdmissionReport:
    producer = producer_identity()
    evidence = read_sead_evidence(
        raw_root, normalized_root, expected_identity=expected_identity
    )
    protected = tuple(evidence.roots().values())
    destination = checked_output_directory(output_directory, input_roots=protected)
    accounting = sead_accounting(evidence)
    chronology = ChronologyAccounting(accounting)
    countries: dict[str, Counter[str]] = {code: Counter() for code in _COUNTRIES}
    summaries: dict[str, Counter[str]] = {
        key: Counter()
        for key in (
            "observation_table",
            "source_value_presence",
            "native_value_type",
            "source_unit_id",
            "numeric_scalar_status",
            "source_count_status",
            "source_age_type",
            "source_comparability",
            "observation_method_id",
        )
    }
    counters: Counter[str] = Counter()
    samples: dict[str, set[int]] = {code: set() for code in _COUNTRIES}
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )

    def observations() -> Iterable[dict[str, Any]]:
        for source in evidence.rows("source_native_observations.json", "observations"):
            record = accounting.observation(source)
            row = record["source_observation"]
            value = row["source_value"]
            countries[row["country_code"]]["observations"] += 1
            method = record["source_method"]
            values = {
                "observation_table": row["source_table"],
                "source_value_presence": record["source_value_presence"],
                "native_value_type": type(value).__name__,
                "source_unit_id": canonical_bytes(
                    row["source_semantics"]["source_unit_id"]
                )
                .decode()
                .strip(),
                "numeric_scalar_status": record["numeric_scalar_compatibility"],
                "source_count_status": record["source_count_compatibility"],
                "observation_method_id": canonical_bytes(
                    method["method_id"] if method else None
                )
                .decode()
                .strip(),
            }
            for key, value_key in values.items():
                summaries[key][value_key] += 1
            counters["numeric_zeros"] += int(type(value) in (int, float) and value == 0)
            counters["text_zeros"] += int(value == "0")
            counters["pollen_method_observations"] += int(
                record["source_pollen_method_candidate"]
            )
            counters["observations_without_taxon_relation"] += int(
                record["source_taxon_relation"] is None
            )
            yield record

    def claims() -> Iterable[dict[str, Any]]:
        for source in evidence.rows("chronology_claims.json", "claims"):
            record = chronology.claim(source)
            row = record["source_claim"]
            countries[row["country_code"]]["chronology_claims"] += 1
            summaries["source_age_type"][row["source_age_type"]] += 1
            summaries["source_comparability"][row["comparability_status"]] += 1
            counters["claims_with_observations"] += int(
                record["observation_count_at_analysis_entity"] > 0
            )
            yield record

    def entities() -> Iterable[dict[str, Any]]:
        for source in accounting.entities.values():
            record = chronology.entity(source)
            row = record["source_entity_relation"]
            country = countries[row["country_code"]]
            country["analysis_entities"] += 1
            country["observed_analysis_entities"] += int(
                record["observation_count"] > 0
            )
            sample = row["physical_sample_id"]
            if type(sample) is int:
                samples[row["country_code"]].add(sample)
            else:
                counters["entities_without_physical_sample"] += 1
            yield record

    _write_rows(stage / "observations.jsonl", observations())
    _write_rows(stage / "chronology.jsonl", claims())
    _write_rows(stage / "analysis-entities.jsonl", entities())
    _write_rows(
        stage / "relations.jsonl",
        (
            {"source_locator": source.locator(), "source_relation": source.payload()}
            for field in _RELATION_FIELDS
            for source in evidence.rows("observation_relation_index.json", field)
        ),
    )
    _write_rows(
        stage / "raw-lookups.jsonl",
        (
            {"source_table": table, "source_row": row}
            for table in ("tbl_methods", "tbl_abundance_elements", "tbl_units")
            for row in evidence.raw_rows(table)
        ),
    )
    _write_rows(
        stage / "raw-projection-replay.json",
        [json_object(evidence.replay_receipt_bytes)],
    )
    source_observations = evidence.document("source_native_observations.json")
    observation_count = sum(summaries["observation_table"].values())
    if observation_count != source_observations["observation_count"]:
        raise ValueError(
            "SEAD observation accounting does not cover the source denominator"
        )
    manifest = evidence.manifest()
    if sum(chronology.claim_counts.values()) != manifest["chronology_claim_count"]:
        raise ValueError("SEAD claim accounting does not cover the source denominator")
    if (
        len(accounting.entities)
        != evidence.document("observation_relation_index.json")["entity_relation_count"]
    ):
        raise ValueError("SEAD entity accounting does not cover the source denominator")
    files = []
    for path in sorted(stage.iterdir()):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        files.append(
            {"path": path.name, "sha256": digest, "size_bytes": path.stat().st_size}
        )
    fields = (
        "observations",
        "chronology_claims",
        "analysis_entities",
        "observed_analysis_entities",
    )
    sample_count = len(set().union(*samples.values()))
    source_sample_count = source_observations["source_table_counts"][
        "tbl_physical_samples"
    ]
    if sample_count > source_sample_count:
        raise ValueError("Entity-linked physical samples exceed the raw denominator")
    payload = {
        "schema_version": "sead-lra-admission-audit.v1",
        "source_family": "sead",
        "source_run_id": manifest["source_run_id"],
        "normalized_build_id": manifest["build_id"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "inputs": evidence.input_records(),
        "artifacts": files,
        "producer": producer,
        "source_table_count": manifest["source_table_count"],
        "available_observations": observation_count,
        "available_analysis_entities": len(accounting.entities),
        "entity_linked_physical_samples": sample_count,
        "source_physical_samples": source_sample_count,
        "physical_samples_without_analysis_entity": source_sample_count - sample_count,
        "physical_sample_scope": "country rows and AdmissionReport samples cover only physical samples with an analysis entity; unlinked raw samples have no inferred country",
        "source_table_row_counts": source_observations["source_table_counts"],
        "chronology_claims": sum(chronology.claim_counts.values()),
        "country_accounting": {
            code: {
                **{key: counts[key] for key in fields},
                "entity_linked_physical_samples": len(samples[code]),
            }
            for code, counts in countries.items()
        },
        **{
            f"{key}_counts": dict(sorted(counts.items()))
            for key, counts in summaries.items()
        },
        "counters": dict(sorted(counters.items())),
        "palynology_lookup_present": any(
            row.get("method_id") == 14 for row in accounting.methods.values()
        ),
        "method_scope": "lookup presence differs from an observed dataset-method link; method alone is not pollen grain eligibility",
        "lra_admission_status": "refused",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "scientific_review_status": "not_supplied",
        "count_semantics": "source_absolute_element_counts_are_not_approved_pollen_grain_counts",
        "chronology_policy": "all source claims retained at their analysis entity; no selected chronology or inferred physical-sample transfer",
    }
    content = canonical_bytes(payload)
    with (stage / "manifest.json").open("xb") as manifest_stream:
        manifest_stream.write(content)
        manifest_stream.flush()
        os.fsync(manifest_stream.fileno())
    evidence.assert_unchanged()
    if producer_identity() != producer:
        raise ValueError("Host producer implementation changed during SEAD audit")
    checked_output_directory(destination, input_roots=protected)
    publish_new_output_tree(final_output_root=destination, staging_output_root=stage)
    return AdmissionReport(
        destination,
        hashlib.sha256(content).hexdigest(),
        sample_count,
        sample_count,
        observation_count,
        observation_count,
    )
