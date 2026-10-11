"""Keep isolated native worker measurements honest about units and inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import resource

import numpy as np
import pytest

from bijux_pollenomics_dev.native_backend import memory_compare


@pytest.mark.parametrize(
    "system,raw,expected", [("Darwin", 17, 17), ("Linux", 17, 17408)]
)
def test_process_peak_units(
    monkeypatch: pytest.MonkeyPatch, system: str, raw: int, expected: int
) -> None:
    class Usage:
        ru_maxrss = raw

    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(resource, "getrusage", lambda _: Usage())
    assert memory_compare._peak_bytes() == expected


def test_child_receipt_retains_owned_output_and_input_identity(tmp_path: Path) -> None:
    destination = tmp_path / "output.npy"
    receipt = memory_compare.child(
        "numpy", memory_compare.SHAPES[0], tmp_path / "unused.so", destination
    )
    result = np.load(destination)
    assert result.shape == tuple(receipt["output_shape"])
    assert receipt["method"] == "numpy"
    assert receipt["shape"] == list(memory_compare.SHAPES[0])
    assert (
        receipt["post_call_process_peak_rss_bytes"]
        >= receipt["pre_call_process_peak_rss_bytes"]
    )
    assert receipt["observed_peak_increment_bytes"] >= 0
    assert receipt["input_sha256"] != receipt["output_sha256"]
    assert (
        receipt["output_sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest()
    )
    json.dumps(receipt, allow_nan=False)


@pytest.mark.parametrize("method,shape", [("other", (1, 8, 3)), ("numpy", (2, 8, 3))])
def test_child_refuses_undeclared_cases(
    tmp_path: Path, method: str, shape: tuple[int, int, int]
) -> None:
    with pytest.raises(ValueError, match="Undeclared"):
        memory_compare.child(
            method, shape, tmp_path / "unused.so", tmp_path / "output.npy"
        )
    assert not (tmp_path / "output.npy").exists()


def test_producer_requires_absent_artifact_destination(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    compiler = Path("/usr/bin/clang++")
    with pytest.raises(ValueError, match="Absent output root"):
        memory_compare.run(repository, tmp_path / "elsewhere", compiler)
    (repository / "artifacts").mkdir()
    existing = repository / "artifacts" / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="Absent output root"):
        memory_compare.run(repository, existing, compiler)
