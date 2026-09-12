"""Selected bytes bind native values, Unicode, global context and URL ownership."""

from __future__ import annotations

import hashlib
import json

import pytest

from .support import run_controller, view_fixture


def test_export_bytes_keep_full_native_rows_and_hash() -> None:
    view = view_fixture()
    result = run_controller(
        view,
        "const first = await controller.exportSelection(); const second = await controller.exportSelection(); console.log(JSON.stringify({first,second}));",
    )
    assert result["first"] == result["second"]
    exported = result["first"]
    assert json.loads(exported["bytes"]) == exported["payload"]
    assert hashlib.sha256(exported["bytes"].encode()).hexdigest() == exported["sha256"]
    assert exported["payload"]["rows"] == view["rows"]
    assert exported["payload"]["rows"][2]["native_value"] == "0.25000000000000001"
    assert exported["payload"]["counts"]["missing_values"] == 1
    assert exported["payload"]["publication_authorized"] is False


@pytest.mark.parametrize(
    "case", ["stale", "duplicate", "unknown", "duplicate_json", "missing"]
)
def test_url_refuses_stale_or_ambiguous_selection(case: str) -> None:
    mutation = {
        "stale": "params.set('lra_view','f'.repeat(64));",
        "duplicate": "params.append('lra_view','e'.repeat(64));",
        "unknown": "const bad=controller.snapshot().selection;bad.taxa=['unknown'];params.set('lra_selection',JSON.stringify(bad));",
        "duplicate_json": "params.set('lra_selection',params.get('lra_selection').replace('{','{\"taxa\":[],'));",
        "missing": "params.delete('lra_view');",
    }[case]
    result = run_controller(
        view_fixture(),
        "const params=new URLSearchParams();controller.writeHash(params);"
        + mutation
        + "controller.restoreHash(params);const copied=new URLSearchParams();controller.writeHash(copied);console.log(JSON.stringify({snapshot:controller.snapshot(),preserved:copied.toString()===params.toString()}));",
    )
    assert result["snapshot"]["refusal"]
    assert result["snapshot"]["counts"]["selected_rows"] == 0
    assert result["preserved"]
