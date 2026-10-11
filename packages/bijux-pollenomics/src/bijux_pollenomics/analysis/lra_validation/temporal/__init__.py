"""Explicit synthetic temporal admission, separate from forecasting and calibration."""

from .admission import TemporalAdmissionResult, admit_forward_time_training
from .contracts import CalendarSupport, RecordChronology, TemporalAdmissionPlan

__all__ = [
    "CalendarSupport",
    "RecordChronology",
    "TemporalAdmissionPlan",
    "TemporalAdmissionResult",
    "admit_forward_time_training",
]
