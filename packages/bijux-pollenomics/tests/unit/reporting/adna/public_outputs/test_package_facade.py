from __future__ import annotations

import bijux_pollenomics.reporting.adna.public_outputs as public_outputs
from bijux_pollenomics.reporting.adna.public_outputs.chronology_comparisons import (
    _interval_from_row as owned_interval_from_row,
    _intervals_overlap as owned_intervals_overlap,
    _normalize_interval as owned_normalize_interval,
)
from bijux_pollenomics.reporting.adna.public_outputs.farming_scenario import (
    _build_farming_history_scenario as owned_build_farming_history_scenario,
)
from bijux_pollenomics.reporting.adna.public_outputs.first_appearance import (
    _build_first_appearance_by_country as owned_build_first_appearance_by_country,
    _first_signal_bp as owned_first_signal_bp,
)


def test_package_facade_preserves_the_public_contract() -> None:
    assert public_outputs.__all__ == ["publish_public_animal_reporting_outputs"]
    assert callable(public_outputs.publish_public_animal_reporting_outputs)


def test_package_facade_preserves_existing_private_consumer_imports() -> None:
    assert public_outputs._interval_from_row is owned_interval_from_row
    assert public_outputs._intervals_overlap is owned_intervals_overlap
    assert public_outputs._normalize_interval is owned_normalize_interval
    assert (
        public_outputs._build_farming_history_scenario
        is owned_build_farming_history_scenario
    )
    assert (
        public_outputs._build_first_appearance_by_country
        is owned_build_first_appearance_by_country
    )
    assert public_outputs._first_signal_bp is owned_first_signal_bp
