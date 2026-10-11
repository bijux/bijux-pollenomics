"""Independent vector arithmetic and reference-coordinate contract checks."""

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray
import pandas as pd
import pytest

from bijux_pollenomics_dev.lra_validation.retained_reference.comparison import (
    compare_core_case,
    compare_domain_case,
    contains_statement,
    require_core_population,
    require_domain_parameters,
    require_fixture_sources,
    require_shared_setup,
)


@dataclass
class _CoreCase:
    """Bind synthetic vector coordinates and declared comparison tolerances."""

    name: str
    api: str
    mode: str
    expected: NDArray[np.generic]
    rtol: float
    atol: float
    exact_indices: tuple[int, ...]


@dataclass
class _NamedCase:
    """Retain one synthetic identity for the complete population refusal checks."""

    name: str


@dataclass
class _DomainCase:
    """Declare synthetic domain identity separately from geometry observations."""

    id: str
    kind: str
    semantics: str


def core(
    values: Sequence[float] | Sequence[str] | NDArray[np.float64],
    *,
    exact_indices: tuple[int, ...] = (),
) -> _CoreCase:
    """Describe a synthetic public API vector without running an oracle."""
    return _CoreCase(
        name="fractions",
        api="synthetic",
        mode="unmodified_function",
        expected=np.asarray(values),
        rtol=1e-10,
        atol=1e-10,
        exact_indices=exact_indices,
    )


def row(case: _CoreCase) -> dict[str, object]:
    """Declare the reference coordinates and precommitted tolerances."""
    return {
        "id": "C0000",
        "values": case.expected.size,
        "name": case.name,
        "api": case.api,
        "mode": case.mode,
        "rtol": case.rtol,
        "atol": case.atol,
        "exact_indices": list(case.exact_indices),
    }


def test_independent_rational_vector_and_predeclared_tolerance() -> None:
    """Independent rational vector and predeclared tolerance."""
    expected = np.array([float(Fraction(i, 7)) for i in range(1, 5)])
    case = core(np.arange(1, 5) / 7)
    assert compare_core_case(row(case), case, expected)["status"] == "passed"
    expected[2] += 1e-4
    result = compare_core_case(row(case), case, expected)
    assert result["status"] == "failed"
    assert result["values"] == 4


def test_exact_coordinate_cannot_hide_inside_approximate_tolerance() -> None:
    """Exact coordinate cannot hide inside approximate tolerance."""
    case = core([1.0, 2.0], exact_indices=(0,))
    assert (
        compare_core_case(row(case), case, np.array([1.0, 2.0 + 1e-11]))["status"]
        == "passed"
    )
    assert (
        compare_core_case(row(case), case, np.array([1.0 + 1e-11, 2.0]))["status"]
        == "failed"
    )


@pytest.mark.parametrize(
    "retained",
    [
        [np.nan, np.inf, -np.inf, 2.0],
        [np.nan, -np.inf, -np.inf, 2.0],
        [2.0, np.inf, -np.inf, np.nan],
    ],
)
def test_nonfinite_coordinates_and_infinity_signs(retained: list[float]) -> None:
    """Nonfinite coordinates and infinity signs."""
    case = core([np.nan, np.inf, -np.inf, 2.0])
    result = compare_core_case(row(case), case, np.array(retained))
    assert result["status"] == (
        "passed" if retained[1] > 0 and np.isnan(retained[0]) else "failed"
    )


def test_character_error_sentinel_is_exact() -> None:
    """Character error sentinel is exact."""
    case = core(["error", "radius must be positive"])
    assert (
        compare_core_case(row(case), case, case.expected.copy())["status"] == "passed"
    )
    assert (
        compare_core_case(row(case), case, np.array(["error", "different reason"]))[
            "status"
        ]
        == "failed"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("rtol", 1.0),
        ("atol", 1.0),
        ("api", "other"),
        ("mode", "other"),
        ("exact_indices", [1]),
        ("values", 3),
    ],
)
def test_manifest_contract_drift_refused(field: str, value: object) -> None:
    """Manifest contract drift refused."""
    case = core([1.0, 2.0])
    manifest = row(case)
    manifest[field] = value
    with pytest.raises(ValueError, match="contract differs"):
        compare_core_case(manifest, case, case.expected)


def test_vector_shape_drift_refused() -> None:
    """Vector shape drift refused."""
    case = core([1.0, 2.0])
    with pytest.raises(ValueError, match="contract differs"):
        compare_core_case(row(case), case, np.array([[1.0, 2.0]]))


def test_all_43_core_names_and_ids_required() -> None:
    """All 43 core names and ids required."""
    cases = [_NamedCase(name=f"case-{i}") for i in range(43)]
    manifest = [{"id": f"C{i:04d}", "name": case.name} for i, case in enumerate(cases)]
    require_core_population(manifest, cases)
    with pytest.raises(ValueError, match="43-core"):
        require_core_population(manifest[:-1], cases)
    manifest[1] = dict(manifest[0])
    with pytest.raises(ValueError, match="43-core"):
        require_core_population(manifest, cases)


