"""Coordinate and chronology value objects for aDNA records."""

from __future__ import annotations

from dataclasses import dataclass

from ....core.temporal_semantics import (
    InvalidBpIntervalError,
    build_temporal_semantics,
    canonical_bp_interval,
)


@dataclass(frozen=True)
class AdnaCoordinate:
    """Typed coordinate contract for ancient-DNA records."""

    latitude: float | None
    longitude: float | None
    latitude_text: str
    longitude_text: str
    confidence: str = "unknown"

    def as_dict(self) -> dict[str, object]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class AdnaChronology:
    """Typed chronology contract for ancient-DNA records."""

    original_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    date_stddev_bp: str = ""
    source_mean_bp_text: str = ""
    dating_basis: str = "unknown"
    evidence_class: str = "unresolved"
    precision_posture: str = "unresolved"
    refusal_reason_code: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "original_text": self.original_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "time_mean_bp": self.time_mean_bp,
            "date_stddev_bp": self.date_stddev_bp,
            "source_mean_bp_text": self.source_mean_bp_text,
            "dating_basis": self.dating_basis,
            "evidence_class": self.evidence_class,
            "precision_posture": self.precision_posture,
            "refusal_reason_code": self.refusal_reason_code,
        }

    def as_temporal_semantics(
        self,
        *,
        source_family: str,
        provenance_path: str = "",
        provenance_locator: str = "",
        provenance_excerpt: str = "",
        comparison_note: str = "",
    ) -> dict[str, object]:
        """Expose one shared temporal semantics payload for direct-evidence chronology."""
        numeric_postures = {
            "sample_precise_point",
            "sample_precise_interval",
        }
        caveated_numeric_postures = {
            "sample_approximate_or_modeled",
            "contextual_interval",
        }
        try:
            interval = canonical_bp_interval(self.time_start_bp, self.time_end_bp)
        except InvalidBpIntervalError:
            interval = None

        has_numeric_interval = interval is not None
        comparability_posture = "refused" if self.refusal_reason_code else "unresolved"
        if (
            not self.refusal_reason_code
            and has_numeric_interval
            and self.precision_posture in numeric_postures
        ):
            comparability_posture = "numeric_interval"
        elif (
            not self.refusal_reason_code
            and has_numeric_interval
            and self.precision_posture in caveated_numeric_postures
        ):
            comparability_posture = "numeric_interval_with_caveat"
        elif not self.refusal_reason_code and self.original_text.strip():
            comparability_posture = "contextual_label_only"

        time_start_bp = (
            self.time_start_bp if "numeric_interval" in comparability_posture else None
        )
        time_end_bp = (
            self.time_end_bp if "numeric_interval" in comparability_posture else None
        )
        time_mean_bp = (
            self.time_mean_bp
            if "numeric_interval" in comparability_posture
            and self.time_mean_bp is not None
            and self.time_start_bp is not None
            and self.time_end_bp is not None
            and self.time_start_bp <= self.time_mean_bp <= self.time_end_bp
            else None
        )
        resolved_note = comparison_note.strip()
        if not resolved_note:
            if comparability_posture == "numeric_interval":
                resolved_note = "This chronology supports interval-based comparison without implying more than the published sample interval."
            elif comparability_posture == "numeric_interval_with_caveat":
                resolved_note = "This chronology carries numeric values, but its evidence class or precision posture still requires caution."
            elif comparability_posture == "contextual_label_only":
                resolved_note = "This chronology is text-led or period-led and should not be compared as a sample-owned numeric date."
            else:
                resolved_note = "This chronology does not yet support trustworthy temporal comparison."
        return build_temporal_semantics(
            source_family=source_family,
            evidence_class=self.evidence_class,
            precision_posture=self.precision_posture,
            comparability_posture=comparability_posture,
            time_start_bp=time_start_bp,
            time_end_bp=time_end_bp,
            time_mean_bp=time_mean_bp,
            summary_label=self.original_text,
            comparison_note=resolved_note,
            refusal_reason_code=self.refusal_reason_code,
            provenance_path=provenance_path,
            provenance_locator=provenance_locator,
            provenance_excerpt=provenance_excerpt,
            original_labels=tuple(
                label
                for label in (
                    self.original_text,
                    f"Source mean BP: {self.source_mean_bp_text}"
                    if self.source_mean_bp_text
                    else "",
                )
                if label
            ),
            uncertainty_notes=(self.refusal_reason_code,)
            if self.refusal_reason_code
            else (),
        ).as_dict()
