"""Explicit signal and country endpoint selection for evaluated propagation rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..network import COUNTRY_CODES, PhenomenonEvent

CountryMode = Literal[
    "all", "origin", "destination", "either_endpoint", "within_country", "cross_border"
]
_RESOLUTION_PREFIXES = {
    "whole_pollen": "whole:",
    "ecological_group": "group:",
    "ecological_subgroup": "subgroup:",
    "ecological_role": "role:",
    "taxon": "taxon:",
}


@dataclass(frozen=True)
class PropagationSelection:
    """Select stored endpoint countries without changing scientific eligibility.

    ``signals=None`` retains all signals; an empty tuple retains none.
    Within-country requires equal countries among the selected codes. Cross-border
    requires distinct countries with either endpoint among the selected codes.
    """

    scenario_id: str = "rectangular_100km_100yr_v1"
    country_mode: CountryMode = "all"
    countries: tuple[str, ...] = COUNTRY_CODES
    signals: tuple[tuple[str, str], ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be nonempty")
        if self.country_mode not in {
            "all",
            "origin",
            "destination",
            "either_endpoint",
            "within_country",
            "cross_border",
        }:
            raise ValueError("unsupported country endpoint selection mode")
        if not isinstance(self.countries, tuple) or any(
            code not in COUNTRY_CODES for code in self.countries
        ):
            raise ValueError("countries must contain governed Nordic country codes")
        object.__setattr__(self, "countries", tuple(sorted(set(self.countries))))
        if self.signals is not None:
            if not isinstance(self.signals, tuple):
                raise ValueError("signals must be a tuple of resolution/feature keys")
            for identity in self.signals:
                if not isinstance(identity, tuple) or len(identity) != 2:
                    raise ValueError("each signal requires resolution and feature key")
                resolution, feature = identity
                prefix = _RESOLUTION_PREFIXES.get(resolution)
                if (
                    not isinstance(feature, str)
                    or prefix is None
                    or not feature.startswith(prefix)
                    or feature == prefix
                ):
                    raise ValueError("signal feature key must match its resolution")
            object.__setattr__(self, "signals", tuple(sorted(set(self.signals))))

    def matches(self, source: PhenomenonEvent, target: PhenomenonEvent) -> bool:
        """Keep signal identities separate and evaluate the requested endpoint rule."""
        if (
            self.signals is not None
            and (source.resolution, source.feature_key) not in self.signals
        ):
            return False
        origin, destination = source.country_code, target.country_code
        if self.country_mode == "all":
            return True
        if self.country_mode == "origin":
            return origin in self.countries
        if self.country_mode == "destination":
            return destination in self.countries
        if self.country_mode == "either_endpoint":
            return origin in self.countries or destination in self.countries
        if self.country_mode == "within_country":
            return origin == destination and origin in self.countries
        return origin != destination and (
            origin in self.countries or destination in self.countries
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "country_mode": self.country_mode,
            "countries": list(self.countries),
            "signals": None
            if self.signals is None
            else [list(identity) for identity in self.signals],
        }
