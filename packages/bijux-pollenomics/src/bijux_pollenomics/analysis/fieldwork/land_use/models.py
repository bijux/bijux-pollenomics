from __future__ import annotations

from dataclasses import dataclass

LANDCLIM_DATASET_ID = "937075"
CONTEXT_RADIUS_KM = 20
HOJEA_REPORT_URL = (
    "https://hojea.se/rapporter/"
    "2003_Arkeologisk_foerundersoekning_Gullaakra_Vesums_mossar.pdf"
)


@dataclass(frozen=True)
class _Target:
    requested_name: str
    registry_name: str
    latitude: float
    longitude: float
    target_class: str
    lake_decision: str
    decision_reason: str
    coordinate_source: str


GOVERNED_NAMED_TARGETS = (
    _Target(
        requested_name="Finjasjön",
        registry_name="Finjasjön",
        latitude=56.133926,
        longitude=13.703841,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Östra Ringsjön",
        registry_name="Östra Ringsjön",
        latitude=55.872216,
        longitude=13.536269,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Havgårdssjön",
        registry_name="Havgårdssjön",
        latitude=55.485801,
        longitude=13.354724,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Named project lake resolved to one official SVAR lake.",
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Bjäresjösjön",
        registry_name="Bjäresjö",
        latitude=55.45927,
        longitude=13.751909,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason=(
            "Project name Bjäresjösjön resolved to the official SVAR water-surface "
            "name Bjäresjö."
        ),
        coordinate_source="project brief coordinate; official registry identity published separately",
    ),
    _Target(
        requested_name="Gullåkra",
        registry_name="",
        latitude=55.656945,
        longitude=13.210916,
        target_class="archaeological_wetland_context",
        lake_decision="exclude_lake_ranking_include_context",
        decision_reason=(
            "The named place is Gullåkra mosse in the archaeological report and has "
            "no unique SMHI SVAR lake match. It belongs in wetland and archaeology "
            "context, not the lake-sampling ranking."
        ),
        coordinate_source=(
            "Höje å report project coordinate converted from RT90 2.5 gon V; "
            "project-area precision"
        ),
    ),
    _Target(
        requested_name="Vesums mossar",
        registry_name="",
        latitude=55.659062,
        longitude=13.213319,
        target_class="archaeological_wetland_context",
        lake_decision="exclude_lake_ranking_include_context",
        decision_reason=(
            "The named place is Vesums mosse in the archaeological report and has "
            "no unique SMHI SVAR lake match. It belongs in wetland and archaeology "
            "context, not the lake-sampling ranking."
        ),
        coordinate_source=(
            "Höje å report project coordinate converted from RT90 2.5 gon V; "
            "project-area precision"
        ),
    ),
)
