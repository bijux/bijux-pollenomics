"""Immutable inputs and receipts for explicitly scoped final evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
import json
import re
from typing import Literal, NoReturn, cast

from ..channels import ObservationChannels, ObservedPollenAdmission
from ..contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    finite_number,
    identity_values,
    manifest_sha256,
    required_identity,
)

Target = Literal["vegetation_cover", "pollen_composition"]
Experiment = Literal["local_pollen_available", "all_target_pollen_withheld"]
SourceModelKind = Literal[
    "fitted_spatial",
    "admitted_reconstruction_training_mean",
    "local_pollen_assimilation",
]
EnvelopeVersion = Literal[
    "pollenomics-evaluation-prediction.v1",
    "pollenomics-evaluation-prediction.v2",
]


def refuse(message: str) -> NoReturn:
    raise ValidationRefusal("invalid_final_evaluation", message)


def digest(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        refuse("A canonical SHA-256 identity is required")
    return value


@dataclass(frozen=True)
class Support:
    """Declared geographic/temporal support; radii and uncertainty use metres."""

    latitude: float
    longitude: float
    radius_m: float
    coordinate_uncertainty_m: float
    younger_bp: float
    older_bp: float
    footprint_sha256: str
    coordinate_crs: str
    age_type: str
    spatial_profile: str
    temporal_profile: str

    def __post_init__(self) -> None:
        for name in (
            "latitude",
            "longitude",
            "radius_m",
            "coordinate_uncertainty_m",
            "younger_bp",
            "older_bp",
        ):
            object.__setattr__(self, name, finite_number(getattr(self, name)))
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            refuse("Support coordinates must be WGS84 latitude/longitude")
        if (
            self.radius_m < 0
            or self.coordinate_uncertainty_m < 0
            or self.younger_bp > self.older_bp
        ):
            refuse("Support radii/uncertainties and typed BP interval are invalid")
        digest(self.footprint_sha256)
        if (
            self.coordinate_crs,
            self.age_type,
            self.spatial_profile,
            self.temporal_profile,
        ) != ("EPSG:4326", "BP", "bounded-footprint-radius-v1", "typed-bp-interval-v1"):
            refuse("Unsupported coordinate, age type or support profile")


@dataclass(frozen=True)
class EvaluationSite:
    """Outcome-independent site/bin and group membership fixed before access."""

    record_id: str
    site_id: str
    group_id: str
    block_id: str
    bin_id: str
    strata: tuple[str, ...]
    vegetation_observation_id: str
    pollen_observation_id: str
    support: Support | None

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "site_id",
            "group_id",
            "block_id",
            "bin_id",
            "vegetation_observation_id",
            "pollen_observation_id",
        ):
            required_identity(getattr(self, name))
        keys = identity_values(self.strata)
        if len(keys) != len(set(keys)):
            refuse("Duplicate site subgroup membership")
        object.__setattr__(self, "strata", tuple(sorted(keys)))
        if self.support is not None and not isinstance(self.support, Support):
            refuse("Site support must be typed or explicitly missing")


@dataclass(frozen=True)
class ExternalInput:
    """Declared external input role; declaration does not authenticate provenance."""

    input_id: str
    role: Literal[
        "observed_source",
        "fixed_parameter",
        "target_geometry",
        "training_derived_product",
    ]
    source_manifest_sha256: str
    support: Support | None

    def __post_init__(self) -> None:
        required_identity(self.input_id)
        digest(self.source_manifest_sha256)
        if self.role not in {
            "observed_source",
            "fixed_parameter",
            "target_geometry",
            "training_derived_product",
        }:
            refuse("Unsupported external input role")
        if self.role == "observed_source" and not isinstance(self.support, Support):
            refuse("Observed external sources require geographic and temporal support")


@dataclass(frozen=True)
class EvaluationScope:
    """The complete declared site universe, folds and source dependency graph."""

    scope_id: str
    sites: tuple[EvaluationSite, ...]
    folds: tuple[Fold, ...]
    dependency_graph: tuple[tuple[str, tuple[str, ...]], ...]
    taxa: tuple[str, ...]
    external_inputs: tuple[ExternalInput, ...] = ()
    observation_channels: tuple[ObservationChannels, ...] = ()

    def __post_init__(self) -> None:
        required_identity(self.scope_id)
        if not isinstance(self.observation_channels, tuple) or any(
            not isinstance(x, ObservationChannels) for x in self.observation_channels
        ):
            refuse("Observation ownership catalogue must be a typed tuple")
        taxa = identity_values(self.taxa)
        if not taxa or len(taxa) != len(set(taxa)):
            refuse("Scope requires a nonempty unique frozen taxon denominator")
        object.__setattr__(self, "taxa", tuple(sorted(taxa)))
        if (
            not isinstance(self.sites, tuple)
            or not self.sites
            or any(not isinstance(x, EvaluationSite) for x in self.sites)
        ):
            refuse("Scope requires typed sites")
        if (
            not isinstance(self.folds, tuple)
            or not self.folds
            or any(not isinstance(x, Fold) for x in self.folds)
        ):
            refuse("Scope requires typed folds")
        for values in (
            [x.record_id for x in self.sites],
            [x.fold_id for x in self.folds],
        ):
            if len(values) != len(set(values)):
                refuse("Scope record and fold identities must be unique")
        sites = {site.record_id: site for site in self.sites}
        for fold in self.folds:
            if set(fold.train_record_ids) | set(fold.test_record_ids) != set(sites):
                refuse("Each fold must partition the complete declared site universe")
            train = {sites[key].group_id for key in fold.train_record_ids}
            test = {sites[key].group_id for key in fold.test_record_ids}
            if (
                train & test
                or train != set(fold.train_group_ids)
                or test != set(fold.test_group_ids)
            ):
                refuse("Fold record and independent-group membership disagree")
        observation_ids = [
            key
            for site in self.sites
            for key in (site.vegetation_observation_id, site.pollen_observation_id)
        ]
        if len(observation_ids) != len(set(observation_ids)):
            refuse(
                "Duplicate observed units must be reconciled before final evaluation"
            )
        group_blocks: dict[str, str] = {}
        groups: dict[str, str] = {}
        for site in self.sites:
            if site.site_id in groups and groups[site.site_id] != site.group_id:
                refuse("A physical site cannot be divided into independent groups")
            groups[site.site_id] = site.group_id
            if (
                site.group_id in group_blocks
                and group_blocks[site.group_id] != site.block_id
            ):
                refuse(
                    "An independent site group cannot span different resampling blocks"
                )
            group_blocks[site.group_id] = site.block_id
        if not isinstance(self.dependency_graph, tuple):
            refuse("Dependency graph must contain explicit tuple entries")
        graph = []
        for key, parents in self.dependency_graph:
            graph.append((required_identity(key), identity_values(parents)))
        if len(graph) != len(dict(graph)):
            refuse("Duplicate dependency graph node")
        object.__setattr__(self, "dependency_graph", tuple(sorted(graph)))
        if not isinstance(self.external_inputs, tuple) or any(
            not isinstance(x, ExternalInput) for x in self.external_inputs
        ):
            refuse("External inputs need typed roles and provenance")
        if len(self.external_inputs) != len({x.input_id for x in self.external_inputs}):
            refuse("Duplicate external input identity")
        external_ids = {item.input_id for item in self.external_inputs}
        if external_ids & (set(sites) | set(observation_ids)):
            refuse("External input IDs cannot shadow site or observation identities")
        graph_map = dict(self.dependency_graph)
        if any(
            item.role == "training_derived_product" and not graph_map.get(item.input_id)
            for item in self.external_inputs
        ):
            refuse(
                "Training-derived products require explicit nonempty source ancestry"
            )
        object.__setattr__(
            self, "sites", tuple(sorted(self.sites, key=lambda x: x.record_id))
        )
        object.__setattr__(
            self, "folds", tuple(sorted(self.folds, key=lambda x: x.fold_id))
        )
        object.__setattr__(
            self,
            "external_inputs",
            tuple(sorted(self.external_inputs, key=lambda x: x.input_id)),
        )

    @property
    def scope_sha256(self) -> str:
        return manifest_sha256(
            {
                "scope_id": self.scope_id,
                "taxa": self.taxa,
                "sites": [asdict(x) for x in self.sites],
                "dependency_graph": self.dependency_graph,
                "external_inputs": [asdict(x) for x in self.external_inputs],
                "observation_channels": [asdict(x) for x in self.observation_channels],
            }
        )

    @property
    def split_sha256(self) -> str:
        return manifest_sha256([fold.as_dict() for fold in self.folds])


@dataclass(frozen=True)
class PredictiveInterval:
    """Marginal composition intervals, with named propagated uncertainty only."""

    profile_id: str
    nominal_coverage: float
    propagated_sources: tuple[str, ...]
    uncertainty_kind: Literal[
        "predictive_observation", "latent_composition", "parameter_only"
    ]
    limits: tuple[tuple[str, float, float], ...]


_SOURCE_MODEL_FACTORY_TOKEN = object()


@dataclass(frozen=True, init=False)
class SourceModelIdentity:
    """A typed producer-authenticated model identity, never a caller assertion."""

    kind: SourceModelKind
    sha256: str

    def __init__(
        self,
        kind: SourceModelKind,
        sha256: str,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _SOURCE_MODEL_FACTORY_TOKEN:
            refuse("Source-model identities require an authenticated producer")
        if kind not in {
            "fitted_spatial",
            "admitted_reconstruction_training_mean",
            "local_pollen_assimilation",
        }:
            refuse("Unsupported source-model kind")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "sha256", digest(sha256))


def _authenticated_source_model(
    kind: str,
    sha256: str,
) -> SourceModelIdentity:
    if kind not in {
        "fitted_spatial",
        "admitted_reconstruction_training_mean",
        "local_pollen_assimilation",
    }:
        refuse("Unsupported authenticated source-model kind")
    return SourceModelIdentity(
        cast(SourceModelKind, kind),
        sha256,
        _factory_token=_SOURCE_MODEL_FACTORY_TOKEN,
    )


@dataclass(frozen=True)
class EvaluationRow:
    """One requested model/site/bin/target outcome; absent outputs are explicit."""

    fold_id: str
    record_id: str
    model_id: str
    target: Target
    experiment: Experiment
    status: Literal["predicted", "prediction_failed", "excluded"]
    prediction: tuple[tuple[str, float], ...] | None
    observation: tuple[tuple[str, float | int | None], ...] | None
    observation_reference_id: str | None
    observation_kind: str | None
    observation_support: Support | None
    prediction_sha256: str | None
    prediction_manifest_json: str | None
    fitted_model_sha256: str | None
    prediction_frozen_at: datetime | None
    fit_input_ids: tuple[str, ...]
    interval: PredictiveInterval | None = None
    reason: str | None = None
    observed_pollen: ObservedPollenAdmission | None = None
    source_model: SourceModelIdentity | None = None


@dataclass(frozen=True)
class AcceptanceCell:
    cell_id: str
    experiment: Experiment
    target: Target
    model_id: str
    baseline_id: str
    subgroup: str
    maximum_mae_pp: float
    minimum_baseline_improvement_pp: float
    minimum_sites: int
    minimum_blocks: int
    maximum_prediction_failure_fraction: float
    maximum_exclusion_fraction: float
    nominal_predictive_coverage: float
    coverage_tolerance: float
    interval_profile_id: str


@dataclass(frozen=True)
class EvaluationPolicy:
    canonical_policy_json: str
    policy_sha256: str
    scope_sha256: str
    split_sha256: str
    first_test_access_at: datetime
    cells: tuple[AcceptanceCell, ...]
    minimum_buffer_m: float
    independent_vegetation_reference_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationResult:
    """Finite immutable receipt: engineering evaluation is not reviewer approval."""

    canonical_result_json: str
    result_sha256: str
    status: Literal["passed", "failed", "ineligible"]


def _prediction_payload_v1(row: EvaluationRow) -> dict[str, object]:
    """Preserve the historical wire byte-for-byte; never add v2 fields here."""
    return {
        "schema_version": "pollenomics-evaluation-prediction.v1",
        "fold_id": row.fold_id,
        "record_id": row.record_id,
        "model_id": row.model_id,
        "target": row.target,
        "experiment": row.experiment,
        "prediction": row.prediction,
        "fitted_model_sha256": row.fitted_model_sha256,
        "fit_input_ids": row.fit_input_ids,
        "frozen_at": row.prediction_frozen_at.isoformat()
        if row.prediction_frozen_at
        else None,
        "interval": asdict(row.interval) if row.interval else None,
        "observed_pollen": asdict(row.observed_pollen) if row.observed_pollen else None,
    }


def _validated_source_model(row: EvaluationRow) -> SourceModelIdentity:
    source = row.source_model
    if not isinstance(source, SourceModelIdentity):
        refuse("A typed authenticated source-model identity is required")
    values = identity_values(row.fit_input_ids)
    if (
        not isinstance(row.fit_input_ids, tuple)
        or not values
        or len(values) != len(set(values))
    ):
        refuse("Source-model input identities must be a nonempty unique tuple")
    if source.kind == "fitted_spatial":
        if row.model_id != "clr-wgs84-rbf-ridge-v1":
            refuse("Fitted spatial source requires the governed model method")
        if row.fitted_model_sha256 != source.sha256:
            refuse("Fitted source and legacy fitted-model identities differ")
    elif source.kind == "admitted_reconstruction_training_mean":
        if row.model_id != "training_mean":
            refuse("Training-mean source requires the governed baseline method")
        if row.fitted_model_sha256 is not None:
            refuse("A training-mean baseline cannot populate fitted_model_sha256")
    else:
        if (
            row.model_id != "analytical_love_local_pollen"
            or row.experiment != "local_pollen_available"
            or row.target != "vegetation_cover"
        ):
            refuse("Local-pollen source requires the governed local vegetation method")
        if row.fitted_model_sha256 is not None:
            refuse("A local-pollen assimilation cannot populate fitted_model_sha256")
    return source


def _prediction_payload_v2(row: EvaluationRow) -> dict[str, object]:
    source = _validated_source_model(row)
    return {
        "schema_version": "pollenomics-evaluation-prediction.v2",
        "fold_id": row.fold_id,
        "record_id": row.record_id,
        "model_id": row.model_id,
        "target": row.target,
        "experiment": row.experiment,
        "prediction": row.prediction,
        "source_model": asdict(source),
        "model_input_ids": row.fit_input_ids,
        "frozen_at": row.prediction_frozen_at.isoformat()
        if row.prediction_frozen_at
        else None,
        "interval": asdict(row.interval) if row.interval else None,
        "observed_pollen": asdict(row.observed_pollen) if row.observed_pollen else None,
    }


def prediction_payload(row: EvaluationRow) -> dict[str, object]:
    """Return the exact v1 wire or the additive typed v2 wire."""
    if row.source_model is None:
        return _prediction_payload_v1(row)
    return _prediction_payload_v2(row)


def validate_frozen_prediction(row: EvaluationRow) -> EnvelopeVersion:
    """Reopen exact v1/v2 bytes without upgrading or relabelling either schema."""
    if not isinstance(row.prediction_manifest_json, str):
        refuse("Frozen prediction envelope bytes are required")
    if not isinstance(row.prediction_sha256, str):
        refuse("Frozen prediction envelope identity is required")
    try:
        loaded = json.loads(row.prediction_manifest_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed frozen prediction envelope: {exc}")
    if not isinstance(loaded, dict):
        refuse("Frozen prediction envelope must be an object")
    version = loaded.get("schema_version")
    if version == "pollenomics-evaluation-prediction.v1":
        if row.source_model is not None:
            refuse("Historical v1 cannot carry a v2 source-model identity")
        expected = _prediction_payload_v1(row)
    elif version == "pollenomics-evaluation-prediction.v2":
        expected = _prediction_payload_v2(row)
    else:
        refuse("Unsupported frozen prediction envelope version")
    if (
        row.prediction_manifest_json != canonical_json(loaded)
        or canonical_json(loaded) != canonical_json(expected)
        or manifest_sha256(loaded) != digest(row.prediction_sha256)
    ):
        refuse("Frozen prediction bytes differ from the typed evaluation row")
    return cast(EnvelopeVersion, version)


def freeze_evaluation_prediction(row: EvaluationRow) -> EvaluationRow:
    """Bind an outcome-free adapter row before the scoring process reads outcomes.

    The host experiment owns the separate first-access receipt. This helper stamps
    the current freeze time and refuses supplied outcomes or an existing binding;
    it does not authenticate a human's prior knowledge of observation values.
    """
    if (
        row.status != "predicted"
        or row.prediction is None
        or row.observation is not None
    ):
        refuse("Only an outcome-free successful prediction can be frozen")
    if (
        row.prediction_sha256 is not None
        or row.prediction_manifest_json is not None
        or row.prediction_frozen_at is not None
    ):
        refuse("An existing or predated prediction binding cannot be replaced")
    stamped = replace(row, prediction_frozen_at=datetime.now(UTC))
    payload = prediction_payload(stamped)
    return replace(
        stamped,
        prediction_sha256=manifest_sha256(payload),
        prediction_manifest_json=canonical_json(payload),
    )
