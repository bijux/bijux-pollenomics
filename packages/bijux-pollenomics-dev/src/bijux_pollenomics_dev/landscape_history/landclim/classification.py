"""Operational vegetation groups on the published 31-taxon denominator."""

from __future__ import annotations

from collections.abc import Mapping
from math import fsum, isfinite

GROUPS = {
    "conifers": ("Abies.alba", "Picea", "Pinus"),
    "broadleaved_trees": (
        "Alnus.glutinosa",
        "Betula",
        "Carpinus.betulus",
        "Carpinus.orientalis",
        "Castanea",
        "Fagus.sylvatica",
        "Fraxinus",
        "Quercus.deciduous",
        "Quercus.evergreen",
        "Tilia",
        "Ulmus",
    ),
    "shrubs_heath": (
        "Buxus.sempervirens",
        "Calluna.vulgaris",
        "Corylus.avellana",
        "Ericaceae",
        "Juniperus",
        "Phillyrea",
        "Pistacia",
        "Salix",
    ),
    "non_cereal_herbs": (
        "Amanranthaceae.Chenopodiaceae",
        "Artemisia",
        "Cyperaceae",
        "Filipendula",
        "Plantago.lanceolata.type",
        "Poaceae",
        "Rumex.acetosa.t",
    ),
    "cereals": ("Cerealia.t", "Secale"),
}
TAXA = tuple(taxon for members in GROUPS.values() for taxon in members)
CLOSURE_TOLERANCE_PP = 1e-8
METRIC_KEYS = (
    *GROUPS,
    "tree_assigned",
    "non_tree",
    "other_non_tree",
    "source_OL",
    "source_AL",
    "cereal_share_non_tree",
)
DEFINITIONS = {
    "unit": "percentage_cover",
    "groups": GROUPS,
    "tree_assigned": "Conifers plus broadleaved trees; tree-associated operational proxy, not measured forest.",
    "shrubs_heath": "Operationally includes Corylus, Juniperus, Salix, Buxus, Phillyrea, Pistacia and heath; mixed tree/shrub life forms remain an assumption.",
    "non_tree": "Shrubs/heath plus non-cereal herbs plus cereals on the same 31-taxon denominator; not the published OL class.",
    "other_non_tree": "Shrubs/heath plus non-cereal herbs; cereals are excluded.",
    "source_OL": "Unchanged published OL=LSE+GL+AL; includes cereals and low shrubs, but not all operational shrubs.",
    "source_AL": "Unchanged published AL agricultural/cereal cover; nested within source OL.",
    "cereal_share_non_tree": "100*cereals/non_tree; ratio of aggregated covers, not average of cell ratios; undefined at zero denominator.",
    "source_ET_ST": "Source ET and ST include tall-shrub PFTs; their sum is not shrub-exclusive forest.",
    "denominator": "31 modeled taxa, direct sums without clipping or renormalization.",
}


def classify_means(estimates: Mapping[str, float]) -> dict[str, float | None]:
    """Refuse unsupported compositions and sum a disjoint operational partition."""
    if not set(TAXA).issubset(estimates) or not {"OL", "AL"}.issubset(estimates):
        raise ValueError("missing_mean")
    if any(not isfinite(v) for v in estimates.values()):
        raise ValueError("nonfinite_mean")
    if any(v < 0 for v in estimates.values()):
        raise ValueError("negative_mean")
    total = fsum(estimates[t] for t in TAXA)
    if total == 0:
        raise ValueError("zero_mass")
    if abs(total - 100) > CLOSURE_TOLERANCE_PP:
        raise ValueError("closure_mismatch")
    groups = {
        key: fsum(estimates[t] for t in members) for key, members in GROUPS.items()
    }
    if abs(groups["cereals"] - estimates["AL"]) > CLOSURE_TOLERANCE_PP:
        raise ValueError("cereal_source_mismatch")
    taxon_open = fsum(
        (estimates["Calluna.vulgaris"], groups["non_cereal_herbs"], groups["cereals"])
    )
    if abs(taxon_open - estimates["OL"]) > CLOSURE_TOLERANCE_PP:
        raise ValueError("open_source_mismatch")
    if {"LSE", "GL"}.issubset(estimates) and abs(
        fsum(estimates[t] for t in ("LSE", "GL", "AL")) - estimates["OL"]
    ) > CLOSURE_TOLERANCE_PP:
        raise ValueError("open_source_mismatch")
    non_tree = fsum(groups[k] for k in ("shrubs_heath", "non_cereal_herbs", "cereals"))
    return {
        **groups,
        "tree_assigned": fsum(groups[k] for k in ("conifers", "broadleaved_trees")),
        "non_tree": non_tree,
        "other_non_tree": fsum(groups[k] for k in ("shrubs_heath", "non_cereal_herbs")),
        "source_OL": estimates["OL"],
        "source_AL": estimates["AL"],
        "cereal_share_non_tree": 100 * groups["cereals"] / non_tree
        if non_tree
        else None,
    }
