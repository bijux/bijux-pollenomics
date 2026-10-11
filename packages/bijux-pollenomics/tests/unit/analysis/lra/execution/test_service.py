"""Changes during computation invalidate the completed numerical result."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import service

from ..outputs.test_publication import Result, binding
from ..support import request_fixture


@pytest.mark.parametrize("change", ["code", "source"])
def test_run_binds_inputs_before_and_after_computation(
    tmp_path: Path, change: str
) -> None:
    engine = binding(tmp_path)
    payload = request_fixture(tmp_path)
    destination = tmp_path / "output"

    def changed_result(*args: object) -> Result:
        target = tmp_path / (
            "installed/api.py" if change == "code" else "raw_snapshot.txt"
        )
        target.write_text("changed during computation")
        return Result()

    with (
        patch.object(service, "load_engine", return_value=engine),
        patch.object(service, "reconstruct", side_effect=changed_result),
        pytest.raises(LRARefusal) as error,
    ):
        service.run_lra_request(payload, input_root=tmp_path, destination=destination)
    expected = (
        "lra_code_changed_during_run"
        if change == "code"
        else "evidence_digest_mismatch"
    )
    assert error.value.reason_code == expected
    assert not destination.exists()
