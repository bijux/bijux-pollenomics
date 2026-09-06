"""Conservative ROOTSI metadata normalization and observation refusal."""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import NoReturn

from ..quarantine import ArchiveIdentity, IntakeRefusal, sha256_stream
from .authority import (
    ARCHIVE_SHA256,
    ARCHIVE_SIZE_BYTES,
    CANDIDATE_DATASET_DOI,
    CANDIDATE_DATASET_LICENSE,
    METADATA_HEADERS,
    METADATA_MEMBER,
    METADATA_SHA256,
    METADATA_SITE_COUNT,
    METADATA_SIZE_BYTES,
)
from .models import RootsiIntakePosture, RootsiSiteMetadataClaim
from .ooxml import read_first_worksheet

_COLUMNS = tuple(chr(ord("A") + index) for index in range(len(METADATA_HEADERS)))


def identify_rootsi_archive(path: Path) -> ArchiveIdentity:
    """Validate receipt bytes without claiming that 7z members were admitted."""
    with path.open("rb") as stream:
        size_bytes = os.fstat(stream.fileno()).st_size
        digest = sha256_stream(stream)
    if digest != ARCHIVE_SHA256:
        raise IntakeRefusal(
            "archive_digest_mismatch", f"expected {ARCHIVE_SHA256}, got {digest}"
        )
    if size_bytes != ARCHIVE_SIZE_BYTES:
        raise IntakeRefusal("archive_size_mismatch", str(size_bytes))
    return ArchiveIdentity(path.name, size_bytes, digest, "application/x-7z-compressed")


def _optional(value: str | None) -> str | None:
    if value is None or not value.strip() or value.strip() == "-":
        return None
    return value


def _required(value: str | None, *, field: str, row: int) -> str:
    result = _optional(value)
    if result is None:
        raise IntakeRefusal("missing_rootsi_metadata", f"row {row} {field}")
    return result


def _optional_decimal(value: str | None, *, field: str, row: int) -> Decimal | None:
    text = _optional(value)
    if text is None:
        return None
    try:
        result = Decimal(text)
    except InvalidOperation as exc:
        raise IntakeRefusal("invalid_rootsi_decimal", f"row {row} {field}") from exc
    if not result.is_finite():
        raise IntakeRefusal("invalid_rootsi_decimal", f"row {row} {field}")
    return result


def _sample_count(value: str | None, *, row: int) -> int | None:
    number = _optional_decimal(value, field="nr_samples", row=row)
    if number is None:
        return None
    if number != number.to_integral_value() or number < 0:
        raise IntakeRefusal("invalid_rootsi_sample_count", f"row {row}")
    return int(number)


def _headers(row: dict[str, str | None]) -> None:
    actual = tuple(row.get(column) for column in _COLUMNS)
    if actual != METADATA_HEADERS:
        raise IntakeRefusal("rootsi_metadata_header_mismatch", repr(actual))


def _normalize_row(
    row: dict[str, str | None], *, row_number: int
) -> RootsiSiteMetadataClaim:
    country = _required(row.get("A"), field="Country", row=row_number)
    if country != "SWE":
        raise IntakeRefusal(
            "unsupported_rootsi_country", f"row {row_number}: {country}"
        )
    source_values = tuple(
        (header, row.get(column))
        for column, header in zip(_COLUMNS, METADATA_HEADERS, strict=True)
    )
    unsupported = tuple(
        (column, value)
        for column, value in sorted(row.items())
        if column not in _COLUMNS and value is not None and value.strip()
    )
    return RootsiSiteMetadataClaim(
        source_row_number=row_number,
        country_native=country,
        site_name=_required(row.get("B"), field="Site name", row=row_number),
        site_id_native=_required(row.get("C"), field="site_ID", row=row_number),
        record_id_native=_required(row.get("D"), field="R_ID", row=row_number),
        sample_count_claim=_sample_count(row.get("E"), row=row_number),
        site_label=_required(row.get("F"), field="Site label", row=row_number),
        observation_workbook_claim=_optional(row.get("G")),
        latitude_dms_claim=_optional(row.get("H")),
        latitude_decimal_claim=_optional_decimal(
            row.get("I"), field="LatDD", row=row_number
        ),
        longitude_dms_claim=_optional(row.get("J")),
        longitude_decimal_claim=_optional_decimal(
            row.get("K"), field="LongDD", row=row_number
        ),
        elevation_m_claim=_optional_decimal(
            row.get("L"), field="Elevation", row=row_number
        ),
        site_area_ha_claim=_optional_decimal(
            row.get("M"), field="Site area", row=row_number
        ),
        site_radius_m_claim=_optional_decimal(
            row.get("N"), field="Site radius", row=row_number
        ),
        date_count_claim=_optional(row.get("O")),
        basin_type_claim=_optional(row.get("P")),
        source_values=source_values,
        unsupported_values=unsupported,
        source_archive_sha256=ARCHIVE_SHA256,
        source_member=METADATA_MEMBER,
        source_member_sha256=METADATA_SHA256,
    )


