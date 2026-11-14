"""Behavioral checks for published-model landscape history."""

from __future__ import annotations

import pytest

from .support import TAXA, means


def test_partition_keeps_shrubs_and_cereals_distinct() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.classification import (
        GROUPS,
        classify_means,
    )

    flattened = [taxon for taxa in GROUPS.values() for taxon in taxa]
    assert sorted(flattened) == sorted(TAXA)
    assert len(flattened) == len(set(flattened)) == 31
    x = classify_means(
        means(
            Pinus=20,
            Betula=30,
            **{
                "Corylus.avellana": 10,
                "Salix": 5,
                "Juniperus": 5,
                "Poaceae": 20,
                "Cerealia.t": 6,
                "Secale": 4,
            },
        )
    )
    assert x["conifers"] == 20
    assert x["broadleaved_trees"] == 30
    assert x["shrubs_heath"] == 20
    assert x["non_cereal_herbs"] == 20
    assert x["cereals"] == 10
    assert x["tree_assigned"] == 50
    assert x["non_tree"] == 50
    assert x["other_non_tree"] == 40
    assert x["cereal_share_non_tree"] == 20
    assert x["source_OL"] == 30
    assert x["source_AL"] == 10


@pytest.mark.parametrize("change", ["negative", "missing", "nan", "closure", "cereals"])
def test_unsupported_mean_vectors_are_refused(change: str) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.classification import (
        classify_means,
    )

    x = means(Pinus=100)
    if change == "negative":
        x["Betula"] = -1
        x["Pinus"] = 101
    elif change == "missing":
        del x["Betula"]
    elif change == "nan":
        x["Betula"] = float("nan")
    elif change == "closure":
        x["Pinus"] = 99
    else:
        x["AL"] = 2
    with pytest.raises(ValueError):
        classify_means(x)


def test_zero_non_tree_has_no_cereal_ratio() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.classification import (
        classify_means,
    )

    assert classify_means(means(Pinus=100))["cereal_share_non_tree"] is None


def test_low_heath_and_tall_heath_do_not_share_source_open_definition() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.classification import (
        classify_means,
    )

    x = classify_means(means(Pinus=30, Ericaceae=50, **{"Calluna.vulgaris": 20}))
    assert x["shrubs_heath"] == 70
    assert x["non_tree"] == 70
    assert x["source_OL"] == 20


def test_source_open_cannot_reclassify_tall_heath_as_low_heath() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.classification import (
        classify_means,
    )

    values = means(Ericaceae=100)
    values["OL"] = 100
    with pytest.raises(ValueError, match="open_source_mismatch"):
        classify_means(values)
