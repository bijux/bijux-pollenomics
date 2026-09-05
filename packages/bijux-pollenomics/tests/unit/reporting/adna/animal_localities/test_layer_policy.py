"""Animal atlas layer-role, chronology, and styling policy tests."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_pollenomics.core.repository import repository_data_root
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


def test_real_animal_layers_withhold_context_dates_from_numeric_playback(
    tmp_path: Path,
) -> None:
    bundle = animal_localities.build_tracked_animal_atlas_bundle(
        data_root=repository_data_root(__file__),
        output_dir=tmp_path,
        atlas_slug="chronology-contract",
    )
    layers = {str(layer["species_latin_name"]): layer for layer in bundle.point_layers}
    pig_layer = layers["Sus scrofa domesticus"]
    pig_features = cast(list[dict[str, object]], pig_layer["features"])

    assert pig_layer["applies_time_filter"] is False
    assert {
        str(feature["title"]): (
            feature["time_start_bp"],
            feature["time_end_bp"],
            cast(dict[str, object], feature["temporal_semantics"])[
                "comparability_posture"
            ],
        )
        for feature in pig_features
    } == {
        "Bundsø": (None, None, "contextual_label_only"),
        "Trelleborg": (None, None, "contextual_label_only"),
    }

    all_features = [
        feature
        for layer in bundle.point_layers
        for feature in cast(list[dict[str, object]], layer["features"])
    ]
    numeric_caveated = [
        feature
        for feature in all_features
        if cast(dict[str, object], feature["temporal_semantics"])[
            "comparability_posture"
        ]
        == "numeric_interval_with_caveat"
    ]
    untimed = [
        feature
        for feature in all_features
        if feature["time_start_bp"] is None and feature["time_end_bp"] is None
    ]

    assert numeric_caveated == []
    assert len(untimed) == 67
    assert {
        cast(dict[str, object], feature["temporal_semantics"])["comparability_posture"]
        for feature in untimed
    } == {"contextual_label_only", "unresolved"}

    cat_layer = layers["Felis catus"]
    cat_features = cast(list[dict[str, object]], cat_layer["features"])
    wildcat_feature = next(
        feature
        for feature in cat_features
        if "Felis silvestris silvestris"
        in cast(list[str], feature["source_native_scientific_names"])
    )
    wildcat_popup = {
        str(item["label"]): str(item["value"])
        for item in cast(list[dict[str, object]], wildcat_feature["popup_rows"])
    }
    assert "Felis silvestris silvestris" in wildcat_popup["Source-native taxa"]
    assert "project species mismatch" in wildcat_popup["Taxon alignment"]
    assert any(
        "different from the configured project species" in str(item["value"])
        for item in cast(list[dict[str, object]], wildcat_feature["popup_rows"])
        if item["label"] == "Warning"
    )

    for feature in pig_features:
        popup = {
            str(item["label"]): str(item["value"])
            for item in cast(list[dict[str, object]], feature["popup_rows"])
        }
        assert popup["Chronology evidence class"] == "archaeological context date"
        assert popup["Chronology precision posture"] == "sample approximate or modeled"
        assert "radiocarbon" not in " ".join(popup.values()).casefold()
