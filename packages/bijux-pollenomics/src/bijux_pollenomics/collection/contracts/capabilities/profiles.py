from __future__ import annotations

from dataclasses import asdict

from .constants import (
    _NORMATIVE_CONTRACT_ID,
    _NORMATIVE_CONTRACT_VERSION,
    _NORMATIVE_SOURCE_KEYS,
    _SUPPORT_STATUSES,
    CAPABILITY_DIMENSIONS,
)
from .models import SourceCapabilityProfile
from .paths import _source_evidence_paths


def build_source_capability_profiles() -> tuple[SourceCapabilityProfile, ...]:
    """Declare source-native capability independently of repository state."""
    profiles = (
        _profile(
            "landclim",
            evidence_class="modelled_vegetation_or_land_cover",
            allowed_role="modelled vegetation and land-cover context",
            unsupported={"relative_chronology"},
            partial={
                "four_country_coverage",
                "within_site_hierarchy",
                "chronology_uncertainty",
                "taxon_identity",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "dataset_provenance",
                "pollen_propagation_event",
            },
            evidence_paths=_source_evidence_paths("landclim"),
            prohibited_claims=(
                "model output is an observed pollen find",
                "model gradients prove migration or causation",
            ),
            human_review_reason="qualified_model_semantics_review_missing",
        ),
        _profile(
            "neotoma",
            evidence_class="observed_paleoecological",
            allowed_role="sample- and taxon-resolved observed pollen evidence",
            unsupported=set(),
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "derived_pollen_group",
                "derived_ecological_role",
            },
            evidence_paths=_source_evidence_paths("neotoma"),
            prohibited_claims=(
                "site envelopes are first-occurrence events",
                "incompatible observation units are interchangeable",
            ),
            human_review_reason="qualified_ecological_classification_review_missing",
        ),
        _profile(
            "sead",
            evidence_class="observed_archaeological_environmental",
            allowed_role="multidisciplinary environmental archaeology evidence",
            unsupported=set(),
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            evidence_paths=_source_evidence_paths("sead"),
            prohibited_claims=(
                "site inventory presence is chronology",
                "context-only dates are pollen propagation events",
            ),
            human_review_reason="qualified_sead_ecological_classification_review_missing",
        ),
        _profile(
            "raa",
            evidence_class="archaeological_context",
            allowed_role="Sweden-only archaeological context",
            unsupported={
                "four_country_coverage",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "within_site_hierarchy",
                "numeric_chronology",
                "chronology_uncertainty",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("raa"),
            prohibited_claims=(
                "named periods are numeric BP without a governed crosswalk",
                "archaeological density is population or pollen presence",
            ),
            human_review_reason="qualified_raa_source_review_missing",
        ),
        _profile(
            "svar",
            evidence_class="modern_environmental_context",
            allowed_role="Sweden lake identity and sampling context",
            unsupported={
                "four_country_coverage",
                "numeric_chronology",
                "chronology_uncertainty",
                "relative_chronology",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={"within_site_hierarchy", "dataset_provenance"},
            evidence_paths=_source_evidence_paths("svar"),
            prohibited_claims=(
                "modern lake attributes are historical pollen chronology",
                "environmental similarity is propagation",
            ),
            human_review_reason="qualified_svar_publication_review_missing",
        ),
        _profile(
            "aadr",
            evidence_class="human_ancient_dna",
            allowed_role="human ancient-DNA sample and locality context",
            unsupported={
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("aadr"),
            prohibited_claims=(
                "human ancient DNA is pollen evidence",
                "co-occurrence proves ecological or demographic causation",
            ),
            human_review_reason="qualified_human_adna_source_review_missing",
        ),
        _profile(
            "animal_adna",
            evidence_class="observed_genetic_or_zooarchaeological",
            allowed_role="animal genetic and zooarchaeological context",
            unsupported={
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "pollen_propagation_event",
            },
            partial={
                "four_country_coverage",
                "chronology_uncertainty",
                "relative_chronology",
                "native_ecological_class",
                "quantitative_observation",
                "observation_unit",
            },
            evidence_paths=_source_evidence_paths("animal_adna"),
            prohibited_claims=(
                "animal ancient DNA is pollen evidence",
                "animal-human-pollen co-occurrence proves causation",
            ),
            human_review_reason="qualified_animal_adna_source_review_missing",
        ),
        _profile(
            "boundaries",
            evidence_class="geographic_framing",
            allowed_role="map framing and governed country assignment",
            unsupported={
                "within_site_hierarchy",
                "numeric_chronology",
                "chronology_uncertainty",
                "relative_chronology",
                "taxon_identity",
                "native_ecological_class",
                "derived_pollen_group",
                "derived_ecological_role",
                "crop_cereal_resolution",
                "quantitative_observation",
                "observation_unit",
                "pollen_propagation_event",
            },
            partial=set(),
            evidence_paths=_source_evidence_paths("boundaries"),
            prohibited_claims=(
                "modern borders are historical ecological barriers",
                "country framing supplies observations or chronology",
            ),
            human_review_reason="qualified_boundary_inclusion_review_missing",
        ),
    )
    _validate_profiles(profiles)
    return profiles


def build_source_capability_contract_payload() -> dict[str, object]:
    """Build the immutable source-support side of the capability contract."""
    profiles = build_source_capability_profiles()
    return {
        "schema_version": "source-capability-contract.v1",
        "dimension_count": len(CAPABILITY_DIMENSIONS),
        "source_count": len(profiles),
        "normative_contract": {
            "contract_id": _NORMATIVE_CONTRACT_ID,
            "schema_version": _NORMATIVE_CONTRACT_VERSION,
            "source_count": len(_NORMATIVE_SOURCE_KEYS),
            "source_keys": list(_NORMATIVE_SOURCE_KEYS),
        },
        "extension_sources": ["aadr"],
        "dimensions": list(CAPABILITY_DIMENSIONS),
        "sources": [asdict(profile) for profile in profiles],
    }


def _profile(
    source_key: str,
    *,
    evidence_class: str,
    allowed_role: str,
    unsupported: set[str],
    partial: set[str],
    evidence_paths: dict[str, tuple[str, ...]],
    prohibited_claims: tuple[str, ...],
    human_review_reason: str | None,
) -> SourceCapabilityProfile:
    support = {
        dimension: (
            "unsupported"
            if dimension in unsupported
            else "partial"
            if dimension in partial
            else "supported"
        )
        for dimension in CAPABILITY_DIMENSIONS
    }
    governed_evidence_paths = {
        dimension: () if dimension in unsupported else paths
        for dimension, paths in evidence_paths.items()
    }
    return SourceCapabilityProfile(
        source_key=source_key,
        evidence_class=evidence_class,
        allowed_role=allowed_role,
        prohibited_claims=prohibited_claims,
        support_by_dimension=support,
        evidence_paths_by_dimension=governed_evidence_paths,
        human_review_required=human_review_reason is not None,
        human_review_reason=human_review_reason,
    )


def _validate_profiles(profiles: tuple[SourceCapabilityProfile, ...]) -> None:
    source_keys = [profile.source_key for profile in profiles]
    if len(source_keys) != len(set(source_keys)):
        raise ValueError("source capability profiles contain duplicate source keys")
    expected_dimensions = set(CAPABILITY_DIMENSIONS)
    for profile in profiles:
        if set(profile.support_by_dimension) != expected_dimensions:
            raise ValueError(
                f"incomplete capability support profile: {profile.source_key}"
            )
        if set(profile.evidence_paths_by_dimension) != expected_dimensions:
            raise ValueError(
                f"incomplete capability evidence profile: {profile.source_key}"
            )
        if not set(profile.support_by_dimension.values()) <= _SUPPORT_STATUSES:
            raise ValueError(f"invalid capability support status: {profile.source_key}")
        for dimension, paths in profile.evidence_paths_by_dimension.items():
            if profile.support_by_dimension[dimension] != "unsupported" and not paths:
                raise ValueError(
                    f"supported capability has no evidence path: {profile.source_key}/{dimension}"
                )
            if len(paths) != len(set(paths)):
                raise ValueError(
                    f"duplicate capability evidence path: {profile.source_key}/{dimension}"
                )
