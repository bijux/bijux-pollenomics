"""Immutable pre-observation counting designs and complete bounded unit identities."""

from __future__ import annotations

from dataclasses import dataclass
import re

from ..contracts import (
    ValidationRefusal,
    finite_number,
    manifest_sha256,
    required_identity,
)
from ..experiments.configuration import (
    InputReference,
    identity,
    object_list,
    object_mapping,
)

PROFILE = "synthetic-conditional-pollen-observation-v1"
MAX_CELLS = 1_000_000


def digest(value: str) -> str:
    """Require an explicit exact byte identity without coercion."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationRefusal("invalid_observation_plan", "Expected a SHA-256")
    return value


def bounded_integer(value: object, name: str, lower: int, upper: int) -> int:
    """Refuse booleans and implicit numerical conversions."""
    if type(value) is not int or not lower <= value <= upper:
        raise ValidationRefusal("invalid_observation_plan", name)
    return value


@dataclass(frozen=True)
class EffortDeclaration:
    """One requested prediction unit, including units whose prediction failed."""

    fold_id: str
    record_id: str
    bin_id: str
    method: str
    taxa: tuple[str, ...]
    effort: int
    seed: int
    evidence_path: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        for value in (self.fold_id, self.record_id, self.bin_id, self.method):
            required_identity(value)
        if not isinstance(self.taxa, tuple) or not 1 <= len(self.taxa) <= 128:
            raise ValidationRefusal("invalid_observation_plan", "Require 1–128 taxa")
        for taxon in self.taxa:
            required_identity(taxon)
        if self.taxa != tuple(sorted(set(self.taxa))):
            raise ValidationRefusal(
                "invalid_observation_plan", "Taxa must be sorted and unique"
            )
        bounded_integer(self.effort, "effort", 1, 2**31 - 1)
        bounded_integer(self.seed, "seed", 0, 2**32 - 1)
        InputReference.parse(
            {"path": self.evidence_path, "sha256": self.evidence_sha256}, "effort"
        )

    @property
    def key(self) -> tuple[str, str]:
        return self.fold_id, self.method

    @property
    def reference(self) -> InputReference:
        return InputReference(self.evidence_path, self.evidence_sha256)

    def as_dict(self) -> dict[str, object]:
        return {
            "fold_id": self.fold_id,
            "record_id": self.record_id,
            "bin_id": self.bin_id,
            "method": self.method,
            "taxa": self.taxa,
            "effort": self.effort,
            "seed": self.seed,
            "evidence": {"path": self.evidence_path, "sha256": self.evidence_sha256},
        }


@dataclass(frozen=True)
class ObservationUncertaintyPlan:
    """Caller declaration fixed before uncertainty generation or outcome access."""

    prediction_manifest_sha256: str
    entries: tuple[EffortDeclaration, ...]
    repeats: int
    coverage: float

    def __post_init__(self) -> None:
        digest(self.prediction_manifest_sha256)
        bounded_integer(self.repeats, "repeats", 2, 10_000)
        level = finite_number(self.coverage)
        if not 0 < (1 - level) / 2 < 0.5:
            raise ValidationRefusal(
                "invalid_observation_plan", "Invalid marginal coverage"
            )
        object.__setattr__(self, "coverage", level)
        if not isinstance(self.entries, tuple) or not 1 <= len(self.entries) <= 1000:
            raise ValidationRefusal(
                "invalid_observation_plan", "Require 1–1000 requested units"
            )
        if any(not isinstance(e, EffortDeclaration) for e in self.entries):
            raise ValidationRefusal(
                "invalid_observation_plan", "Invalid counting declaration"
            )
        if len({e.key for e in self.entries}) != len(self.entries):
            raise ValidationRefusal(
                "invalid_observation_plan", "Duplicate requested unit"
            )
        if sum(len(e.taxa) * self.repeats for e in self.entries) > MAX_CELLS:
            raise ValidationRefusal(
                "observation_resource_budget_exceeded",
                "Total requested draw cells exceed one million",
            )
        efforts: dict[tuple[str, str], tuple[int, str, str]] = {}
        for entry in self.entries:
            key = entry.record_id, entry.bin_id
            value = entry.effort, entry.evidence_path, entry.evidence_sha256
            if key in efforts and efforts[key] != value:
                raise ValidationRefusal("inconsistent_target_effort", entry.record_id)
            efforts[key] = value
        object.__setattr__(
            self, "entries", tuple(sorted(self.entries, key=lambda e: e.key))
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-observation-uncertainty-plan.v1",
            "profile": PROFILE,
            "prediction_manifest_sha256": self.prediction_manifest_sha256,
            "entries": [e.as_dict() for e in self.entries],
            "repeats": self.repeats,
            "coverage": self.coverage,
            "effort_basis": "declared_before_outcome_access_not_independently_authenticated",
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())

    @classmethod
    def from_dict(cls, value: object) -> ObservationUncertaintyPlan:
        """Reconstruct immutable declarations, refusing extra fields and type coercion."""
        row = object_mapping(value, "observation_plan")
        entries = []
        try:
            for item in object_list(row["entries"], "entries"):
                entry = object_mapping(item, "effort")
                evidence = InputReference.parse(entry["evidence"], "effort")
                parsed = EffortDeclaration(
                    identity(entry["fold_id"]),
                    identity(entry["record_id"]),
                    identity(entry["bin_id"]),
                    identity(entry["method"]),
                    tuple(identity(t) for t in object_list(entry["taxa"], "taxa")),
                    bounded_integer(entry["effort"], "effort", 1, 2**31 - 1),
                    bounded_integer(entry["seed"], "seed", 0, 2**32 - 1),
                    evidence.path,
                    evidence.sha256,
                )
                if manifest_sha256(parsed.as_dict()) != manifest_sha256(entry):
                    raise ValueError("Unexpected effort fields")
                entries.append(parsed)
            plan = cls(
                identity(row["prediction_manifest_sha256"]),
                tuple(entries),
                bounded_integer(row["repeats"], "repeats", 2, 10000),
                finite_number(row["coverage"]),
            )
            if manifest_sha256(plan.as_dict()) != manifest_sha256(row):
                raise ValueError("Unexpected plan fields")
            return plan
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationRefusal("invalid_observation_plan", str(exc)) from exc
