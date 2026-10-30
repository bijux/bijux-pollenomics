"""Bound native method declarations become readable without scientific admission."""

from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
import json
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document.native_lra import bind_native_view
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from ..browser_semantics.support import run_node_json
from .support import view_fixture
from .test_rendering import _render


def declared_view() -> dict[str, Any]:
    view = view_fixture()
    view["method"] = {
        "profile": "source-compatible-test-profile",
        "configuration": {
            "seed": 0,
            "reveals": {"stochastic": False, "iterations": 12},
            "love": {"method": "analytical", "source_option": None},
        },
        "versions": {"taxa": "source-taxa.v1", "configuration": "configuration.v3"},
    }
    view["uncertainty_omissions"] = [
        "Chronology uncertainty not propagated",
        "PPE uncertainty not propagated",
    ]
    return view


def context(view: dict[str, Any], *, mounted: bool = False) -> dict[str, Any]:
    bound = bind_native_view(view)
    script = (
        NATIVE_LRA_CONTROLLER
        + "\nconst bound="
        + json.dumps(bound)
        + ";const view=JSON.parse(bound.bytes);"
        + "const original=JSON.stringify(view);let html;"
    )
    if mounted:
        script += """
function node(){return {innerHTML:'',hidden:true,dataset:{},options:[],children:[],
  append(child){this.children.push(child);this.options.push(child)},
  addEventListener(){},setAttribute(key,value){this[key]=value},
  replaceChildren(){this.children=[]}}}
const nodes=new Map();
const document={createElement(){return node()},getElementById(id){
  if(!nodes.has(id)){const item=node();item.tBodies=[node()];nodes.set(id,item)}
  return nodes.get(id)}};
const controller=createNativeLraController(view,bound.sha256,{
  globalContext:()=>({time_window_bp:[10,20],active_layer_keys:['layer-r','layer-l']}),changed(){}});
const before=controller.snapshot();controller.mount();html=nodes.get('lra-method-context').innerHTML;
if(JSON.stringify(before)!==JSON.stringify(controller.snapshot()))throw Error('Metadata mount changed scientific selection');
"""
    else:
        script += "html=nativeLraMethodContextHtml(view);"
    script += "console.log(JSON.stringify({html,unchanged:original===JSON.stringify(view),view}));"
    return cast(dict[str, Any], run_node_json(script))


def test_actual_bound_view_and_controller_mount_keep_literal_declarations() -> None:
    view = declared_view()
    before = deepcopy(view)
    observed = context(view, mounted=True)
    document = ET.fromstring("<div>" + observed["html"] + "</div>")
    assert document.findtext("h4") == "Method and declared uncertainty"
    tables = document.findall(".//table")
    assert [table.findtext("caption") for table in tables] == [
        "Declared configuration",
        "Declared versions",
    ]
    values = {
        row.findtext("th"): row.findtext("td")
        for table in tables
        for row in table.findall("tbody/tr")
    }
    assert values["seed"] == "0"
    assert values["reveals.stochastic"] == "false"
    assert values["love.source_option"] == "null"
    assert values["reveals.iterations"] == "12"
    assert values["taxa"] == '"source-taxa.v1"'
    assert [item.text for item in document.findall("ul/li")] == view[
        "uncertainty_omissions"
    ]
    text = " ".join(document.itertext())
    assert "source-compatible-test-profile" in text
    assert "not validated assumptions or scientific approval" in text
    assert "Display filters do not refit the model" in text
    assert "do not establish total uncertainty or held-out predictive coverage" in text
    assert all(
        th.get("scope") == "col"
        for table in tables
        for th in table.findall("thead/tr/th")
    )
    assert all(
        th.get("scope") == "row"
        for table in tables
        for th in table.findall("tbody/tr/th")
    )
    assert observed["unchanged"] is True and observed["view"] == before
    assert view == before


@pytest.mark.parametrize(
    "method",
    [
        None,
        [],
        "unavailable",
        0,
        {"profile": False, "configuration": [], "versions": None},
    ],
)
def test_missing_or_malformed_method_fields_are_explicitly_unavailable(
    method: object,
) -> None:
    view = declared_view()
    view["method"] = method
    observed = context(view)
    document = ET.fromstring("<div>" + observed["html"] + "</div>")
    assert not document.findall(".//table")
    text = " ".join(document.itertext())
    assert "Unavailable: no valid method profile supplied" in text
    assert "Declared configuration unavailable" in text
    assert "Declared versions unavailable" in text
    assert "Chronology uncertainty not propagated" in text
    assert observed["unchanged"] is True


def test_legacy_absence_remains_missing_without_inferred_defaults() -> None:
    view = view_fixture()
    del view["method"]
    del view["uncertainty_omissions"]
    observed = context(view)
    text = " ".join(ET.fromstring("<div>" + observed["html"] + "</div>").itertext())
    assert "no valid method profile supplied" in text
    assert "Declared uncertainty omissions unavailable" in text
    assert "seed" not in text and "analytical" not in text


@pytest.mark.parametrize(
    "omissions", [None, "none", [False], [None], [""], {"missing": "unknown"}]
)
def test_malformed_uncertainty_list_never_becomes_zero_uncertainty(
    omissions: object,
) -> None:
    view = declared_view()
    view["uncertainty_omissions"] = omissions
    document = ET.fromstring("<div>" + context(view)["html"] + "</div>")
    text = " ".join(document.itertext())
    assert "Declared uncertainty omissions unavailable" in text
    assert "seed" in text  # Independent valid configuration remains visible.
    assert not document.findall("ul")


def test_empty_declarations_do_not_imply_complete_uncertainty_or_defaults() -> None:
    view = view_fixture()
    view["uncertainty_omissions"] = []
    document = ET.fromstring("<div>" + context(view)["html"] + "</div>")
    text = " ".join(document.itertext())
    assert "Declared configuration: no fields declared" in text
    assert "Declared versions: no fields declared" in text
    assert "No uncertainty omissions were declared" in text
    assert "does not establish complete uncertainty coverage" in text


def test_labels_versions_and_omissions_are_escaped_without_html_interpretation() -> (
    None
):
    view = declared_view()
    hostile = '</p><img src="x" onerror="alert(1)"><script>unsafe</script>'
    view["method"]["profile"] = hostile
    view["method"]["configuration"] = {hostile: hostile}
    view["method"]["versions"] = {"review": hostile}
    view["uncertainty_omissions"] = [hostile]
    document = ET.fromstring("<div>" + context(view)["html"] + "</div>")
    assert document.find(".//img") is None and document.find(".//script") is None
    text = " ".join(document.itertext())
    assert hostile in text
    assert json.dumps(hostile) in text


def test_semantic_mount_is_present_only_in_the_native_control_body() -> None:
    class Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.stack: list[str] = []
            self.context: dict[str, str | None] | None = None
            self.native_ancestor = False

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            values = dict(attrs)
            if values.get("id") == "lra-method-context":
                self.context = values
                self.native_ancestor = "lra-controls" in self.stack
            if tag not in {"meta", "link", "input", "br", "hr", "img"}:
                self.stack.append(values.get("id") or tag)

        def handle_endtag(self, tag: str) -> None:
            if self.stack:
                self.stack.pop()

    parser = Parser()
    parser.feed(_render(declared_view()))
    assert parser.context is not None and parser.native_ancestor is True
    assert parser.context["aria-label"] == "Native LRA method and declared uncertainty"
    assert 'id="lra-method-context"' not in _render(None)
