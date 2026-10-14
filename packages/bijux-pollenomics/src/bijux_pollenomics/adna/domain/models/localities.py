"""Species-aware locality summaries derived from aDNA samples."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from .chronology import AdnaChronology, AdnaCoordinate
from .identity import AdnaLocalityIdentity


@dataclass(frozen=True)
class AdnaSampleChronologySupport:
    """Exact sample-owned chronology retained alongside a display coverage hull."""

    sample_id: str
    chronology: AdnaChronology
    source_release: str = ""
    provenance_path: str = ""
    provenance_locator: str = ""
    provenance_excerpt: str = ""
    provenance_kind: str = ""
    chronology_strength: str = ""
    normalization_status: str = ""
    conflict_note: str = ""
    reference_epoch: str = "not_separately_declared"
    age_type: str = "not_separately_declared"
    calibration_status: str = "not_separately_declared"
    model: str = "not_separately_declared"

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> AdnaSampleChronologySupport:
        """Read an exact owned support; malformed metadata is never a hull fallback."""
        if payload.get("schema_version") != "adna-sample-chronology-support.v1":
            raise ValueError("Unsupported sample chronology support schema")
        chronology = payload.get("chronology")
        if not isinstance(chronology, Mapping):
            raise TypeError("Sample chronology support requires chronology metadata")

        chronology = cast(Mapping[str, object], chronology)

        def text(source: Mapping[str, object], key: str, default: str = "") -> str:
            value = source.get(key, default)
            if not isinstance(value, str):
                raise TypeError(f"Sample chronology {key} must be text")
            return value

        def endpoint(key: str) -> int | None:
            value = chronology.get(key)
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"Sample chronology {key} must be integer BP or null")
            return value

        return cls(
            sample_id=text(payload, "sample_id"),
            chronology=AdnaChronology(
                original_text=text(chronology, "original_text"),
                time_start_bp=endpoint("time_start_bp"),
                time_end_bp=endpoint("time_end_bp"),
                time_mean_bp=endpoint("time_mean_bp"),
                date_stddev_bp=text(chronology, "date_stddev_bp"),
                source_mean_bp_text=text(chronology, "source_mean_bp_text"),
                dating_basis=text(chronology, "dating_basis", "unknown"),
                evidence_class=text(chronology, "evidence_class", "unresolved"),
                precision_posture=text(chronology, "precision_posture", "unresolved"),
                refusal_reason_code=text(chronology, "refusal_reason_code"),
            ),
            source_release=text(payload, "source_release"),
            provenance_path=text(payload, "provenance_path"),
            provenance_locator=text(payload, "provenance_locator"),
            provenance_excerpt=text(payload, "provenance_excerpt"),
            provenance_kind=text(payload, "provenance_kind"),
            chronology_strength=text(payload, "chronology_strength"),
            normalization_status=text(payload, "normalization_status"),
            conflict_note=text(payload, "conflict_note"),
            reference_epoch=text(payload, "reference_epoch", "not_separately_declared"),
            age_type=text(payload, "age_type", "not_separately_declared"),
            calibration_status=text(
                payload, "calibration_status", "not_separately_declared"
            ),
            model=text(payload, "model", "not_separately_declared"),
        )

    @classmethod
    def from_sample_payload(
        cls, payload: Mapping[str, object]
    ) -> AdnaSampleChronologySupport:
        """Join the explicit original sample identity and chronology, never its site hull."""
        fields: dict[str, object] = {
            "schema_version": "adna-sample-chronology-support.v1",
            "sample_id": payload.get("master_id", ""),
            "chronology": payload.get("chronology"),
            "source_release": payload.get("source_release", ""),
            "provenance_path": payload.get("chronology_provenance_path", ""),
            "provenance_locator": payload.get("chronology_provenance_locator", ""),
            "provenance_excerpt": payload.get("chronology_provenance_text", ""),
            "provenance_kind": payload.get("chronology_provenance_kind", ""),
            "chronology_strength": payload.get("chronology_strength", ""),
            "normalization_status": payload.get("chronology_normalization_status", ""),
            "conflict_note": payload.get("chronology_conflict_note", ""),
        }
        for key in ("reference_epoch", "age_type", "calibration_status", "model"):
            if key in payload:
                fields[key] = payload[key]
        return cls.from_dict(fields)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "adna-sample-chronology-support.v1",
            "sample_id": self.sample_id,
            "chronology": self.chronology.as_dict(),
            "source_release": self.source_release,
            "provenance_path": self.provenance_path,
            "provenance_locator": self.provenance_locator,
            "provenance_excerpt": self.provenance_excerpt,
            "provenance_kind": self.provenance_kind,
            "chronology_strength": self.chronology_strength,
            "normalization_status": self.normalization_status,
            "conflict_note": self.conflict_note,
            "reference_epoch": self.reference_epoch,
            "age_type": self.age_type,
            "calibration_status": self.calibration_status,
            "model": self.model,
        }


@dataclass(frozen=True)
class AdnaLocalitySummary:
    """Species-aware locality summary derived from normalized ancient-DNA samples."""

    identity: AdnaLocalityIdentity
    species_latin_name: str
    species_common_name: str
    source_family: str
    source_releases: tuple[str, ...]
    record_modalities: tuple[str, ...]
    review_strengths: tuple[str, ...]
    provenance_qualities: tuple[str, ...]
    locality: str | None
    coordinates: AdnaCoordinate
    sample_count: int
    sample_ids: tuple[str, ...]
    datasets: tuple[str, ...]
    chronology: AdnaChronology
    sample_namespace: str
    project_accessions: tuple[str, ...] = ()
    original_location_text: str = ""
    nordic_inclusion: bool = False
    nordic_inclusion_reason: str = ""
    interpretation_note: str = ""
    sample_chronologies: tuple[AdnaSampleChronologySupport, ...] = ()

    @property
    def latitude(self) -> float | None:
        return self.coordinates.latitude

    @property
    def longitude(self) -> float | None:
        return self.coordinates.longitude

    @property
    def latitude_text(self) -> str:
        return self.coordinates.latitude_text

    @property
    def longitude_text(self) -> str:
        return self.coordinates.longitude_text

    @property
    def coordinate_confidence(self) -> str:
        return self.coordinates.confidence

    @property
    def locality_namespace(self) -> str:
        return self.identity.namespace

    @property
    def locality_token(self) -> str:
        return self.identity.stable_token

    @property
    def time_start_bp(self) -> int | None:
        return self.chronology.time_start_bp

    @property
    def time_end_bp(self) -> int | None:
        return self.chronology.time_end_bp

    @property
    def time_mean_bp(self) -> int | None:
        return self.chronology.time_mean_bp

    @property
    def time_label(self) -> str:
        return self.chronology.original_text

    @property
    def dating_basis(self) -> str:
        return self.chronology.dating_basis

    def as_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity.as_dict(),
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "source_family": self.source_family,
            "source_releases": list(self.source_releases),
            "record_modalities": list(self.record_modalities),
            "review_strengths": list(self.review_strengths),
            "provenance_qualities": list(self.provenance_qualities),
            "locality": self.locality,
            "coordinates": self.coordinates.as_dict(),
            "sample_count": self.sample_count,
            "sample_ids": list(self.sample_ids),
            "datasets": list(self.datasets),
            "chronology": self.chronology.as_dict(),
            "chronology_role": "locality_sample_coverage_hull",
            "sample_chronologies": [row.as_dict() for row in self.sample_chronologies],
            "sample_namespace": self.sample_namespace,
            "project_accessions": list(self.project_accessions),
            "original_location_text": self.original_location_text,
            "nordic_inclusion": self.nordic_inclusion,
            "nordic_inclusion_reason": self.nordic_inclusion_reason,
            "interpretation_note": self.interpretation_note,
        }
