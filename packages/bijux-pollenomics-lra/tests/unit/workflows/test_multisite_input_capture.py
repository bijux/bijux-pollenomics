"""Multisite source inputs remain validated at numerical consumption."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    ValidationError,
    run_reveals_multisite,
)
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.workflows import multisite


def _draws() -> dict[str, np.ndarray]:
    return {"recent": np.zeros((1000, 2), dtype=int)}


@pytest.mark.parametrize(
    "name,value",
    [
        ("counts", -100.0),
        ("ppe", -1.0),
        ("ppe_covariance", -1.0),
        ("fall_speed_m_s", -1.0),
        ("bin_bounds_bp", -1.0),
        ("basin_radius_m", -1.0),
        ("availability", False),
        ("basin_type", "ocean"),
    ],
)
def test_preexisting_input_mutation_refuses_at_consumption(
    publication_inputs: MultisiteRevealsInput, name: str, value: object
) -> None:
    array = getattr(publication_inputs, name)
    array.setflags(write=True)
    array.flat[-1 if name == "bin_bounds_bp" else 0] = value
    with pytest.raises(ValidationError):
        run_reveals_multisite(
            publication_inputs,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices=_draws(),
        )


def test_calculation_and_manifest_use_same_captured_input(
    publication_inputs: MultisiteRevealsInput, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = publication_inputs
    config = PublicationRevealsConfig("synthetic-bp-v1")
    expected = run_reveals_multisite(inputs, config, bootstrap_indices=_draws())
    before = sha256_object(inputs)
    original = cast(Any, multisite).publication_deposition
    for value in (inputs.counts, inputs.ppe, inputs.basin_type, inputs.basin_radius_m):
        value.setflags(write=True)
    changed = False

    def mutate_source(*args: Any, **kwargs: Any) -> Any:
        nonlocal changed
        if not changed:
            inputs.counts[0, 0, 0] = 1
            inputs.ppe[0] = 2
            inputs.basin_type[0, 0] = "lake"
            inputs.basin_radius_m[0, 0] = 40
            changed = True
        return original(*args, **kwargs)

    monkeypatch.setattr(multisite, "publication_deposition", mutate_source)
    actual = run_reveals_multisite(inputs, config, bootstrap_indices=_draws())
    assert changed and sha256_object(inputs) != before
    pd.testing.assert_frame_equal(actual.cover, expected.cover, check_exact=True)
    assert actual.manifest.inputs["inputs"] == before


def test_refuses_mutable_basin_type_objects(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    from dataclasses import replace

    class MutableBasin:
        def __eq__(self, other: object) -> bool:
            return other == "peatland"

        def __str__(self) -> str:
            return "peatland"

    types = publication_inputs.basin_type.copy()
    types[0, 0] = MutableBasin()
    inputs = replace(publication_inputs, basin_type=types)
    with pytest.raises(ValidationError, match="immutable"):
        run_reveals_multisite(
            inputs,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices=_draws(),
        )


def test_refuses_mutable_string_identity_objects(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    from dataclasses import replace

    class MutableName(str):
        pass

    inputs = replace(publication_inputs, site_ids=(MutableName("small"), "large"))
    with pytest.raises(ValidationError, match="immutable"):
        run_reveals_multisite(
            inputs,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices=_draws(),
        )


def test_bootstrap_membership_is_checked_on_the_owned_copy(
    publication_inputs: MultisiteRevealsInput, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = PublicationRevealsConfig("synthetic-bp-v1")
    supplied = _draws()
    expected = run_reveals_multisite(
        publication_inputs, config, bootstrap_indices=supplied
    )
    original = np.isin

    def mutate_after_check(values: Any, choices: Any) -> np.ndarray:
        checked = original(values, choices)
        supplied["recent"][0, 0] = 99
        return checked

    monkeypatch.setattr(np, "isin", mutate_after_check)
    actual = run_reveals_multisite(
        publication_inputs, config, bootstrap_indices=supplied
    )
    pd.testing.assert_frame_equal(actual.cover, expected.cover, check_exact=True)
    assert (
        actual.manifest.inputs["bootstrap_indices"]
        == expected.manifest.inputs["bootstrap_indices"]
    )


def test_subclass_cannot_bypass_base_input_validation(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    from dataclasses import fields

    class UncheckedInput(MultisiteRevealsInput):
        def __post_init__(self) -> None:
            pass

    values = {
        field.name: getattr(publication_inputs, field.name)
        for field in fields(MultisiteRevealsInput)
    }
    values["counts"] = publication_inputs.counts.copy()
    values["counts"][0, 0, 0] = -100
    unchecked = UncheckedInput(**values)
    with pytest.raises(ValidationError, match="standard MultisiteRevealsInput"):
        run_reveals_multisite(
            unchecked,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices=_draws(),
        )


def test_standard_numpy_string_inputs_preserve_manifest_identity(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    from dataclasses import replace

    types = np.array([[np.str_("peatland")], [np.str_("lake")]], dtype=object)
    inputs = replace(
        publication_inputs,
        site_ids=(np.str_("small"), np.str_("large")),
        basin_type=types,
    )
    before = sha256_object(inputs)
    result = run_reveals_multisite(
        inputs, PublicationRevealsConfig("synthetic-bp-v1"), bootstrap_indices=_draws()
    )
    assert result.manifest.inputs["inputs"] == before == sha256_object(inputs)
    assert np.all(np.isfinite(result.cover.to_numpy()))


def test_masked_bootstrap_index_refuses_unresolved_site(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    mask = np.zeros((1000, 2), dtype=bool)
    mask[0, 0] = True
    supplied = np.ma.array(np.zeros((1000, 2), dtype=int), mask=mask)
    with pytest.raises(ValidationError, match="masked"):
        run_reveals_multisite(
            publication_inputs,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices={"recent": supplied},
        )


def test_all_false_bootstrap_mask_preserves_result_and_identity(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    indices = _draws()["recent"]
    config = PublicationRevealsConfig("synthetic-bp-v1")
    expected = run_reveals_multisite(
        publication_inputs, config, bootstrap_indices={"recent": indices}
    )
    actual = run_reveals_multisite(
        publication_inputs,
        config,
        bootstrap_indices={"recent": np.ma.array(indices, mask=False)},
    )
    pd.testing.assert_frame_equal(actual.cover, expected.cover, check_exact=True)
    assert (
        actual.manifest.inputs["bootstrap_indices"]
        == expected.manifest.inputs["bootstrap_indices"]
    )
