"""Chronology-node and materialization identity models."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import NODE_LEVELS


@dataclass(frozen=True)
class SourceChronologyNode:
    """Dated source evidence explicitly unavailable for propagation."""

    node_id: str
    source_family: str
    source_snapshot_id: str
    source_record_id: str
    site_id: str
    observation_ids: tuple[str, ...]
    node_level: str
    feature_key: str
    source_variable_ids: tuple[str, ...]
    source_taxon_id: int | str | None
    source_reported_name: str | None
    source_ecological_group: str | None
    source_unit: str
    country_code: str
    latitude: float
    longitude: float
    coordinate_quality: str
    chronology_claim_id: str
    chronology_id: str | None
    chronology_name: str | None
    is_default_chronology: bool
    chronology_selection_posture: str
    younger_bp: float | int
    older_bp: float | int
    provenance_record_id: str
    input_digest: str
    config_digest: str
    producer_version: str
    build_id: str
    candidate_refusal_reason: str
    propagation_eligible: bool = False
    candidate_generation_status: str = "refused"
    source_element_type: str = "pollen"
    comparability_status: str = "comparable"
    schema_version: str = "neotoma-source-chronology-node.v2"

    def __post_init__(self) -> None:
        if self.node_level not in NODE_LEVELS:
            raise ValueError("node_level is not a governed source-node level")
        if self.source_family != "neotoma":
            raise ValueError("source chronology node requires Neotoma source identity")
        if self.source_element_type != "pollen":
            raise ValueError("source chronology node requires pollen evidence")
        if self.comparability_status != "comparable":
            raise ValueError("source chronology node requires comparable chronology")
        expected_default = (
            self.chronology_selection_posture == "selected_source_default"
        )
        if self.chronology_selection_posture not in {
            "selected_source_default",
            "selected_unique_nondefault",
        }:
            raise ValueError("source chronology node requires a selection posture")
        if self.is_default_chronology is not expected_default:
            raise ValueError("chronology default status contradicts selection posture")
        observation_ids = tuple(sorted(set(self.observation_ids)))
        if not observation_ids:
            raise ValueError("source chronology node requires observation identity")
        object.__setattr__(self, "observation_ids", observation_ids)
        object.__setattr__(
            self, "source_variable_ids", tuple(sorted(set(self.source_variable_ids)))
        )
        if self.propagation_eligible:
            raise ValueError("source chronology nodes are not propagation events")
        expected_reason = {
            "source_sample_presence": "reviewed_pollen_sum_not_available",
            "source_ecological_code": "source_ecological_equivalence_not_reviewed",
            "source_taxon": "source_taxon_equivalence_not_reviewed",
        }[self.node_level]
        if self.candidate_refusal_reason != expected_reason:
            raise ValueError("candidate refusal reason does not match node level")
        self._validate_source_facets()

    def _validate_source_facets(self) -> None:
        if self.node_level == "source_sample_presence" and (
            self.source_variable_ids
            or any(
                value is not None
                for value in (
                    self.source_taxon_id,
                    self.source_reported_name,
                    self.source_ecological_group,
                )
            )
        ):
            raise ValueError("sample-presence node must not claim a source facet")
        if (
            self.node_level == "source_ecological_code"
            and self.source_ecological_group is None
        ):
            raise ValueError("source-code node requires a literal source code")
        if self.node_level == "source_ecological_code" and any(
            value is not None
            for value in (self.source_taxon_id, self.source_reported_name)
        ):
            raise ValueError("source-code node must not claim a source taxon")
        if self.node_level == "source_taxon" and (
            not self.source_variable_ids
            or self.source_taxon_id is None
            or self.source_reported_name is None
        ):
            raise ValueError("source-taxon node requires exact source identity")
        if (
            self.node_level == "source_taxon"
            and self.source_ecological_group is not None
        ):
            raise ValueError("source-taxon node must not claim an ecological code")
        if self.node_level != "source_taxon" and self.source_variable_ids:
            raise ValueError("non-taxon node must not claim source variables")

    def as_dict(self) -> dict[str, object]:
        return {
            **dict(self.__dict__),
            "observation_ids": list(self.observation_ids),
            "source_variable_ids": list(self.source_variable_ids),
        }


@dataclass(frozen=True)
class SourceNodeMaterializationResult:
    """Identity and disposition of one deterministic node bundle."""

    output_root: str
    disposition: str
    manifest_sha256: str
    file_count: int
    chronology_node_count: int
    propagation_eligible_event_count: int = 0


__all__ = ["SourceChronologyNode", "SourceNodeMaterializationResult"]
