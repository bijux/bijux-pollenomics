from __future__ import annotations


_ACCEPTED_STATUSES = {"accepted", "accepted_qualified"}


_AMBIGUOUS_STATUSES = {"contested", "refused"}


_CLASSIFICATION_CONTRACT_VERSION = "1.0.0"


_COUNTRY_CODES = {"SE", "DK", "NO", "FI"}


_SOURCE_COUNTRY_CODES = {*_COUNTRY_CODES, "UNASSIGNED", "OUTSIDE"}


_COORDINATE_QUALITIES = {"exact", "reported", "approximate", "centroid"}


_CLASSIFICATION_CONFIDENCES = {"high", "moderate", "low"}


_QUALIFIERS = {
    "exact",
    "cf",
    "aff",
    "type",
    "group",
    "aggregate",
    "undifferentiated",
    "unknown",
}


_POLLEN_HIERARCHY = {
    "forest_woodland": {
        "coniferous_trees",
        "broadleaved_deciduous_trees",
        "broadleaved_evergreen_trees",
        "shrubs_and_dwarf_shrubs",
        "forest_understory",
    },
    "open_ground": {
        "grassland_meadow",
        "heathland",
        "ruderal_disturbance",
        "pastoral_associated",
        "open_ground_other",
    },
    "cultivated_plants": {
        "cereals",
        "pulses_legumes",
        "fibre_oil_crops",
        "other_field_crops",
        "horticultural_orchard",
    },
    "wetland_aquatic": {
        "emergent_wetland",
        "aquatic_submerged_floating",
        "shoreline_riparian",
        "wetland_aquatic_other",
    },
    "other_pollen": {
        "ecology_unresolved",
        "taxon_unidentified",
        "mixed_pollen_aggregate",
    },
}


_ROLE_IDS = {
    "direct_crop_confirmed",
    "crop_type_qualified",
    "anthropogenic_indicator",
    "pastoral_indicator",
    "ruderal_disturbance_indicator",
    "arboreal",
    "non_arboreal",
    "conifer",
    "broadleaved_deciduous",
    "broadleaved_evergreen",
    "shrub",
    "open_ground",
    "wetland",
    "aquatic",
    "cultivated",
    "indicator_only",
    "ecology_unresolved",
}


_DIRECT_CROP_ROLES = {"direct_crop_confirmed", "crop_type_qualified"}


_INDICATOR_ROLES = {
    "anthropogenic_indicator",
    "pastoral_indicator",
    "ruderal_disturbance_indicator",
    "indicator_only",
}


_QUALIFIED_TAXONOMIC_QUALIFIERS = {
    "cf",
    "aff",
    "type",
    "group",
    "aggregate",
    "undifferentiated",
}


_TAXON_EVENT_QUALIFIERS = {"exact", "cf", "aff", "type"}


_BIOLOGICAL_RANKS = {
    "species",
    "subspecies",
    "variety",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
}


_QUALIFIER_ACCEPTED_RANKS = {
    "exact": _BIOLOGICAL_RANKS,
    "cf": _BIOLOGICAL_RANKS,
    "aff": _BIOLOGICAL_RANKS,
    "type": {"type", "morphological_type"},
    "group": {"group"},
    "aggregate": {"aggregate"},
    "undifferentiated": {"undifferentiated"},
}


_ROLE_HIERARCHY_COMPATIBILITY = {
    "direct_crop_confirmed": {("cultivated_plants", "*")},
    "crop_type_qualified": {("cultivated_plants", "*")},
    "anthropogenic_indicator": {("open_ground", "*")},
    "pastoral_indicator": {("open_ground", "pastoral_associated")},
    "ruderal_disturbance_indicator": {("open_ground", "ruderal_disturbance")},
    "arboreal": {
        ("forest_woodland", "coniferous_trees"),
        ("forest_woodland", "broadleaved_deciduous_trees"),
        ("forest_woodland", "broadleaved_evergreen_trees"),
    },
    "non_arboreal": {
        ("forest_woodland", "shrubs_and_dwarf_shrubs"),
        ("forest_woodland", "forest_understory"),
        ("open_ground", "*"),
        ("cultivated_plants", "*"),
        ("wetland_aquatic", "*"),
        ("other_pollen", "*"),
    },
    "conifer": {("forest_woodland", "coniferous_trees")},
    "broadleaved_deciduous": {("forest_woodland", "broadleaved_deciduous_trees")},
    "broadleaved_evergreen": {("forest_woodland", "broadleaved_evergreen_trees")},
    "shrub": {("forest_woodland", "shrubs_and_dwarf_shrubs")},
    "open_ground": {("open_ground", "*")},
    "wetland": {("wetland_aquatic", "*")},
    "aquatic": {
        ("wetland_aquatic", "aquatic_submerged_floating"),
        ("wetland_aquatic", "wetland_aquatic_other"),
    },
    "cultivated": {("cultivated_plants", "*")},
    "indicator_only": {("open_ground", "*")},
    "ecology_unresolved": {("other_pollen", "*")},
}


_RESOLUTIONS = (
    "whole_pollen",
    "ecological_group",
    "ecological_subgroup",
    "ecological_role",
    "taxon",
)
