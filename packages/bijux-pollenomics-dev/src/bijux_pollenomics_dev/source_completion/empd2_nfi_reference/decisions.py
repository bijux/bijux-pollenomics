"""Validate complete EMPD2--NFI review returns and construct typed cohorts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    COHORT_DECISION_PROFILE,
    EvaluationSite,
    ExternalInput,
    ReviewedEvaluationCohort,
    admit_reviewed_evaluation_cohort,
)

from .admission import derived_group_ids, parse_admission
from .projection import (
    build_empd2_nfi_decision_projection,
    digest,
    identities,
    identity,
    iso_date,
)
from .receipt import validated_taxon_receipt
from .review_inputs import validated_review_inputs

_RETURN_KEYS = {
    "schema_version",
    "projection_sha256",
    "admission_id",
    "reviewer_id",
    "reviewer_authority",
    "decision_date",
    "rationale",
    "outcome_access_status",
    "taxon_ppe_receipt",
    "decisions",
}
_DECISION_KEYS = {
    "record_id",
    "source_row_sha256",
    "disposition",
    "reason_codes",
    "evidence_reference_ids",
    "admission",
}


@dataclass(frozen=True)
class Empd2NfiDecisionResult:
    """An NFI-outcome-blind projection and optional declared-intent cohort."""

    projection: dict[str, Any]
    validation: dict[str, Any]
    cohort: ReviewedEvaluationCohort | None


def _pending(projection: dict[str, Any]) -> Empd2NfiDecisionResult:
    validation = {
        "schema_version": "empd2-nfi-reference-decision-validation.v1",
        "projection_sha256": projection["projection_sha256"],
        "decision_status": "awaiting_qualified_return",
        "candidate_count": 16,
        "declared_inclusion_count": 0,
        "scientific_admitted_pair_count": 0,
        "refused_pair_count": 0,
        "awaiting_review_count": 16,
        "outcome_access_status": "not_started",
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
    }
    validation["validation_sha256"] = digest(validation)
    return Empd2NfiDecisionResult(projection, validation, None)


def review_empd2_nfi_decisions(
    *,
    dossier_bytes: bytes,
    dossier_sha256: str,
    spatial_bytes: bytes,
    spatial_sha256: str,
    guide_bytes: bytes,
    guide_sha256: str,
    workbook_sha256: str,
    returned: dict[str, Any] | None = None,
    taxon_ppe_receipt_sha256: str | None = None,
    evidence_manifest_bytes: bytes | None = None,
    evidence_manifest_sha256: str | None = None,
    pollen_count_index_bytes: bytes | None = None,
    pollen_count_index_sha256: str | None = None,
    pollen_count_producer_attestation_bytes: bytes | None = None,
    pollen_count_producer_attestation_sha256: str | None = None,
    taxon_mapping_manifest_bytes: bytes | None = None,
    taxon_mapping_manifest_sha256: str | None = None,
    taxon_parameter_manifest_bytes: bytes | None = None,
    taxon_parameter_manifest_sha256: str | None = None,
    nfi_schema_bytes: bytes | None = None,
    nfi_schema_sha256: str | None = None,
) -> Empd2NfiDecisionResult:
    """Project source leads or validate one complete NFI-outcome-blind return.

    Inclusion requires pinned evidence, a sealed-payload index, source mapping, and
    exact parameter content. No quantitative pollen payload or NFI outcome is opened.
    Content pins do not authenticate reviewers, completeness, or scientific acceptance.
    """
    projection = build_empd2_nfi_decision_projection(
        dossier_bytes=dossier_bytes,
        dossier_sha256=dossier_sha256,
        spatial_bytes=spatial_bytes,
        spatial_sha256=spatial_sha256,
        guide_bytes=guide_bytes,
        guide_sha256=guide_sha256,
        workbook_sha256=workbook_sha256,
    )
    if returned is None:
        if any(
            value is not None
            for value in (
                taxon_ppe_receipt_sha256,
                evidence_manifest_bytes,
                evidence_manifest_sha256,
                pollen_count_index_bytes,
                pollen_count_index_sha256,
                pollen_count_producer_attestation_bytes,
                pollen_count_producer_attestation_sha256,
                taxon_mapping_manifest_bytes,
                taxon_mapping_manifest_sha256,
                taxon_parameter_manifest_bytes,
                taxon_parameter_manifest_sha256,
                nfi_schema_bytes,
                nfi_schema_sha256,
            )
        ):
            raise ValueError("awaiting-review projection must not carry review baggage")
        return _pending(projection)
    initial = digest(returned)
    if (
        set(returned) != _RETURN_KEYS
        or returned.get("schema_version") != "empd2-nfi-reference-decisions.v1"
        or returned.get("projection_sha256") != projection["projection_sha256"]
        or returned.get("reviewer_authority") != "declared_not_authenticated"
        or returned.get("outcome_access_status") != "not_started"
    ):
        raise ValueError("returned decisions target an unsupported projection")
    admission_id = identity(returned["admission_id"], "admission_id")
    reviewer_id = identity(returned["reviewer_id"], "reviewer_id")
    decision_date = iso_date(returned["decision_date"], "decision_date")
    rationale = identity(returned["rationale"], "rationale")
    raw_decisions = returned["decisions"]
    if not isinstance(raw_decisions, list) or any(
        not isinstance(item, dict) for item in raw_decisions
    ):
        raise ValueError("decisions must be an explicit object array")
    candidates = {row["record_id"]: row for row in projection["candidate_rows"]}
    accepted_requested = any(
        item.get("disposition") == "declared_inclusion" for item in raw_decisions
    )
    receipt_data = (
        validated_taxon_receipt(
            returned["taxon_ppe_receipt"], projection, taxon_ppe_receipt_sha256
        )
        if accepted_requested
        else None
    )
    if not accepted_requested and returned["taxon_ppe_receipt"] is not None:
        raise ValueError("all-refused returns must not carry a taxon/PPE receipt")
    if not accepted_requested and taxon_ppe_receipt_sha256 is not None:
        raise ValueError("all-refused returns must not carry a taxon/PPE receipt pin")
    receipt = receipt_data[0] if receipt_data is not None else None
    receipt_sha = receipt_data[1] if receipt_data is not None else None
    if accepted_requested:
        if (
            evidence_manifest_bytes is None
            or evidence_manifest_sha256 is None
            or pollen_count_index_bytes is None
            or pollen_count_index_sha256 is None
            or pollen_count_producer_attestation_bytes is None
            or pollen_count_producer_attestation_sha256 is None
            or taxon_mapping_manifest_bytes is None
            or taxon_mapping_manifest_sha256 is None
            or taxon_parameter_manifest_bytes is None
            or taxon_parameter_manifest_sha256 is None
            or nfi_schema_bytes is None
            or nfi_schema_sha256 is None
        ):
            raise ValueError(
                "declared inclusion requires all pinned evidence and source manifests"
            )
        assert receipt is not None
        evidence_rows = validated_review_inputs(
            projection=projection,
            receipt=receipt,
            reviewer_id=reviewer_id,
            decision_date=decision_date,
            evidence_bytes=evidence_manifest_bytes,
            evidence_sha256=evidence_manifest_sha256,
            index_bytes=pollen_count_index_bytes,
            index_sha256=pollen_count_index_sha256,
            attestation_bytes=pollen_count_producer_attestation_bytes,
            attestation_sha256=pollen_count_producer_attestation_sha256,
            mapping_bytes=taxon_mapping_manifest_bytes,
            mapping_sha256=taxon_mapping_manifest_sha256,
            parameter_bytes=taxon_parameter_manifest_bytes,
            parameter_sha256=taxon_parameter_manifest_sha256,
            nfi_schema_bytes=nfi_schema_bytes,
            nfi_schema_sha256=nfi_schema_sha256,
        )
    else:
        if any(
            value is not None
            for value in (
                evidence_manifest_bytes,
                evidence_manifest_sha256,
                pollen_count_index_bytes,
                pollen_count_index_sha256,
                pollen_count_producer_attestation_bytes,
                pollen_count_producer_attestation_sha256,
                taxon_mapping_manifest_bytes,
                taxon_mapping_manifest_sha256,
                taxon_parameter_manifest_bytes,
                taxon_parameter_manifest_sha256,
                nfi_schema_bytes,
                nfi_schema_sha256,
            )
        ):
            raise ValueError("all-refused returns must not carry review manifests")
        evidence_rows = {}
    seen: set[str] = set()
    records: list[SiteRecord] = []
    site_payloads: list[dict[str, Any]] = []
    channel_payloads: list[ObservationChannels] = []
    external_inputs: dict[str, ExternalInput] = {}
    manifest_decisions = []
    seen_vegetation_observations: set[str] = set()
    admitted = 0
    refused = 0
    for raw in cast(list[dict[str, Any]], raw_decisions):
        if set(raw) != _DECISION_KEYS:
            raise ValueError("returned decision fields differ from the exact schema")
        record_id = identity(raw["record_id"], "record_id")
        candidate = candidates.get(record_id)
        if candidate is None or record_id in seen:
            raise ValueError("returned decision identity is unknown or duplicated")
        seen.add(record_id)
        if raw["source_row_sha256"] != candidate["source_row_sha256"]:
            raise ValueError("returned decision targets stale source evidence")
        reasons = identities(raw["reason_codes"], "reason codes")
        evidence = identities(raw["evidence_reference_ids"], "decision evidence")
        evidence = sorted({*evidence, f"returned-decisions-sha256:{initial}"})
        if evidence_manifest_sha256 is not None:
            evidence = sorted(
                {*evidence, f"reviewed-evidence-sha256:{evidence_manifest_sha256}"}
            )
        if pollen_count_index_sha256 is not None:
            evidence = sorted(
                {
                    *evidence,
                    f"pollen-count-index-sha256:{pollen_count_index_sha256}",
                }
            )
        disposition = raw["disposition"]
        if disposition == "declared_inclusion":
            if receipt is None or receipt_sha is None:
                raise ValueError("admission requires a pinned taxon/PPE receipt")
            record, site, channel, external = parse_admission(
                raw["admission"],
                candidate,
                evidence_rows[record_id],
                projection,
                receipt,
                receipt_sha,
            )
            vegetation_observation = site["vegetation_observation_id"]
            if vegetation_observation in seen_vegetation_observations:
                raise ValueError(
                    "multiple declared inclusions share one NFI observation"
                )
            seen_vegetation_observations.add(vegetation_observation)
            previous = external_inputs.get(external.input_id)
            if previous is not None and previous != external:
                raise ValueError(
                    "cross-record vegetation input has conflicting provenance"
                )
            external_inputs[external.input_id] = external
            records.append(record)
            site_payloads.append(site)
            channel_payloads.append(channel)
            admitted += 1
        elif disposition == "refused":
            if raw["admission"] is not None:
                raise ValueError("refused decisions must not carry admission claims")
            refused += 1
        else:
            raise ValueError(
                "decision disposition must be declared_inclusion or refused"
            )
        manifest_decisions.append(
            {
                "record_id": record_id,
                "decision": (
                    "admitted" if disposition == "declared_inclusion" else disposition
                ),
                "reason_codes": reasons,
                "evidence_reference_ids": evidence,
            }
        )
    if seen != set(candidates) or len(raw_decisions) != 16:
        raise ValueError("returned decisions do not close the 16-lead denominator")
    if [row["record_id"] for row in raw_decisions] != sorted(seen):
        raise ValueError("returned decisions must use canonical record order")
    groups = derived_group_ids(records)
    sites = tuple(
        EvaluationSite(group_id=groups[site["record_id"]], **site)
        for site in site_payloads
    )
    channels = tuple(
        ObservationChannels(
            record_id=channel.record_id,
            group_id=groups[channel.record_id],
            pollen_channels=channel.pollen_channels,
            vegetation_input_ids=channel.vegetation_input_ids,
        )
        for channel in channel_payloads
    )
    observation_ids = [
        value
        for site in sites
        for value in (site.vegetation_observation_id, site.pollen_observation_id)
    ]
    input_kinds: dict[str, str] = {}
    for channel in channels:
        for pollen in channel.pollen_channels:
            previous_kind = input_kinds.setdefault(pollen.input_id, "pollen")
            if previous_kind != "pollen":
                raise ValueError("input identity is reused across observation kinds")
        for vegetation in channel.vegetation_input_ids:
            previous_kind = input_kinds.setdefault(vegetation, "vegetation")
            if previous_kind != "vegetation":
                raise ValueError("input identity is reused across observation kinds")
    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError(
            "cross-record observed units must be reconciled before inclusion"
        )
    manifest = {
        "schema_version": COHORT_DECISION_PROFILE,
        "admission_id": admission_id,
        "reviewer_id": reviewer_id,
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": decision_date,
        "rationale": rationale,
        "candidate_source_manifest_sha256": projection[
            "candidate_source_manifest_sha256"
        ],
        "outcome_access_status": "not_started",
        "decisions": manifest_decisions,
    }
    cohort = None
    if records:
        assert receipt is not None and receipt_sha is not None
        assert taxon_parameter_manifest_sha256 is not None
        parameter_input_id = f"taxon-parameters:{taxon_parameter_manifest_sha256}"
        external_inputs[parameter_input_id] = ExternalInput(
            input_id=parameter_input_id,
            role="fixed_parameter",
            source_manifest_sha256=taxon_parameter_manifest_sha256,
            support=None,
        )
        nodes: dict[str, tuple[str, ...]] = {}
        for record, channel in zip(records, channels, strict=True):
            pollen_id = channel.pollen_channels[0].input_id
            vegetation_id = channel.vegetation_input_ids[0]
            nodes[record.record_id] = (
                pollen_id,
                vegetation_id,
                parameter_input_id,
            )
            nodes[pollen_id] = ()
            nodes[vegetation_id] = ()
        nodes[parameter_input_id] = ()
        cohort = admit_reviewed_evaluation_cohort(
            canonical_json(manifest),
            manifest_sha256(manifest),
            records=tuple(records),
            sites=sites,
            observation_channels=channels,
            dependency_graph=tuple(sorted(nodes.items())),
            taxa=tuple(receipt["accepted_taxon_ids"]),
            external_inputs=tuple(
                external_inputs[key] for key in sorted(external_inputs)
            ),
        )
    validation = {
        "schema_version": "empd2-nfi-reference-decision-validation.v1",
        "projection_sha256": projection["projection_sha256"],
        "returned_decisions_sha256": initial,
        "evidence_manifest_sha256": evidence_manifest_sha256 if records else None,
        "pollen_count_index_sha256": (pollen_count_index_sha256 if records else None),
        "pollen_count_closure": (
            "externally_attested_not_runtime_verified" if records else None
        ),
        "pollen_count_producer_attestation_sha256": (
            pollen_count_producer_attestation_sha256 if records else None
        ),
        "taxon_mapping_manifest_sha256": (
            taxon_mapping_manifest_sha256 if records else None
        ),
        "taxon_parameter_manifest_sha256": (
            taxon_parameter_manifest_sha256 if records else None
        ),
        "decision_manifest_sha256": manifest_sha256(manifest),
        "decision_status": "complete_declared_review",
        "candidate_count": 16,
        "declared_inclusion_count": admitted,
        "scientific_admitted_pair_count": 0,
        "refused_pair_count": refused,
        "awaiting_review_count": 0,
        "reviewer_authority": "declared_not_authenticated",
        "taxon_review_receipt_trust_anchor": (
            "externally_pinned_canonical_receipt_sha256" if records else None
        ),
        "taxon_ppe_receipt_sha256": receipt_sha if records else None,
        "outcome_access_status": "not_started",
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
        "publication_allowed": False,
        "cohort_status": (
            "declared_reviewed_inclusion_engineering_intent"
            if records
            else "no_declared_inclusion"
        ),
    }
    validation["validation_sha256"] = digest(validation)
    if initial != digest(returned):
        raise ValueError("returned decision evidence changed during validation")
    return Empd2NfiDecisionResult(projection, validation, cohort)
