"""Original whole-site folds and explicit synthetic chronology declarations."""

from collections.abc import Mapping

from bijux_pollenomics.analysis.lra_validation.contracts import Fold, site_group_id
from bijux_pollenomics.analysis.lra_validation.temporal import (
    CalendarSupport,
    RecordChronology,
    TemporalAdmissionPlan,
)


def support(*intervals: tuple[float, float]) -> CalendarSupport:
    return CalendarSupport(
        intervals or ((5400, 5600),), "a" * 64, "synthetic-calendar-support"
    )


def plan(
    *,
    ages: Mapping[str, CalendarSupport | None] | None = None,
    train_groups: tuple[tuple[str, ...], ...] = (
        ("anchor",),
        ("source", "source-alias"),
    ),
    test_groups: tuple[tuple[str, ...], ...] = (("target",),),
    embargo: float = 200,
    lead: float = 600,
) -> TemporalAdmissionPlan:
    training = tuple(record for group in train_groups for record in group)
    targets = tuple(record for group in test_groups for record in group)
    groups = train_groups + test_groups
    fold = Fold(
        "outer-original",
        training,
        targets,
        tuple(site_group_id(group) for group in train_groups),
        tuple(site_group_id(group) for group in test_groups),
    )
    supplied: dict[str, CalendarSupport | None] = {
        record: support() for record in training
    }
    supplied.update({record: support((5000, 5200)) for record in targets})
    supplied.update(ages or {})
    return TemporalAdmissionPlan(
        fold,
        tuple((record, site_group_id(group)) for group in groups for record in group),
        tuple(
            RecordChronology(record, supplied[record]) for record in training + targets
        ),
        ("anchor",),
        embargo,
        lead,
        "b" * 64,
        "declared synthetic scenario; no reviewer authentication",
    )
