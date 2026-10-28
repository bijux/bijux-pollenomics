"""Open original scoring-role counts only after new prediction authentication."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.inputs import decode

from .geometry import require


class ObservationReader:
    """Keep raw target counts out of the cached-fit numerical candidate."""

    def __init__(
        self,
        repository: Path,
        packet: dict[str, Any],
        admission: dict[str, Any],
        prediction_freeze_sha256: str,
    ) -> None:
        require(
            re.fullmatch(r"[a-f0-9]{64}", prediction_freeze_sha256) is not None,
            "Authenticated new prediction freeze identity required",
        )
        self.repository = repository.resolve(strict=True)
        self.axis = packet["axis"]
        self.refs = {row["target_id"]: row for row in packet["observation_refs"]}
        self.allowed = {
            row["target_id"]
            for row in admission["roles"]
            if row["status"] == "admitted"
        }
        self.freeze = prediction_freeze_sha256
        self.accesses: list[dict[str, Any]] = []

    def _read(self, pin: dict[str, Any]) -> Any:
        relative = Path(pin["path"])
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "Repository-relative observation reference required",
        )
        path = self.repository / relative
        require(
            path.is_file()
            and not any(part.is_symlink() for part in (path, *path.parents)),
            "Ordinary original observation required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"],
            "Original scoring object changed",
        )
        return decode(raw)

    def read(self, target_id: str) -> dict[str, int]:
        """Use only an admitted target's same-bin, same-axis source observation."""
        require(
            target_id in self.allowed,
            "A geographically refused target cannot be scored",
        )
        require(
            not any(row["target_id"] == target_id for row in self.accesses),
            "One scoring-role observation access per admitted target required",
        )
        ref = self.refs[target_id]
        geometry = self._read(ref["geometry"])
        raw = self._read(ref["raw"])
        require(
            set(raw) == {"data_kind", "taxa", "sample"}
            and raw["data_kind"] == "source_observations"
            and raw["taxa"] == self.axis,
            "Source scoring type and taxon axis differ",
        )
        sample, metadata = raw["sample"], geometry["sample_metadata"]
        require(
            set(sample) == set(metadata) | {"counts"}
            and all(sample[key] == expected for key, expected in metadata.items()),
            "Source scoring owner, support or chronology differ",
        )
        require(
            sample["sample_id"] == target_id
            and sample["bin_id"] == "cal-bp-2700-3200"
            and sample["age_type"] == "calendar_bp"
            and sample["age_support_bp"] == [[2700, 3200]],
            "Original same-owner calendar-bin scoring support required",
        )
        values = sample["counts"]
        require(
            type(values) is list
            and len(values) == len(self.axis)
            and all(type(value) is int and value >= 0 for value in values)
            and 0 < sum(values) <= 2**53,
            "Positive integer source denominator required",
        )
        self.accesses.append(
            {
                "target_id": target_id,
                "role": "scoring_after_new_prediction_readback",
                "prediction_freeze_sha256": self.freeze,
                "raw_reference": ref["raw"],
                "scope": "previously_exposed_role_specific_access_not_globally_unread",
            }
        )
        return dict(zip(self.axis, values, strict=True))
