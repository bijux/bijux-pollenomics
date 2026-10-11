"""Reviewed context projection with explicit category and role denominators."""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import cast

from ..events.eligibility import (
    ClassificationEligibilityResult,
    _assess_classification_eligibility,
)
from ..events.identity import _canonical, _digest
from ..events.models import ClassificationReviewContext

_ROLE_LABELS = {
    "direct_crop_confirmed": ("Direct crop taxon evidence", "local cultivation"),
    "crop_type_qualified": ("Qualified crop-type evidence", "local cultivation"),
    "anthropogenic_indicator": (
        "Anthropogenic or land-use indicator",
        "human activity",
    ),
    "pastoral_indicator": ("Pastoral-associated indicator", "grazing"),
    "ruderal_disturbance_indicator": (
        "Ruderal or disturbance-associated indicator",
        "human disturbance",
    ),
}


def assess_reviewed_context(
    *,
    observation_memberships: Sequence[Mapping[str, object]],
    classification_mappings: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    context: ClassificationReviewContext,
) -> ClassificationEligibilityResult:
    """Retain authorized categories without creating taxon or propagation claims.

    The complete governed mapping universe, source identity, input lineage and
    named review remain mandatory. Zero/null/absent measurements are preserved;
    category membership counts are observation counts, never measurement sums.
    The whole-pollen category denominator includes reviewed unidentified pollen
    and excludes spores, charcoal, laboratory elements and all refused rows.
    Neither this denominator nor a positive context review admits an LRA run or
    a pollen event. Existing taxon and detection admission remain separate.
    """
    payload = _assess_classification_eligibility(
        observation_memberships=observation_memberships,
        classification_mappings=classification_mappings,
        observations=observations,
        context=context,
        retain_context=True,
    ).as_dict()
    payload["schema_version"] = "classification-reviewed-context.v1"
    payload["scope"] = "reviewed_source_context_only"
    payload["unassessed"] = [
        "counts",
        "units",
        "detection",
        "chronology",
        "geometry",
        "ppe",
        "pollen_event_admission",
    ]
    rows = cast(list[dict[str, object]], payload["rows"])
    categories: Counter[tuple[str, str]] = Counter()
    role_observations: dict[str, set[str]] = {role: set() for role in _ROLE_LABELS}
    whole_pollen = 0
    for row in rows:
        eligible = row["review_eligibility"] == "eligible"
        mapping = cast(dict[str, object] | None, row["classification_mapping"])
        pollen = (
            eligible
            and mapping is not None
            and mapping["source_element_type"] == "pollen"
        )
        row["participates_in_whole_pollen_category"] = pollen
        row["role_display"] = []
        if not eligible or mapping is None:
            continue
        whole_pollen += int(pollen)
        categories[
            (str(mapping["primary_group_id"]), str(mapping["primary_subgroup_id"]))
        ] += 1
        displays: list[dict[str, object]] = []
        for role in cast(Sequence[str], mapping["role_ids"]):
            if role not in _ROLE_LABELS:
                continue
            label, claim = _ROLE_LABELS[role]
            role_observations[role].add(str(row["observation_id"]))
            displays.append(
                {
                    "role_id": role,
                    "label": label,
                    "taxonomic_qualifier": mapping["taxonomic_qualifier"],
                    "pollen_alone_proves": False,
                    "unproven_claim": claim,
                }
            )
        row["role_display"] = displays
    payload["category_counts"] = [
        {
            "primary_group_id": group,
            "primary_subgroup_id": subgroup,
            "unique_observation_count": count,
        }
        for (group, subgroup), count in sorted(categories.items())
    ]
    payload["whole_pollen_category_observation_count"] = whole_pollen
    payload["crop_indicator_totals"] = [
        {
            "role_id": role,
            "label": label,
            "unique_observation_count": len(role_observations[role]),
            "pollen_alone_proves": False,
            "unproven_claim": claim,
        }
        for role, (label, claim) in _ROLE_LABELS.items()
    ]
    payload["crop_indicator_union_observation_count"] = len(
        set().union(*role_observations.values())
    )
    return ClassificationEligibilityResult(_canonical(payload), _digest(payload))
