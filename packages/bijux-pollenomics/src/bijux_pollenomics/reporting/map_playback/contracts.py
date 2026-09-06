"""Immutable scientific contracts for deterministic atlas playback."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal


class PlaybackContractError(ValueError):
    """Report an input that cannot be represented without changing its meaning."""


EvidenceRole = Literal["observation_chronology", "modeled_context"]
SelectorKind = Literal[
    "source_sample_presence",
    "source_ecological_code",
    "source_taxon",
    "modeled_metric",
]
PLAYBACK_COUNTRY_VOCABULARY = frozenset({"Denmark", "Finland", "Norway", "Sweden"})


def validate_playback_countries(countries: tuple[str, ...]) -> None:
    """Require an explicit, canonical country selection for every capture frame."""
    if (
        not isinstance(countries, tuple)
        or not countries
        or any(
            not isinstance(country, str)
            or not country.strip()
            or country != country.strip()
            for country in countries
        )
        or len(countries) != len(set(countries))
        or countries != tuple(sorted(countries))
        or not set(countries) <= PLAYBACK_COUNTRY_VOCABULARY
    ):
        raise PlaybackContractError(
            "playback countries must be a non-empty, unique, canonical tuple"
        )


def _finite_nonnegative_number(value: float, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise PlaybackContractError(f"{field} must be a finite non-negative number")
    if not math.isfinite(float(value)) or value < 0:
        raise PlaybackContractError(f"{field} must be a finite non-negative number")


@dataclass(frozen=True, slots=True)
class PlaybackFrame:
    """One closed BP interval shown without interpolation or inferred movement."""

    ordinal: int
    younger_bp: float | int
    older_bp: float | int
    label: str
    source_window_label: str | None = None
    feature_count: int | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.ordinal, bool)
            or not isinstance(self.ordinal, int)
            or self.ordinal < 0
        ):
            raise PlaybackContractError("frame ordinal must be a non-negative integer")
        _finite_nonnegative_number(self.younger_bp, field="younger_bp")
        _finite_nonnegative_number(self.older_bp, field="older_bp")
        if self.younger_bp > self.older_bp:
            raise PlaybackContractError(
                "frame interval must follow [younger_bp, older_bp] semantics"
            )
        if not isinstance(self.label, str) or not self.label.strip():
            raise PlaybackContractError("frame label must not be empty")
        if self.feature_count is not None and (
            isinstance(self.feature_count, bool)
            or not isinstance(self.feature_count, int)
            or self.feature_count < 0
        ):
            raise PlaybackContractError(
                "frame feature_count must be a non-negative integer or null"
            )

    def as_dict(self) -> dict[str, object]:
        """Return the stable browser-facing frame representation."""
        return {
            "ordinal": self.ordinal,
            "time_start_bp": self.younger_bp,
            "time_end_bp": self.older_bp,
            "label": self.label,
            "source_window_label": self.source_window_label,
            "feature_count": self.feature_count,
        }


@dataclass(frozen=True, slots=True)
class PlaybackStory:
    """A scientifically bounded oldest-to-present sequence for one selector."""

    story_id: str
    title: str
    dataset_id: str
    evidence_role: EvidenceRole
    selector_kind: SelectorKind
    selector_value: str
    frames: tuple[PlaybackFrame, ...]
    countries: tuple[str, ...]
    selector_family: str | None = None
    node_count: int | None = None
    observation_denominator: int | None = None
    interpolation_allowed: bool = False
    propagation_claim_allowed: bool = False
    edge_count: int = 0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.story_id, str)
            or not self.story_id.strip()
            or not isinstance(self.title, str)
            or not self.title.strip()
        ):
            raise PlaybackContractError("story identity and title must not be empty")
        if (
            not isinstance(self.dataset_id, str)
            or not self.dataset_id.strip()
            or not isinstance(self.selector_value, str)
            or not self.selector_value.strip()
        ):
            raise PlaybackContractError("story dataset and selector must not be empty")
        if self.evidence_role not in {"observation_chronology", "modeled_context"}:
            raise PlaybackContractError("story has an unsupported evidence role")
        if self.selector_kind not in {
            "source_sample_presence",
            "source_ecological_code",
            "source_taxon",
            "modeled_metric",
        }:
            raise PlaybackContractError("story has an unsupported selector kind")
        if not self.frames:
            raise PlaybackContractError(
                "a playback story must contain at least one frame"
            )
        validate_playback_countries(self.countries)
        if self.interpolation_allowed:
            raise PlaybackContractError(
                "playback interpolation is not scientifically allowed"
            )
        if self.propagation_claim_allowed or self.edge_count != 0:
            raise PlaybackContractError(
                "observation/context playback cannot contain propagation edges"
            )
        for field, value in (
            ("node_count", self.node_count),
            ("observation_denominator", self.observation_denominator),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                raise PlaybackContractError(f"story {field} must be positive or null")
        if tuple(frame.ordinal for frame in self.frames) != tuple(
            range(len(self.frames))
        ):
            raise PlaybackContractError("frame ordinals must be contiguous from zero")
        for older, newer in zip(self.frames, self.frames[1:], strict=False):
            if newer.older_bp > older.older_bp:
                raise PlaybackContractError(
                    "playback frames must be ordered from oldest to present"
                )

    def as_dict(self) -> dict[str, object]:
        """Return the stable browser-facing story representation."""
        return {
            "story_id": self.story_id,
            "title": self.title,
            "dataset_id": self.dataset_id,
            "evidence_role": self.evidence_role,
            "countries": list(self.countries),
            "selector": {
                "kind": self.selector_kind,
                "value": self.selector_value,
                "family": self.selector_family,
            },
            "temporal_direction": "oldest_to_present",
            "interval_semantics": "[younger_bp, older_bp]",
            "interpolation_allowed": self.interpolation_allowed,
            "propagation_claim_allowed": self.propagation_claim_allowed,
            "edge_count": self.edge_count,
            "node_count": self.node_count,
            "observation_denominator": self.observation_denominator,
            "frame_count": len(self.frames),
            "frames": [self._capture_frame(frame) for frame in self.frames],
        }

    def _capture_frame(self, frame: PlaybackFrame) -> dict[str, object]:
        serialized = frame.as_dict()
        serialized["basemap"] = "none"
        serialized["countries"] = list(self.countries)
        if self.evidence_role == "observation_chronology":
            serialized.update(
                {
                    "story_kind": "source_chronology",
                    "source_level": self.selector_kind,
                }
            )
            if self.selector_kind == "source_ecological_code":
                serialized["source_code"] = self.selector_value
            elif self.selector_kind == "source_taxon":
                serialized["source_taxon"] = self.selector_value
        else:
            serialized.update(
                {
                    "story_kind": "modeled_context",
                    "metric_key": self.selector_value,
                }
            )
            if self.selector_family is not None:
                serialized["metric_family_key"] = self.selector_family
        return serialized


@dataclass(frozen=True, slots=True)
class ExactTaxonDiscovery:
    """One exact Neotoma source identity available for user-selected playback."""

    feature_key: str
    source_taxon_id: str
    label: str
    node_count: int
    observation_denominator: int
    younger_bp: float | int
    older_bp: float | int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.feature_key, str)
            or not self.feature_key.strip()
            or not isinstance(self.source_taxon_id, str)
            or not self.source_taxon_id.strip()
        ):
            raise PlaybackContractError("exact taxon source identity must not be empty")
        if not isinstance(self.label, str) or not self.label.strip():
            raise PlaybackContractError("exact taxon label must not be empty")
        if (
            isinstance(self.node_count, bool)
            or not isinstance(self.node_count, int)
            or self.node_count <= 0
        ):
            raise PlaybackContractError("exact taxon node_count must be positive")
        if (
            isinstance(self.observation_denominator, bool)
            or not isinstance(self.observation_denominator, int)
            or self.observation_denominator <= 0
        ):
            raise PlaybackContractError(
                "exact taxon observation_denominator must be positive"
            )
        _finite_nonnegative_number(self.younger_bp, field="younger_bp")
        _finite_nonnegative_number(self.older_bp, field="older_bp")
        if self.younger_bp > self.older_bp:
            raise PlaybackContractError(
                "exact taxon interval must follow [younger_bp, older_bp] semantics"
            )

    def as_dict(self) -> dict[str, object]:
        """Return a selector record without manufacturing a bulk media story."""
        return {
            "feature_key": self.feature_key,
            "source_taxon_id": self.source_taxon_id,
            "label": self.label,
            "node_count": self.node_count,
            "observation_denominator": self.observation_denominator,
            "time_start_bp": self.younger_bp,
            "time_end_bp": self.older_bp,
            "story_materialization": "user_selected_only",
            "story_kind": "source_chronology",
            "source_level": "source_taxon",
            "source_taxon": self.feature_key,
        }


@dataclass(frozen=True, slots=True)
class PlaybackRefusal:
    """A terminal refusal that cannot be mistaken for an empty successful story."""

    product_key: str
    reason_code: str
    detail: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.product_key, str)
            or not self.product_key.strip()
            or not isinstance(self.reason_code, str)
            or not self.reason_code.strip()
        ):
            raise PlaybackContractError("refusal identity and reason must not be empty")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise PlaybackContractError("refusal detail must not be empty")

    def as_dict(self) -> dict[str, object]:
        """Return the fail-closed publication posture."""
        return {
            "product_key": self.product_key,
            "status": "refused",
            "reason_code": self.reason_code,
            "detail": self.detail,
            "story_count": 0,
            "edge_count": 0,
        }


__all__ = [
    "PLAYBACK_COUNTRY_VOCABULARY",
    "ExactTaxonDiscovery",
    "PlaybackContractError",
    "PlaybackFrame",
    "PlaybackRefusal",
    "PlaybackStory",
    "SelectorKind",
    "validate_playback_countries",
]
