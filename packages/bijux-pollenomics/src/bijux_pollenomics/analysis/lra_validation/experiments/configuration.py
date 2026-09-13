"""Immutable synthetic experiment scope and deferred source references."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import json
from pathlib import PurePosixPath
import re
from typing import Literal, cast

from ..contracts import (
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    finite_number,
)
from ..contracts import (
    required_identity as _required_identity,
)

Baseline = Literal["training_mean", "nearest_site", "inverse_distance_squared"]
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
PROFILE = "synthetic-withheld-site-baselines-v1"
TEMPORAL_PROFILE = "synthetic-forward-time-persistence-v1"
FITTED_PROFILE = "synthetic-withheld-site-fitted-spatial-v1"
BLOCK_PROFILE = "synthetic-spatial-block-fitted-v1"
BLOCK_SPLIT = "grouped-spatial-block-support-buffer-v1"
FITTED_METHOD = "clr-wgs84-rbf-ridge-v1"
FITTED_ROLES = {
    "vegetation_cover": "heldout_prediction",
    "pollen_composition": "heldout_prediction",
}
LOCAL_PROFILE = "synthetic-local-pollen-available-v1"
LOCAL_METHOD = "analytical_love_local_pollen"
LOCAL_EVALUATION_ROLES = {
    "vegetation_cover": "heldout_prediction",
    "pollen_composition": "in_sample_diagnostic",
}


def identity(value: object) -> str:
    """Validate a JSON identity before narrowing it to the shared contract."""
    if not isinstance(value, str):
        raise ValidationRefusal("invalid_identity", "Expected an exact string identity")
    return _required_identity(value)


def object_mapping(value: object, name: str) -> dict[str, object]:
    """Admit a JSON object without manufacturing or coercing keys."""
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValidationRefusal("invalid_experiment", f"{name} must be an object")
    return dict(value)


def object_list(value: object, name: str) -> list[object]:
    """Admit an explicit JSON array."""
    if not isinstance(value, (list, tuple)):
        raise ValidationRefusal("invalid_experiment", f"{name} must be an array")
    return list(value)


@dataclass(frozen=True)
class InputReference:
    """A relative file identity whose contents can be opened after fold admission."""

    path: str
    sha256: str

    @classmethod
    def parse(cls, value: object, name: str) -> InputReference:
        row = object_mapping(value, name)
        if set(row) != {"path", "sha256"}:
            raise ValidationRefusal("invalid_experiment_reference", name)
        path = row["path"]
        digest = row["sha256"]
        if (
            not isinstance(path, str)
            or not path
            or "\\" in path
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValidationRefusal("invalid_experiment_reference", name)
        return cls(path, digest)


@dataclass(frozen=True)
class ExperimentSite:
    """Grouping metadata is separate from unopened pollen and target geometry."""

    record: SiteRecord
    raw: InputReference
    geometry: InputReference


@dataclass(frozen=True)
class ExperimentScope:
    """Shared immutable input scope; observation-channel admission is separate."""

    sites: tuple[ExperimentSite, ...]
    regional_priority: tuple[str, ...]
    local_ring_count: int
    local_support_radius_m: float
    support_profile: str
    canonical_template: str

    def template(self) -> dict[str, object]:
        """Return an independent template without target observations."""
        return object_mapping(json.loads(self.canonical_template), "template")


def _scope(
    payload: Mapping[str, object], *, profile: str, selection_field: str
) -> ExperimentScope:
    row = object_mapping(payload, "experiment")
    if set(row) != {
        "schema_version",
        "profile",
        "sites",
        "regional_priority",
        selection_field,
        "local_ring_count",
        "local_support_radius_m",
        "support_profile",
        "request_template",
    }:
        raise ValidationRefusal(
            "invalid_experiment", "Unexpected or missing experiment fields"
        )
    if row["schema_version"] != "lra-experiment.v1" or row["profile"] != profile:
        raise ValidationRefusal(
            "unsupported_experiment_profile",
            "Only the explicit synthetic exploratory profile is implemented",
        )
    count = row["local_ring_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValidationRefusal(
            "invalid_experiment", "local_ring_count must be a positive integer"
        )
    support = finite_number(row["local_support_radius_m"])
    if support <= 0 or row["support_profile"] != "same-outer-radius-homogeneous-v1":
        raise ValidationRefusal(
            "unsupported_experiment_support",
            "Declare a positive common support radius and homogeneous profile",
        )
    sites = []
    for value in object_list(row["sites"], "sites"):
        site = object_mapping(value, "site")
        if set(site) != {
            "record_id",
            "site_id",
            "identity_keys",
            "raw",
            "geometry",
        }:
            raise ValidationRefusal("invalid_experiment", "Unexpected site fields")
        keys = tuple(
            identity(key) for key in object_list(site["identity_keys"], "identity_keys")
        )
        record = SiteRecord(
            identity(site["record_id"]), identity(site["site_id"]), keys
        )
        sites.append(
            ExperimentSite(
                record,
                InputReference.parse(site["raw"], "raw"),
                InputReference.parse(site["geometry"], "geometry"),
            )
        )
    if not 3 <= len(sites) <= 128 or len(
        {site.record.record_id for site in sites}
    ) != len(sites):
        raise ValidationRefusal(
            "invalid_experiment", "Require 3–128 uniquely identified records"
        )
    priority = tuple(
        identity(item)
        for item in object_list(row["regional_priority"], "regional_priority")
    )
    record_ids = {site.record.record_id for site in sites}
    if (
        not priority
        or len(set(priority)) != len(priority)
        or not set(priority).issubset(record_ids)
    ):
        raise ValidationRefusal(
            "invalid_experiment",
            "Regional priority must name unique catalogued records",
        )
    template = validate_template(row["request_template"])
    return ExperimentScope(
        tuple(sites),
        priority,
        count,
        support,
        "same-outer-radius-homogeneous-v1",
        canonical_json(template),
    )


def validate_template(value: object) -> dict[str, object]:
    """Admit the common synthetic template before execution or retained reopening."""
    template = object_mapping(value, "request_template")
    if (
        template.get("data_kind") != "synthetic"
        or template.get("purpose") != "exploratory"
        or template.get("operation") != "lra"
    ):
        raise ValidationRefusal(
            "unsupported_experiment_profile",
            "Real/final experiments require a separately implemented reviewed policy",
        )
    if any(key in template for key in ("local", "regional", "rings")):
        raise ValidationRefusal(
            "invalid_experiment",
            "Template cannot embed site observations or geometry",
        )
    required = {
        "schema_version",
        "operation",
        "data_kind",
        "purpose",
        "method_profile",
        "taxa",
        "pollen_unit",
        "configuration",
        "parameters",
        "evidence",
        "exclusions",
        "uncertainty_omissions",
        "temporal_matching",
        "versions",
    }
    if set(template) != required:
        raise ValidationRefusal(
            "invalid_experiment_template",
            "Initial template requires the closed host request fields except site-specific inputs",
        )
    configuration = object_mapping(template.get("configuration"), "configuration")
    for method in ("reveals", "love"):
        config = object_mapping(configuration.get(method), method)
        if config.get("stochastic") is not False:
            raise ValidationRefusal(
                "unsupported_experiment_profile",
                "Initial profile uses deterministic source computations",
            )
    if object_mapping(configuration["love"], "love").get("method") != "analytical":
        raise ValidationRefusal(
            "unsupported_experiment_profile",
            "Initial extraction supports analytical LOVE",
        )
    for evidence in object_list(template.get("evidence"), "evidence"):
        if object_mapping(evidence, "evidence").get("role") not in {
            "chronology",
            "taxa",
            "parameters",
            "dependency_lock",
            "decision",
        }:
            raise ValidationRefusal(
                "invalid_experiment",
                "Site raw/geometry evidence must come from admitted per-fold inputs",
            )
    canonical_json(template)
    return template


@dataclass(frozen=True, init=False)
class ExperimentSpec(ExperimentScope):
    """All target pollen withheld; explicit spatial baselines only."""

    baselines: tuple[Baseline, ...]

    def __init__(self, payload: Mapping[str, object]) -> None:
        scope = _scope(payload, profile=PROFILE, selection_field="baselines")
        row = object_mapping(payload, "experiment")
        methods = object_list(row["baselines"], "baselines")
        if (
            not methods
            or any(method not in BASELINES for method in methods)
            or len(set(map(str, methods))) != len(methods)
        ):
            raise ValidationRefusal(
                "invalid_experiment", "Baselines must be supported and unique"
            )
        super().__init__(
            scope.sites,
            scope.regional_priority,
            scope.local_ring_count,
            scope.local_support_radius_m,
            scope.support_profile,
            scope.canonical_template,
        )
        object.__setattr__(
            self, "baselines", cast(tuple[Baseline, ...], tuple(methods))
        )


@dataclass(frozen=True, init=False)
class LocalPollenSpec(ExperimentScope):
    """Observe target pollen explicitly; vegetation remains unopened."""

    method: str

    def __init__(self, payload: Mapping[str, object]) -> None:
        scope = _scope(payload, profile=LOCAL_PROFILE, selection_field="method")
        if payload["method"] != LOCAL_METHOD:
            raise ValidationRefusal(
                "unsupported_local_pollen_method",
                "Explicit analytical local-pollen assimilation is required",
            )
        super().__init__(
            scope.sites,
            scope.regional_priority,
            scope.local_ring_count,
            scope.local_support_radius_m,
            scope.support_profile,
            scope.canonical_template,
        )
        object.__setattr__(self, "method", LOCAL_METHOD)


@dataclass(frozen=True, init=False)
class FittedSpatialExperimentSpec(ExperimentScope):
    """Fixed spatial parameters with both target observation channels withheld."""

    length_scale_km: float
    ridge_penalty: float

    def __init__(self, payload: Mapping[str, object]) -> None:
        scope = _scope(payload, profile=FITTED_PROFILE, selection_field="method")
        method = object_mapping(payload["method"], "method")
        if (
            set(method) != {"profile", "length_scale_km", "ridge_penalty"}
            or method["profile"] != FITTED_METHOD
        ):
            raise ValidationRefusal(
                "unsupported_fitted_spatial_method",
                "Declare the fixed CLR spatial model",
            )
        scale, penalty = (
            finite_number(method["length_scale_km"]),
            finite_number(method["ridge_penalty"]),
        )
        if scale <= 0 or penalty <= 0:
            raise ValidationRefusal(
                "invalid_spatial_configuration", "Parameters must be positive"
            )
        super().__init__(
            scope.sites,
            scope.regional_priority,
            scope.local_ring_count,
            scope.local_support_radius_m,
            scope.support_profile,
            scope.canonical_template,
        )
        object.__setattr__(self, "length_scale_km", scale)
        object.__setattr__(self, "ridge_penalty", penalty)


@dataclass(frozen=True, init=False)
class SpatialBlockExperimentSpec(FittedSpatialExperimentSpec):
    """Original geographic blocks with explicit outcome-free support declarations."""

    minimum_buffer_m: float
    support_references: tuple[tuple[str, InputReference], ...]

    def __init__(self, payload: Mapping[str, object]) -> None:
        original = object_mapping(payload, "block_experiment")
        if original.get("profile") != BLOCK_PROFILE:
            raise ValidationRefusal(
                "unsupported_experiment_profile", "Declare spatial-block profile"
            )
        split = object_mapping(original.pop("split", None), "split")
        if (
            set(split) != {"profile", "minimum_buffer_m"}
            or split["profile"] != BLOCK_SPLIT
        ):
            raise ValidationRefusal(
                "invalid_block_split", "Declare the exact support-buffer scenario"
            )
        minimum = finite_number(split["minimum_buffer_m"])
        if minimum < 0:
            raise ValidationRefusal(
                "invalid_block_split", "Buffer is nonnegative metres"
            )
        sites, blocks, references = [], {}, []
        for value in object_list(original["sites"], "sites"):
            row = object_mapping(value, "site")
            record = identity(row["record_id"])
            blocks[record] = identity(row.pop("block_id", None))
            references.append(
                (record, InputReference.parse(row.pop("support", None), "support"))
            )
            sites.append(row)
        original.update(profile=FITTED_PROFILE, sites=sites)
        super().__init__(original)
        object.__setattr__(
            self,
            "sites",
            tuple(
                replace(
                    site,
                    record=replace(site.record, block_id=blocks[site.record.record_id]),
                )
                for site in self.sites
            ),
        )
        object.__setattr__(self, "minimum_buffer_m", minimum)
        object.__setattr__(self, "support_references", tuple(sorted(references)))
        reveals = object_mapping(
            object_mapping(self.template()["configuration"], "configuration")[
                "reveals"
            ],
            "reveals",
        )
        if (
            "region_cutoff_m" not in reveals
            or finite_number(reveals["region_cutoff_m"]) <= 0
        ):
            raise ValidationRefusal(
                "missing_block_source_support",
                "Explicit regional integration cutoff is required",
            )

    def request(self) -> dict[str, object]:
        """Serialize the complete normalized declaration without reading observation files."""
        references = dict(self.support_references)
        return {
            "schema_version": "lra-experiment.v1",
            "profile": BLOCK_PROFILE,
            "sites": [
                {
                    "record_id": site.record.record_id,
                    "site_id": site.record.site_id,
                    "identity_keys": list(site.record.identity_keys),
                    "block_id": site.record.block_id,
                    "raw": {"path": site.raw.path, "sha256": site.raw.sha256},
                    "geometry": {
                        "path": site.geometry.path,
                        "sha256": site.geometry.sha256,
                    },
                    "support": {
                        "path": references[site.record.record_id].path,
                        "sha256": references[site.record.record_id].sha256,
                    },
                }
                for site in self.sites
            ],
            "regional_priority": list(self.regional_priority),
            "local_ring_count": self.local_ring_count,
            "local_support_radius_m": self.local_support_radius_m,
            "support_profile": self.support_profile,
            "request_template": self.template(),
            "method": {
                "profile": FITTED_METHOD,
                "length_scale_km": self.length_scale_km,
                "ridge_penalty": self.ridge_penalty,
            },
            "split": {
                "profile": BLOCK_SPLIT,
                "minimum_buffer_m": self.minimum_buffer_m,
            },
        }
