"""Prospective, outcome-free uncertainty declarations for spatial-block rows."""

from __future__ import annotations

from dataclasses import dataclass

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
from .contracts import MAX_CELLS, bounded_integer, digest

BLOCK_OBSERVATION_PROFILE = "synthetic-spatial-block-conditional-pollen-observation-v1"


@dataclass(frozen=True)
class BlockEffortDeclaration:
    """One exact block-fold, target-record and method unit fixed before outcomes."""

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
        if (
            not isinstance(self.taxa, tuple)
            or not 1 <= len(self.taxa) <= 128
            or any(not isinstance(value, str) for value in self.taxa)
        ):
            raise ValidationRefusal(
                "invalid_block_observation_plan", "Require 1–128 exact taxa"
            )
        for taxon in self.taxa:
            required_identity(taxon)
        if self.taxa != tuple(sorted(set(self.taxa))):
            raise ValidationRefusal(
                "invalid_block_observation_plan", "Taxa must be sorted and unique"
            )
        bounded_integer(self.effort, "effort", 1, 2**31 - 1)
        bounded_integer(self.seed, "seed", 0, 2**32 - 1)
        InputReference.parse(
            {"path": self.evidence_path, "sha256": self.evidence_sha256},
            "effort",
        )

    @property
    def key(self) -> tuple[str, str, str]:
        return self.fold_id, self.record_id, self.method

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
            "evidence": {
                "path": self.evidence_path,
                "sha256": self.evidence_sha256,
            },
        }


@dataclass(frozen=True)
class BlockObservationUncertaintyPlan:
    """Complete caller-pinned block denominator fixed before uncertainty work."""

    prediction_manifest_sha256: str
    entries: tuple[BlockEffortDeclaration, ...]
    repeats: int
    coverage: float

    def __post_init__(self) -> None:
        digest(self.prediction_manifest_sha256)
        bounded_integer(self.repeats, "repeats", 2, 10_000)
        level = finite_number(self.coverage)
        if not 0 < (1 - level) / 2 < 0.5:
            raise ValidationRefusal(
                "invalid_block_observation_plan", "Invalid marginal coverage"
            )
        object.__setattr__(self, "coverage", level)
        if (
            not isinstance(self.entries, tuple)
            or not 1 <= len(self.entries) <= 5000
            or any(
                not isinstance(value, BlockEffortDeclaration) for value in self.entries
            )
        ):
            raise ValidationRefusal(
                "invalid_block_observation_plan", "Require 1–5000 typed units"
            )
        if len({entry.key for entry in self.entries}) != len(self.entries):
            raise ValidationRefusal(
                "invalid_block_observation_plan",
                "Duplicate fold/record/method unit",
            )
        if sum(len(entry.taxa) * self.repeats for entry in self.entries) > MAX_CELLS:
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
            self,
            "entries",
            tuple(sorted(self.entries, key=lambda value: value.key)),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-spatial-block-observation-uncertainty-plan.v1",
            "profile": BLOCK_OBSERVATION_PROFILE,
            "prediction_manifest_sha256": self.prediction_manifest_sha256,
            "entries": [entry.as_dict() for entry in self.entries],
            "repeats": self.repeats,
            "coverage": self.coverage,
            "effort_basis": (
                "declared_before_outcome_access_not_independently_authenticated"
            ),
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())

    @classmethod
    def from_dict(cls, value: object) -> BlockObservationUncertaintyPlan:
        """Reopen the exact canonical declaration without coercion or extra fields."""
        row = object_mapping(value, "block_observation_plan")
        entries = []
        try:
            for value in object_list(row["entries"], "entries"):
                item = object_mapping(value, "entry")
                evidence = InputReference.parse(item["evidence"], "effort")
                entry = BlockEffortDeclaration(
                    identity(item["fold_id"]),
                    identity(item["record_id"]),
                    identity(item["bin_id"]),
                    identity(item["method"]),
                    tuple(
                        identity(taxon) for taxon in object_list(item["taxa"], "taxa")
                    ),
                    bounded_integer(item["effort"], "effort", 1, 2**31 - 1),
                    bounded_integer(item["seed"], "seed", 0, 2**32 - 1),
                    evidence.path,
                    evidence.sha256,
                )
                if manifest_sha256(entry.as_dict()) != manifest_sha256(item):
                    raise ValueError("Unexpected block effort fields")
                entries.append(entry)
            plan = cls(
                identity(row["prediction_manifest_sha256"]),
                tuple(entries),
                bounded_integer(row["repeats"], "repeats", 2, 10_000),
                finite_number(row["coverage"]),
            )
            if manifest_sha256(plan.as_dict()) != manifest_sha256(row):
                raise ValueError("Unexpected block plan fields")
            return plan
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationRefusal("invalid_block_observation_plan", str(exc)) from exc
