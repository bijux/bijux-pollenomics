"""Publish a complete refused-source ledger without executing a numerical model."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any

from bijux_pollenomics.core.owned_tree import publish_new_output_tree
from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from .models import AdmissionReport, canonical_bytes, producer_identity
from .neotoma import MISSING_LRA_EVIDENCE, source_accounting
from .paths import checked_output_directory
from .reading import NeotomaEvidence, read_neotoma_evidence


def output_destination(path: Path, evidence: NeotomaEvidence) -> Path:
    """Refuse unsafe or source-overlapping output before creating any files."""
    return checked_output_directory(
        path, input_roots=(evidence.raw_root, evidence.normalized_root)
    )


def run_materialization(
    *,
    raw_root: Path,
    normalized_root: Path,
    output_directory: Path,
    selected_sample_ids: Sequence[str] | None,
) -> AdmissionReport:
    """Reconcile every source row, with an explicit selected/unselected partition."""
    producer = producer_identity()
    evidence = read_neotoma_evidence(raw_root, normalized_root)
    destination = output_destination(output_directory, evidence)
    accounting = source_accounting(evidence, selected_sample_ids)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )
    countries: dict[str, Counter[str]] = {code: Counter() for code in COUNTRY_CODES}
    count_statuses: Counter[str] = Counter()
    total_observations = selected_observations = orphaned_observations = 0
    with (stage / "observations.jsonl").open("wb") as stream:
        for source in evidence.rows("observations"):
            record = accounting.observation(source)
            stream.write(canonical_bytes(record))
            total_observations += 1
            selected = record["selected"]
            selected_observations += int(selected)
            source_record = record["source_observation"]
            orphaned_observations += int(
                source_record["sample_id"] not in accounting.indexes["samples"]
            )
            country = countries[source_record["country_code"]]
            country["available_observations"] += 1
            country[
                "selected_observations" if selected else "unselected_observations"
            ] += 1
            count_statuses[record["count_status"]] += 1
        stream.flush()
        os.fsync(stream.fileno())
    with (stage / "samples.jsonl").open("wb") as stream:
        for source in accounting.indexes["samples"].values():
            record = accounting.sample(source)
            stream.write(canonical_bytes(record))
            country = countries[record["source_sample"]["country_code"]]
            country["available_samples"] += 1
            country[
                "selected_samples" if record["selected"] else "unselected_samples"
            ] += 1
        stream.flush()
        os.fsync(stream.fileno())
    for surface in ("conflicts", "orphans"):
        with (stage / f"{surface}.jsonl").open("wb") as stream:
            for row in accounting.indexes[surface].values():
                stream.write(
                    canonical_bytes(
                        {
                            "source_locator": row.locator(),
                            "source_record": row.payload(),
                        }
                    )
                )
            stream.flush()
            os.fsync(stream.fileno())
    manifest = evidence.manifest()
    expected_observations = manifest["surfaces"]["observations"]["row_count"]
    if total_observations != expected_observations:
        raise ValueError("Observation accounting does not cover the source denominator")
    artifacts = []
    for path in sorted(stage.iterdir()):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        artifacts.append(
            {"path": path.name, "sha256": digest, "size_bytes": path.stat().st_size}
        )
    fields = (
        "available_samples",
        "selected_samples",
        "unselected_samples",
        "available_observations",
        "selected_observations",
        "unselected_observations",
    )
    payload: dict[str, Any] = {
        "schema_version": "neotoma-lra-admission-audit.v1",
        "source_family": "neotoma",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "normalized_build_id": manifest["build_id"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "inputs": evidence.input_records(),
        "artifacts": artifacts,
        "producer": producer,
        "selection": {
            "mode": "all_source_samples"
            if selected_sample_ids is None
            else "explicit_sample_ids",
            "sample_ids": sorted(accounting.selected_samples),
        },
        "available_samples": len(accounting.indexes["samples"]),
        "selected_samples": len(accounting.selected_samples),
        "unselected_samples": len(accounting.indexes["samples"])
        - len(accounting.selected_samples),
        "available_observations": total_observations,
        "selected_observations": selected_observations,
        "unselected_observations": total_observations - selected_observations,
        "observations_without_materialized_sample": orphaned_observations,
        "count_status_counts": dict(sorted(count_statuses.items())),
        "source_conflicts": len(accounting.indexes["conflicts"]),
        "source_orphans": len(accounting.indexes["orphans"]),
        "source_surface_row_counts": {
            name: value["row_count"] for name, value in manifest["surfaces"].items()
        },
        "country_accounting": {
            code: {key: counts[key] for key in fields}
            for code, counts in countries.items()
        },
        "lra_admission_status": "refused",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "reason_codes": list(MISSING_LRA_EVIDENCE),
        "count_semantics": "necessary_count_candidates_only_not_approved_taxa_or_pollen_denominators",
        "scientific_review_status": "not_supplied",
    }
    manifest_content = canonical_bytes(payload)
    with (stage / "manifest.json").open("wb") as stream:
        stream.write(manifest_content)
        stream.flush()
        os.fsync(stream.fileno())
    evidence.assert_unchanged()
    if producer_identity() != producer:
        raise ValueError("Host producer implementation changed during admission audit")
    output_destination(destination, evidence)
    publish_new_output_tree(final_output_root=destination, staging_output_root=stage)
    return AdmissionReport(
        destination,
        hashlib.sha256(manifest_content).hexdigest(),
        len(accounting.indexes["samples"]),
        len(accounting.selected_samples),
        total_observations,
        selected_observations,
    )
