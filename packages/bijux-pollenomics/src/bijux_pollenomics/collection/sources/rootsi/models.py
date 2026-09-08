"""Explicitly unadmitted ROOTSI metadata claims and policy posture."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .authority import ARCHIVE_SHA256, METADATA_MEMBER, METADATA_SHA256


@dataclass(frozen=True)
class RootsiSiteMetadataClaim:
    """Source-native metadata preserved without coordinate or rights approval."""

    source_row_number: int
    country_native: str
    site_name: str
    site_id_native: str
    record_id_native: str
    sample_count_claim: int | None
    site_label: str
    observation_workbook_claim: str | None
    latitude_dms_claim: str | None
    latitude_decimal_claim: Decimal | None
    longitude_dms_claim: str | None
    longitude_decimal_claim: Decimal | None
    elevation_m_claim: Decimal | None
    site_area_ha_claim: Decimal | None
    site_radius_m_claim: Decimal | None
    date_count_claim: str | None
    basin_type_claim: str | None
    source_values: tuple[tuple[str, str | None], ...]
    unsupported_values: tuple[tuple[str, str], ...]
    source_archive_sha256: str = ARCHIVE_SHA256
    source_member: str = METADATA_MEMBER
    source_member_sha256: str = METADATA_SHA256
    country_code_claim: str = "SE"
    coordinate_status: str = "unadmitted_conflicting_claims"
    chronology_status: str = "not_present_in_metadata"
    taxonomy_status: str = "not_present_in_metadata"
    rights_status: str = "per_sequence_unresolved"
    public_release_allowed: bool = False
    propagation_use_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible evidence while retaining source-native text."""
        return {
            "basin_type_claim": self.basin_type_claim,
            "chronology_status": self.chronology_status,
            "coordinate_status": self.coordinate_status,
            "country_code_claim": self.country_code_claim,
            "country_native": self.country_native,
            "date_count_claim": self.date_count_claim,
            "elevation_m_claim": _decimal_text(self.elevation_m_claim),
            "latitude_decimal_claim": _decimal_text(self.latitude_decimal_claim),
            "latitude_dms_claim": self.latitude_dms_claim,
            "longitude_decimal_claim": _decimal_text(self.longitude_decimal_claim),
            "longitude_dms_claim": self.longitude_dms_claim,
            "observation_workbook_claim": self.observation_workbook_claim,
            "propagation_use_allowed": self.propagation_use_allowed,
            "public_release_allowed": self.public_release_allowed,
            "record_id_native": self.record_id_native,
            "rights_status": self.rights_status,
            "sample_count_claim": self.sample_count_claim,
            "site_area_ha_claim": _decimal_text(self.site_area_ha_claim),
            "site_id_native": self.site_id_native,
            "site_label": self.site_label,
            "site_name": self.site_name,
            "site_radius_m_claim": _decimal_text(self.site_radius_m_claim),
            "source_row_number": self.source_row_number,
            "source_archive_sha256": self.source_archive_sha256,
            "source_member": self.source_member,
            "source_member_sha256": self.source_member_sha256,
            "source_values": dict(self.source_values),
            "taxonomy_status": self.taxonomy_status,
            "unsupported_values": dict(self.unsupported_values),
        }


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


@dataclass(frozen=True)
class RootsiIntakePosture:
    """Fail-closed decision surface for the quarantined archive."""

    lifecycle_state: str
    source_identity_status: str
    candidate_dataset_doi: str
    candidate_dataset_license: str
    candidate_license_applies_to_archive: bool
    licence_id: None
    public_release_allowed: bool
    propagation_use_allowed: bool
    approved_uses: tuple[str, ...]
    blockers: tuple[str, ...]
