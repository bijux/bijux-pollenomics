"""Artifact destination and frozen-source refusal behavior."""

from pathlib import Path

import pytest


def test_workflow_refuses_existing_or_external_destination(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators.workflow import run

    existing = tmp_path / "artifacts" / "existing"
    existing.mkdir(parents=True)
    with pytest.raises(ValueError, match="absent"):
        run(tmp_path, existing)
    with pytest.raises(ValueError, match="artifacts"):
        run(tmp_path, tmp_path / "external")
    assert list(existing.iterdir()) == []


def test_workflow_refuses_changed_frozen_baseline_before_output(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators.inputs import (
        BASE_CSV,
    )
    from bijux_pollenomics_dev.landscape_history.landclim.indicators.workflow import run

    source = tmp_path / BASE_CSV
    source.parent.mkdir(parents=True)
    source.write_text("changed baseline\n")
    output = tmp_path / "artifacts" / "result"
    with pytest.raises(ValueError, match="baseline identity"):
        run(tmp_path, output)
    assert not output.exists()
