"""One timed, coefficient-width frontier over a complete geometry population."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import heapq
import math
import time

from .arithmetic import Interval
from .coefficients import (
    EPSILON,
    Q_WIDTH,
    TRIANGLE_WIDTH,
    CoefficientResult,
    assemble_coefficients,
)
from .kernel import Geometry
from .quadrature import (
    SEVEN_NODE_RULE,
    Box,
    IntegralResult,
    Integrand,
    Panel,
    ResourceRefusal,
    WorkBudget,
    positive_panel,
)
from .radial_partition import RadialPartition


@dataclass(frozen=True)
class PopulationResult:
    results: tuple[CoefficientResult | None, ...]
    refusals: tuple[str | None, ...]
    budgets: tuple[WorkBudget, ...]
    elapsed_seconds: float

    def __post_init__(self) -> None:
        if not (
            type(self.results) is tuple
            and type(self.refusals) is tuple
            and type(self.budgets) is tuple
            and 1 <= len(self.results) <= 6
            and len(self.results) == len(self.refusals) == len(self.budgets)
            and math.isfinite(self.elapsed_seconds)
            and self.elapsed_seconds >= 0
        ):
            raise ValueError("Complete bounded population disposition required")


@dataclass
class _Domain:
    function: Integrand
    dimension: int
    target: Fraction
    queue: list[tuple[Fraction, int, Panel]]
    lower: Fraction
    upper: Fraction

    def result(self, refusal: str | None) -> IntegralResult:
        enclosure = Interval(self.lower, self.upper)
        closed = enclosure.width <= self.target
        return IntegralResult(
            enclosure,
            tuple(row[2] for row in sorted(self.queue, key=lambda row: row[1])),
            "certified_width" if closed else "refuse_unresolved",
            None if closed else refusal,
            SEVEN_NODE_RULE,
        )


@dataclass
class _Case:
    partition: RadialPartition
    budget: WorkBudget
    domains: list[_Domain] = field(default_factory=list)
    result: CoefficientResult | None = None
    refusal: str | None = None
    sequence: int = 0

    def assemble(self) -> None:
        self.result = assemble_coefficients(
            self.partition.geometry,
            tuple(domain.result(self.refusal) for domain in self.domains),
            rule=SEVEN_NODE_RULE,
            conditioning=self.partition,
            require_local_allocations=False,
        )

    @property
    def score(self) -> Fraction:
        assert self.result is not None
        return (
            max(
                self.result.homogeneous.width,
                self.result.first.width,
                self.result.second.width,
            )
            / EPSILON
        )


def _initial_domains(case: _Case) -> None:
    model = case.partition.geometry
    functions: tuple[Integrand, ...] = (
        lambda arguments: model.contact_survival(arguments[0]),
        lambda arguments: model.outer_survival(arguments[0]),
    ) + tuple(domain.evaluate for domain in case.partition.domains)
    local_width = 2 * TRIANGLE_WIDTH / len(case.partition.domains)
    for index, function in enumerate(functions):
        if len(case.domains) >= case.budget.max_queue:
            raise ResourceRefusal("queue_ceiling")
        case.budget.add_leaf()
        dimension = 1 if index < 2 else 2
        box: Box = ((Fraction(0), Fraction(1)),) * dimension
        panel = positive_panel(function, box, case.budget, rule=SEVEN_NODE_RULE)
        enclosure = panel.enclosure
        case.domains.append(
            _Domain(
                function,
                dimension,
                Q_WIDTH if index < 2 else local_width,
                [(-enclosure.width, case.sequence, panel)],
                enclosure.lower,
                enclosure.upper,
            )
        )
        case.sequence += 1
    case.assemble()


def _refine(case: _Case) -> None:
    case.budget.check()
    if sum(len(domain.queue) for domain in case.domains) + 1 > case.budget.max_queue:
        raise ResourceRefusal("queue_ceiling")
    index = min(
        range(len(case.domains)),
        key=lambda i: (
            case.domains[i].queue[0][0] * (2 if i < 2 else 1),
            i,
            case.domains[i].queue[0][1],
        ),
    )
    domain = case.domains[index]
    parent = domain.queue[0][2]
    axis = max(range(domain.dimension), key=lambda j: (parent.directional_radii[j], -j))
    lower, upper = parent.box[axis]
    midpoint = (lower + upper) / 2
    boxes: list[Box] = []
    for interval in ((lower, midpoint), (midpoint, upper)):
        coordinates = list(parent.box)
        coordinates[axis] = interval
        boxes.append(tuple(coordinates))
    case.budget.add_leaf()
    # Attempted work remains charged, but neither child replaces its parent
    # unless both certificates have closed within the common resource envelope.
    children = [
        positive_panel(domain.function, box, case.budget, rule=SEVEN_NODE_RULE)
        for box in boxes
    ]
    heapq.heappop(domain.queue)
    domain.lower -= parent.enclosure.lower
    domain.upper -= parent.enclosure.upper
    for child in children:
        case.sequence += 1
        heapq.heappush(domain.queue, (-child.enclosure.width, case.sequence, child))
        domain.lower += child.enclosure.lower
        domain.upper += child.enclosure.upper
    case.assemble()


def enclose_population(
    geometries: tuple[Geometry, ...],
    *,
    wall_seconds: float = 160,
    max_leaves: int = 4096,
    max_attempts: int = 8191,
    max_nodes: int = 73719,
    max_queue: int = 4096,
) -> PopulationResult:
    """Close every initial domain, then refine the worst unresolved final width.

    Geometries are the sole mathematical inputs. Local quadrature allocations
    remain visible diagnostics; only complete coverage and all three final full
    widths at most EPSILON establish scientific precision. Each case keeps its
    own non-resetting work counters, all tied to one population start and clock.
    """
    if (
        type(geometries) is not tuple
        or not 1 <= len(geometries) <= 6
        or any(type(model) is not Geometry for model in geometries)
    ):
        raise TypeError("One to six exact geometries in an ordered tuple required")
    if (
        type(wall_seconds) not in (int, float)
        or not math.isfinite(wall_seconds)
        or not 0 < wall_seconds <= 160
    ):
        raise ValueError("Population wall limit must only lower the 160-second ceiling")
    started = time.monotonic()
    budgets = tuple(
        WorkBudget(
            max_leaves=max_leaves,
            max_attempts=max_attempts,
            max_nodes=max_nodes,
            max_queue=max_queue,
            wall_seconds=wall_seconds,
            started=started,
        )
        for _ in geometries
    )
    cases: list[_Case | None] = []
    refusals: list[str | None] = []
    for model, budget in zip(geometries, budgets, strict=True):
        try:
            cases.append(_Case(RadialPartition.build(model), budget))
            refusals.append(None)
        except ResourceRefusal as error:
            cases.append(None)
            refusals.append(str(error))
    for index, case in enumerate(cases):
        if case is None:
            continue
        try:
            case.budget.check()
            _initial_domains(case)
        except ResourceRefusal as error:
            prefix = (
                "initial_coverage_incomplete"
                if case.domains or case.budget.attempts
                else "not_executed"
            )
            case.refusal = f"{prefix}:{error}"
            refusals[index] = case.refusal
    while True:
        active = [
            (i, case)
            for i, case in enumerate(cases)
            if case is not None
            and case.result is not None
            and case.result.status != "certified_width"
            and case.refusal is None
        ]
        if not active:
            break
        index, case = min(active, key=lambda row: (-row[1].score, row[0]))
        try:
            _refine(case)
        except ResourceRefusal as error:
            case.refusal = str(error)
            refusals[index] = case.refusal
            case.assemble()
    return PopulationResult(
        tuple(case.result if case is not None else None for case in cases),
        tuple(refusals),
        budgets,
        time.monotonic() - started,
    )
