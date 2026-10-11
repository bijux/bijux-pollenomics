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


def site_group_id(record_ids: Iterable[str]) -> str:
    """Bind a complete physical group's sorted member IDs to the split authority."""
    members = identity_values(record_ids)
    if not members or len(set(members)) != len(members):
        raise ValidationRefusal(
            "invalid_site_group", "Group members must be nonempty and unique"
        )
    return "site-group:" + manifest_sha256(sorted(members))


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


@dataclass(frozen=True)
class TrainingAdmission:
    """Explicit whole-group training subpartition; the original outer Fold is retained.

    Record/group ownership is outcome-free declared identity, not a quantitative
    source edge. The criterion is a canonical, hash-bound receipt; the caller
    must establish that its domain-specific decisions satisfy that criterion.
    """

    fold: Fold
    record_groups: tuple[tuple[str, str], ...]
    admitted_group_ids: tuple[str, ...]
    criterion_json: str

    def __post_init__(self) -> None:
        self.validate(self.fold)
        object.__setattr__(self, "record_groups", tuple(sorted(self.record_groups)))
        object.__setattr__(
            self, "admitted_group_ids", tuple(sorted(self.admitted_group_ids))
        )

    def validate(self, fold: Fold) -> None:
        """Recheck exact ownership and whole-group partitions, including replaced state."""
        if not isinstance(self.fold, Fold) or self.fold != fold:
            raise ValidationRefusal(
                "training_admission_fold_mismatch", "Original Fold differs"
            )
        if not isinstance(self.record_groups, tuple) or any(
            not isinstance(pair, tuple) or len(pair) != 2 for pair in self.record_groups
        ):
            raise ValidationRefusal(
                "invalid_training_admission", "Require explicit record/group pairs"
            )
        ownership = {
            required_identity(record): required_identity(group)
            for record, group in self.record_groups
        }
        if len(ownership) != len(self.record_groups) or set(ownership) != {
            *fold.train_record_ids,
            *fold.test_record_ids,
        }:
            raise ValidationRefusal(
                "training_admission_membership_mismatch",
                "Complete unique original record ownership is required",
            )
        if {ownership[key] for key in fold.train_record_ids} != set(
            fold.train_group_ids
        ) or {ownership[key] for key in fold.test_record_ids} != set(
            fold.test_group_ids
        ):
            raise ValidationRefusal(
                "training_admission_membership_mismatch",
                "Original whole-group ownership differs",
            )
        for group in {*fold.train_group_ids, *fold.test_group_ids}:
            members = tuple(
                record for record, owner in ownership.items() if owner == group
            )
            if site_group_id(members) != group:
                raise ValidationRefusal(
                    "training_admission_membership_mismatch",
                    "Original group identity does not match its complete record membership",
                )
        admitted = identity_values(self.admitted_group_ids)
        if (
            not admitted
            or len(set(admitted)) != len(admitted)
            or not set(admitted).issubset(fold.train_group_ids)
        ):
            raise ValidationRefusal(
                "invalid_training_admission",
                "Admit nonempty unique original training groups",
            )
        try:
            criterion = json.loads(self.criterion_json)
            if (
                not isinstance(criterion, dict)
                or canonical_json(criterion) != self.criterion_json
            ):
                raise ValueError("Criterion must be a canonical JSON object")
            profile = criterion.get("profile")
            if not isinstance(profile, str):
                raise ValueError("Criterion profile must be an exact identity")
            required_identity(profile)
        except (ValueError, TypeError) as exc:
            raise ValidationRefusal("invalid_training_criterion", str(exc)) from exc

    @property
    def admitted_record_ids(self) -> tuple[str, ...]:
        """Every record in each admitted physical group, with no alias selection."""
        return tuple(
            sorted(
                record
                for record, group in self.record_groups
                if group in self.admitted_group_ids
            )
        )

    @property
    def excluded_group_ids(self) -> tuple[str, ...]:
        """Excluded training groups stay distinct from the original test partition."""
        return tuple(
            sorted(set(self.fold.train_group_ids) - set(self.admitted_group_ids))
        )

    @property
    def excluded_record_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(set(self.fold.train_record_ids) - set(self.admitted_record_ids))
        )

    def as_dict(self) -> dict[str, object]:
        """Bind the original Fold, all admitted/excluded ownership and the criterion."""
        self.validate(self.fold)
        criterion = json.loads(self.criterion_json)
        return {
            "schema_version": "lra-training-admission.v1",
            "original_fold": self.fold.as_dict(),
            "original_fold_sha256": manifest_sha256(self.fold.as_dict()),
            "record_groups": dict(self.record_groups),
            "admitted_training_group_ids": self.admitted_group_ids,
            "admitted_training_record_ids": self.admitted_record_ids,
            "excluded_training_group_ids": self.excluded_group_ids,
            "excluded_training_record_ids": self.excluded_record_ids,
            "criterion": criterion,
            "criterion_sha256": manifest_sha256(criterion),
        }
