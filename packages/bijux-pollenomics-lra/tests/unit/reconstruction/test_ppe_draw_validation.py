"""PPE sampling must not discard complex measurements."""

from copy import deepcopy
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.draws import rnorm_reveals


@pytest.mark.parametrize("field", ["mean", "sds"])
@pytest.mark.parametrize(
    "value",
    [
        1 + 0j,
        [1 + 99j],
        np.array([1 + 99j]),
        np.array([1 + 99j], dtype=object),
        pd.Series([1 + 99j]),
    ],
)
def test_complex_ppe_input_refuses_before_generator_advances(
    field: str, value: object
) -> None:
    rng = np.random.default_rng(123)
    before = deepcopy(rng.bit_generator.state)
    arguments: dict[str, object] = {"mean": np.array([1.0]), "sds": np.array([0.1])}
    arguments[field] = value
    with pytest.raises(ValidationError, match=field + " cannot contain complex"):
        rnorm_reveals(1, mean=arguments["mean"], sds=arguments["sds"], rng=rng)
    assert rng.bit_generator.state == before


def test_real_scalar_broadcast_remains_reproducible() -> None:
    rng = np.random.default_rng(123)
    expected_rng = np.random.default_rng(123)
    actual = rnorm_reveals(2, mean=1.0, sds=0.1, rng=rng)
    expected = expected_rng.normal(np.ones(2), np.full(2, 0.1))
    np.testing.assert_array_equal(actual, expected)
    assert rng.bit_generator.state == expected_rng.bit_generator.state


def test_array_source_is_consumed_once_before_sampling() -> None:
    class ChangingArray:
        def __init__(self) -> None:
            self.calls = 0

        def __array__(self, dtype: Any = None) -> np.ndarray[Any, Any]:
            self.calls += 1
            return cast(
                np.ndarray[Any, Any],
                np.array([1.0] if self.calls == 1 else [1.0 + 99j], dtype=dtype),
            )

    value = ChangingArray()
    result = rnorm_reveals(1, mean=value, sds=0, rng=1)
    assert value.calls == 1
    np.testing.assert_array_equal(result, [1.0])


def test_high_level_reveals_parameter_admission_already_refuses_complex_ppe() -> None:
    from bijux_pollenomics_lra.models.configuration import RevealsConfig
    from bijux_pollenomics_lra.resources.examples import load_love_example
    from bijux_pollenomics_lra.workflows.regional import run_reveals

    _, regional, examples, _ = load_love_example()
    parameters = examples["ppes"].copy()
    parameters["ppe"] = parameters["ppe"].astype(complex)
    with pytest.raises(ValidationError, match="complex"):
        run_reveals(regional, parameters, RevealsConfig("lake", 300, iterations=2))