def normalize_rootsi_site_metadata(path: Path) -> tuple[RootsiSiteMetadataClaim, ...]:
    """Normalize only the exact metadata member, retaining unadmitted claims."""
    with path.open("rb") as stream:
        digest = sha256_stream(stream)
        if digest != METADATA_SHA256:
            raise IntakeRefusal(
                "rootsi_metadata_digest_mismatch",
                f"expected {METADATA_SHA256}, got {digest}",
            )
        if os.fstat(stream.fileno()).st_size != METADATA_SIZE_BYTES:
            raise IntakeRefusal("rootsi_metadata_size_mismatch", str(path))
        rows = read_first_worksheet(stream)
        if sha256_stream(stream) != digest:
            raise IntakeRefusal("rootsi_metadata_changed_during_read", str(path))
    if not rows:
        raise IntakeRefusal("rootsi_metadata_empty", str(path))
    _headers(rows[0])
    claims = tuple(
        _normalize_row(row, row_number=index)
        for index, row in enumerate(rows[1:], start=2)
    )
    if len(claims) != METADATA_SITE_COUNT:
        raise IntakeRefusal("rootsi_metadata_site_count_mismatch", str(len(claims)))
    _require_unique_ids(claims)
    return claims


def _require_unique_ids(claims: tuple[RootsiSiteMetadataClaim, ...]) -> None:
    site_ids = [claim.site_id_native for claim in claims]
    if len(set(site_ids)) != len(site_ids):
        raise IntakeRefusal("duplicate_rootsi_site_id", "site_ID values repeat")
    record_ids = [claim.record_id_native for claim in claims]
    if len(set(record_ids)) != len(record_ids):
        raise IntakeRefusal("duplicate_rootsi_record_id", "R_ID values repeat")


def refuse_rootsi_observations() -> NoReturn:
    """Prevent XLS observation values from entering products before admission."""
    raise IntakeRefusal(
        "rootsi_observations_not_admitted",
        "rights, coordinates, chronology, taxonomy, units, denominators, and lineage require review",
    )


def rootsi_intake_posture() -> RootsiIntakePosture:
    """Return the strongest truthful use decision supported by offline evidence."""
    return RootsiIntakePosture(
        lifecycle_state="quarantined",
        source_identity_status="candidate",
        candidate_dataset_doi=CANDIDATE_DATASET_DOI,
        candidate_dataset_license=CANDIDATE_DATASET_LICENSE,
        candidate_license_applies_to_archive=False,
        licence_id=None,
        public_release_allowed=False,
        propagation_use_allowed=False,
        approved_uses=("quarantined_read_only_review", "synthetic_fixture_development"),
        blockers=(
            "source_identity_unresolved",
            "per_sequence_rights_unresolved",
            "coordinate_claim_conflict",
            "time_basis_mixed",
            "classification_unreviewed",
            "unit_denominator_unresolved",
            "four_country_observations_incomplete",
        ),
    )
