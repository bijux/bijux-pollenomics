"""Own numeric buffers safely across the private experimental native boundary."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ctypes
from pathlib import Path

import numpy as np
import pytest

import bijux_pollenomics_dev.native_backend.forward_compare as comparison
from bijux_pollenomics_dev.native_backend.forward_compare import (
    ForwardBatch,
    compile_library,
    inputs,
)


@pytest.fixture(scope="module")
def library(tmp_path_factory: pytest.TempPathFactory) -> ctypes.CDLL:
    compiler = Path("/usr/bin/clang++")
    if not compiler.is_file():
        pytest.skip(
            "experimental comparison requires the declared local clang++ compiler"
        )
    source = Path(comparison.__file__).with_name("forward_kernel.cpp")
    output = tmp_path_factory.mktemp("native-forward") / "forward.so"
    result, _ = compile_library(source, output, compiler)
    return result


def test_batch_matches_optimized_numpy_and_owns_output(library: ctypes.CDLL) -> None:
    batch = ForwardBatch(*inputs(3, 8, 4))
    before = batch.cover.copy()
    result = batch.native(library)
    np.testing.assert_allclose(result, batch.numpy(), rtol=1e-10, atol=1e-12)
    np.testing.assert_array_equal(batch.cover, before)
    assert result.flags.owndata
    assert not np.shares_memory(result, batch.cover)


def test_readonly_and_strided_input_conversion_is_explicit(
    library: ctypes.CDLL,
) -> None:
    cover, regional, kernels, fractions, productivity = inputs(3, 8, 4)
    arrays = (
        cover[:, ::-1],
        regional[::-1],
        kernels[:, ::-1],
        fractions,
        productivity[::-1],
    )
    for value in arrays:
        value.setflags(write=False)
    before = [value.tobytes() for value in arrays]
    batch = ForwardBatch(*arrays)
    assert batch.cover.flags.c_contiguous and batch.cover.flags.aligned
    np.testing.assert_allclose(
        batch.native(library), batch.numpy(), rtol=1e-10, atol=1e-12
    )
    assert [value.tobytes() for value in arrays] == before


def test_dimension_failure_precedes_native_entry() -> None:
    arrays = list(inputs(3, 8, 4))
    arrays[1] = np.ones(3)
    with pytest.raises(ValueError, match="dimensions"):
        ForwardBatch(*arrays)


def test_native_refuses_input_mutated_after_shared_validation(
    library: ctypes.CDLL,
) -> None:
    batch = ForwardBatch(*inputs(3, 8, 4))
    batch.cover[0, 0] = np.nan
    with pytest.raises(ValueError, match="native forward refused"):
        batch.native(library)
    with pytest.raises(ValueError, match="nonfinite or zero"):
        batch.numpy()


def test_zero_mass_is_refused_in_both_paths(library: ctypes.CDLL) -> None:
    cover, regional, kernels, fractions, productivity = inputs(3, 8, 4)
    regional[:] = 0
    kernels[:] = 0
    batch = ForwardBatch(cover, regional, kernels, fractions, productivity)
    with pytest.raises(ValueError, match="native forward refused"):
        batch.native(library)
    with pytest.raises(ValueError, match="nonfinite or zero"):
        batch.numpy()


def test_two_concurrent_native_calls_keep_independent_owned_outputs(
    library: ctypes.CDLL,
) -> None:
    batch = ForwardBatch(*inputs(3, 8, 4))
    with ThreadPoolExecutor(max_workers=2) as workers:
        outputs = list(workers.map(lambda _: batch.native(library), range(2)))
    for output in outputs:
        np.testing.assert_allclose(output, batch.numpy(), rtol=1e-10, atol=1e-12)
    assert not np.shares_memory(outputs[0], outputs[1])
