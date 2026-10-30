"""Authenticate role-specific scoring observations after prediction readback."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from .inputs import decode, require


class OutcomeReader:
    """Enforce fold-local exclusion without claiming a globally unread cohort."""

    def __init__(
        self,
        archive_root: Path,
        packet: dict[str, Any],
        protocol: dict[str, Any],
        prediction_freeze_sha256: str,
    ) -> None:
        """Initialize outcome references and retain the declared prediction-freeze identity."""
        require(
            re.fullmatch(r"[0-9a-f]{64}", prediction_freeze_sha256) is not None,
            "Authenticated prediction freeze identity required",
        )
        self.archive = archive_root.resolve(strict=True)
        self.taxa = packet["taxa"]
        self.refs = {row["record_id"]: row for row in packet["observation_refs"]}
        self.geometries = {
            row["path"]: row
            for row in protocol["author_inputs"]
            if row["path"].endswith("-geometry.json")
        }
        self.prediction_freeze = prediction_freeze_sha256
        self.selection_freeze: str | None = None
        self.accesses: list[dict[str, Any]] = []

    def _read(self, pin: dict[str, Any]) -> Any:
        sha = pin["sha256"]
        path = self.archive / "objects" / sha[:2] / sha
        require(
            path.is_file()
            and not any(parent.is_symlink() for parent in (path, *path.parents)),
            "An ordinary original scoring object is required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == sha,
            "Scoring object identity changed",
        )
        return decode(raw)

    def read(self, record_id: str, *, outer_target: str, role: str) -> dict[str, int]:
        """Open one allowed label for its explicit training or scoring role."""
        require(role in {"inner_training", "outer_scoring"}, "Unknown outcome role")
        require(
            (role == "inner_training" and record_id != outer_target)
            or (
                role == "outer_scoring"
                and record_id == outer_target
                and isinstance(self.selection_freeze, str)
                and re.fullmatch(r"[0-9a-f]{64}", self.selection_freeze) is not None
            ),
            "Withheld outcome access precedes its role-specific freeze",
        )
        pin = self.refs[record_id]
        value = self._read(pin)
        geometry_name = pin["path"].removesuffix("-raw.json") + "-geometry.json"
        geometry = self._read(self.geometries[geometry_name])
        metadata = geometry["sample_metadata"]
        sample = value["sample"]
        require(
            set(value) == {"data_kind", "taxa", "sample"}
            and value["data_kind"] == "source_observations"
            and value["taxa"] == self.taxa
            and set(sample) == set(metadata) | {"counts"}
            and all(sample[key] == expected for key, expected in metadata.items())
            and type(sample["counts"]) is list
            and len(sample["counts"]) == len(self.taxa)
            and all(type(count) is int and count >= 0 for count in sample["counts"])
            and 0 < sum(sample["counts"]) <= 2**53,
            "Exact owner, support, chronology and integer denominator required",
        )
        self.accesses.append(
            {
                "outer_target": outer_target,
                "observed_record_id": record_id,
                "role": role,
                "observation_reference": pin,
                "freeze_sha256": self.prediction_freeze
                if role == "inner_training"
                else self.selection_freeze,
            }
        )
        return dict(zip(self.taxa, sample["counts"], strict=True))
