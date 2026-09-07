"""Chronology parsing and locality interval aggregation."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import cast

from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
)

from ....core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
    normalize_bp_interval,
    parse_bp_window_label,
)
from ...projects.evidence.chronology import AdnaProjectSampleChronologyRow
from ...projects.registry.samples import AdnaCuratedSampleRow

_BP_MEAN_STDDEV_RE = re.compile(
    r"(?P<mean>\d{1,5})\s*(?:±|\+/-)\s*(?P<stddev>\d{1,4})\s*BP",
    re.IGNORECASE,
)


_BP_SINGLE_RE = re.compile(r"(?P<mean>\d{1,5})\s*BP", re.IGNORECASE)


_CENSORED_CHRONOLOGY_RE = re.compile(
    r"^\s*(?:<=|>=|<|>|≤|≥)\s*\d",
    re.IGNORECASE,
)


_BCE_RANGE_RE = re.compile(
    r"(?P<start>\d{1,5})\s*-\s*(?P<end>\d{1,5})\s*(?:cal\s*)?BCE",
    re.IGNORECASE,
)


_BCE_SINGLE_RE = re.compile(r"(?P<year>\d{1,5})\s*(?:cal\s*)?BCE", re.IGNORECASE)


_CE_RANGE_RE = re.compile(
    r"(?P<start>\d{1,4})\s*-\s*(?P<end>\d{1,4})\s*CE",
    re.IGNORECASE,
)


_CE_SINGLE_RE = re.compile(r"(?P<year>\d{1,4})\s*CE", re.IGNORECASE)


def normalize_chronology_text(
    value: str,
    *,
    dating_basis: str = "unknown",
) -> AdnaChronology:
    """Normalize common non-human chronology expressions without overclaiming precision."""
    text = value.strip()
    basis = dating_basis or "unknown"
    if not text:
        return AdnaChronology(
            original_text="",
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            dating_basis=basis,
        )
    if _CENSORED_CHRONOLOGY_RE.search(text):
        return AdnaChronology(
            original_text=text,
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            dating_basis=basis,
        )
    if bp_window := parse_bp_window_label(text):
        return AdnaChronology(
            original_text=text,
            time_start_bp=bp_window[0],
            time_end_bp=bp_window[1],
            time_mean_bp=midpoint_bp_year(bp_window[0], bp_window[1]),
            dating_basis=basis,
        )
    if bce_range := _BCE_RANGE_RE.search(text):
        older_bp = _bce_to_bp(int(bce_range.group("start")))
        younger_bp = _bce_to_bp(int(bce_range.group("end")))
        interval = normalize_bp_interval(older_bp, younger_bp)
        if interval is None:
            raise ValueError(f"BCE range could not be normalized: {text}")
        return AdnaChronology(
            original_text=text,
            time_start_bp=interval[0],
            time_end_bp=interval[1],
            time_mean_bp=midpoint_bp_year(interval[0], interval[1]),
            dating_basis=basis,
        )
    if ce_range := _CE_RANGE_RE.search(text):
        first_bp = _ce_to_bp(int(ce_range.group("start")))
        second_bp = _ce_to_bp(int(ce_range.group("end")))
        interval = normalize_bp_interval(first_bp, second_bp)
        if interval is None:
            raise ValueError(f"CE range could not be normalized: {text}")
        return AdnaChronology(
            original_text=text,
            time_start_bp=interval[0],
            time_end_bp=interval[1],
            time_mean_bp=midpoint_bp_year(interval[0], interval[1]),
            dating_basis=basis,
        )
    if bce_single := _BCE_SINGLE_RE.search(text):
        year_bp = _bce_to_bp(int(bce_single.group("year")))
        return AdnaChronology(
            original_text=text,
            time_start_bp=year_bp,
            time_end_bp=year_bp,
            time_mean_bp=year_bp,
            dating_basis=basis,
        )
    if ce_single := _CE_SINGLE_RE.search(text):
        year_bp = _ce_to_bp(int(ce_single.group("year")))
        return AdnaChronology(
            original_text=text,
            time_start_bp=year_bp,
            time_end_bp=year_bp,
            time_mean_bp=year_bp,
            dating_basis=basis,
        )
    if mean_match := _BP_MEAN_STDDEV_RE.search(text):
        mean_bp = int(mean_match.group("mean"))
        stddev_bp = mean_match.group("stddev")
        return AdnaChronology(
            original_text=text,
            time_start_bp=mean_bp,
            time_end_bp=mean_bp,
            time_mean_bp=mean_bp,
            date_stddev_bp=stddev_bp,
            dating_basis=basis,
        )
    if point_match := _BP_SINGLE_RE.search(text):
        mean_bp = int(point_match.group("mean"))
        return AdnaChronology(
            original_text=text,
            time_start_bp=mean_bp,
            time_end_bp=mean_bp,
            time_mean_bp=mean_bp,
            dating_basis=basis,
        )
    return AdnaChronology(
        original_text=text,
        time_start_bp=None,
        time_end_bp=None,
        time_mean_bp=None,
        dating_basis=basis,
    )


def normalize_explicit_bp_window(
    start_bp: int | None,
    end_bp: int | None,
    *,
    original_text: str = "",
    dating_basis: str = "bp_window",
) -> AdnaChronology:
    """Normalize an explicit structured BP interval while refusing inverted input."""
    if start_bp is None or end_bp is None:
        raise ValueError("Structured BP windows require both start and end values")
    if start_bp > end_bp:
        raise ValueError("Structured BP windows must be ordered younger-to-older")
    return AdnaChronology(
        original_text=original_text or build_bp_interval_label(start_bp, end_bp),
        time_start_bp=start_bp,
        time_end_bp=end_bp,
        time_mean_bp=midpoint_bp_year(start_bp, end_bp),
        dating_basis=dating_basis,
    )


def _aggregate_locality_chronology(
    *,
    sample_rows: tuple[AdnaCuratedSampleRow, ...],
    chronology_lookup: Mapping[str, AdnaProjectSampleChronologyRow],
    fallback_text: str,
    fallback_start_bp: int | None,
    fallback_end_bp: int | None,
    dating_basis: str,
) -> AdnaChronology:
    chronology_rows = [
        chronology_lookup[row.stable_sample_id]
        for row in sample_rows
        if row.stable_sample_id in chronology_lookup
    ]
    interval_rows = [
        row
        for row in chronology_rows
        if row.time_start_bp is not None and row.time_end_bp is not None
    ]
    censored_rows = [
        row
        for row in chronology_rows
        if _CENSORED_CHRONOLOGY_RE.search(row.chronology_text.strip())
    ]
    if interval_rows and censored_rows:
        source_claims = tuple(
            dict.fromkeys(
                row.chronology_text.strip()
                for row in chronology_rows
                if row.chronology_text.strip()
            )
        )
        chronology = AdnaChronology(
            original_text="; ".join(source_claims),
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            dating_basis=dating_basis,
        )
        return _apply_chronology_semantics(
            chronology,
            evidence_class="unresolved",
            precision_posture="sample_approximate_or_modeled",
        )
    if interval_rows:
        start_bp = min(cast(int, row.time_start_bp) for row in interval_rows)
        end_bp = max(cast(int, row.time_end_bp) for row in interval_rows)
        chronology = normalize_explicit_bp_window(
            start_bp,
            end_bp,
            original_text=_locality_chronology_label(start_bp, end_bp),
            dating_basis=dating_basis,
        )
        return _apply_chronology_semantics(
            chronology,
            evidence_class=_aggregate_locality_evidence_class(
                chronology_rows, chronology
            ),
            precision_posture=_aggregate_locality_precision_posture(
                chronology_rows, chronology
            ),
        )
    if fallback_start_bp is not None and fallback_end_bp is not None:
        chronology = normalize_explicit_bp_window(
            fallback_start_bp,
            fallback_end_bp,
            original_text=fallback_text,
            dating_basis=dating_basis,
        )
        return _apply_chronology_semantics(
            chronology,
            evidence_class=_fallback_chronology_evidence_class(
                chronology=chronology,
                dating_basis=dating_basis,
            ),
            precision_posture="contextual_interval",
        )
    chronology = normalize_chronology_text(fallback_text, dating_basis=dating_basis)
    return _apply_chronology_semantics(
        chronology,
        evidence_class=_fallback_chronology_evidence_class(
            chronology=chronology,
            dating_basis=dating_basis,
        ),
        precision_posture=_fallback_chronology_precision_posture(chronology),
    )


def _locality_chronology_label(start_bp: int, end_bp: int) -> str:
    if start_bp == end_bp:
        return f"{start_bp} BP"
    return f"{start_bp}-{end_bp} BP"


def _apply_chronology_semantics(
    chronology: AdnaChronology,
    *,
    evidence_class: str,
    precision_posture: str,
) -> AdnaChronology:
    return AdnaChronology(
        original_text=chronology.original_text,
        time_start_bp=chronology.time_start_bp,
        time_end_bp=chronology.time_end_bp,
        time_mean_bp=chronology.time_mean_bp,
        date_stddev_bp=chronology.date_stddev_bp,
        source_mean_bp_text=chronology.source_mean_bp_text,
        dating_basis=chronology.dating_basis,
        evidence_class=evidence_class,
        precision_posture=precision_posture,
        refusal_reason_code=chronology.refusal_reason_code,
    )


def _fallback_chronology_evidence_class(
    *,
    chronology: AdnaChronology,
    dating_basis: str | None,
) -> str:
    basis = (dating_basis or "").casefold()
    text = chronology.original_text.casefold()
    if not chronology.original_text and chronology.time_start_bp is None:
        return "unresolved"
    if any(
        token in text
        for token in ("bronze", "iron", "neolithic", "medieval", "viking", "period")
    ):
        return "broad_period_label"
    if basis in {
        "historical_attribution",
        "historical_and_archaeological_context",
        "modern_sampling",
    }:
        return "historical_or_recent_date"
    if basis in {"archaeological_period", "archaeological_period_assignment"}:
        return "archaeological_context_date"
    if any(
        token in text
        for token in ("bayesian", "modeled", "modelled", "calibrated", "2σ", "1σ")
    ):
        return "modeled_sample_date"
    if chronology.time_start_bp is not None:
        return "direct_radiocarbon_date"
    return "unresolved"


def _fallback_chronology_precision_posture(chronology: AdnaChronology) -> str:
    text = chronology.original_text.casefold()
    if chronology.time_start_bp is None or chronology.time_end_bp is None:
        if any(
            token in text
            for token in ("bronze", "iron", "neolithic", "medieval", "viking", "period")
        ):
            return "broad_period_only"
        return (
            "unresolved"
            if not chronology.original_text
            else "sample_approximate_or_modeled"
        )
    if any(
        token in text
        for token in (
            "ca.",
            "circa",
            "approx",
            "bayesian",
            "modeled",
            "modelled",
            "~",
            "calibrated",
            "2σ",
            "1σ",
        )
    ):
        return "sample_approximate_or_modeled"
    if chronology.time_start_bp == chronology.time_end_bp:
        return "sample_precise_point"
    return "sample_precise_interval"


def _aggregate_locality_evidence_class(
    chronology_rows: list[AdnaProjectSampleChronologyRow],
    chronology: AdnaChronology,
) -> str:
    classes = {
        str(getattr(row, "chronology_evidence_class", "")).strip()
        for row in chronology_rows
        if str(getattr(row, "chronology_evidence_class", "")).strip()
    }
    if "direct_radiocarbon_date" in classes:
        return "direct_radiocarbon_date"
    if "modeled_sample_date" in classes:
        return "modeled_sample_date"
    if "archaeological_context_date" in classes:
        return "archaeological_context_date"
    if "historical_or_recent_date" in classes:
        return "historical_or_recent_date"
    if "broad_period_label" in classes:
        return "broad_period_label"
    return _fallback_chronology_evidence_class(
        chronology=chronology,
        dating_basis=chronology.dating_basis,
    )


def _aggregate_locality_precision_posture(
    chronology_rows: list[AdnaProjectSampleChronologyRow],
    chronology: AdnaChronology,
) -> str:
    postures = {
        str(getattr(row, "chronology_precision_posture", "")).strip()
        for row in chronology_rows
        if str(getattr(row, "chronology_precision_posture", "")).strip()
    }
    if postures & {"sample_approximate_or_modeled"}:
        return "sample_approximate_or_modeled"
    if (
        postures <= {"sample_precise_point"}
        and postures
        and chronology.time_start_bp == chronology.time_end_bp
    ):
        return "sample_precise_point"
    if postures & {"sample_precise_interval", "sample_precise_point"}:
        return "sample_precise_interval"
    if "contextual_interval" in postures:
        return "contextual_interval"
    if "broad_period_only" in postures:
        return "broad_period_only"
    return _fallback_chronology_precision_posture(chronology)


def _bce_to_bp(year_bce: int) -> int:
    return year_bce + 1949


def _ce_to_bp(year_ce: int) -> int:
    return max(0, 1950 - year_ce)
