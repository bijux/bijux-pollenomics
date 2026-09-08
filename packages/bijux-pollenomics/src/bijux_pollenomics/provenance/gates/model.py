"""Immutable product gate specification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .codec import _digest_json
from .producer import _LOCAL_ATTESTATION, _producer_record
from .repository import _repository_root


@dataclass(frozen=True)
class RecordedGateSpecification:
    """Trusted execution shape for one product-owned verification gate."""

    gate_id: str
    required: bool
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    input_paths: tuple[str, ...]
    artifacts_directory: str
    junit_path: str
    timeout_seconds: float | None = None
    runtime_identity: tuple[tuple[str, str], ...] = ()

    def as_record(self, repository_root: Path) -> dict[str, object]:
        """Return the canonical root-bound specification record."""
        root = _repository_root(repository_root)
        return {
            "gate_id": self.gate_id,
            "required": self.required,
            "argv": list(self.argv),
            "environment": dict(self.environment),
            "input_paths": list(self.input_paths),
            "artifacts_directory": self.artifacts_directory,
            "junit_path": self.junit_path,
            "timeout_seconds": self.timeout_seconds,
            "runtime_identity": dict(self.runtime_identity),
            "repository_root_digest": _digest_json(root.as_posix()),
            "producer": _producer_record(),
            "attestation": dict(_LOCAL_ATTESTATION),
        }
