"""Reuse requires complete bytes, live source evidence and exact implementation."""

from __future__ import annotations

from contextlib import ExitStack
import copy
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import cache

from ..outputs.test_publication import Result, binding
from ..support import request_fixture


def test_warm_cache_skips_computation_and_parameter_changes_do_not(
    tmp_path: Path,
) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    with (
        patch.object(cache, "load_engine", return_value=engine),
        patch.object(cache, "validate_engine_configuration"),
        patch.object(cache, "reconstruct", return_value=Result()) as reconstruct,
    ):
        first = cache.run_lra_cached(
            payload, input_root=tmp_path, cache_root=tmp_path / "cache"
        )
        warm = cache.run_lra_cached(
            payload, input_root=tmp_path, cache_root=tmp_path / "cache"
        )
        assert not first.cache_hit and warm.cache_hit
        assert first.product == warm.product
        assert reconstruct.call_count == 1
        changed = copy.deepcopy(payload)
        changed["parameters"][0]["ppe"] = 5
        other = cache.run_lra_cached(
            changed, input_root=tmp_path, cache_root=tmp_path / "cache"
        )
        assert other.cache_key != first.cache_key and not other.cache_hit
        assert reconstruct.call_count == 2


@pytest.mark.parametrize("change", ["source", "code", "runtime", "corrupt", "busy"])
def test_cache_invalidation_and_refusals(tmp_path: Path, change: str) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    root = tmp_path / "cache"
    with (
        patch.object(cache, "load_engine", return_value=engine),
        patch.object(cache, "validate_engine_configuration"),
        patch.object(cache, "reconstruct", return_value=Result()) as reconstruct,
        ExitStack() as stack,
    ):
        first = cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
        if change == "source":
            (tmp_path / "raw_snapshot.txt").write_text("changed source")
        elif change == "code":
            (tmp_path / "installed/api.py").write_text("changed code")
        elif change == "runtime":
            stack.enter_context(patch.dict("os.environ", {"OMP_NUM_THREADS": "3"}))
        elif change == "corrupt":
            (first.product.directory / "numerical/reconstruction.csv").write_text(
                "corrupt"
            )
        else:
            (root / f".{first.cache_key}.cache.lock").write_text("active owner")
        if change in {"code", "runtime"}:
            second = cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
            assert second.cache_key != first.cache_key and not second.cache_hit
            assert reconstruct.call_count == 2
        else:
            with pytest.raises(LRARefusal) as error:
                cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
            assert (
                error.value.reason_code
                == {
                    "source": "evidence_digest_mismatch",
                    "corrupt": "invalid_lra_product",
                    "busy": "lra_cache_busy",
                }[change]
            )
            assert reconstruct.call_count == 1


def test_failed_calculation_leaves_no_hit_and_can_retry(tmp_path: Path) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    root = tmp_path / "cache"
    with (
        patch.object(cache, "load_engine", return_value=engine),
        patch.object(cache, "validate_engine_configuration"),
        patch.object(
            cache,
            "reconstruct",
            side_effect=[LRARefusal("no_solution", "failed"), Result()],
        ),
    ):
        with pytest.raises(LRARefusal, match="failed"):
            cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
        assert list(root.iterdir()) == []
        recovered = cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
        assert not recovered.cache_hit


def test_source_mutation_during_serialization_cannot_create_cache_hit(
    tmp_path: Path,
) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    root = tmp_path / "cache"

    def mutate() -> None:
        (tmp_path / "raw_snapshot.txt").write_text("changed while serializing")

    with (
        patch.object(cache, "load_engine", return_value=engine),
        patch.object(cache, "validate_engine_configuration"),
        patch.object(cache, "reconstruct", return_value=Result(mutate)),
        pytest.raises(LRARefusal) as error,
    ):
        cache.run_lra_cached(payload, input_root=tmp_path, cache_root=root)
    assert error.value.reason_code == "evidence_digest_mismatch"
    assert not [path for path in root.iterdir() if not path.name.startswith(".")]
    assert list(root.glob(".*.pending-*"))
