"""Compatibility facade for authenticated spatial-block intervals."""

from ..intervals.spatial_blocks import (
    AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE,
    freeze_authenticated_block_pollen_interval,
    freeze_authenticated_block_pollen_rows,
)

__all__ = [
    "AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE",
    "freeze_authenticated_block_pollen_interval",
    "freeze_authenticated_block_pollen_rows",
]
