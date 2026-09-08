"""Per-site provenance for the SEAD atlas projection."""

from __future__ import annotations

from .models import EvidenceBundle


def build_provenance_tab(
    bundle: EvidenceBundle, source_site_id: str, site_uuid: str
) -> dict[str, object]:
    """Expose acquisition, evidence, and stable site lineage together."""
    return {
        "site_uuid": site_uuid,
        "source_run_id": bundle.run_id,
        "build_id": bundle.build_id,
        "acquisition_manifest_sha256": bundle.acquisition_manifest_sha256,
        "parent_admission_sha256": bundle.parent_admission_sha256,
        "evidence_bundle_path": f"data/sead/normalized/acquisitions/{bundle.run_id}",
        "evidence_file_set_sha256": bundle.file_set_sha256,
        "claim_locator_contract": "chronology_claims.json#chronology_claim_id={chronology_claim_id}",
        "observation_locator_contract": "source_native_observations.json#observation_id={observation_id}",
        "relation_locator_contract": "observation_relation_index.json#{relation_id}",
        "event_refusal_locator_contract": "evidence_events.json#observation_id={observation_id}",
        "record_locator": f"tbl_sites#site_id={source_site_id}",
        "acquisition_release_status": bundle.admission.get("release_status"),
        "propagation_status": bundle.claims.get("propagation_status"),
        "propagation_reason_code": bundle.claims.get("propagation_reason_code"),
    }
