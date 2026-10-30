"""Constructed positive source quantities; no copied publisher observations."""

from __future__ import annotations

from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.inputs import (
    RADII,
    SITES,
    NativeSource,
)


def synthetic_source() -> NativeSource:
    """Provide ten labelled synthetic sites on all declared radius labels."""
    return NativeSource(
        {site: (10 + i, 20, 30, 40, 10) for i, site in enumerate(SITES)},
        {
            (site, radius): (float(i + 1), 2.0, 3.0, 4.0, 5.0)
            for i, site in enumerate(SITES)
            for radius in RADII
        },
        {
            (site, radius): (str(i + 1) + ".00", "2.0", "3.000", "4", "5.0")
            for i, site in enumerate(SITES)
            for radius in RADII
        },
        {site: (0.0, float(i)) for i, site in enumerate(SITES)},
    )
