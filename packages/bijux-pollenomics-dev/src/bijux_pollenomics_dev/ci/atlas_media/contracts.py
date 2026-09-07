"""Fail-closed contracts for deterministic atlas media materialization."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import cast

from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasCandidate

from .catalog import (
    CORE_SOURCE_STORIES,
    DEFAULT_EXACT_TAXA,
    DEFAULT_MODELED_METRICS,
    DEFAULT_SOURCE_LABEL_PRESETS,
    PUBLICATION_STORIES,
)

_SAFE_SLUG = re.compile(r"[a-z][a-z0-9-]*")


class AtlasMediaError(ValueError):
    """Report an input or runtime state that cannot produce governed media."""


SOURCE_CHRONOLOGY_INTERPRETATION = (
    "Dated source-observation chronology; site, node, and cluster counts are not "
    "abundance; not flow, propagation, migration, or causation."
)
SOURCE_PRESET_INTERPRETATION = (
    "Literal source-label union chronology; not classification or abundance; "
    "not flow, propagation, migration, or causation."
)
MODELED_CONTEXT_INTERPRETATION = (
    "Non-interpolated modeled context; not an observed pollen trajectory; "
    "not flow, propagation, migration, or causation."
)


def story_interpretation(evidence_role: str, selector_kind: str) -> str:
    """Return the single conservative interpretation for every media surface."""
    if selector_kind == "source_label_preset":
        return SOURCE_PRESET_INTERPRETATION
    if evidence_role == "observation_chronology":
        return SOURCE_CHRONOLOGY_INTERPRETATION
    return MODELED_CONTEXT_INTERPRETATION


def _safe_relative_file(value: str, *, suffix: str, label: str) -> None:
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix != suffix
        or any(part in {"", "."} for part in path.parts)
    ):
        raise AtlasMediaError(f"{label} must be a safe {suffix} repository path")


@dataclass(frozen=True, slots=True)
class StorySelection:
    """Explicit story selectors with scientifically conservative defaults."""

    include_core_source_stories: bool = True
    source_label_presets: tuple[str, ...] = DEFAULT_SOURCE_LABEL_PRESETS
    exact_taxa: tuple[str, ...] = DEFAULT_EXACT_TAXA
    modeled_metrics: tuple[str, ...] = DEFAULT_MODELED_METRICS

    def __post_init__(self) -> None:
        """Reject ambiguous, empty, or unbounded story selections."""
        if not isinstance(self.include_core_source_stories, bool):
            raise AtlasMediaError("include_core_source_stories must be boolean")
        for label, values in (
            ("source_label_presets", self.source_label_presets),
            ("exact_taxa", self.exact_taxa),
            ("modeled_metrics", self.modeled_metrics),
        ):
            if (
                not isinstance(values, tuple)
                or len(values) != len(set(values))
                or any(
                    not isinstance(value, str)
                    or not value.strip()
                    or value != value.strip()
                    for value in values
                )
            ):
                raise AtlasMediaError(f"{label} must contain unique non-empty strings")
            if len(values) > 8:
                raise AtlasMediaError(f"{label} selection exceeds eight stories")
        if (
            not self.include_core_source_stories
            and not self.source_label_presets
            and not self.exact_taxa
            and not self.modeled_metrics
        ):
            raise AtlasMediaError("at least one atlas media story must be selected")
        selected_count = (
            (len(CORE_SOURCE_STORIES) if self.include_core_source_stories else 0)
            + len(self.source_label_presets)
            + len(self.exact_taxa)
            + len(self.modeled_metrics)
        )
        if selected_count > len(PUBLICATION_STORIES):
            raise AtlasMediaError("atlas media selection exceeds publication catalog")


@dataclass(frozen=True, slots=True)
class AtlasMediaPlan:
    """Validated immutable inputs for one content-bound media build."""

    repository_root: Path
    artifact_root: Path
    browser_binary: Path
    node_binary: Path
    ffmpeg_binary: Path
    ffprobe_binary: Path
    atlas_document: str
    atlas_manifest: str
    storyboard_manifest: str
    candidate: AtlasCandidate
    selection: StorySelection = StorySelection()
    width: int = 1440
    height: int = 900
    frames_per_second: int = 12
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        """Reject unsafe paths, missing tools, and unbounded encodings."""
        repository_root = self.repository_root.resolve()
        artifact_root = self.artifact_root.resolve()
        if not repository_root.is_dir():
            raise AtlasMediaError("repository_root must be an existing directory")
        if (
            repository_root == artifact_root
            or repository_root not in artifact_root.parents
        ):
            raise AtlasMediaError("artifact_root must be inside the repository")
        if "artifacts" not in artifact_root.relative_to(repository_root).parts:
            raise AtlasMediaError("artifact_root must be under repository artifacts/")
        for label, binary in (
            ("browser_binary", self.browser_binary),
            ("node_binary", self.node_binary),
            ("ffmpeg_binary", self.ffmpeg_binary),
            ("ffprobe_binary", self.ffprobe_binary),
        ):
            if not binary.is_file():
                raise AtlasMediaError(f"{label} must be an existing file")
        _safe_relative_file(self.atlas_document, suffix=".html", label="atlas_document")
        _safe_relative_file(self.atlas_manifest, suffix=".json", label="atlas_manifest")
        _safe_relative_file(
            self.storyboard_manifest,
            suffix=".json",
            label="storyboard_manifest",
        )
        for path in (
            self.atlas_document,
            self.atlas_manifest,
            self.storyboard_manifest,
        ):
            candidate_path = repository_root / path
            if not candidate_path.is_file():
                raise AtlasMediaError(f"required media input is absent: {path}")
            resolved = candidate_path.resolve(strict=True)
            if repository_root not in resolved.parents:
                raise AtlasMediaError(
                    f"required media input escapes repository: {path}"
                )
        if Path(self.atlas_document).parent != Path(self.atlas_manifest).parent:
            raise AtlasMediaError("atlas document and manifest must share a directory")
        if self.width != 1440 or self.height != 900:
            raise AtlasMediaError(
                "media dimensions must use the canonical 1440x900 viewport"
            )
        if (
            isinstance(self.frames_per_second, bool)
            or not 1 <= self.frames_per_second <= 60
        ):
            raise AtlasMediaError("frames_per_second must be in [1, 60]")
        if (
            isinstance(self.timeout_seconds, bool)
            or not 10 <= self.timeout_seconds <= 300
        ):
            raise AtlasMediaError("timeout_seconds must be in [10, 300]")


@dataclass(frozen=True, slots=True)
class SelectedStory:
    """One governed story and its exact capture frames."""

    story_id: str
    title: str
    evidence_role: str
    selector_kind: str
    selector_value: str
    frames: tuple[dict[str, object], ...]
    selector_family: str | None = None
    site_count: int | None = None
    node_count: int | None = None
    observation_denominator: int | None = None
    frame_feature_denominators: tuple[int, ...] | None = None
    frame_no_pollen_data_counts: tuple[int, ...] | None = None
    expected_visible_feature_counts: tuple[int, ...] | None = None
    expected_visible_site_counts: tuple[int, ...] | None = None
    expected_visible_observation_counts: tuple[int, ...] | None = None
    source_authority_sha256: str | None = None
    source_preset_member_taxon_ids: tuple[int, ...] | None = None
    source_preset_catalog_sha256: str | None = None

    def __post_init__(self) -> None:
        """Reject stories that violate source and modeled-evidence contracts."""
        if _SAFE_SLUG.fullmatch(self.story_id) is None:
            raise AtlasMediaError("story_id must be a durable lowercase slug")
        if not self.title.strip():
            raise AtlasMediaError("story title must not be empty")
        if self.evidence_role not in {"observation_chronology", "modeled_context"}:
            raise AtlasMediaError("story evidence_role is unsupported")
        if not self.frames or len(self.frames) > 300:
            raise AtlasMediaError("story frame count must be in [1, 300]")
        if (
            not isinstance(self.selector_value, str)
            or not self.selector_value.strip()
            or self.selector_value != self.selector_value.strip()
        ):
            raise AtlasMediaError("story selector value must not be empty")
        if self.evidence_role == "observation_chronology":
            if self.selector_kind not in {
                "source_sample_presence",
                "source_ecological_code",
                "source_taxon",
                "source_label_preset",
            }:
                raise AtlasMediaError("source story selector kind is unsupported")
            if self.selector_kind == "source_label_preset":
                if self.selector_family != "literal_source_label_membership":
                    raise AtlasMediaError(
                        "source-label preset selector family differs"
                    )
                if (
                    not isinstance(self.source_preset_member_taxon_ids, tuple)
                    or not self.source_preset_member_taxon_ids
                    or len(self.source_preset_member_taxon_ids)
                    != len(set(self.source_preset_member_taxon_ids))
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, int)
                        or value <= 0
                        for value in self.source_preset_member_taxon_ids
                    )
                ):
                    raise AtlasMediaError(
                        "source-label preset member IDs are invalid"
                    )
                _sha256(
                    self.source_preset_catalog_sha256,
                    "source_preset_catalog_sha256",
                )
            elif (
                self.selector_family is not None
                or self.source_preset_member_taxon_ids is not None
                or self.source_preset_catalog_sha256 is not None
            ):
                raise AtlasMediaError(
                    "non-preset source story carries preset authority"
                )
            if (
                self.selector_kind == "source_sample_presence"
                and self.selector_value != "all"
            ):
                raise AtlasMediaError(
                    "source sample-presence selector value must be all"
                )
            _positive_denominator(self.node_count, "node_count")
            _positive_denominator(self.site_count, "site_count")
            _positive_denominator(
                self.observation_denominator,
                "observation_denominator",
            )
            if self.frame_feature_denominators is not None:
                raise AtlasMediaError("source story cannot carry modeled denominators")
            if self.frame_no_pollen_data_counts is not None:
                raise AtlasMediaError(
                    "source story cannot carry modeled quality counts"
                )
            if (
                not isinstance(self.expected_visible_feature_counts, tuple)
                or len(self.expected_visible_feature_counts) != len(self.frames)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    or value > cast(int, self.node_count)
                    for value in self.expected_visible_feature_counts
                )
                or sum(self.expected_visible_feature_counts) <= 0
            ):
                raise AtlasMediaError(
                    "source story requires exact nonempty frame visibility evidence"
                )
            if (
                not isinstance(self.expected_visible_site_counts, tuple)
                or len(self.expected_visible_site_counts) != len(self.frames)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    or value > cast(int, self.site_count)
                    or value > self.expected_visible_feature_counts[index]
                    for index, value in enumerate(self.expected_visible_site_counts)
                )
                or sum(self.expected_visible_site_counts) <= 0
            ):
                raise AtlasMediaError(
                    "source story requires exact nonempty site visibility evidence"
                )
            if (
                not isinstance(self.expected_visible_observation_counts, tuple)
                or len(self.expected_visible_observation_counts) != len(self.frames)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    or value > cast(int, self.observation_denominator)
                    or (self.expected_visible_feature_counts[index] == 0) != (value == 0)
                    for index, value in enumerate(
                        self.expected_visible_observation_counts
                    )
                )
                or sum(self.expected_visible_observation_counts) <= 0
            ):
                raise AtlasMediaError(
                    "source story requires exact observation visibility evidence"
                )
            if (
                not isinstance(self.source_authority_sha256, str)
                or len(self.source_authority_sha256) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in self.source_authority_sha256
                )
            ):
                raise AtlasMediaError("source story authority digest is invalid")
        else:
            if self.selector_kind != "modeled_metric":
                raise AtlasMediaError(
                    "modeled story selector kind must be modeled_metric"
                )
            if (
                not isinstance(self.selector_family, str)
                or not self.selector_family.strip()
            ):
                raise AtlasMediaError("modeled story selector family must not be empty")
            if (
                self.site_count is not None
                or self.node_count is not None
                or self.observation_denominator is not None
            ):
                raise AtlasMediaError("modeled story cannot carry source denominators")
            if (
                self.expected_visible_feature_counts is not None
                or self.expected_visible_site_counts is not None
                or self.expected_visible_observation_counts is not None
                or self.source_authority_sha256 is not None
                or self.source_preset_member_taxon_ids is not None
                or self.source_preset_catalog_sha256 is not None
            ):
                raise AtlasMediaError("modeled story cannot carry source authority")
            if (
                not isinstance(self.frame_feature_denominators, tuple)
                or len(self.frame_feature_denominators) != len(self.frames)
                or any(
                    isinstance(value, bool) or not isinstance(value, int) or value <= 0
                    for value in self.frame_feature_denominators
                )
            ):
                raise AtlasMediaError(
                    "modeled story requires one positive feature denominator per frame"
                )
            if (
                not isinstance(self.frame_no_pollen_data_counts, tuple)
                or len(self.frame_no_pollen_data_counts) != len(self.frames)
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                    or value > self.frame_feature_denominators[index]
                    for index, value in enumerate(self.frame_no_pollen_data_counts)
                )
            ):
                raise AtlasMediaError(
                    "modeled story requires one governed no-pollen-data count per frame"
                )
        previous_younger: float | int | None = None
        zero_width_count = 0
        for ordinal, frame in enumerate(self.frames):
            _validate_capture_frame(
                frame,
                ordinal=ordinal,
                evidence_role=self.evidence_role,
                selector_kind=self.selector_kind,
                selector_value=self.selector_value,
                selector_family=self.selector_family,
            )
            younger = cast("float | int", frame["time_start_bp"])
            older = cast("float | int", frame["time_end_bp"])
            if previous_younger is not None and older != previous_younger:
                raise AtlasMediaError(
                    "story frames must be exactly continuous from oldest to present"
                )
            previous_younger = younger
            if younger == older:
                zero_width_count += 1
            feature_count = frame.get("feature_count")
            if self.evidence_role == "observation_chronology":
                if feature_count is not None:
                    raise AtlasMediaError(
                        "source story frame cannot carry a modeled denominator"
                    )
                if frame.get("no_pollen_data_count") is not None:
                    raise AtlasMediaError(
                        "source story frame cannot carry modeled quality counts"
                    )
            elif (
                self.frame_feature_denominators is None
                or feature_count != self.frame_feature_denominators[ordinal]
            ):
                raise AtlasMediaError("modeled frame feature denominator differs")
            elif (
                self.frame_no_pollen_data_counts is None
                or frame.get("no_pollen_data_count")
                != self.frame_no_pollen_data_counts[ordinal]
            ):
                raise AtlasMediaError("modeled frame no-pollen-data count differs")
        if zero_width_count and (zero_width_count != 1 or len(self.frames) != 1):
            raise AtlasMediaError(
                "an exact-instant story must contain one unique zero-width frame"
            )


def _positive_denominator(value: object, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AtlasMediaError(f"story {label} must be a positive integer")


def _sha256(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AtlasMediaError(f"story {label} must be a lowercase SHA-256")


def _frame_number(frame: dict[str, object], field: str) -> float | int:
    value = frame.get(field)
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise AtlasMediaError(f"story frame {field} must be finite and non-negative")
    return value


def _validate_capture_frame(
    frame: dict[str, object],
    *,
    ordinal: int,
    evidence_role: str,
    selector_kind: str,
    selector_value: str,
    selector_family: str | None,
) -> None:
    if frame.get("ordinal") != ordinal:
        raise AtlasMediaError("story frame ordinals must be contiguous from zero")
    younger = _frame_number(frame, "time_start_bp")
    older = _frame_number(frame, "time_end_bp")
    if younger > older:
        raise AtlasMediaError("story frame has a reversed BP interval")
    if evidence_role == "observation_chronology":
        expected_level = (
            "source_taxon"
            if selector_kind == "source_label_preset"
            else selector_kind
        )
        if (
            frame.get("story_kind") != "source_chronology"
            or frame.get("source_level") != expected_level
            or (
                selector_kind == "source_ecological_code"
                and frame.get("source_code") != selector_value
            )
            or (
                selector_kind != "source_ecological_code"
                and frame.get("source_code") not in {None, ""}
            )
            or (
                selector_kind == "source_taxon"
                and frame.get("source_taxon") != selector_value
            )
            or (
                selector_kind == "source_label_preset"
                and frame.get("source_taxon") != "all"
            )
            or (
                selector_kind not in {"source_taxon", "source_label_preset"}
                and frame.get("source_taxon") not in {None, ""}
            )
            or (
                selector_kind == "source_label_preset"
                and frame.get("source_preset") != selector_value
            )
            or (
                selector_kind != "source_label_preset"
                and frame.get("source_preset") not in {None, ""}
            )
            or frame.get("metric_family_key") not in {None, ""}
            or frame.get("metric_key") not in {None, ""}
        ):
            raise AtlasMediaError(
                "source frame selector differs from its story selector"
            )
        return
    if (
        frame.get("story_kind") != "modeled_context"
        or frame.get("metric_family_key") != selector_family
        or frame.get("metric_key") != selector_value
        or not isinstance(frame.get("source_window_label"), str)
        or not cast(str, frame["source_window_label"]).strip()
        or frame.get("source_level") not in {None, ""}
        or frame.get("source_code") not in {None, ""}
        or frame.get("source_taxon") not in {None, ""}
        or frame.get("source_preset") not in {None, ""}
    ):
        raise AtlasMediaError("modeled frame selector differs from its story selector")


__all__ = [
    "AtlasMediaError",
    "AtlasMediaPlan",
    "SelectedStory",
    "StorySelection",
]
