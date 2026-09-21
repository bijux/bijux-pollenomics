"""Owned regional-cover draws selected from a governed multi-site result."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
import re

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.provenance.identity import sha256_object


_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class RegionalCoverDrawSource:
    """One named BP bin and its immutable, ordered fraction-valued draws.

    File digests are literal custody claims. The host must verify the parent
    bundle and draw member before constructing this object.
    """

    values: np.ndarray
    taxon_ids: tuple[str, ...]
    bin_id: str
    younger_bp: float
    older_bp: float
    draw_ids: tuple[int, ...]
    regional_site_ids: tuple[str, ...]
    eligible_site_ids: tuple[str, ...]
    parent_manifest_sha256: str
    draw_member_sha256: str
    selected_tensor_sha256: str
    diagnostic_prefix: bool = False

    def __post_init__(self) -> None:
        """Refuse ambiguous axes, invalid fractions or unverifiable digests."""
        for name in ("taxon_ids", "regional_site_ids", "eligible_site_ids"):
            value = tuple(getattr(self, name))
            if not value or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValidationError(f"{name} requires nonempty string identifiers")
            if len(value) != len(set(value)):
                raise ValidationError(f"{name} contains duplicate identifiers")
            object.__setattr__(self, name, value)
        if not isinstance(self.bin_id, str) or not self.bin_id.strip():
            raise ValidationError("bin_id is required")
        if any(
            isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            for value in (self.younger_bp, self.older_bp)
        ) or not (
            np.isfinite(self.younger_bp)
            and np.isfinite(self.older_bp)
            and self.younger_bp < self.older_bp
        ):
            raise ValidationError("BP bin requires finite younger < older")
        if not set(self.eligible_site_ids).issubset(self.regional_site_ids):
            raise ValidationError(
                "Eligible sites must belong to the original site axis"
            )
        if len(self.eligible_site_ids) < 2:
            raise ValidationError(
                "Regional draw source requires multiple eligible sites"
            )
        if (
            tuple(
                item
                for item in self.regional_site_ids
                if item in self.eligible_site_ids
            )
            != self.eligible_site_ids
        ):
            raise ValidationError("Eligible sites must retain original site order")
        if any(
            not isinstance(item, str) or not _DIGEST.fullmatch(item)
            for item in (
                self.parent_manifest_sha256,
                self.draw_member_sha256,
                self.selected_tensor_sha256,
            )
        ):
            raise ValidationError("Regional draw source requires SHA-256 digests")
        original = np.asarray(self.values)
        if original.dtype.kind not in "iuf" or original.ndim != 2:
            raise ValidationError("Regional draws must be a numeric [draw,taxon] array")
        values = np.array(original, dtype=np.float64, copy=True)
        count = values.shape[0]
        if values.shape[1] != len(self.taxon_ids) or count < 1:
            raise ValidationError("Regional draw axes do not match taxon identities")
        if not isinstance(self.diagnostic_prefix, bool):
            raise ValidationError("diagnostic_prefix must be boolean")
        if not self.diagnostic_prefix and count != 1000:
            raise ValidationError("Publication profile requires exactly 1000 draws")
        ids = tuple(self.draw_ids)
        if any(type(item) is not int for item in ids) or ids != tuple(range(count)):
            raise ValidationError(
                "Regional draw IDs must be consecutive and zero based"
            )
        if (
            not np.isfinite(values).all()
            or np.any(values < 0)
            or np.any(values > 1)
            or not np.allclose(values.sum(axis=1), 1, rtol=0, atol=1e-12)
        ):
            raise ValidationError("Regional draws must be closed finite fractions")
        if sha256_object(values) != self.selected_tensor_sha256:
            raise ValidationError("Selected regional tensor digest differs")
        # An owning ndarray can have WRITEABLE switched back on by a caller.
        # A bytes-backed view keeps the verified tensor immutable afterwards.
        sealed = np.frombuffer(values.tobytes(order="C"), dtype=np.float64).reshape(
            values.shape
        )
        object.__setattr__(self, "values", sealed)
        object.__setattr__(self, "draw_ids", ids)

    def as_provenance(self) -> dict[str, object]:
        """Expose literal source hashes and ordered axes for a run manifest."""
        source = {
            "bin_id": self.bin_id,
            "bin_age_type": "calendar_bp",
            "younger_bp": self.younger_bp,
            "older_bp": self.older_bp,
            "taxon_ids": list(self.taxon_ids),
            "draw_ids": list(self.draw_ids),
            "regional_site_ids": list(self.regional_site_ids),
            "eligible_site_ids": list(self.eligible_site_ids),
            "parent_manifest_sha256": self.parent_manifest_sha256,
            "draw_member_sha256": self.draw_member_sha256,
            "selected_tensor_sha256": self.selected_tensor_sha256,
            "diagnostic_prefix": self.diagnostic_prefix,
        }
        source["selected_source_sha256"] = sha256_object(
            {"axes_and_custody": source, "values": self.values}
        )
        return source
