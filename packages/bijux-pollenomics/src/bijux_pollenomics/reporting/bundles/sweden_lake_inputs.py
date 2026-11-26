"""Captured, caller-pinned inputs for optional Sweden lake map layers."""

from dataclasses import dataclass
import hashlib
from pathlib import Path

from bijux_pollenomics.core.filesystem import read_regular_file

_MAX_LAKE_INPUT_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CapturedLakeFile:
    """Own exact bytes and a caller-supplied digest for one lake input."""

    name: str
    content: bytes
    sha256: str

    def __post_init__(self) -> None:
        if (
            not self.name
            or Path(self.name).name != self.name
            or self.name in {".", ".."}
            or "\\" in self.name
        ):
            raise ValueError("Sweden lake input name differs")
        if type(self.content) is not bytes or len(self.content) > _MAX_LAKE_INPUT_BYTES:
            raise ValueError("Sweden lake input bytes differ")
        if (
            len(self.sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.sha256)
            or hashlib.sha256(self.content).hexdigest() != self.sha256
        ):
            raise ValueError("Sweden lake input digest differs")

    @classmethod
    def read(cls, path: Path, sha256: str) -> "CapturedLakeFile":
        """Capture one regular file through the anchored bounded reader."""
        if not path.is_absolute():
            raise ValueError("Sweden lake input path must be absolute")
        return cls(
            path.name, read_regular_file(path, max_bytes=_MAX_LAKE_INPUT_BYTES), sha256
        )


@dataclass(frozen=True)
class SwedenLakeInputs:
    """Select explicit immutable inputs; an empty request selects no lake layers."""

    scenario: CapturedLakeFile | None = None
    registry: CapturedLakeFile | None = None
    traceability: CapturedLakeFile | None = None

    def __post_init__(self) -> None:
        if any(
            item is not None and not isinstance(item, CapturedLakeFile)
            for item in (self.scenario, self.registry, self.traceability)
        ):
            raise ValueError("Sweden lake inputs must be captured files")
        if self.scenario is None and (
            self.registry is not None or self.traceability is not None
        ):
            raise ValueError("Sweden lake scenario is required for other inputs")

    def validate_version(self, version: str) -> None:
        """Refuse files that do not belong to the requested release."""
        for role, item, suffix in (
            ("scenario", self.scenario, "_scenarios.csv"),
            ("registry", self.registry, "_registry.csv"),
            ("traceability", self.traceability, ".md"),
        ):
            if (
                item is not None
                and item.name != f"sweden_lake_evidence_richness_{version}{suffix}"
            ):
                raise ValueError(f"Sweden lake {role} input release differs")

    def identity(self) -> dict[str, str | None]:
        """Return exact selected input hashes without implying source admission."""
        return {
            "scenario": self.scenario.sha256 if self.scenario else None,
            "registry": self.registry.sha256 if self.registry else None,
            "traceability": self.traceability.sha256 if self.traceability else None,
        }
