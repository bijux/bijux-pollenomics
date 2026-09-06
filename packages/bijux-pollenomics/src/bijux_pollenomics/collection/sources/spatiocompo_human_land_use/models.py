"""Typed evidence and refusal surfaces for SpatioCompoMixed exports."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CategoricalPeriod:
    key: str
    label: str
    header_token: str
    oldest_to_present_index: int


@dataclass(frozen=True)
class ModelVariant:
    key: str
    header_token: str
    covariate_posture: str


@dataclass(frozen=True)
class ExportFileAuthority:
    relative_path: str
    size_bytes: int
    sha256: str
    git_blob_sha: str
    period: CategoricalPeriod
    variant: ModelVariant
    upstream_status: str = "available"
    observed_valid_row_count: int = 679
    observed_malformed_row_count: int = 0


@dataclass(frozen=True)
class ModeledHumanLandUseCell:
    source_relative_path: str
    source_file_sha256: str
    source_git_blob_sha: str
    source_row_number: int
    source_values: tuple[str, ...]
    period_key: str
    period_label: str
    oldest_to_present_index: int
    model_variant: str
    model_covariate_posture: str
    longitude_claim: Decimal
    latitude_claim: Decimal
    lcc_coniferous_proportion: Decimal
    lcc_broadleaved_proportion: Decimal
    lcc_unforested_proportion: Decimal
    nlc_coniferous_proportion: Decimal
    nlc_broadleaved_proportion: Decimal
    nlc_open_proportion: Decimal
    human_land_use_proportion: Decimal
    source_repository: str
    source_commit: str
    source_citation_doi: str
    source_data_license: str
    attribution_requirement: str
    uncertainty_status: str = "not_supplied_in_export"
    chronology_status: str = "source_native_categorical_period_center_unreviewed"
    time_start_bp: None = None
    time_end_bp: None = None
    evidence_kind: str = "derived_modeled_human_land_use"
    evidence_role: str = "context_only"
    observed_pollen_use_allowed: bool = False
    propagation_use_allowed: bool = False
    interpolation_allowed: bool = False
    public_release_allowed: bool = False
    release_refusal_reasons: tuple[str, ...] = (
        "qualified_model_semantics_review_required",
        "human_licensing_review_required",
        "source_temporal_interval_not_supplied",
        "uncertainty_not_supplied_in_export",
    )


@dataclass(frozen=True)
class ModeledHumanLandUseSlice:
    authority: ExportFileAuthority
    coordinate_grid_sha256: str
    cells: tuple[ModeledHumanLandUseCell, ...]

    @property
    def row_count(self) -> int:
        return len(self.cells)


@dataclass(frozen=True)
class SliceRefusal:
    relative_path: str
    period_key: str
    model_variant: str
    reason_code: str
    detail: str
    expected_row_count: int = 679
    substitute_variant_allowed: bool = False
    propagation_use_allowed: bool = False
    public_release_allowed: bool = False


@dataclass(frozen=True)
class SpatioCompoHumanLandUseCollection:
    periods_oldest_to_present: tuple[str, ...]
    slices: tuple[ModeledHumanLandUseSlice, ...]
    refusals: tuple[SliceRefusal, ...]
    expected_source_file_count: int = 10
    expected_rows_per_slice: int = 679
    evidence_role: str = "context_only"
    propagation_use_allowed: bool = False
    interpolation_allowed: bool = False
    public_release_allowed: bool = False

    @property
    def admitted_row_count(self) -> int:
        return sum(source_slice.row_count for source_slice in self.slices)
