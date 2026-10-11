"""Provenance manifest for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import importlib.metadata
import json
from pathlib import Path
import platform
from typing import Any

from bijux_pollenomics_lra.provenance.identity import _canonical, sha256_object
from bijux_pollenomics_lra.version import (
    COMPATIBILITY_MODE,
    NUMERICAL_BACKEND,
    REFERENCE_ARCHIVE_SHA256,
    REFERENCE_PACKAGE,
    REFERENCE_VERSION,
    __version__,
)


def _version_or_unknown(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Machine-readable provenance for one model execution."""

    algorithm: str
    parameters: Mapping[str, Any]
    inputs: Mapping[str, str]
    stochastic: bool
    seed: int | None
    compatibility_mode: str = COMPATIBILITY_MODE
    package: str = "bijux-pollenomics-lra"
    package_version: str = __version__
    reference_package: str = REFERENCE_PACKAGE
    reference_version: str = REFERENCE_VERSION
    reference_archive_sha256: str = REFERENCE_ARCHIVE_SHA256
    schema_version: str = "1.0.0"
    generated_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    runtime: Mapping[str, str] = field(
        default_factory=lambda: {
            "numerical_backend": NUMERICAL_BACKEND,
            "python": platform.python_version(),
            "numpy": _version_or_unknown("numpy"),
            "scipy": _version_or_unknown("scipy"),
            "pandas": _version_or_unknown("pandas"),
            "platform": platform.platform(),
        }
    )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible manifest."""
        return {key: _canonical(value) for key, value in asdict(self).items()}

    def scientific_identity(self) -> dict[str, Any]:
        """Stable run content excluding only the operational creation timestamp.

        Runtime versions remain included because numeric backend changes matter.
        Parent workflows hash this view to avoid timestamps entering identity.
        """
        identity = self.as_dict()
        identity.pop("generated_at_utc")
        return identity

    def write(self, path: str | Path) -> Path:
        """Write indented JSON."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return destination


def build_manifest(
    algorithm: str,
    parameters: Mapping[str, Any],
    inputs: Mapping[str, Any],
    *,
    stochastic: bool,
    seed: int | None,
) -> RunManifest:
    """Build a manifest with canonical hashes for each named input."""
    return RunManifest(
        algorithm=algorithm,
        parameters=_canonical(parameters),
        inputs={name: sha256_object(value) for name, value in inputs.items()},
        stochastic=bool(stochastic),
        seed=seed,
    )
