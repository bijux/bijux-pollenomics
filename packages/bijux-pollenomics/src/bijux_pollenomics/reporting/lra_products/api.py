"""Supported local exploratory report facade; numerical execution is separate."""

from .contracts import LRAPresentation, LRAPresentationRefusal, TemporalProfile
from .workflow import render_lra_report

__all__ = [
    "LRAPresentation",
    "LRAPresentationRefusal",
    "render_lra_report",
    "TemporalProfile",
]
