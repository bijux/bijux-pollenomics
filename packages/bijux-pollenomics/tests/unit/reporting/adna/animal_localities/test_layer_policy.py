"""Animal atlas layer-role and styling policy tests."""

from bijux_pollenomics.reporting.adna import animal_localities


def test_role_policy_keeps_comparator_and_domesticated_products_separate() -> None:
    comparator: dict[str, object] = {"product_role": "comparator"}
    domesticated: dict[str, object] = {"product_role": "domesticated_core"}

    assert animal_localities._layer_group_for(comparator["product_role"]) == (
        "animal-comparator-evidence"
    )
    assert animal_localities._animal_scope_for(comparator) == "comparator"
    assert animal_localities._layer_group_for(domesticated["product_role"]) == (
        "animal-domesticated-evidence"
    )
    assert animal_localities._animal_scope_for(domesticated) == "domesticated_core"


def test_species_style_and_alpha_fallbacks_are_stable() -> None:
    assert animal_localities._layer_style_for("Ovis aries") == {
        "fill": "#15803d",
        "stroke": "#14532d",
    }
    assert animal_localities._layer_style_for("Unknown species") == {
        "fill": "#475569",
        "stroke": "#1e293b",
    }
    assert animal_localities._alpha("#15803d", 0.1) == "rgba(21, 128, 61, 0.10)"
    assert animal_localities._alpha("invalid", 0.1) == "invalid"
