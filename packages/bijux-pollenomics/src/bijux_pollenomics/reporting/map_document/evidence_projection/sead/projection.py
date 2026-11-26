"""SEAD atlas projection workflow."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
import hashlib
from pathlib import Path

from .accounting import build_accounting
from .admission import load_evidence_bundle
from .chronology import index_claims
from .chronology_overlay import (
    HistoricalChronologyRequest,
    _canonical,
    apply_overlay,
)
from .detail_records import build_detail_records
from .observations import index_observations
from .relations import index_relations
from .site_custody import validate_site_binding
from .sites import index_sites


def project_sead(
    context_root: Path,
    layers: Sequence[MutableMapping[str, object]],
    *,
    expected_run_id: str,
    expected_manifest_sha256: str,
    expected_admission_sha256: str,
    historical_chronology: HistoricalChronologyRequest | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Validate and project governed SEAD evidence into atlas details."""
    bundle = load_evidence_bundle(
        context_root,
        expected_run_id=expected_run_id,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_admission_sha256=expected_admission_sha256,
    )
    claims = index_claims(bundle)
    relations = index_relations(bundle)
    observations = index_observations(bundle, claims, relations)
    sites = index_sites(bundle, claims, observations, layers)
    derived = None
    if historical_chronology is not None:
        from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
            build_historical_chronology_overlay,
        )

        overlay = build_historical_chronology_overlay(
            context_root,
            historical_chronology.country_authority_root,
            lineage_sha256=historical_chronology.lineage_sha256,
        )
        if (
            overlay.get("schema_version")
            != "sead-historical-derived-chronology-overlay.v1"
            or overlay.get("source_run_id") != bundle.run_id
            or overlay.get("admission_sha256") != expected_admission_sha256
            or overlay.get("evidence_manifest_sha256") != expected_manifest_sha256
            or overlay.get("lineage_sha256") != historical_chronology.lineage_sha256
        ):
            raise ValueError("SEAD historical chronology overlay identity differs")
        validate_site_binding(
            context_root, historical_chronology.lineage_sha256, sites.rows_by_id, layers
        )
        claims = apply_overlay(claims, overlay)
        derived = {
            "schema_version": "sead-atlas-derived-chronology.v1",
            "overlay_sha256": hashlib.sha256(_canonical(overlay)).hexdigest(),
            "lineage_sha256": historical_chronology.lineage_sha256,
            "evidence_manifest_sha256": expected_manifest_sha256,
            "evidence_file_set_sha256": bundle.file_set_sha256,
            "claim_id_set_sha256": overlay["claim_id_set_sha256"],
            "changed_claim_count": overlay["changed_claim_count"],
            "country_membership": overlay.get("country_membership"),
            "producer_code_identity": "external_execution_receipt_required",
            "source_locator_posture": "original evidence locator precedes the derived overlay",
        }
    records = build_detail_records(bundle, claims, relations, observations, sites)
    if derived is not None:
        for record in records:
            tabs = record["tabs"]
            if not isinstance(tabs, dict) or not isinstance(
                tabs.get("provenance"), dict
            ):
                raise ValueError("SEAD derived chronology provenance differs")
            tabs["provenance"]["derived_chronology"] = dict(derived)
    accounting = build_accounting(
        bundle, claims, relations, observations, sites, layers, records
    )
    if derived is not None:
        accounting["derived_chronology"] = derived
    return records, accounting
