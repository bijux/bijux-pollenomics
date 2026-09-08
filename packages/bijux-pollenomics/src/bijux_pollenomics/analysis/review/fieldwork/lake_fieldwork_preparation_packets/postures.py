"""Fieldwork readiness postures and required-review actions."""

from __future__ import annotations


def identity_posture(ambiguity_flags: tuple[str, ...]) -> str:
    flags = set(ambiguity_flags)
    if "duplicate_sweden_name" in flags:
        return "duplicate_name_resolution_required"
    if "non_official_registry_name" in flags:
        return "registry_name_review_required"
    if "source_coordinate_spread" in flags or "source_name_variants" in flags:
        return "registry_cross_check_required"
    return "registry_clear"


def sead_context_posture(sead_site_count: int) -> str:
    if sead_site_count >= 20:
        return "high"
    if sead_site_count >= 5:
        return "medium"
    return "low"


def palaeopen_alignment_posture(
    *,
    direct_pollen_source_count: int,
    evidence_family_count: int,
) -> str:
    if direct_pollen_source_count >= 2 and evidence_family_count >= 4:
        return "high"
    if direct_pollen_source_count >= 2 and evidence_family_count >= 3:
        return "medium"
    return "low"


def preparation_posture(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    sampling_fit: float,
    human_context_posture: str,
    direct_pollen_source_count: int,
    evidence_family_count: int,
    sead_site_count: int,
    human_locality_count: int,
    scenario_consistency_posture: str,
) -> str:
    if ambiguity_flags:
        return "identity_resolution_required"
    if sampling_posture == "small_lake_review" or sampling_fit < 0.5:
        return "sampling_fit_review_required"
    if human_context_posture in {
        "extended_human_adna_context",
        "outer_human_adna_context",
        "human_adna_context_absent",
    }:
        return "human_context_review_required"
    if (
        human_context_posture in {"core_human_adna_context", "near_human_adna_context"}
        and scenario_consistency_posture == "high"
        and direct_pollen_source_count >= 2
        and evidence_family_count >= 4
        and sead_site_count >= 10
    ):
        return "fieldwork_review_ready"
    if (
        human_context_posture in {"core_human_adna_context", "near_human_adna_context"}
        and direct_pollen_source_count >= 2
        and scenario_consistency_posture in {"high", "medium"}
        and evidence_family_count >= 4
    ):
        return "context_review_ready"
    if evidence_family_count >= 3 and (
        sead_site_count >= 1 or human_locality_count >= 1
    ):
        return "context_review_ready"
    return "evidence_screen_only"


def required_actions(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    human_context_posture: str,
    scenario_consistency_posture: str,
    sead_context_posture: str,
    palaeopen_alignment_posture: str,
    preparation_posture: str,
) -> list[str]:
    actions: list[str] = []
    flags = set(ambiguity_flags)
    if "duplicate_sweden_name" in flags:
        actions.append(
            "confirm the exact Swedish lake registry match before field planning"
        )
    if "source_coordinate_spread" in flags:
        actions.append(
            "reconcile source coordinates against the basin description and lake outline"
        )
    if "source_name_variants" in flags:
        actions.append(
            "normalize source name variants against the lake registry and tracked source records"
        )
    if "non_official_registry_name" in flags:
        actions.append(
            "confirm the official Swedish lake registry name before field planning"
        )
    if sampling_posture == "small_lake_review":
        actions.append(
            "verify basin depth, access, and sediment suitability before treating this small lake as a field target"
        )
    if human_context_posture in {
        "extended_human_adna_context",
        "outer_human_adna_context",
    }:
        actions.append(
            "treat this lake as context-rich but aDNA-distant until a nearer human aDNA locality supports field planning"
        )
    if human_context_posture == "human_adna_context_absent":
        actions.append(
            "do not promote this lake for field planning until human aDNA support is present in the checked-in context"
        )
    if scenario_consistency_posture == "low":
        actions.append(
            "stress-test this candidate against alternative distance-band scenarios before field planning"
        )
    if sead_context_posture in {"high", "medium"}:
        actions.append(
            "inspect linked SEAD records before narrowing the archaeology-context interpretation"
        )
    if palaeopen_alignment_posture == "high":
        actions.append(
            "prepare interoperable metadata notes for wider palaeoecological comparison"
        )
    if not actions and preparation_posture == "fieldwork_review_ready":
        actions.append(
            "prepare a site-specific fieldwork review with access, coring, and basin constraints"
        )
    if preparation_posture in {"fieldwork_review_ready", "context_review_ready"}:
        actions.append(
            "complete bathymetry, sediment, access, permit, hazard, and logistics review before sampling"
        )
    return actions


def scenario_top20_presence_count(
    *, aggregate_rank: int, scenario_ranks: dict[str, int]
) -> int:
    return int(aggregate_rank <= 20) + sum(
        1 for rank in scenario_ranks.values() if rank <= 20
    )


def scenario_consistency_posture(top20_presence_count: int) -> str:
    if top20_presence_count >= 4:
        return "high"
    if top20_presence_count >= 2:
        return "medium"
    return "low"


def google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude:.6f},{longitude:.6f}"
