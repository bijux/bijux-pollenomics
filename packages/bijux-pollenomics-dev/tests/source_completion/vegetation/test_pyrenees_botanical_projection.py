"""Keep botanical assumptions and scientific refusal populations explicit."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[5]
DOMAIN = ROOT / "reports/science/vegetation-reference/pyrenees-botanical-projection"


def module(name: str) -> ModuleType:
    path = DOMAIN / (name + ".py")
    spec = importlib.util.spec_from_file_location("bijux_botanical_" + name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def records() -> list[dict[str, Any]]:
    return [
        {
            "source": {"row": 6},
            "axis": "Poaceae",
            "association_status": "associated",
            "analyst_associated_native_id": "10",
            "native_chain": [{"num_nom": "10"}],
        },
        {
            "source": {"row": 7},
            "axis": "Poaceae",
            "association_status": "associated",
            "analyst_associated_native_id": "11",
            "native_chain": [{"num_nom": "11"}, {"num_nom": "10"}],
        },
    ]


def test_unknown_blanks_refuse_a_complete_vector() -> None:
    domain = module("botanical_projection")
    result = domain.project(
        records(),
        ["plot"],
        {(6, "plot"): None, (7, "plot"): "14"},
        domain.PARENTS[0],
        domain.BLANKS[0],
    )
    row = result["outcomes"][0]
    assert row["status"] == "refused"
    assert row["closed_panel_fraction"] is None
    assert row["source_blank_counts_by_axis"]["Poaceae"] == 1
    assert "Salix" in row["unrepresented_axes"]
    assert row["blank_zero_imputation_assumed"] is False


def test_explicit_zero_assumption_does_not_erase_source_loss_accounts() -> None:
    domain = module("botanical_projection")
    result = domain.project(
        records(),
        ["plot"],
        {(6, "plot"): "3", (7, "plot"): "14"},
        domain.PARENTS[1],
        domain.BLANKS[1],
    )
    assert (
        result["outcomes"][0]["closed_panel_fraction"][domain.AXES.index("Poaceae")]
        == 1
    )
    assert result["positive_observation_loss_ledger"] == [
        {
            "plot": "plot",
            "source_row": 6,
            "literal_cover_percent": "3",
            "status": "omitted-inventory-parent",
            "axis": "Poaceae",
        },
        {
            "plot": "plot",
            "source_row": 7,
            "literal_cover_percent": "14",
            "status": "included-panel-observation",
            "axis": "Poaceae",
        },
    ]


def test_positive_unresolved_taxonomy_cannot_be_imputed_as_zero() -> None:
    domain = module("botanical_projection")
    source = records()
    source[0]["association_status"] = "unresolved"
    source[0]["axis"] = None
    result = domain.project(
        source,
        ["plot"],
        {(6, "plot"): "3", (7, "plot"): "14"},
        domain.PARENTS[0],
        domain.BLANKS[1],
    )
    assert result["outcomes"][0]["closed_panel_fraction"] is None
    assert result["outcomes"][0]["unknown_positive_source_rows"] == [6]
    assert (
        result["positive_observation_loss_ledger"][0]["status"]
        == "unresolved-association"
    )


@pytest.mark.parametrize(
    "values", [[0, 0], [-1, 2], [float("nan"), 1], [float("inf"), 1]]
)
def test_invalid_or_empty_cover_cannot_be_closed(values: list[float]) -> None:
    with pytest.raises(ValueError):
        module("botanical_projection").close(values)


def test_partial_source_packet_fails_before_output_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    monkeypatch.setattr(
        sys, "argv", ["replay", "--source-root", str(source), "--output", str(output)]
    )
    with pytest.raises(ValueError, match="Pinned immutable scientific input differs"):
        module("replay").main()
    assert not output.exists()


def test_replay_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "observations.json"
    existing.write_text("retained observations\n")
    monkeypatch.setattr(
        sys, "argv", ["replay", "--source-root", str(source), "--output", str(output)]
    )
    with pytest.raises(ValueError, match="Owned output root must be absent"):
        module("replay").main()
    assert existing.read_text() == "retained observations\n"
