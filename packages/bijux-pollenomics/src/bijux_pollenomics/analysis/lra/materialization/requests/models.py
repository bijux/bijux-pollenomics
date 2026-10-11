"""Explicit source-cell and chronology selections for declared synthetic fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _identity(value: object) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Bindings require exact nonempty string identities")


@dataclass(frozen=True)
class SourceCellBinding:
    """One source observation supplies exactly one retained matrix cell."""

    role: str
    sample_id: str
    taxon: str
    observation_id: str

    def __post_init__(self) -> None:
        for value in (self.role, self.sample_id, self.taxon, self.observation_id):
            _identity(value)
        if self.role not in {"regional", "local"}:
            raise ValueError("Cell role must be regional or local")


@dataclass(frozen=True)
class SampleChronologyBinding:
    """An explicit claim selection, never inferred from a default or midpoint."""

    sample_id: str
    chronology_claim_id: str

    def __post_init__(self) -> None:
        _identity(self.sample_id)
        _identity(self.chronology_claim_id)


@dataclass(frozen=True)
class SyntheticRequestReport:
    """Published exploratory fixture request; no empirical acceptance claim."""

    output_directory: Path
    request_sha256: str
    manifest_sha256: str
    synthetic_fixture_id: str
    selected_samples: int
    selected_cells: int
