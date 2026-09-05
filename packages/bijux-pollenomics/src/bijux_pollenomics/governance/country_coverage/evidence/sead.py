"""SEAD country evidence orchestration."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection
from bijux_pollenomics.evidence.sources.sead import SEAD_GOVERNED_EVIDENCE_RUN_ID

from ..boundaries import _validate_admission_copied_file
from ..constants import (
    SEAD_ADMISSION_PATH,
    SEAD_DECISIONS_PATH,
    SEAD_PUBLIC_SITES_PATH,
    SEAD_SITES_PATH,
    CountryCoverageError,
    _NORDIC_COUNTRY_CODES,
)
from ..decoding import _geojson_country_counts, _integer_counts, _sha256
from .partitions import EvidenceMap, _site_partition
from .sead_decisions import admitted_sead_sites, derive_sead_country_decisions
from .sead_validation import _validate_sead_country_summaries


def add_sead_evidence(
    evidence: EvidenceMap,
    documents: Mapping[str, Mapping[str, object]],
    *,
    input_bytes: Mapping[str, bytes],
    boundary_digest: str,
    boundary_version: str,
    boundary_collections: CountryBoundaryCollection,
    boundary_counts: Mapping[str, int],
    claim_document: Mapping[str, object],
) -> None:
    admission = documents[SEAD_ADMISSION_PATH]
    decision_document = documents[SEAD_DECISIONS_PATH]
    admitted_sites = admitted_sead_sites(admission, documents[SEAD_SITES_PATH])
    decision_evidence = derive_sead_country_decisions(
        decision_document,
        admitted_sites=admitted_sites,
        boundary_collections=boundary_collections,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
    )
    _site_partition(
        evidence,
        "sead",
        "source_reported",
        Counter({"UNASSIGNED": len(decision_evidence.decisions)}),
    )
    _validate_sead_country_summaries(
        admission,
        decision_document,
        decision_count=len(decision_evidence.decisions),
        decision_statuses=decision_evidence.statuses,
        decision_methods=decision_evidence.methods,
        decision_country_codes=decision_evidence.country_codes,
        governed=decision_evidence.governed,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        country_assignment_sha256=decision_evidence.country_assignment_sha256,
        boundary_counts=boundary_counts,
        boundary_manifest=documents["data/boundaries/raw/source_manifest.json"],
        boundary_manifest_sha256=_sha256(
            input_bytes["data/boundaries/raw/source_manifest.json"]
        ),
    )
    _validate_admission_copied_file(
        admission,
        relative_path="country-decisions.json",
        payload=input_bytes[SEAD_DECISIONS_PATH],
    )
    _validate_admission_copied_file(
        admission,
        relative_path="payloads/tbl_sites.json",
        payload=input_bytes[SEAD_SITES_PATH],
    )
    _site_partition(evidence, "sead", "governed_assignment", decision_evidence.governed)
    _add_sead_chronology_counts(
        evidence,
        admission=admission,
        claim_document=claim_document,
        governed=decision_evidence.governed,
    )
    _site_partition(
        evidence,
        "sead",
        "publication",
        _geojson_country_counts(documents[SEAD_PUBLIC_SITES_PATH]),
        published=True,
    )
    claim_country_counts = _integer_counts(
        claim_document.get("country_counts"), "SEAD claim countries"
    )
    for country in _NORDIC_COUNTRY_CODES:
        evidence[("sead", "publication", country)]["age_claims"] = claim_country_counts[
            country
        ]
    for country in ("UNASSIGNED", "OUTSIDE"):
        evidence[("sead", "publication", country)]["age_claims"] = 0


def _add_sead_chronology_counts(
    evidence: EvidenceMap,
    *,
    admission: Mapping[str, object],
    claim_document: Mapping[str, object],
    governed: Mapping[str, int],
) -> None:
    if claim_document.get("schema_version") != "sead-chronology-claim-bundle.v1":
        raise CountryCoverageError("SEAD chronology claim schema is inconsistent")
    if claim_document.get("source_run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID:
        raise CountryCoverageError(
            "SEAD chronology claims do not bind the governed run"
        )
    if (
        claim_document.get("propagation_status") != "refused"
        or claim_document.get("propagation_reason_code")
        != "source_classification_not_accepted"
    ):
        raise CountryCoverageError(
            "SEAD chronology claims do not preserve classification refusal"
        )
    if claim_document.get("acquisition_manifest_sha256") != admission.get(
        "acquisition_manifest_sha256"
    ):
        raise CountryCoverageError("SEAD chronology claims do not bind the admission")
    claim_country_counts = _integer_counts(
        claim_document.get("country_counts"), "SEAD claim countries"
    )
    if set(claim_country_counts) != set(_NORDIC_COUNTRY_CODES):
        raise CountryCoverageError("SEAD claim country partitions are incomplete")
    for country in ("SE", "DK", "NO", "FI"):
        counts = evidence[("sead", "governed_assignment", country)]
        counts["accepted_records"] = counts["sites"]
        counts["unresolved_records"] = 0
        counts["excluded_records"] = 0
        counts["age_claims"] = claim_country_counts[country]
    review_counts = evidence[("sead", "governed_assignment", "UNASSIGNED")]
    review_counts.update(
        accepted_records=0,
        age_claims=0,
        unresolved_records=governed["UNASSIGNED"],
        excluded_records=0,
    )
    outside_counts = evidence[("sead", "governed_assignment", "OUTSIDE")]
    outside_counts.update(
        accepted_records=0,
        age_claims=0,
        unresolved_records=0,
        excluded_records=governed["OUTSIDE"],
    )
