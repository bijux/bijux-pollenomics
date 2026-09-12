"""Python/JavaScript selections agree without treating map refusals as missing data."""

from __future__ import annotations

import json
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.native_lra import select_native_rows

from .support import run_controller, selection_fixture, view_fixture


@pytest.mark.parametrize("case", ["all", "empty", "regional", "taxon", "layer", "time"])
def test_native_selection_parity(case: str) -> None:
    view = view_fixture()
    selection = selection_fixture(view)
    context = {"time_window_bp": [10, 20], "active_layer_keys": ["layer-r", "layer-l"]}
    if case == "empty":
        selection["taxa"] = []
    if case == "regional":
        selection["roles"] = ["regional"]
    if case == "taxon":
        selection["taxa"] = ["Alnus🌿"]
    if case == "layer":
        context["active_layer_keys"] = []
    if case == "time":
        context["time_window_bp"] = [30, 40]
    expected = select_native_rows(view, selection, context)
    observed = run_controller(
        view,
        f"controller.setSelection({json.dumps(selection)}); console.log(JSON.stringify(controller.snapshot()));",
        context=context,
    )
    assert all(observed[key] == value for key, value in expected.items())
    if case in ("time", "layer"):
        assert expected["selected_row_ids"] == ["r2"]
        assert expected["counts"]["refused_sites"] == 1


@pytest.mark.parametrize("value", [[True, 20], [-1, 20], [30, 20], [None, 20]])
def test_invalid_global_time_refuses(value: list[Any]) -> None:
    view = view_fixture()
    context = {"time_window_bp": value, "active_layer_keys": []}
    with pytest.raises(ValueError, match="global time"):
        select_native_rows(view, selection_fixture(view), context)
    result = run_controller(
        view,
        "try {controller.snapshot(); console.log('false')} catch(error) {console.log('true')}",
        context=context,
    )
    assert result is True


def test_unknown_selection_refuses_export_and_can_recover() -> None:
    view = view_fixture()
    observed = run_controller(
        view,
        "const valid = controller.snapshot().selection; try {controller.setSelection({...valid,taxa:['invented']})} catch(error) {} const refused = controller.snapshot(); let exportRefused = false; try {await controller.exportSelection()} catch(error) {exportRefused = true} controller.setSelection(valid); console.log(JSON.stringify({refused,exportRefused,recovered:controller.snapshot()}));",
    )
    assert observed["refused"]["selected_row_ids"] == []
    assert observed["exportRefused"] is True
    assert observed["recovered"]["counts"]["selected_rows"] == 3
