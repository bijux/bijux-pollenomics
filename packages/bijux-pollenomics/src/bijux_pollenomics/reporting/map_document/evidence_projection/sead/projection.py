"""SEAD atlas projection workflow."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from pathlib import Path

from .accounting import build_accounting
from .admission import load_evidence_bundle
from .chronology import index_claims
from .detail_records import build_detail_records
from .observations import index_observations
from .relations import index_relations
from .sites import index_sites


def project_sead(
    context_root: Path,
    layers: Sequence[MutableMapping[str, object]],
    *,
    expected_run_id: str,
    expected_manifest_sha256: str,
    expected_admission_sha256: str,
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
    records = build_detail_records(bundle, claims, relations, observations, sites)
    accounting = build_accounting(
        bundle, claims, relations, observations, sites, layers, records
    )
    return records, accounting
