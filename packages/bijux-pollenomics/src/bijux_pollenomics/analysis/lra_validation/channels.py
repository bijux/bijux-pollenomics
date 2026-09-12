"""Admit explicitly observed pollen channels without changing an outer fold.

Ownership is not a quantitative dependency edge. Callers retain both, and bind
pollen-only source bytes before reading. This module validates the declared
catalogue and dependency closure; it does not authenticate source contents.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import NoReturn

from .contracts import Fold, ValidationRefusal, identity_values, required_identity
from .splits import _input_closure

__all__ = [
    "ObservationChannels",
    "ObservedPollenAdmission",
    "PollenChannel",
    "assert_channel_inputs",
]


def _refuse(message: str) -> NoReturn:
    raise ValidationRefusal("invalid_observation_channels", message)


@dataclass(frozen=True)
class PollenChannel:
    """A quantitative pollen source identity and its exact byte digest."""

    input_id: str
    source_sha256: str

    def __post_init__(self) -> None:
        required_identity(self.input_id)
        if (
            not isinstance(self.source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.source_sha256) is None
        ):
            _refuse("Pollen source requires a lowercase SHA256 byte digest")


def _pollen(values: tuple[PollenChannel, ...]) -> tuple[PollenChannel, ...]:
    if (
        not isinstance(values, tuple)
        or not values
        or any(not isinstance(value, PollenChannel) for value in values)
    ):
        _refuse("Pollen channels must be a nonempty typed tuple")
    if len(values) != len({value.input_id for value in values}):
        _refuse("Duplicate pollen channel identity")
    return tuple(sorted(values, key=lambda value: value.input_id))


@dataclass(frozen=True)
class ObservationChannels:
    """Structural record/group ownership, independent of quantitative edges."""

    record_id: str
    group_id: str
    pollen_channels: tuple[PollenChannel, ...]
    vegetation_input_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        required_identity(self.record_id)
        required_identity(self.group_id)
        object.__setattr__(self, "pollen_channels", _pollen(self.pollen_channels))
        vegetation = identity_values(self.vegetation_input_ids)
        if not vegetation or len(vegetation) != len(set(vegetation)):
            _refuse("Vegetation channels require nonempty unique identities")
        object.__setattr__(self, "vegetation_input_ids", tuple(sorted(vegetation)))


@dataclass(frozen=True)
class ObservedPollenAdmission:
    """Exactly the target-group pollen channels intentionally observed."""

    record_id: str
    group_id: str
    pollen_channels: tuple[PollenChannel, ...]

    def __post_init__(self) -> None:
        required_identity(self.record_id)
        required_identity(self.group_id)
        object.__setattr__(self, "pollen_channels", _pollen(self.pollen_channels))


def _catalogue(
    fold: Fold, channels: tuple[ObservationChannels, ...]
) -> tuple[dict[str, ObservationChannels], dict[str, tuple[str, str]], dict[str, str]]:
    if (
        not isinstance(channels, tuple)
        or not channels
        or any(not isinstance(item, ObservationChannels) for item in channels)
    ):
        _refuse("Complete typed ownership catalogue required")
    by_record = {item.record_id: item for item in channels}
    records = set(fold.train_record_ids) | set(fold.test_record_ids)
    if len(by_record) != len(channels) or set(by_record) != records:
        _refuse("Catalogue must name every original fold record exactly once")
    train_groups = {by_record[key].group_id for key in fold.train_record_ids}
    test_groups = {by_record[key].group_id for key in fold.test_record_ids}
    if (
        train_groups != set(fold.train_group_ids)
        or test_groups != set(fold.test_group_ids)
        or train_groups & test_groups
    ):
        _refuse("Catalogue and original fold group memberships disagree")
    pollen: dict[str, tuple[str, str]] = {}
    vegetation: dict[str, str] = {}
    for item in channels:
        for channel in item.pollen_channels:
            entry = (item.group_id, channel.source_sha256)
            if channel.input_id in pollen and pollen[channel.input_id] != entry:
                _refuse("Pollen alias crosses groups or has conflicting source bytes")
            pollen[channel.input_id] = entry
        for key in item.vegetation_input_ids:
            if key in vegetation and vegetation[key] != item.group_id:
                _refuse("Vegetation alias crosses independent groups")
            vegetation[key] = item.group_id
    if set(pollen) & set(vegetation) or (set(pollen) | set(vegetation)) & records:
        _refuse("Channel IDs cannot collide with record owners or other channels")
    return by_record, pollen, vegetation


def assert_channel_inputs(
    fold: Fold,
    input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    *,
    channels: tuple[ObservationChannels, ...],
    observed_pollen: ObservedPollenAdmission | None = None,
    admitted_external_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    """Validate unchanged quantitative edges against complete channel ownership.

    Every held-out owner remains forbidden, including an owner appearing as an
    actual parent of an otherwise admitted pollen channel. All held-out
    vegetation and other target pollen remain forbidden despite external labels.
    Every explicitly admitted pollen channel must occur in the returned closure.
    """
    inputs = tuple(sorted(set(identity_values(input_ids))))
    if not inputs:
        raise ValidationRefusal(
            "missing_fit_inputs", "Fit input identities cannot be empty"
        )
    catalogue, pollen, vegetation = _catalogue(fold, channels)
    external = set(identity_values(admitted_external_ids))
    train = set(fold.train_group_ids)
    test = set(fold.test_group_ids)
    allowed = set(fold.train_record_ids) | external
    allowed.update(key for key, (group, _) in pollen.items() if group in train)
    allowed.update(key for key, group in vegetation.items() if group in train)
    forbidden = set(fold.test_record_ids)
    forbidden.update(key for key, (group, _) in pollen.items() if group in test)
    forbidden.update(key for key, group in vegetation.items() if group in test)
    admitted: set[str] = set()
    if observed_pollen is not None:
        owner = catalogue.get(observed_pollen.record_id)
        if (
            owner is None
            or owner.record_id not in fold.test_record_ids
            or owner.group_id != observed_pollen.group_id
        ):
            _refuse("Observed pollen must name an actual target record and group")
        owner_channels = {
            channel.input_id: channel for channel in owner.pollen_channels
        }
        for channel in observed_pollen.pollen_channels:
            if pollen.get(channel.input_id) != (owner.group_id, channel.source_sha256):
                _refuse("Observed pollen digest or target-group ownership mismatch")
            admitted.add(channel.input_id)
        if not admitted & set(owner_channels):
            _refuse("Admission must consume a channel owned by the named target record")
        allowed.update(admitted)
        forbidden.difference_update(admitted)
    closure = _input_closure(
        inputs, dependency_graph, allowed=allowed, forbidden=forbidden
    )
    if not admitted <= set(closure):
        _refuse(
            "Explicit observed pollen admission is absent from the consumed closure"
        )
    return closure
