"""Selected-source guards retain their domain owner through the public facade."""

import pytest


def test_selected_source_guards_are_public_and_preserve_native_semantics() -> None:
    from bijux_pollenomics.collection.sources import neotoma
    from bijux_pollenomics.collection.sources.neotoma.client import (
        validate_neotoma_selected_download,
    )
    from bijux_pollenomics.collection.sources.neotoma.relational.chronology import (
        require_neotoma_point_age,
    )
    from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
        is_native_pollen,
    )

    assert (
        neotoma.validate_neotoma_selected_download is validate_neotoma_selected_download
    )
    assert neotoma.require_neotoma_point_age is require_neotoma_point_age
    assert neotoma.is_native_pollen is is_native_pollen
    assert neotoma.require_neotoma_point_age(100, younger_bp=50, older_bp=150) == 100
    with pytest.raises(ValueError, match="point_outside_interval"):
        neotoma.require_neotoma_point_age(200, younger_bp=50, older_bp=150)
    assert neotoma.is_native_pollen("pollen", "pollen")
    assert not neotoma.is_native_pollen("pollen", "spore")
