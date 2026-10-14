"""Freeze and verify outcome-free experiment splits before numerical work."""

from .persistence import PrefitSplitAuthority, freeze_experiment_split

__all__ = ["PrefitSplitAuthority", "freeze_experiment_split"]
