"""Immutable supplied joint atoms; their physical law needs separate admission."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import re

from ....lra.engine.errors import LRARefusal
from ....lra.uncertainty.contracts import NUMERICAL_REASONS
from ....lra.uncertainty.contracts import mass as joint_mass
from ...contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
    required_identity,
)
from ...prediction import ForwardInputs
from ..configuration import SiteCoordinate

UPSTREAM_SOURCES = frozenset(
    {
        "training_count",
        "ppe",
        "chronology",
        "training_geometry",
        "forward_geometry",
        "regional_reconstruction",
        "local_reconstruction",
    }
)
CONDITIONED_SOURCES = frozenset(
    {
        "target_coordinate",
        "spatial_residual_process",
        "observation_process",
        "hyperparameter_selection",
        "taxon_model",
    }
)


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValidationRefusal("invalid_spatial_draw_plan", detail)


def sha256(value: str) -> str:
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        "Exact source SHA-256 required",
    )
    return value


@dataclass(frozen=True)
class JointSpatialDraw:
    """One coupled training/forward projection, never independently shuffled axes.

    Tuples prevent mutation after construction. ``source_evidence_sha256`` is a
    supplied upstream identity, not an assertion that its scientific law passed
    review. A producer must authenticate that evidence before constructing atoms.
    """

    draw_id: str
    mass: Fraction
    source_evidence_sha256: str
    compositions: tuple[tuple[str, tuple[tuple[str, float], ...]], ...]
    coordinates: tuple[tuple[str, SiteCoordinate], ...]
    forward: ForwardInputs
    input_ids: tuple[str, ...]
    input_lineage: tuple[tuple[str, tuple[str, ...]], ...]
    admitted_external_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        required_identity(self.draw_id)
        sha256(self.source_evidence_sha256)
        require(
            type(self.mass) is Fraction and 0 < self.mass <= 1,
            "Exact positive rational mass required",
        )
        require(
            isinstance(self.forward, ForwardInputs), "Typed forward context required"
        )
        try:
            joint_mass(
                {"numerator": self.mass.numerator, "denominator": self.mass.denominator}
            )
        except LRARefusal as exc:
            raise ValidationRefusal("invalid_spatial_draw_plan", str(exc)) from exc
        for entries in (self.compositions, self.coordinates, self.input_lineage):
            require(
                type(entries) is tuple and bool(entries),
                "Immutable nonempty named axis required",
            )
            require(
                all(type(item) is tuple and len(item) == 2 for item in entries),
                "Named axis pairs required",
            )
            keys = tuple(item[0] for item in entries)
            require(
                keys == tuple(sorted(set(keys))), "Named axis must be sorted and unique"
            )
            for key in keys:
                required_identity(key)
        for _, values in self.compositions:
            require(
                type(values) is tuple and bool(values), "Immutable taxon axis required"
            )
            require(
                all(type(row) is tuple and len(row) == 2 for row in values),
                "Taxon/value pairs required",
            )
            require(
                tuple(row[0] for row in values) == self.forward.taxa,
                "Exact forward taxon order required",
            )
        for _, point in self.coordinates:
            require(
                isinstance(point, SiteCoordinate), "Typed training coordinates required"
            )
        for identities in (
            self.input_ids,
            self.admitted_external_ids,
            *(row[1] for row in self.input_lineage),
        ):
            require(
                type(identities) is tuple, "Immutable lineage identity axis required"
            )
            require(
                len(identities) == len(set(identities)), "Duplicate lineage identities"
            )
            for identity_value in identities:
                required_identity(identity_value)
        # Refuse nonfinite/nonserializable payloads before any fit or callback.
        canonical_json(self.as_dict())

    def as_dict(self) -> dict[str, object]:
        return {
            "draw_id": self.draw_id,
            "mass": {
                "numerator": self.mass.numerator,
                "denominator": self.mass.denominator,
            },
            "source_evidence_sha256": self.source_evidence_sha256,
            "training_compositions": dict(self.compositions),
            "training_coordinates": {
                key: value.as_dict() for key, value in self.coordinates
            },
            "forward_inputs": self.forward.as_dict(),
            "input_ids": self.input_ids,
            "input_lineage": dict(self.input_lineage),
            "admitted_external_ids": self.admitted_external_ids,
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())


@dataclass(frozen=True)
class UnavailableSpatialDraw:
    """An original upstream refusal/interruption, without invented numerical data.

    The source row is preserved, including its allocation-bin identity and cause.
    Mapping that bin to the declared target support requires upstream scientific
    admission, just as projection of a successful upstream reconstruction does.
    """

    source_row_json: str
    source_evidence_sha256: str
    temporal_support_id: str
    input_ids: tuple[str, ...]
    input_lineage: tuple[tuple[str, tuple[str, ...]], ...]
    admitted_external_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        sha256(self.source_evidence_sha256)
        require(
            type(self.source_row_json) is str, "Exact serialized upstream row required"
        )
        required_identity(self.temporal_support_id)
        try:
            row = json.loads(self.source_row_json)
            require(type(row) is dict, "Upstream row must be a serialized object")
            required_identity(row["draw_id"])
            required_identity(row["bin_id"])
            joint_mass(row["mass"])
            status, reason = row["status"], row["reason_code"]
            require(
                (
                    status == "refused"
                    and reason
                    in {
                        "missing_role_in_bin",
                        "ambiguous_role_in_bin",
                        "nonfinite_child_cover",
                        "numerical_refusal",
                    }
                )
                or (status == "not_run" and reason == "interrupted"),
                "Require an original known upstream refusal or interruption",
            )
            if reason == "numerical_refusal":
                error = row["error"]
                require(
                    type(error) is dict
                    and error["status"] == "refused"
                    and error["reason_code"] in NUMERICAL_REASONS
                    and type(error["detail"]) is str,
                    "Preserve the original typed numerical refusal envelope",
                )
            canonical_json(row)
        except (KeyError, TypeError, ValueError, LRARefusal) as exc:
            if isinstance(exc, ValidationRefusal):
                raise
            raise ValidationRefusal("invalid_spatial_draw_plan", str(exc)) from exc
        require(
            type(self.input_lineage) is tuple and bool(self.input_lineage),
            "Immutable complete upstream lineage required",
        )
        require(
            all(type(pair) is tuple and len(pair) == 2 for pair in self.input_lineage),
            "Lineage pairs required",
        )
        keys = tuple(key for key, _ in self.input_lineage)
        require(
            keys == tuple(sorted(set(keys))), "Sorted unique upstream lineage required"
        )
        for identities in (
            self.input_ids,
            self.admitted_external_ids,
            keys,
            *(parents for _, parents in self.input_lineage),
        ):
            require(
                type(identities) is tuple and len(identities) == len(set(identities)),
                "Immutable unique upstream lineage identities required",
            )
            for identity in identities:
                required_identity(identity)

    @property
    def draw_id(self) -> str:
        return str(json.loads(self.source_row_json)["draw_id"])

    @property
    def mass(self) -> Fraction:
        return joint_mass(json.loads(self.source_row_json)["mass"])

    def as_dict(self) -> dict[str, object]:
        return {
            "source_row": json.loads(self.source_row_json),
            "source_evidence_sha256": self.source_evidence_sha256,
            "temporal_support_id": self.temporal_support_id,
            "input_ids": self.input_ids,
            "input_lineage": dict(self.input_lineage),
            "admitted_external_ids": self.admitted_external_ids,
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())
