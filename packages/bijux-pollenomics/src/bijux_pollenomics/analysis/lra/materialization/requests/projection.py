"""Derive complete count matrices from explicitly selected synthetic source cells."""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
from typing import Any, cast

from ...engine.errors import LRARefusal
from ..chronology import chronology_projection
from ..models import canonical_bytes
from ..neotoma import SourceAccounting, source_accounting
from ..reading import NeotomaEvidence
from .inputs import verify_raw_projection
from .models import SampleChronologyBinding, SourceCellBinding


def project_cells(
    template: dict[str, Any],
    evidence: NeotomaEvidence,
    cells: Sequence[SourceCellBinding],
    chronologies: Sequence[SampleChronologyBinding],
    files: dict[str, tuple[str, bytes]],
) -> dict[str, Any]:
    verification = verify_raw_projection(evidence)
    samples = {
        (role, row["sample_id"]): row
        for role in ("regional", "local")
        if role in template
        for row in template[role]["samples"]
    }
    declared_sample_count = sum(
        len(template[role]["samples"])
        for role in ("regional", "local")
        if role in template
    )
    selected = [identity for _, identity in samples]
    if len(set(selected)) != declared_sample_count:
        raise LRARefusal(
            "duplicate_sample_id", "Every selected source sample must be unique"
        )
    accounting = source_accounting(evidence, selected)
    if accounting.indexes["conflicts"] or accounting.indexes["orphans"]:
        raise LRARefusal(
            "unresolved_synthetic_source_relations",
            "This fixture profile requires a conflict-free, orphan-free source universe",
        )
    expected = {
        (role, sample, taxon) for role, sample in samples for taxon in template["taxa"]
    }
    bindings = {(row.role, row.sample_id, row.taxon): row for row in cells}
    if (
        set(bindings) != expected
        or len(bindings) != len(cells)
        or len({row.observation_id for row in cells}) != len(cells)
    ):
        raise LRARefusal(
            "source_cell_inventory_mismatch", "No implicit cells or reused observations"
        )
    claims = {row.sample_id: row.chronology_claim_id for row in chronologies}
    if set(claims) != set(selected) or len(claims) != len(chronologies):
        raise LRARefusal(
            "chronology_binding_inventory_mismatch",
            "Select one explicit claim per sample",
        )
    observations = {}
    selected_rows = set()
    for source in evidence.rows("observations"):
        record = accounting.observation(source)
        if record["selected"]:
            identity = record["source_observation"]["observation_id"]
            observations[identity] = record
            selected_rows.add(identity)
    if selected_rows != {row.observation_id for row in cells}:
        raise LRARefusal(
            "unaccounted_sample_observations",
            "Every selected sample observation needs one cell",
        )
    lineage = []
    units = set()
    for (role, sample_id), target in samples.items():
        if any(key in target for key in ("counts", "age_type", "age_support_bp")):
            raise LRARefusal("prefilled_derived_source_field", sample_id)
        sample = accounting.indexes["samples"][sample_id].payload()
        if target["site_id"] != sample["site_id"]:
            raise LRARefusal("source_sample_site_mismatch", sample_id)
        counts = []
        for taxon in template["taxa"]:
            binding = bindings[(role, sample_id, taxon)]
            record = observations[binding.observation_id]
            observation = record["source_observation"]
            if (
                observation["sample_id"] != sample_id
                or observation["source_reported_name"] != taxon
                or observation.get("source_element_type") != "pollen"
            ):
                raise LRARefusal(
                    "source_cell_identity_mismatch", binding.observation_id
                )
            if record["count_status"] != "count_candidate":
                raise LRARefusal(
                    "source_cell_not_count", str(record["count_reason_codes"])
                )
            counts.append(record["typed_count"])
            units.add(canonical_bytes(observation["source_unit"]))
            lineage.append(
                {
                    "role": role,
                    "sample_id": sample_id,
                    "taxon": taxon,
                    "count": record["typed_count"],
                    "source_observation": observation,
                    "source_locator": record["source_locator"],
                }
            )
        target["counts"] = counts
        _bind_chronology(target, claims[sample_id], accounting, files)
        raw_id = target["raw_evidence_id"]
        if files[raw_id][1] != (evidence.raw_root / "manifest.json").read_bytes():
            raise LRARefusal("raw_snapshot_binding_mismatch", sample_id)
    if len(units) != 1:
        raise LRARefusal(
            "incompatible_source_count_units",
            "Mixed native count units require a governed transform",
        )
    excluded = set(accounting.indexes["samples"]) - set(selected)
    supplied_exclusions = [row["sample_id"] for row in template["exclusions"]]
    if set(supplied_exclusions) != excluded or len(supplied_exclusions) != len(
        excluded
    ):
        raise LRARefusal(
            "source_sample_denominator_mismatch",
            "Declare every unselected source sample exactly once",
        )
    return {
        "source_projection_verification": verification,
        "source_snapshot_id": evidence.manifest()["source_snapshot_id"],
        "normalized_build_id": evidence.manifest()["build_id"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "selected_samples": len(selected),
        "selected_cells": len(cells),
        "available_samples": len(accounting.indexes["samples"]),
        "available_observations": sum(accounting.observations.values()),
        "excluded_samples": sorted(excluded),
        "cells": lineage,
        "chronology_bindings": [
            {"sample_id": sample_id, "chronology_claim_id": claim_id}
            for sample_id, claim_id in sorted(claims.items())
        ],
    }


def _bind_chronology(
    target: dict[str, Any],
    claim_id: str,
    accounting: SourceAccounting,
    files: dict[str, tuple[str, bytes]],
) -> None:
    source = accounting.indexes["age_claims"].get(claim_id)
    if source is None:
        raise LRARefusal("missing_source_chronology_claim", claim_id)
    sample = accounting.indexes["samples"][target["sample_id"]].payload()
    projection = chronology_projection(sample, [source])
    claim = source.payload()
    projected_claims = cast(list[dict[str, Any]], projection["claims"])
    if projected_claims[0]["ownership_mismatches"]:
        raise LRARefusal("chronology_sample_ownership_mismatch", claim_id)
    chronology = accounting.indexes["chronologies"].get(claim["chronology_id"])
    if chronology is None or any(
        chronology.payload()[field] != sample[field]
        for field in ("collection_unit_id", "site_id", "country_code")
    ):
        raise LRARefusal("chronology_source_ownership_mismatch", claim_id)
    types = {
        "Calendar years BP": "calendar_bp",
        "Calibrated radiocarbon years BP": "calibrated_bp",
    }
    if (
        claim["comparability_status"] != "comparable"
        or claim["source_age_type"] not in types
    ):
        raise LRARefusal("source_chronology_not_comparable", claim_id)
    if (
        files[target["chronology_evidence_id"]][1]
        != (accounting.evidence.normalized_root / source.path).read_bytes()
    ):
        raise LRARefusal("chronology_evidence_binding_mismatch", claim_id)
    target["age_type"] = types[claim["source_age_type"]]
    target["age_support_bp"] = [[claim["younger_bp"], claim["older_bp"]]]
