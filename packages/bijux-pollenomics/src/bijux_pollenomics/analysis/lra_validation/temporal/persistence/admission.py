"""Bind full declared temporal supports to admitted source geometry before pollen."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import cast

from ...contracts import ValidationRefusal, canonical_json, manifest_sha256
from ...experiments.configuration import (
    InputReference,
    identity,
    object_list,
    object_mapping,
)
from ...experiments.inputs import (
    _reference_bytes,
    _unique_pairs,
    read_geometry,
    read_reference,
)
from ...experiments.prediction import _support
from ..admission import TemporalAdmissionResult, admit_forward_time_training
from ..contracts import CalendarSupport, _number
from .configuration import TemporalPersistenceSpec, YoungerCalendarBin


def _evidence(spec: TemporalPersistenceSpec) -> dict[str, InputReference]:
    references: dict[str, InputReference] = {}
    all_ids: set[str] = set()
    raw_paths = {str(Path(site.raw.path)) for site in spec.older_experiment.sites}
    raw_hashes = {site.raw.sha256 for site in spec.older_experiment.sites}
    for value in object_list(spec.older_experiment.template()["evidence"], "evidence"):
        row = object_mapping(value, "evidence")
        key = identity(row["evidence_id"])
        if key in all_ids:
            raise ValidationRefusal("duplicate_temporal_evidence", key)
        all_ids.add(key)
        reference = InputReference.parse(
            {"path": row["path"], "sha256": row["sha256"]}, "evidence"
        )
        if str(Path(reference.path)) in raw_paths or reference.sha256 in raw_hashes:
            raise ValidationRefusal("temporal_source_role_collision", key)
        if row["role"] == "chronology":
            references[key] = reference
    for site in spec.older_experiment.sites:
        if (
            str(Path(site.geometry.path)) in raw_paths
            or site.geometry.sha256 in raw_hashes
        ):
            raise ValidationRefusal(
                "temporal_source_role_collision", site.record.record_id
            )
    return references


def _selection(
    spec: TemporalPersistenceSpec, decision: TemporalAdmissionResult
) -> tuple[str, ...]:
    admission = decision.require_training_admission()
    admitted = admission.admitted_record_ids
    anchor = next(
        (key for key in spec.older_experiment.regional_priority if key in admitted),
        None,
    )
    if anchor != spec.temporal_plan.required_regional_record_ids[0]:
        raise ValidationRefusal(
            "temporal_regional_priority_mismatch",
            "Required source is not first eligible declared anchor",
        )
    for group in admission.admitted_group_ids:
        if sum(owner == group for _, owner in admission.record_groups) != 1:
            raise ValidationRefusal(
                "unsupported_temporal_training_group",
                "Numerical observation selection for aliases is not declared",
            )
    return tuple(sorted((*admitted, *spec.temporal_plan.fold.test_record_ids)))


def _bind_support(
    geometry: dict[str, object],
    support: CalendarSupport,
    bounds: YoungerCalendarBin,
    evidence: dict[str, InputReference],
) -> str:
    metadata = object_mapping(geometry["sample_metadata"], "sample_metadata")
    if metadata["age_type"] != "calendar_bp" or metadata["bin_id"] != bounds.bin_id:
        raise ValidationRefusal(
            "temporal_geometry_support_mismatch", "Geometry age type or bin differs"
        )
    intervals = []
    for value in object_list(metadata["age_support_bp"], "age_support_bp"):
        pair = object_list(value, "component")
        if len(pair) != 2:
            raise ValidationRefusal(
                "temporal_geometry_support_mismatch", "Require full interval components"
            )
        intervals.append((_number(pair[0]), _number(pair[1])))
    if tuple(intervals) != support.intervals_bp or any(
        not bounds.younger_bp <= young <= old <= bounds.older_bp
        for young, old in intervals
    ):
        raise ValidationRefusal(
            "temporal_geometry_support_mismatch",
            "Full geometry components differ from declaration or lie outside bin",
        )
    # This numerical pairing coordinate is not a chronology model or age estimator.
    _number(metadata["coordinate"])
    evidence_id = identity(metadata["chronology_evidence_id"])
    reference = evidence.get(evidence_id)
    if reference is None or reference.sha256 != support.chronology_manifest_sha256:
        raise ValidationRefusal("temporal_chronology_evidence_mismatch", evidence_id)
    return evidence_id


@dataclass(frozen=True)
class TemporalSourceAdmission:
    """Owned source declarations; byte verification does not authenticate supplied ages."""

    spec: TemporalPersistenceSpec
    geometry_json: str
    source_text_json: str

    def __post_init__(self) -> None:
        if not isinstance(self.spec, TemporalPersistenceSpec) or not isinstance(
            self.geometry_json, str
        ):
            raise ValidationRefusal(
                "invalid_temporal_source_admission",
                "Require typed spec and canonical geometry",
            )
        try:
            geometries = object_mapping(json.loads(self.geometry_json), "geometries")
            if canonical_json(geometries) != self.geometry_json:
                raise ValidationRefusal(
                    "invalid_temporal_source_admission", "Geometry must be canonical"
                )
            texts = object_mapping(
                json.loads(self.source_text_json), "geometry_source_text"
            )
            if canonical_json(texts) != self.source_text_json or set(texts) != set(
                geometries
            ):
                raise ValidationRefusal(
                    "temporal_geometry_bytes_mismatch",
                    "Exact geometry byte receipts are required",
                )
            sites = {
                site.record.record_id: site for site in self.spec.older_experiment.sites
            }
            for record, text in texts.items():
                if (
                    not isinstance(text, str)
                    or record not in sites
                    or hashlib.sha256(text.encode("utf-8")).hexdigest()
                    != sites[record].geometry.sha256
                ):
                    raise ValidationRefusal("temporal_geometry_bytes_mismatch", record)
                parsed = json.loads(text, object_pairs_hook=_unique_pairs)
                if canonical_json(parsed) != canonical_json(geometries[record]):
                    raise ValidationRefusal("temporal_geometry_bytes_mismatch", record)
            decision = self.decision
            if decision.training_admission is None:
                if geometries:
                    raise ValidationRefusal(
                        "invalid_temporal_source_admission",
                        "Refused chronology cannot admit geometry",
                    )
                return
            if set(geometries) != set(_selection(self.spec, decision)):
                raise ValidationRefusal(
                    "temporal_geometry_catalogue_mismatch",
                    "Require every admitted and target geometry, no excluded inputs",
                )
            evidence = _evidence(self.spec)
            supports = {
                row.record_id: row.support
                for row in self.spec.temporal_plan.chronologies
            }
            target = self.spec.temporal_plan.fold.test_record_ids[0]
            anchor = self.spec.temporal_plan.required_regional_record_ids[0]
            for record, value in geometries.items():
                geometry = object_mapping(value, "geometry")
                support = supports[record]
                if support is None:
                    raise ValidationRefusal("missing_temporal_geometry_support", record)
                _bind_support(
                    geometry,
                    support,
                    self.spec.younger_bin
                    if record == target
                    else self.spec.older_bin(),
                    evidence,
                )
                if record != target:
                    _support(
                        self.spec.older_experiment,
                        geometry,
                        object_mapping(geometries[anchor], "anchor"),
                    )
        except ValidationRefusal:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationRefusal(
                "invalid_temporal_source_admission", str(exc)
            ) from exc

    @property
    def decision(self) -> TemporalAdmissionResult:
        return admit_forward_time_training(self.spec.temporal_plan)

    def geometries(self) -> dict[str, object]:
        return cast(dict[str, object], json.loads(self.geometry_json))

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-temporal-source-admission.v1",
            "spec_sha256": self.spec.sha256,
            "temporal_decision": self.decision.as_dict(),
            "geometries": self.geometries(),
            "geometry_source_text": json.loads(self.source_text_json),
            "older_bin": self.spec.older_bin().as_dict(),
            "younger_bin": self.spec.younger_bin.as_dict(),
            "source_age_authenticity": "not_verified",
            "chronology_model_identity": "caller_declaration_not_evidence_identity",
            "scientific_approval": "not_verified",
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())


def admit_temporal_sources(
    spec: TemporalPersistenceSpec,
    *,
    input_root: Path,
    consumed_geometry: set[str] | None = None,
    consumed_chronology: set[str] | None = None,
) -> TemporalSourceAdmission:
    """Evaluate temporal selection before any file access; never open pollen here."""
    decision = admit_forward_time_training(spec.temporal_plan)
    if decision.training_admission is None:
        return TemporalSourceAdmission(spec, canonical_json({}), canonical_json({}))
    selected = _selection(spec, decision)
    references = _evidence(spec)
    sites = {site.record.record_id: site for site in spec.older_experiment.sites}
    geometries: dict[str, object] = {}
    texts: dict[str, str] = {}
    read_ids: set[str] = set()
    for record in selected:
        geometry = read_geometry(
            input_root,
            sites[record],
            spec.older_experiment,
            consumed_geometry=consumed_geometry,
        )
        geometries[record] = geometry
        texts[record] = _reference_bytes(input_root, sites[record].geometry).decode(
            "utf-8"
        )
        metadata = object_mapping(geometry["sample_metadata"], "sample_metadata")
        read_ids.add(identity(metadata["chronology_evidence_id"]))
    result = TemporalSourceAdmission(
        spec, canonical_json(geometries), canonical_json(texts)
    )
    for key in sorted(read_ids):
        read_reference(input_root, references[key])
        if consumed_chronology is not None:
            consumed_chronology.add(key)
    return result
