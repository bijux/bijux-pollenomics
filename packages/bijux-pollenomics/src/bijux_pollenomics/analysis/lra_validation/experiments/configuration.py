"""Immutable synthetic experiment scope and deferred source references."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True, init=False)
class ExperimentSpec:
    """One explicit exploratory profile; it cannot authorize final-test access."""

    sites: tuple[ExperimentSite, ...]
    regional_priority: tuple[str, ...]
    baselines: tuple[Baseline, ...]
    local_ring_count: int
    local_support_radius_m: float
    support_profile: str
    canonical_template: str

    def __init__(self, payload: Mapping[str, object]) -> None:
        row = object_mapping(payload, "experiment")
        if set(row) != {
            "schema_version",
            "profile",
            "sites",
            "regional_priority",
            "baselines",
            "local_ring_count",
            "local_support_radius_m",
            "support_profile",
            "request_template",
        }:
            raise ValidationRefusal(
                "invalid_experiment", "Unexpected or missing experiment fields"
            )
        if row["schema_version"] != "lra-experiment.v1" or row["profile"] != PROFILE:
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
                identity(key)
                for key in object_list(site["identity_keys"], "identity_keys")
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
        methods = object_list(row["baselines"], "baselines")
        if (
            not methods
            or any(method not in BASELINES for method in methods)
            or len(set(map(str, methods))) != len(methods)
        ):
            raise ValidationRefusal(
                "invalid_experiment", "Baselines must be supported and unique"
            )
        template = object_mapping(row["request_template"], "request_template")
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
        encoded = canonical_json(template)
        object.__setattr__(self, "sites", tuple(sites))
        object.__setattr__(self, "regional_priority", priority)
        object.__setattr__(
            self, "baselines", cast(tuple[Baseline, ...], tuple(methods))
        )
        object.__setattr__(self, "local_ring_count", count)
        object.__setattr__(self, "local_support_radius_m", support)
        object.__setattr__(self, "support_profile", "same-outer-radius-homogeneous-v1")
        object.__setattr__(self, "canonical_template", encoded)

    def template(self) -> dict[str, object]:
        """Return an independent template without target observations."""
        return object_mapping(json.loads(self.canonical_template), "template")