def test_shared_setup_numeric_equivalence_preserves_strings_and_missing_inputs() -> (
    None
):
    """Shared setup numeric equivalence preserves strings and missing inputs."""
    assert require_shared_setup(['x <- c(0.5, "1")'], 'x <- c(0x1p-1, "1")') == ["x"]
    for script in ['x <- c(0.5, "2")', "other <- 0.5", 'x <- c(0.6, "1")']:
        with pytest.raises(ValueError, match="shared R setup differs"):
            require_shared_setup(['x <- c(0.5, "1")'], script)


def test_domain_vector_geometry_and_source_refusal_are_separate() -> None:
    """Domain vector geometry and source refusal are separate."""
    case = _DomainCase(
        id="S001", kind="forward", semantics="synthetic corrected geometry"
    )
    rings = pd.DataFrame({"inner": [0.0, 2.0], "outer": [2.0, 3.0]})
    # Independently derived annulus areas divided by total area.
    expected = np.array([float(Fraction(4, 9)), float(Fraction(5, 9))])
    result = compare_domain_case(
        case, np.array([4 / 9, 5 / 9]), expected, rings, rings.copy()
    )
    assert result["status"] == "passed"
    assert (
        compare_domain_case(case, np.array([-1.0]), np.array([-1.0]), rings, rings)[
            "status"
        ]
        == "passed"
    )
    assert (
        compare_domain_case(case, np.array([np.nan]), np.array([-1.0]), rings, rings)[
            "status"
        ]
        == "failed"
    )
    with pytest.raises(ValueError, match="geometry or vector shape"):
        compare_domain_case(case, expected, expected, rings[["outer", "inner"]], rings)
    changed = rings.copy()
    outer = changed.loc[1, "outer"]
    assert isinstance(outer, (float, np.floating))
    changed.loc[1, "outer"] = outer + 0.1
    with pytest.raises(AssertionError):
        compare_domain_case(case, expected, expected, changed, rings)


def test_domain_source_refusal_marker_is_exact() -> None:
    """Domain source refusal marker is exact."""
    case = _DomainCase(
        id="S003", kind="ring_refusal", semantics="legacy-source-refusal"
    )
    rings = pd.DataFrame({"inner": [0.0], "outer": [1.0]})
    assert (
        compare_domain_case(case, np.array([1.0]), np.array([1.0]), rings, rings)[
            "status"
        ]
        == "passed"
    )
    assert (
        compare_domain_case(
            case, np.array([1.0 + 1e-11]), np.array([1.0]), rings, rings
        )["status"]
        == "failed"
    )


def test_shared_setup_assignment_boundary_cannot_match_prefixed_name() -> None:
    """Shared setup assignment boundary cannot match prefixed name."""
    with pytest.raises(ValueError, match="shared R setup differs"):
        require_shared_setup(['x <- c(0.5, "1")'], 'prefixx <- c(0.5, "1")')


def test_complete_multiline_case_statement_boundaries() -> None:
    """Complete multiline case statement boundaries."""
    statement = 'run_case("C0028",quote({\nx <- 0.5\nx\n}))'
    script = "before <- 1\n" + statement.replace("0.5", "0x1p-1") + "\nafter <- 2"
    assert contains_statement(statement, script)
    assert not contains_statement(statement, "prefix" + statement)
    assert not contains_statement(statement, statement + "suffix")


def test_fixture_source_pin_preserves_math_drift_but_refuses_input_drift() -> None:
    """Fixture source pin preserves math drift but refuses input drift."""
    fixture = "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_source_domains.py"
    math = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/regional.py"
    original = {fixture: "fixture-hash", math: "original-math"}
    require_fixture_sources({fixture: "fixture-hash", math: "current-math"}, original)
    with pytest.raises(ValueError, match="oracle fixture source differs"):
        require_fixture_sources(
            {fixture: "changed-fixture", math: "current-math"}, original
        )


def test_domain_parameters_freeze_labels_and_physical_values() -> None:
    """Domain parameters freeze labels and physical values."""
    parameters = pd.DataFrame(
        {"taxon": ["oak", "pine"], "ppe": [2.0, 3.0], "fall_speed": [0.02, 0.04]}
    )
    require_domain_parameters(parameters, parameters.copy())
    changed = parameters.copy()
    ppe = changed.loc[1, "ppe"]
    assert isinstance(ppe, (float, np.floating))
    changed.loc[1, "ppe"] = ppe + 1e-14
    with pytest.raises(AssertionError):
        require_domain_parameters(parameters, changed)
    with pytest.raises(ValueError, match="table shape differs"):
        require_domain_parameters(
            parameters, parameters[["ppe", "taxon", "fall_speed"]]
        )
