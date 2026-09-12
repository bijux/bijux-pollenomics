"""Small immutable contracts for independently held-out LRA observations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import json
from math import isfinite


class ValidationRefusal(ValueError):
    """An observable refusal with a stable machine-readable reason."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def required_identity(value: str) -> str:
    """Require an exact nonblank identifier without silently rewriting it."""
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValidationRefusal(
            "invalid_identity", "Identity must be nonblank and trimmed"
        )
    return value


def finite_number(value: object) -> float:
    """Refuse booleans, missing data, infinities and NaNs as measurements."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationRefusal(
            "invalid_number", "Expected a finite numeric measurement"
        )
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValidationRefusal(
            "invalid_number", "Measurement exceeds binary64 range"
        ) from exc
    if not isfinite(number):
        raise ValidationRefusal(
            "invalid_number", "Expected a finite numeric measurement"
        )
    return number


def identity_values(values: Iterable[str]) -> tuple[str, ...]:
    """Require an explicit identity collection; one string is not a list of IDs."""
    if isinstance(values, (str, bytes)):
        raise ValidationRefusal(
            "invalid_identity_collection", "Identity lists must not be a bare string"
        )
    try:
        return tuple(required_identity(value) for value in values)
    except TypeError as exc:
        raise ValidationRefusal(
            "invalid_identity_collection", "Expected an iterable identity collection"
        ) from exc


def canonical_json(payload: object) -> str:
    """Serialize deterministic evidence without nonstandard NaN/Infinity literals."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def manifest_sha256(payload: object) -> str:
    """Identify a canonical JSON input or split manifest."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SiteRecord:
    """An outcome-free record identity; aliases must come from a reviewed crosswalk.

    ``identity_keys`` are globally namespaced physical-site, core, duplicate-record,
    or shared observational-lineage keys. They are not display names or shared
    parameter-library identifiers. A source dependency graph is checked separately.
    This type cannot discover unrecorded aliases or certify the crosswalk's review.
    """

    record_id: str
    site_id: str
    identity_keys: tuple[str, ...] = ()
    block_id: str | None = None

    def __post_init__(self) -> None:
        required_identity(self.record_id)
        required_identity(self.site_id)
        keys = tuple(sorted(set(identity_values(self.identity_keys))))
        object.__setattr__(self, "identity_keys", keys)
        if self.block_id is not None:
            required_identity(self.block_id)


@dataclass(frozen=True)
class Fold:
    """An outer split over whole connected physical-site identity groups."""

    fold_id: str
    train_record_ids: tuple[str, ...]
    test_record_ids: tuple[str, ...]
    train_group_ids: tuple[str, ...]
    test_group_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        required_identity(self.fold_id)
        for field in (
            "train_record_ids",
            "test_record_ids",
            "train_group_ids",
            "test_group_ids",
        ):
            values = identity_values(getattr(self, field))
            normalized = tuple(sorted({required_identity(value) for value in values}))
            if not normalized or len(normalized) != len(values):
                raise ValidationRefusal(
                    "invalid_fold", "Fold partitions must be nonempty and unique"
                )
            object.__setattr__(self, field, normalized)
        if set(self.train_record_ids) & set(self.test_record_ids) or set(
            self.train_group_ids
        ) & set(self.test_group_ids):
            raise ValidationRefusal(
                "split_leakage", "Training and test identities overlap"
            )

    def as_dict(self) -> dict[str, object]:
        """Return an outcome-free deterministic manifest row."""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}
