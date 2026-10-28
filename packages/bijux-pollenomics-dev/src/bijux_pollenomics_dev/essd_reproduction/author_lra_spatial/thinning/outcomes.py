"""Open the selected scoring observations after prediction member readback."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from ..inputs import decode, require


class OutcomeReader:
    """Bind one scoring access per selected owner without an unread-cohort claim."""

    def __init__(
        self, archive: Path, packet: dict[str, Any], prediction_freeze_sha256: str
    ) -> None:
        require(
            type(prediction_freeze_sha256) is str
            and re.fullmatch("[0-9a-f]{64}", prediction_freeze_sha256) is not None,
            "Closed prediction readback identity required",
        )
        self.archive = archive.resolve(strict=True)
        self.taxa = packet["taxa"]
        self.selected = set(packet["cohort"]["selected"])
        self.refs = {row["record_id"]: row for row in packet["observation_refs"]}
        require(
            len(self.refs)
            == len(packet["observation_refs"])
            == len(self.selected)
            == 10
            and set(self.refs) == self.selected,
            "Exactly ten selected observation owners required",
        )
        self.geometry_refs = packet["geometry_refs"]
        self.expected_metadata = {
            target: packet["geometries"][target]["sample_metadata"]
            for target in self.selected
        }
        self.freeze = prediction_freeze_sha256
        self.accesses: list[dict[str, Any]] = []
        self.seen: set[str] = set()

    def _read(self, pin: dict[str, Any]) -> Any:
        sha = pin["sha256"]
        require(
            type(sha) is str and re.fullmatch("[0-9a-f]{64}", sha) is not None,
            "Exact scoring object identity required",
        )
        path = self.archive / "objects" / sha[:2] / sha
        require(
            path.is_file()
            and not any(parent.is_symlink() for parent in (path, *path.parents))
            and type(pin["bytes"]) is int
            and 0 < pin["bytes"] <= 131072
            and path.stat().st_size == pin["bytes"],
            "Original bounded scoring object required",
        )
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == sha, "Scoring source changed")
        return decode(raw)

    def read(self, target: str) -> dict[str, int]:
        """Decode an exact original source owner only once in its scoring role."""
        require(
            target in self.selected and target not in self.seen,
            "Scoring target is unselected or already accessed",
        )
        reference, geometry_reference = self.refs[target], self.geometry_refs[target]
        value, geometry = self._read(reference), self._read(geometry_reference)
        require(
            type(value) is dict
            and type(geometry) is dict
            and set(value) == {"data_kind", "taxa", "sample"}
            and type(value["sample"]) is dict
            and geometry.get("sample_metadata") == self.expected_metadata[target],
            "Original target geometry and observation object required",
        )
        metadata, sample = geometry["sample_metadata"], value["sample"]
        require(
            set(value) == {"data_kind", "taxa", "sample"}
            and value["data_kind"] == "source_observations"
            and value["taxa"] == self.taxa
            and set(sample) == set(metadata) | {"counts"}
            and all(sample[key] == item for key, item in metadata.items())
            and metadata["bin_id"] == "author-TW5"
            and metadata["age_type"] == "calendar_bp"
            and metadata["age_support_bp"] == [[1250, 1750]]
            and type(sample["counts"]) is list
            and len(sample["counts"]) == len(self.taxa)
            and all(type(n) is int and n >= 0 for n in sample["counts"])
            and 0 < sum(sample["counts"]) <= 2**53,
            "Exact observation identity, support, axis and integer N required",
        )
        self.seen.add(target)
        self.accesses.append(
            {
                "target": target,
                "role": "outer_scoring_after_prediction_readback",
                "observation_reference": reference,
                "geometry_reference": geometry_reference,
                "prediction_freeze_sha256": self.freeze,
                "scope": "previously_exposed_role_specific_access_not_globally_unread",
            }
        )
        return dict(zip(self.taxa, sample["counts"], strict=True))
