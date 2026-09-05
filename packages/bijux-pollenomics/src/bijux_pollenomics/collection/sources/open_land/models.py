"""Scientific types for modeled land-cover context."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .authority import (
    ARCHIVE_SHA256,
    SOURCE_CITATION_DOI,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_REPOSITORY,
)


@dataclass(frozen=True)
class ModeledLandCoverCell:
    """One source row, preserved as modeled context rather than observation."""

    source_member: str
    source_member_sha256: str
    source_row_number: int
    time_slice_bp: int
    longitude_claim: Decimal
    latitude_claim: Decimal
    coniferous_proportion: Decimal
    broadleaved_proportion: Decimal
    unforested_open_proportion: Decimal
    source_values: tuple[str, str, str, str, str]
    source_archive_sha256: str = ARCHIVE_SHA256
    source_commit: str = SOURCE_COMMIT
    source_repository: str = SOURCE_REPOSITORY
    source_citation_doi: str = SOURCE_CITATION_DOI
    source_data_license: str = SOURCE_DATA_LICENSE
    licensing_status: str = "upstream_license_verified_release_review_required"
    attribution_status: str = "required_not_materialized_for_public_release"
    source_age_label: str = "BP"
    age_system: None = None
    age_reference_epoch_ce: None = None
    chronology_status: str = "source_native_bp_point_slice_unreviewed"
    temporal_comparability: str = "unresolved"
    propagation_eligibility: str = "context_only"
    temporal_extent_kind: str = "source_point_slice"
    spatial_reference_status: str = (
        "source_script_assigns_wgs84_to_generated_geometry_unreviewed"
    )
    evidence_kind: str = "derived_modeled_land_cover"
    country_code: None = None
    taxon_id: None = None
    taxon_semantics: str = "not_applicable_land_cover_aggregate"
    uncertainty: None = None
    land_cover_uncertainty_status: str = "not_supplied"
    public_release_allowed: bool = False
    propagation_use_allowed: bool = False
    refusal_reasons: tuple[str, ...] = (
        "country_boundary_join_required",
        "chronology_conversion_not_reviewed",
        "uncertainty_surface_not_supplied",
        "human_licensing_review_required",
        "scientific_model_review_required",
    )

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible values without float rounding."""
        return {
            "age_reference_epoch_ce": self.age_reference_epoch_ce,
            "age_system": self.age_system,
            "broadleaved_proportion": str(self.broadleaved_proportion),
            "chronology_status": self.chronology_status,
            "coniferous_proportion": str(self.coniferous_proportion),
            "country_code": self.country_code,
            "evidence_kind": self.evidence_kind,
            "land_cover_uncertainty_status": self.land_cover_uncertainty_status,
            "licensing_status": self.licensing_status,
            "latitude_claim": str(self.latitude_claim),
            "longitude_claim": str(self.longitude_claim),
            "propagation_use_allowed": self.propagation_use_allowed,
            "public_release_allowed": self.public_release_allowed,
            "refusal_reasons": list(self.refusal_reasons),
            "source_age_label": self.source_age_label,
            "source_citation_doi": self.source_citation_doi,
            "source_data_license": self.source_data_license,
            "source_member": self.source_member,
            "source_member_sha256": self.source_member_sha256,
            "source_row_number": self.source_row_number,
            "source_archive_sha256": self.source_archive_sha256,
            "source_commit": self.source_commit,
            "source_repository": self.source_repository,
            "source_values": list(self.source_values),
            "spatial_reference_status": self.spatial_reference_status,
            "taxon_id": self.taxon_id,
            "taxon_semantics": self.taxon_semantics,
            "temporal_comparability": self.temporal_comparability,
            "temporal_extent_kind": self.temporal_extent_kind,
            "time_slice_bp": self.time_slice_bp,
            "uncertainty": self.uncertainty,
            "unforested_open_proportion": str(self.unforested_open_proportion),
            "propagation_eligibility": self.propagation_eligibility,
            "attribution_status": self.attribution_status,
        }


@dataclass(frozen=True)
class OpenLandSummary:
    """Reconciled denominator and scope for one archive inspection."""

    archive_sha256: str
    archive_member_count: int
    admitted_csv_count: int
    modeled_cell_count: int
    time_slices_bp: tuple[int, ...]
    longitude_extent: tuple[Decimal, Decimal]
    latitude_extent: tuple[Decimal, Decimal]
    public_release_allowed: bool = False
    propagation_use_allowed: bool = False
