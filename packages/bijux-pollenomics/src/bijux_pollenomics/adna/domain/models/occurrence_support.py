"""Sample-owned chronology components and exact source metadata transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from .chronology import AdnaChronology


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
