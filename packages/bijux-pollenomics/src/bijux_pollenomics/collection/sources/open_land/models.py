"""Scientific types for modeled land-cover context."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .authority import (
    ARCHIVE_SHA256,
    SOURCE_ATTRIBUTION,
    SOURCE_CITATION_DOI,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_DATASET_ID,
    SOURCE_MODEL_KIND,
    SOURCE_REPOSITORY,
    SOURCE_SPATIAL_RESOLUTION_DEGREES,
)


@dataclass(frozen=True)
class ModeledLandCoverCell:
    """One source row, preserved as modeled context rather than observation."""

    source_member: str
    source_member_sha256: str
    source_row_number: int
    time_slice_bp: int
    younger_bp: int
    older_bp: int
    longitude_claim: Decimal
    latitude_claim: Decimal
    coniferous_proportion: Decimal
    broadleaved_proportion: Decimal
    unforested_open_proportion: Decimal
    source_values: tuple[str, str, str, str, str]
    source_archive_sha256: str = ARCHIVE_SHA256
    source_commit: str = SOURCE_COMMIT
    source_dataset_id: str = SOURCE_DATASET_ID
    source_repository: str = SOURCE_REPOSITORY
    source_citation_doi: str = SOURCE_CITATION_DOI
    source_data_license: str = SOURCE_DATA_LICENSE
    source_attribution: str = SOURCE_ATTRIBUTION
    source_model_kind: str = SOURCE_MODEL_KIND
    source_spatial_resolution_degrees: int = SOURCE_SPATIAL_RESOLUTION_DEGREES
    licensing_status: str = "upstream_license_verified_release_review_required"
    attribution_status: str = "required_not_materialized_for_public_release"
    source_age_label: str = "BP"
    age_system: str = "calibrated_bp"
    age_reference_epoch_ce: int = 1950
    chronology_status: str = "source_published_calibrated_bp_interval"
    temporal_comparability: str = "context_only_source_published_interval"
    propagation_eligibility: str = "context_only"
    temporal_extent_kind: str = "source_published_interval"
    spatial_reference_status: str = "source_centers_in_wgs84_one_degree_model_grid"
    spatial_interpolation_status: str = "source_model_is_spatially_interpolated"
    added_spatial_interpolation: bool = False
    added_temporal_interpolation: bool = False
    evidence_kind: str = "derived_modeled_land_cover"
    country_code: None = None
    taxon_id: None = None
    taxon_semantics: str = "not_applicable_land_cover_aggregate"
    uncertainty: None = None
    land_cover_uncertainty_status: str = "not_supplied"
    public_release_allowed: bool = False
    propagation_use_allowed: bool = False
    refusal_reasons: tuple[str, ...] = (
        "uncertainty_surface_not_supplied",
        "human_licensing_review_required",
        "scientific_model_review_required",
        "independent_release_review_required",
    )

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible values without float rounding."""
        return {
            "added_spatial_interpolation": self.added_spatial_interpolation,
            "added_temporal_interpolation": self.added_temporal_interpolation,
            "age_reference_epoch_ce": self.age_reference_epoch_ce,
            "age_system": self.age_system,
            "attribution_status": self.attribution_status,
            "broadleaved_proportion": str(self.broadleaved_proportion),
            "chronology_status": self.chronology_status,
            "coniferous_proportion": str(self.coniferous_proportion),
            "country_code": self.country_code,
            "evidence_kind": self.evidence_kind,
            "land_cover_uncertainty_status": self.land_cover_uncertainty_status,
            "latitude_claim": str(self.latitude_claim),
            "licensing_status": self.licensing_status,
            "longitude_claim": str(self.longitude_claim),
            "older_bp": self.older_bp,
            "propagation_eligibility": self.propagation_eligibility,
            "propagation_use_allowed": self.propagation_use_allowed,
            "public_release_allowed": self.public_release_allowed,
            "refusal_reasons": list(self.refusal_reasons),
            "source_age_label": self.source_age_label,
            "source_archive_sha256": self.source_archive_sha256,
            "source_attribution": self.source_attribution,
            "source_citation_doi": self.source_citation_doi,
            "source_commit": self.source_commit,
            "source_data_license": self.source_data_license,
            "source_dataset_id": self.source_dataset_id,
            "source_member": self.source_member,
            "source_member_sha256": self.source_member_sha256,
            "source_model_kind": self.source_model_kind,
            "source_repository": self.source_repository,
            "source_row_number": self.source_row_number,
            "source_spatial_resolution_degrees": (
                self.source_spatial_resolution_degrees
            ),
            "source_values": list(self.source_values),
            "spatial_interpolation_status": self.spatial_interpolation_status,
            "spatial_reference_status": self.spatial_reference_status,
            "taxon_id": self.taxon_id,
            "taxon_semantics": self.taxon_semantics,
            "temporal_comparability": self.temporal_comparability,
            "temporal_extent_kind": self.temporal_extent_kind,
            "time_slice_bp": self.time_slice_bp,
            "uncertainty": self.uncertainty,
            "unforested_open_proportion": str(self.unforested_open_proportion),
            "younger_bp": self.younger_bp,
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


@dataclass(frozen=True)
class OpenLandProjection:
    """Private-review projection and complete country-decision accounting."""

    feature_collection: dict[str, object]
    country_decisions: tuple[dict[str, object], ...]
    reconciliation: dict[str, object]


@dataclass(frozen=True)
class OpenLandPrivateReview:
    """Immutable paths and digests for one private-review materialization."""

    output_root: Path
    manifest_path: Path
    artifact_sha256: tuple[tuple[str, str], ...]
