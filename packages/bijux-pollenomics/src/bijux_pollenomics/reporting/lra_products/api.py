"""Supported local exploratory report facade; numerical execution is separate."""

from .contracts import LRAPresentation, LRAPresentationRefusal, TemporalProfile
from .joint.api import JointLRAPresentation, render_joint_lra_report
from .workflow import render_lra_report

__all__ = [
    "JointLRAPresentation",
    "LRAPresentation",
    "LRAPresentationRefusal",
    "render_joint_lra_report",
    "render_lra_report",
    "TemporalProfile",
]
