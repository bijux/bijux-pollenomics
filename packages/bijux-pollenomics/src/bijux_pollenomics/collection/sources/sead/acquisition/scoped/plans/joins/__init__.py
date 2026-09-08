"""Full-evidence SEAD relational join plans."""

from __future__ import annotations

from ...models import SeadJoinPlan as SeadJoinPlan
from ..full_tables import _CORE_JOIN_PLANS as _CORE_JOIN_PLANS
from ..full_tables import _LOOKUP_JOIN_PLANS as _LOOKUP_JOIN_PLANS
from .datasets import _DATASET_JOIN_PLANS
from .measurements import _MEASUREMENT_JOIN_PLANS
from .taxonomy import _TAXONOMY_JOIN_PLANS
from .values import _VALUE_JOIN_PLANS

SEAD_FULL_EVIDENCE_JOIN_PLANS = (
    *_CORE_JOIN_PLANS,
    *_LOOKUP_JOIN_PLANS,
    *_MEASUREMENT_JOIN_PLANS,
    *_TAXONOMY_JOIN_PLANS,
    *_VALUE_JOIN_PLANS,
    *_DATASET_JOIN_PLANS,
)
