"""Full-evidence SEAD table acquisition plans."""

from __future__ import annotations

from ...models import SeadDependency as SeadDependency
from ...models import SeadJoinPlan as SeadJoinPlan
from ...models import SeadScopedTablePlan as SeadScopedTablePlan
from ..scoped import _scoped_plan as _scoped_plan
from .foundations import _FOUNDATION_TABLE_PLANS
from .lookup_relations import _LOOKUP_JOIN_PLANS as _LOOKUP_JOIN_PLANS
from .observation_values import _OBSERVATION_VALUE_TABLE_PLANS
from .required_relations import _CORE_JOIN_PLANS as _CORE_JOIN_PLANS
from .semantic_dimensions import _SEMANTIC_DIMENSION_TABLE_PLANS
from .stewardship import _STEWARDSHIP_TABLE_PLANS
from .taxonomy import _TAXONOMY_TABLE_PLANS

SEAD_FULL_EVIDENCE_TABLE_PLANS = (
    *_FOUNDATION_TABLE_PLANS,
    *_OBSERVATION_VALUE_TABLE_PLANS,
    *_TAXONOMY_TABLE_PLANS,
    *_SEMANTIC_DIMENSION_TABLE_PLANS,
    *_STEWARDSHIP_TABLE_PLANS,
)
