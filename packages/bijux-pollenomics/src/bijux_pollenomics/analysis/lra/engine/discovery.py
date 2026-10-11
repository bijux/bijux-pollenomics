"""Resolve one explicitly supported installed numerical implementation.

Importing the host does not import NumPy, SciPy, pandas or the GPL extension.
No plugin enumeration, dynamic fallback or alternate numerical engine is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module, metadata
from types import ModuleType

from .errors import LRARefusal

DISTRIBUTION = "bijux-pollenomics-lra"
GROUP = "bijux_pollenomics.extensions"
TARGET = "bijux_pollenomics_lra.api:extension_descriptor"
API_MODULE = "bijux_pollenomics_lra.api"
OPERATIONS = ("run_reveals", "run_love", "run_lra", "run_lra_series")


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


def load_engine() -> EngineBinding:
    """Load the optional engine, refusing missing or incompatible installs."""
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
    return EngineBinding(
        DISTRIBUTION, distribution.version, descriptor["numerical_backend"], api
    )
