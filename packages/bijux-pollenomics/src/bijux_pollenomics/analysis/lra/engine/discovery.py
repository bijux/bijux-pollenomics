"""Resolve one explicitly supported installed numerical implementation.

Importing the host does not import NumPy, SciPy, pandas or the GPL extension.
No plugin enumeration, dynamic fallback or alternate numerical engine is used.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from importlib import import_module, metadata
from inspect import Parameter, signature
from types import ModuleType

from .errors import LRARefusal

DISTRIBUTION = "bijux-pollenomics-lra"
GROUP = "bijux_pollenomics.extensions"
TARGET = "bijux_pollenomics_lra.api:extension_descriptor"
API_MODULE = "bijux_pollenomics_lra.api"
OPERATIONS = ("run_reveals", "run_love", "run_lra", "run_lra_series")
MULTISITE_PUBLICATION_CAPABILITY = "lra.reveals.multisite.publication-source"
LANDCLIM_ANALYTICAL_LOVE_CAPABILITY = (
    "lra.love.analytical.fall-speed-profile.landclimii-2016-gpm-neutral-analytical-v1"
)
MULTISITE_DRAW_LOVE_CAPABILITY = (
    "lra.love.analytical.multisite-cover-draws.landclimii-2016-v1"
)
OPTIMIZED_RING_TAXON_CAPABILITY = "lra.love.optimized.ring-taxon-preserving"
OPTIMIZED_RING_TAXON_PROFILE = "ring-taxon-preserving"
_LANDCLIM_FALL_SPEED_PROFILE = "landclimii-2016-gpm-neutral-analytical-v1"
_OPTIONAL_CAPABILITIES = frozenset(
    (
        MULTISITE_PUBLICATION_CAPABILITY,
        LANDCLIM_ANALYTICAL_LOVE_CAPABILITY,
        MULTISITE_DRAW_LOVE_CAPABILITY,
        OPTIMIZED_RING_TAXON_CAPABILITY,
    )
)


@dataclass(frozen=True)
class EngineBinding:
    """Verified installed distribution metadata and its supported facade."""

    distribution: str
    version: str
    numerical_backend: str
    api: ModuleType

    def as_dict(self) -> dict[str, str]:
        """Return serializable engine identity for a host product manifest."""
        return {
            "distribution": self.distribution,
            "version": self.version,
            "numerical_backend": self.numerical_backend,
            "python_api": API_MODULE,
            "extension_group": GROUP,
            "extension_name": "lra",
            "extension_target": TARGET,
        }


def required_capability_for_profile(method_profile: str) -> str | None:
    """Select an optional facade only for the revised host method profile."""
    if method_profile == OPTIMIZED_RING_TAXON_PROFILE:
        return OPTIMIZED_RING_TAXON_CAPABILITY
    return None


def _require_optional_capability(
    api: ModuleType, descriptor: dict[str, object], capability: str
) -> None:
    """Verify a selected optional method without changing the legacy contract."""
    if not isinstance(capability, str) or capability not in _OPTIONAL_CAPABILITIES:
        raise LRARefusal(
            "lra_extension_capability_unknown", f"Unknown LRA capability: {capability}"
        )
    advertised = descriptor.get("capabilities")
    if advertised is None:
        raise LRARefusal(
            "lra_extension_capability_unavailable",
            f"Installed LRA extension does not advertise {capability}",
        )
    if (
        not isinstance(advertised, list)
        or any(not isinstance(item, str) or not item for item in advertised)
        or len(set(advertised)) != len(advertised)
    ):
        raise LRARefusal(
            "lra_extension_capability_invalid",
            "Installed LRA extension has malformed optional capabilities",
        )
    if capability not in advertised:
        raise LRARefusal(
            "lra_extension_capability_unavailable",
            f"Installed LRA extension does not advertise {capability}",
        )
    if capability == MULTISITE_PUBLICATION_CAPABILITY:
        complete = callable(getattr(api, "run_reveals_multisite", None)) and all(
            isinstance(getattr(api, name, None), type)
            for name in (
                "MultisiteRevealsInput",
                "PublicationRevealsConfig",
                "MultisiteRevealsResult",
            )
        )
        complete = complete and callable(
            getattr(getattr(api, "MultisiteRevealsResult", None), "write", None)
        )
    elif capability == MULTISITE_DRAW_LOVE_CAPABILITY:
        source_type = getattr(api, "RegionalCoverDrawSource", None)
        config_type = getattr(api, "RegionalDrawLoveConfig", None)
        complete = (
            isinstance(source_type, type)
            and callable(getattr(source_type, "from_verified_member", None))
            and isinstance(config_type, type)
            and is_dataclass(config_type)
            and {field.name for field in fields(config_type)}
            >= {
                "local_basin_diameter_m",
                "max_ring",
                "repeats",
                "stochastic",
                "seed",
                "retain_samples",
                "ppe_error",
            }
            and callable(getattr(api, "run_love_from_regional_draws", None))
            and callable(getattr(api, "publication_bin_bounds_sha256", None))
        )
        if complete and isinstance(config_type, type):
            try:
                selected = config_type(
                    local_basin_diameter_m=12.9,
                    max_ring=1,
                    repeats=1000,
                    stochastic=False,
                    seed=7,
                    retain_samples=True,
                    ppe_error=False,
                )
                settings = selected.as_dict()
                expected_settings = {
                    "configuration_kind": "regional-cover-draws",
                    "method": "analytical",
                    "local_basin_diameter_m": 12.9,
                    "max_ring": 1,
                    "distance_weighting": "gpm neutral",
                    "fall_speed_profile": _LANDCLIM_FALL_SPEED_PROFILE,
                    "repeats": 1000,
                    "stochastic": False,
                    "seed": 7,
                    "retain_samples": True,
                    "ppe_error": False,
                }
                complete = (
                    selected.method == "analytical"
                    and selected.distance_weighting == "gpm neutral"
                    and selected.fall_speed_profile == _LANDCLIM_FALL_SPEED_PROFILE
                    and all(
                        settings.get(key) == value
                        for key, value in expected_settings.items()
                    )
                    and not {
                        "regional_basin_type",
                        "regional_basin_diameter_m",
                    }
                    & set(settings)
                )
            except Exception:
                complete = False
    elif capability == OPTIMIZED_RING_TAXON_CAPABILITY:
        config_type = getattr(api, "LoveConfig", None)
        profile_type = getattr(api, "OptimizedLoveProfile", None)
        complete = (
            isinstance(config_type, type)
            and is_dataclass(config_type)
            and {field.name for field in fields(config_type)}
            >= {"method", "optimized_profile"}
            and isinstance(profile_type, type)
            and getattr(
                getattr(profile_type, "RING_TAXON_PRESERVING", None), "value", None
            )
            == OPTIMIZED_RING_TAXON_PROFILE
            and callable(getattr(api, "run_love", None))
        )
        if complete and isinstance(config_type, type):
            try:
                selected = config_type(
                    method="optimized",
                    regional_basin_type="lake",
                    regional_basin_diameter_m=300,
                    local_basin_diameter_m=12.9,
                    max_ring=1,
                    optimized_profile=OPTIMIZED_RING_TAXON_PROFILE,
                    repeats=1,
                    stochastic=False,
                )
                complete = (
                    selected.method == "optimized"
                    and selected.optimized_profile == OPTIMIZED_RING_TAXON_PROFILE
                    and selected.as_dict().get("optimized_profile")
                    == OPTIMIZED_RING_TAXON_PROFILE
                )
            except Exception:
                complete = False
    else:
        config_type = getattr(api, "LoveConfig", None)
        complete = (
            isinstance(config_type, type)
            and is_dataclass(config_type)
            and {field.name for field in fields(config_type)}
            >= {"method", "distance_weighting", "fall_speed_profile"}
            and callable(getattr(api, "run_love", None))
        )
        if complete and isinstance(config_type, type):
            try:
                draw_parameter = signature(api.run_love).parameters.get(
                    "regional_cover_draws"
                )
                if draw_parameter is None or draw_parameter.kind not in (
                    Parameter.KEYWORD_ONLY,
                    Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    complete = False
                selected = config_type(
                    method="analytical",
                    regional_basin_type="lake",
                    regional_basin_diameter_m=300,
                    local_basin_diameter_m=12.9,
                    max_ring=1,
                    distance_weighting="gpm neutral",
                    fall_speed_profile=_LANDCLIM_FALL_SPEED_PROFILE,
                    repeats=1,
                    stochastic=False,
                )
                complete = (
                    complete
                    and selected.method == "analytical"
                    and selected.distance_weighting == "gpm neutral"
                    and selected.fall_speed_profile == _LANDCLIM_FALL_SPEED_PROFILE
                    and selected.as_dict().get("fall_speed_profile")
                    == _LANDCLIM_FALL_SPEED_PROFILE
                )
            except Exception:
                # A broken advertised constructor is an unavailable feature,
                # not a reason to break unrelated installed LRA operations.
                complete = False
    if not complete:
        raise LRARefusal(
            "lra_extension_capability_invalid",
            f"Installed LRA extension advertises {capability} without its facade",
        )


def load_engine(*, required_capability: str | None = None) -> EngineBinding:
    """Load the optional engine, checking selected features only when requested."""
    try:
        distribution = metadata.distribution(DISTRIBUTION)
    except metadata.PackageNotFoundError as exc:
        raise LRARefusal(
            "lra_extension_missing",
            "Install bijux-pollenomics[lra] to run landscape reconstruction.",
        ) from exc
    entries = [
        entry
        for entry in distribution.entry_points
        if entry.group == GROUP and entry.name == "lra"
    ]
    if len(entries) != 1 or entries[0].value != TARGET:
        raise LRARefusal(
            "lra_extension_incompatible",
            "Installed LRA entry-point contract is incompatible.",
        )
    try:
        api = import_module(API_MODULE)
        descriptor = api.extension_descriptor()
    except (ImportError, AttributeError) as exc:
        raise LRARefusal(
            "lra_extension_broken", f"Installed LRA extension could not load: {exc}"
        ) from exc
    required = {
        "schema_version": "1.0.0",
        "distribution": DISTRIBUTION,
        "version": distribution.version,
        "python_api": API_MODULE,
        "extension_group": GROUP,
        "extension_name": "lra",
        "extension_target": TARGET,
    }
    if (
        not isinstance(descriptor, dict)
        or any(descriptor.get(key) != value for key, value in required.items())
        or descriptor.get("numerical_backend") != "python-numpy-scipy"
        or any(not callable(getattr(api, name, None)) for name in OPERATIONS)
    ):
        raise LRARefusal(
            "lra_extension_incompatible",
            "Installed LRA API, identity or backend is incompatible.",
        )
    if required_capability is not None:
        _require_optional_capability(api, descriptor, required_capability)
    return EngineBinding(
        DISTRIBUTION, distribution.version, descriptor["numerical_backend"], api
    )
