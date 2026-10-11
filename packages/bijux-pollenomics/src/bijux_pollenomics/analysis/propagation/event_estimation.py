"""First observed sample events under explicit native measurement profiles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from math import isfinite

from bijux_pollenomics.core.temporal_semantics import canonical_bp_interval

from .network import PhenomenonEvent

_PROFILE_KINDS = {
    "reported_positive_v1": {
        "count",
        "percentage",
        "concentration",
        "influx",
        "presence",
    },
    "count_ge_3_v1": {"count"},
    "percentage_ge_1_v1": {"percentage"},
    "two_consecutive_positive_v1": {
        "count",
        "percentage",
        "concentration",
        "influx",
        "presence",
    },
}


@dataclass(frozen=True)
class GovernedSample:
    """Native value and sample chronology in one explicitly ordered collection."""

    observation_id: str
    source_record_id: str
    source_family: str
    source_snapshot_id: str
    feature_key: str
    site_id: str
    collection_unit_id: str
    sequence_position: int
    value: float
    measure_kind: str
    source_unit: str
    measurement_semantics_id: str
    chronology_claim_id: str
    comparability_status: str
    younger_bp: float | None
    older_bp: float | None
    subject_granularity: str = "sample"
    percentage_denominator: float | None = None
    source_age_value: float | None = None
    source_age_unit: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "observation_id",
            "source_record_id",
            "source_family",
            "source_snapshot_id",
            "feature_key",
            "site_id",
            "collection_unit_id",
            "measurement_semantics_id",
            "chronology_claim_id",
            "source_unit",
        ):
            if (
                not isinstance(getattr(self, name), str)
                or not getattr(self, name).strip()
            ):
                raise ValueError(f"{name} must be nonempty")
        if isinstance(self.sequence_position, bool) or not isinstance(
            self.sequence_position, int
        ):
            raise ValueError("sequence_position must be an integer")
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not isfinite(self.value)
            or self.value < 0
        ):
            raise ValueError("native value must be finite and nonnegative")
        if self.measure_kind == "count" and self.value != int(self.value):
            raise ValueError("count must be integral")
        if self.measure_kind == "percentage" and self.value > 100:
            raise ValueError("percentage must not exceed 100")
        if self.measure_kind == "presence" and self.value not in (0, 1):
            raise ValueError("presence must be zero or one")
        if self.percentage_denominator is not None and (
            isinstance(self.percentage_denominator, bool)
            or not isinstance(self.percentage_denominator, (int, float))
            or not isfinite(self.percentage_denominator)
            or self.percentage_denominator <= 0
        ):
            raise ValueError("percentage denominator must be finite and positive")
        interval = canonical_bp_interval(self.younger_bp, self.older_bp)
        if self.comparability_status not in {
            "comparable",
            "unresolved",
            "context_only",
        }:
            raise ValueError("unsupported chronology comparability status")
        if (self.comparability_status == "comparable") != (interval is not None):
            raise ValueError(
                "canonical interval must agree with chronology comparability"
            )
        if self.source_age_value is not None and (
            isinstance(self.source_age_value, bool)
            or not isinstance(self.source_age_value, (int, float))
            or not isfinite(self.source_age_value)
            or not isinstance(self.source_age_unit, str)
            or not self.source_age_unit.strip()
        ):
            raise ValueError(
                "native source age requires finite value and explicit unit"
            )


@dataclass(frozen=True)
class EventEstimationResult:
    """One event or explicit refusal, with the complete attempted sample universe."""

    event: PhenomenonEvent | None
    reason_code: str
    threshold_profile_id: str
    input_sample_count: int
    ordered_observation_ids: tuple[str, ...]
    supporting_observation_ids: tuple[str, ...]
    input_sha256: str
    label: str = "first observed in governed data"
    establishes_continuous_presence: bool = False
    establishes_global_first: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_first_observed(
    samples: Sequence[GovernedSample],
    *,
    event_template: PhenomenonEvent,
    threshold_profile_id: str = "reported_positive_v1",
) -> EventEstimationResult:
    """Select the oldest qualifying sample, without interpolation or true ages.

    The template supplies source, feature, method and location identity only.
    Every sample must belong to its site and one collection/measurement sequence.
    The source's explicit positions must have definite canonical older-to-younger
    ordering. Missing ages and uncertain order refuse the entire sequence rather
    than hiding potentially earlier detections. Persistence means adjacent
    governed samples, and does not establish presence between samples.
    """
    if threshold_profile_id not in _PROFILE_KINDS:
        raise ValueError("unsupported threshold profile")
    ordered = tuple(
        sorted(samples, key=lambda row: (row.sequence_position, row.observation_id))
    )
    payload = {
        "samples": [asdict(row) for row in ordered],
        "template": event_template.as_dict(),
        "threshold_profile_id": threshold_profile_id,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()

    def result(
        reason: str, event: PhenomenonEvent | None = None, support: tuple[str, ...] = ()
    ) -> EventEstimationResult:
        return EventEstimationResult(
            event,
            reason,
            threshold_profile_id,
            len(ordered),
            tuple(row.observation_id for row in ordered),
            support,
            digest,
        )

    if not ordered:
        return result("empty_sample_sequence")
    for field, reason in (
        ("feature_key", "incompatible_sample_feature"),
        ("source_family", "incompatible_sample_source_family"),
        ("source_snapshot_id", "incompatible_sample_source_snapshot"),
    ):
        if any(
            getattr(row, field) != getattr(event_template, field) for row in ordered
        ):
            return result(reason)
    if any(
        row.subject_granularity not in {"sample", "physical_sample", "analysis_entity"}
        for row in ordered
    ):
        return result("sample_level_sequence_required")
    if (
        any(row.site_id != event_template.site_id for row in ordered)
        or len({row.collection_unit_id for row in ordered}) != 1
    ):
        return result("incompatible_sample_sequence")
    if (
        len({row.observation_id for row in ordered}) != len(ordered)
        or len({row.source_record_id for row in ordered}) != len(ordered)
        or len({row.sequence_position for row in ordered}) != len(ordered)
    ):
        return result("ambiguous_sample_order")
    if threshold_profile_id == "two_consecutive_positive_v1" and any(
        younger.sequence_position != older.sequence_position + 1
        for older, younger in zip(ordered, ordered[1:], strict=False)
    ):
        return result("nonadjacent_sample_sequence")
    if len(
        {
            (row.measure_kind, row.source_unit, row.measurement_semantics_id)
            for row in ordered
        }
    ) != 1 or any(
        row.measurement_semantics_id != event_template.measurement_semantics_id
        for row in ordered
    ):
        return result("incompatible_measurement_semantics")
    if any(
        row.measure_kind not in _PROFILE_KINDS[threshold_profile_id] for row in ordered
    ):
        return result("incompatible_threshold_measure")
    if any(
        row.measure_kind == "percentage" and row.percentage_denominator is None
        for row in ordered
    ):
        return result("percentage_denominator_unknown")
    if any(row.comparability_status != "comparable" for row in ordered):
        return result("chronology_unresolved")
    intervals = tuple(
        canonical_bp_interval(row.younger_bp, row.older_bp) for row in ordered
    )
    if any(interval is None for interval in intervals):
        return result("chronology_unresolved")
    for older, younger in zip(intervals, intervals[1:], strict=False):
        if (
            older is not None
            and younger is not None
            and older.younger_bp <= younger.older_bp
        ):
            return result("chronology_order_indeterminate")
    minimum = (
        3
        if threshold_profile_id == "count_ge_3_v1"
        else 1
        if threshold_profile_id == "percentage_ge_1_v1"
        else 0
    )
    positive = tuple(
        row.value >= minimum if minimum else row.value > 0 for row in ordered
    )
    selected = next(
        (
            index
            for index, passed in enumerate(positive)
            if passed
            and (
                threshold_profile_id != "two_consecutive_positive_v1"
                or (index + 1 < len(ordered) and positive[index + 1])
            )
        ),
        None,
    )
    if selected is None:
        return result(
            "insufficient_persistence"
            if threshold_profile_id == "two_consecutive_positive_v1" and any(positive)
            else "threshold_not_met"
        )
    sample = ordered[selected]
    support: tuple[str, ...] = (sample.observation_id,)
    if threshold_profile_id == "two_consecutive_positive_v1":
        support = (*support, ordered[selected + 1].observation_id)
    event = replace(
        event_template,
        event_id="",
        source_record_id=sample.source_record_id,
        observation_ids=support,
        event_type="derived_first_observed",
        chronology_claim_id=sample.chronology_claim_id,
        younger_bp=sample.younger_bp,
        older_bp=sample.older_bp,
        comparability_status="comparable",
        subject_granularity=sample.subject_granularity,
        threshold_profile_id=threshold_profile_id,
        input_digest=digest,
        config_digest=hashlib.sha256(
            json.dumps([threshold_profile_id, event_template.config_digest]).encode()
        ).hexdigest(),
        producer_version="first-observed-estimation.v1",
    )
    return result("first_observed_sample_selected", event, support)
