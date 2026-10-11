"""Freeze the value-free observation read plan for the six-cell product."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Literal, cast

from ...contracts import canonical_json, manifest_sha256, required_identity
from ..contracts import digest, refuse
from ..prediction_product import SixCellPredictionProduct

OBSERVATION_ACCESS_PLAN_PROFILE = "pollenomics-observation-access-plan.v1"
MEASURED_VEGETATION_READER_PROFILE = "measured-vegetation-reader-v1"
HELDOUT_POLLEN_READER_PROFILE = "heldout-pollen-count-reader-v1"

ObservationKind = Literal["independent_measured_vegetation", "heldout_pollen_counts"]

_PLAN_KEYS = frozenset(
    {
        "schema_version",
        "prediction_product_sha256",
        "release_admission_sha256",
        "scope_sha256",
        "empirical_evaluation_performed",
        "scientific_acceptance",
        "outcome_values_present",
        "protocols",
        "sources",
        "assignments",
    }
)
_PROTOCOL_KEYS = frozenset({"protocol_id", "policy_sha256"})
_SOURCE_KEYS = frozenset(
    {
        "source_kind",
        "path",
        "expected_source_sha256",
        "reader_profile",
        "reader_code_sha256",
        "source_reference_id",
    }
)
_ASSIGNMENT_KEYS = frozenset(
    {
        "protocol_id",
        "cell_id",
        "fold_id",
        "record_id",
        "target",
        "observation_kind",
        "observation_id",
        "source_reference_id",
        "source_locator_sha256",
    }
)
_PLAN_FACTORY_TOKEN = object()


def _source_payload(
    *,
    kind: ObservationKind,
    path: Path,
    expected_source_sha256: str,
    reader_profile: str,
    reader_code_sha256: str,
    source_reference_id: str,
) -> dict[str, str]:
    if not isinstance(path, Path) or not path.is_absolute():
        refuse("Observation source locators require absolute typed paths")
    expected_profile = (
        MEASURED_VEGETATION_READER_PROFILE
        if kind == "independent_measured_vegetation"
        else HELDOUT_POLLEN_READER_PROFILE
    )
    if reader_profile != expected_profile:
        refuse("Observation source locator requires its fixed governed reader")
    return {
        "source_kind": kind,
        "path": str(path),
        "expected_source_sha256": digest(expected_source_sha256),
        "reader_profile": required_identity(reader_profile),
        "reader_code_sha256": digest(reader_code_sha256),
        "source_reference_id": required_identity(source_reference_id),
    }


@dataclass(frozen=True)
class MeasuredVegetationSourceLocator:
    """Planned measured-vegetation reader; construction never opens its path."""

    path: Path
    expected_source_sha256: str
    reader_profile: str
    reader_code_sha256: str
    source_reference_id: str

    def as_dict(self) -> dict[str, str]:
        return _source_payload(
            kind="independent_measured_vegetation",
            path=self.path,
            expected_source_sha256=self.expected_source_sha256,
            reader_profile=self.reader_profile,
            reader_code_sha256=self.reader_code_sha256,
            source_reference_id=self.source_reference_id,
        )


@dataclass(frozen=True)
class HeldoutPollenSourceLocator:
    """Planned held-out count reader; construction never opens its path."""

    path: Path
    expected_source_sha256: str
    reader_profile: str
    reader_code_sha256: str
    source_reference_id: str

    def as_dict(self) -> dict[str, str]:
        return _source_payload(
            kind="heldout_pollen_counts",
            path=self.path,
            expected_source_sha256=self.expected_source_sha256,
            reader_profile=self.reader_profile,
            reader_code_sha256=self.reader_code_sha256,
            source_reference_id=self.source_reference_id,
        )


@dataclass(frozen=True)
class ObservationSourceLocators:
    """The exact two source kinds that later readers may open."""

    vegetation: MeasuredVegetationSourceLocator
    pollen: HeldoutPollenSourceLocator

    def __post_init__(self) -> None:
        if not isinstance(
            self.vegetation, MeasuredVegetationSourceLocator
        ) or not isinstance(self.pollen, HeldoutPollenSourceLocator):
            refuse("Observation access requires typed target-specific source locators")
        vegetation = self.vegetation.as_dict()
        pollen = self.pollen.as_dict()
        if (
            vegetation["path"] == pollen["path"]
            or vegetation["source_reference_id"] == pollen["source_reference_id"]
        ):
            refuse("Vegetation and pollen source locators must remain distinct")

    def as_dict(self) -> dict[str, dict[str, str]]:
        return {
            "independent_measured_vegetation": self.vegetation.as_dict(),
            "heldout_pollen_counts": self.pollen.as_dict(),
        }


@dataclass(frozen=True)
class ObservationAssignment:
    """One model-independent target assignment; it contains no observation value."""

    protocol_id: str
    cell_id: str
    fold_id: str
    record_id: str
    target: str
    observation_kind: ObservationKind
    observation_id: str
    source_reference_id: str
    source_locator_sha256: str

    def __post_init__(self) -> None:
        for value in (
            self.protocol_id,
            self.cell_id,
            self.fold_id,
            self.record_id,
            self.target,
            self.observation_id,
            self.source_reference_id,
        ):
            required_identity(value)
        if self.observation_kind not in {
            "independent_measured_vegetation",
            "heldout_pollen_counts",
        }:
            refuse("Unsupported observation assignment kind")
        digest(self.source_locator_sha256)


def _protocol_payloads(
    product: SixCellPredictionProduct,
) -> list[dict[str, str]]:
    return [
        {
            "protocol_id": protocol.protocol_id,
            "policy_sha256": protocol.policy.policy_sha256,
        }
        for protocol in product.protocols
    ]


def _derive_assignments(
    product: SixCellPredictionProduct,
    sources: ObservationSourceLocators,
) -> tuple[ObservationAssignment, ...]:
    try:
        product_payload = json.loads(product.canonical_product_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed parent prediction product: {exc}")
    if not isinstance(product_payload, dict):
        refuse("Prediction product receipt must be an object")
    protocols_value = product_payload.get("protocols")
    if not isinstance(protocols_value, list):
        refuse("Prediction product protocol denominator is missing")
    typed = {protocol.protocol_id: protocol for protocol in product.protocols}
    source_payloads = sources.as_dict()
    source_hashes = {
        kind: manifest_sha256(payload) for kind, payload in source_payloads.items()
    }
    result: list[ObservationAssignment] = []
    for protocol_value in protocols_value:
        if not isinstance(protocol_value, dict):
            refuse("Prediction product protocol receipt is malformed")
        protocol_id = protocol_value.get("protocol_id")
        if not isinstance(protocol_id, str) or protocol_id not in typed:
            refuse("Prediction product protocol identity is unsupported")
        protocol = typed[protocol_id]
        sites = {site.record_id: site for site in protocol.scope.sites}
        cells = protocol_value.get("cells")
        if not isinstance(cells, list):
            refuse("Prediction product cell denominator is missing")
        for cell in cells:
            if not isinstance(cell, dict):
                refuse("Prediction product cell receipt is malformed")
            target = cell.get("target")
            experiment = cell.get("experiment")
            cell_id = cell.get("cell_id")
            cell_units = cell.get("units")
            if (
                not isinstance(target, str)
                or not isinstance(experiment, str)
                or not isinstance(cell_id, str)
                or not isinstance(cell_units, list)
            ):
                refuse("Prediction product cell identities are malformed")
            locator: MeasuredVegetationSourceLocator | HeldoutPollenSourceLocator
            if target == "vegetation_cover":
                kind: ObservationKind = "independent_measured_vegetation"
                locator = sources.vegetation
            elif (
                target == "pollen_composition"
                and experiment == "all_target_pollen_withheld"
            ):
                kind = "heldout_pollen_counts"
                locator = sources.pollen
            else:
                refuse("Observation access cannot attach this experiment target")
            for unit in cell_units:
                if (
                    not isinstance(unit, list)
                    or len(unit) != 2
                    or any(not isinstance(value, str) for value in unit)
                ):
                    refuse("Prediction product outcome unit is malformed")
                fold_id, record_id = unit
                site = sites.get(record_id)
                if site is None:
                    refuse("Observation assignment target is absent from scope")
                observation_id = (
                    site.vegetation_observation_id
                    if target == "vegetation_cover"
                    else site.pollen_observation_id
                )
                result.append(
                    ObservationAssignment(
                        protocol_id,
                        cell_id,
                        fold_id,
                        record_id,
                        target,
                        kind,
                        observation_id,
                        locator.source_reference_id,
                        source_hashes[kind],
                    )
                )
    ordered = tuple(
        sorted(
            result,
            key=lambda value: (
                value.protocol_id,
                value.cell_id,
                value.fold_id,
                value.record_id,
            ),
        )
    )
    keys = {
        (value.protocol_id, value.cell_id, value.fold_id, value.record_id)
        for value in ordered
    }
    if len(keys) != len(ordered):
        refuse("Observation assignments are duplicated")
    return ordered


def _validate_plan_payload(
    payload: dict[str, object],
    *,
    product: SixCellPredictionProduct,
    sources: ObservationSourceLocators,
    assignments: tuple[ObservationAssignment, ...],
) -> None:
    if frozenset(payload) != _PLAN_KEYS or (
        payload.get("schema_version") != OBSERVATION_ACCESS_PLAN_PROFILE
        or payload.get("prediction_product_sha256") != product.product_sha256
        or payload.get("release_admission_sha256") != product.release_admission_sha256
        or payload.get("scope_sha256") != product.scope_sha256
        or payload.get("empirical_evaluation_performed") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("outcome_values_present") is not False
    ):
        refuse("Observation access plan identity or claim boundary differs")
    protocols = payload.get("protocols")
    if not isinstance(protocols, list) or protocols != _protocol_payloads(product):
        refuse("Observation access plan protocol policies differ")
    if any(
        not isinstance(value, dict) or frozenset(value) != _PROTOCOL_KEYS
        for value in protocols
    ):
        refuse("Observation access protocol fields differ")
    if payload.get("sources") != sources.as_dict():
        refuse("Observation access source locators differ")
    values = payload.get("assignments")
    expected = [asdict(value) for value in assignments]
    if (
        not isinstance(values, list)
        or values != expected
        or any(
            not isinstance(value, dict) or frozenset(value) != _ASSIGNMENT_KEYS
            for value in values
        )
    ):
        refuse("Observation access assignment denominator differs")


@dataclass(frozen=True, init=False)
class ObservationAccessPlan:
    """Factory-only canonical plan that is frozen before source access."""

    canonical_plan_json: str
    plan_sha256: str
    prediction_product: SixCellPredictionProduct
    sources: ObservationSourceLocators
    assignments: tuple[ObservationAssignment, ...]

    def __init__(
        self,
        canonical_plan_json: str,
        plan_sha256: str,
        prediction_product: SixCellPredictionProduct,
        sources: ObservationSourceLocators,
        assignments: tuple[ObservationAssignment, ...],
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _PLAN_FACTORY_TOKEN:
            refuse("Observation access plans require the governed factory")
        object.__setattr__(self, "canonical_plan_json", canonical_plan_json)
        object.__setattr__(self, "plan_sha256", plan_sha256)
        object.__setattr__(self, "prediction_product", prediction_product)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "assignments", tuple(assignments))
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_product, SixCellPredictionProduct):
            refuse("Observation access requires an authenticated prediction product")
        if not isinstance(self.sources, ObservationSourceLocators):
            refuse("Observation access requires typed source locators")
        try:
            loaded = json.loads(self.canonical_plan_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed observation access plan: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != self.canonical_plan_json
            or manifest_sha256(loaded) != digest(self.plan_sha256)
        ):
            refuse("Observation access plan canonical bytes or identity differ")
        derived = _derive_assignments(self.prediction_product, self.sources)
        if derived != self.assignments:
            refuse("Observation assignments differ from the prediction product")
        _validate_plan_payload(
            cast(dict[str, object], loaded),
            product=self.prediction_product,
            sources=self.sources,
            assignments=self.assignments,
        )


def build_observation_access_plan(
    prediction_product: SixCellPredictionProduct,
    *,
    sources: ObservationSourceLocators,
) -> ObservationAccessPlan:
    """Derive the exact model-free assignment denominator without reading outcomes."""
    if not isinstance(prediction_product, SixCellPredictionProduct):
        refuse("Observation access requires an authenticated six-cell product")
    if not isinstance(sources, ObservationSourceLocators):
        refuse("Observation access requires the fixed typed source schema")
    vegetation_reference = sources.vegetation.source_reference_id
    if any(
        vegetation_reference not in protocol.policy.independent_vegetation_reference_ids
        for protocol in prediction_product.protocols
    ):
        refuse("Measured vegetation reference is absent from a protocol policy")
    assignments = _derive_assignments(prediction_product, sources)
    payload = {
        "schema_version": OBSERVATION_ACCESS_PLAN_PROFILE,
        "prediction_product_sha256": prediction_product.product_sha256,
        "release_admission_sha256": prediction_product.release_admission_sha256,
        "scope_sha256": prediction_product.scope_sha256,
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "outcome_values_present": False,
        "protocols": _protocol_payloads(prediction_product),
        "sources": sources.as_dict(),
        "assignments": [asdict(value) for value in assignments],
    }
    canonical = canonical_json(payload)
    return ObservationAccessPlan(
        canonical,
        manifest_sha256(payload),
        prediction_product,
        sources,
        assignments,
        _factory_token=_PLAN_FACTORY_TOKEN,
    )


def reopen_observation_access_plan(
    canonical_plan_json: str,
    plan_sha256: str,
    *,
    prediction_product: SixCellPredictionProduct,
    sources: ObservationSourceLocators,
) -> ObservationAccessPlan:
    """Reopen exact plan bytes against their authenticated parents."""
    assignments = _derive_assignments(prediction_product, sources)
    return ObservationAccessPlan(
        canonical_plan_json,
        plan_sha256,
        prediction_product,
        sources,
        assignments,
        _factory_token=_PLAN_FACTORY_TOKEN,
    )
