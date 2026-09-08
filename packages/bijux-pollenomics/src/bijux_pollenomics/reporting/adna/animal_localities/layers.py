"""Animal atlas layer classification, description, and presentation policy."""

from __future__ import annotations

_SPECIES_STYLES = {
    "Equus caballus": {"fill": "#8b5e34", "stroke": "#5d3f21"},
    "Sus scrofa domesticus": {"fill": "#c2410c", "stroke": "#7c2d12"},
    "Ovis aries": {"fill": "#15803d", "stroke": "#14532d"},
    "Bos taurus": {"fill": "#92400e", "stroke": "#78350f"},
    "Capra hircus": {"fill": "#0f766e", "stroke": "#134e4a"},
    "Canis lupus familiaris": {"fill": "#1d4ed8", "stroke": "#1e3a8a"},
    "Felis catus": {"fill": "#9333ea", "stroke": "#6b21a8"},
    "Camelus dromedarius": {"fill": "#b45309", "stroke": "#78350f"},
    "Rangifer tarandus": {"fill": "#0369a1", "stroke": "#0c4a6e"},
    "Equus asinus": {"fill": "#6d28d9", "stroke": "#4c1d95"},
}

_ANIMAL_SCOPE_GROUPS = {
    "domesticated_core": "animal-domesticated-evidence",
    "comparator": "animal-comparator-evidence",
    "wild_or_progenitor_context": "animal-progenitor-evidence",
}


def _layer_group_for(product_role: object) -> str:
    role = str(product_role).strip()
    if role not in _ANIMAL_SCOPE_GROUPS:
        raise ValueError(f"unsupported animal scope: {role}")
    return _ANIMAL_SCOPE_GROUPS[role]


def _animal_scope_for(dataset_review: dict[str, object]) -> str:
    return (
        "comparator"
        if dataset_review.get("product_role") == "comparator"
        else "domesticated_core"
    )


def _layer_description_for(
    *,
    species_common_name: str,
    dataset_review: dict[str, object],
    animal_scope: str | None = None,
) -> str:
    role = (animal_scope or _animal_scope_for(dataset_review)).replace("_", " ")
    return (
        f"Tracked {species_common_name} aDNA locality leads staged from sample-backed "
        f"or site-backed atlas evidence rows. Current role: {role}."
    )


def _layer_style_for(species_latin_name: str) -> dict[str, str]:
    return _SPECIES_STYLES.get(
        species_latin_name,
        {"fill": "#475569", "stroke": "#1e293b"},
    )


def _alpha(color: str, opacity: float) -> str:
    color = color.lstrip("#")
    if len(color) != 6:
        return color
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {opacity:.2f})"
