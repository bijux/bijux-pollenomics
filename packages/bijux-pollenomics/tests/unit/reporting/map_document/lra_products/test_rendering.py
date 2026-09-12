"""Native view extends the existing renderer without changing legacy controls."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.native_lra import validate_native_layers
from bijux_pollenomics.reporting.map_document.render import (
    render_multi_country_map_html,
)
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

from ..browser_semantics.support import check_javascript_syntax
from .support import view_fixture


def _layers(view: dict[str, Any]) -> list[Any]:
    return [
        {
            "key": site["layer_key"],
            "label": "Synthetic model",
            "group": "environmental-context",
            "semantic_role": "exploratory_lra_model_anchor",
            "default_enabled": True,
            "applies_time_filter": True,
            "applies_country_filter": False,
            "circle_enabled": False,
            "style": {"fill": "#000000", "stroke": "#000000"},
            "features": [
                {
                    "record_id": site["anchor_id"],
                    "latitude": 0,
                    "longitude": 0,
                    "country": "UNASSIGNED",
                    "model_row_ids": site["model_row_ids"],
                    "product_manifest_sha256": view["product_manifest_sha256"],
                    "geometry_sha256": view["geometry_sha256"],
                    "age_type": "calendar_bp",
                    "time_start_bp": 10,
                    "time_end_bp": 20,
                }
            ],
        }
        for site in view["sites"]
        if site["map_status"] == "synthetic_anchor"
    ]


def _render(view: dict[str, Any] | None) -> str:
    return render_multi_country_map_html(
        title="Synthetic",
        version="v0.2.0",
        generated_on="not a release",
        countries=(),
        policy=MAP_SCOPE_POLICIES["custom"],
        point_layers=_layers(view) if view else [],
        polygon_layers=[],
        asset_base_path="assets",
        native_lra=view,
    )


def test_legacy_page_has_no_native_mount_or_controller() -> None:
    html = _render(None)
    assert 'id="lra-controls"' not in html
    assert "function createNativeLraController" not in html
    assert "const NATIVE_LRA_BINDING = null;" in html


def test_native_view_is_script_safe_and_all_inline_scripts_parse(
    tmp_path: Path,
) -> None:
    view = view_fixture()
    view["uncertainty_omissions"] = ['</script><script>alert("x")</script>', "\u2028🌿"]
    html = _render(view)
    assert 'id="lra-controls"' in html
    assert '</script><script>alert("x")</script>' not in html
    assert "__NATIVE_LRA_" not in html
    for index, (attributes, script) in enumerate(
        re.findall(r"<script([^>]*)>(.*?)</script>", html, re.S)
    ):
        if 'type="application/json"' in attributes:
            json.loads(script)
        elif script.strip():
            check_javascript_syntax(script, tmp_path / f"script-{index}.js")


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "membership",
        "identity",
        "duplicate",
        "time",
        "boolean_time",
        "boolean_coordinate",
        "age_type",
    ],
)
def test_view_and_actual_layer_cannot_disagree(case: str) -> None:
    view = view_fixture()
    layers = _layers(view)
    if case == "missing":
        layers.pop()
    if case == "membership":
        layers[0]["features"][0]["model_row_ids"] = []
    if case == "identity":
        layers[0]["features"][0]["geometry_sha256"] = "e" * 64
    if case == "duplicate":
        layers.append(layers[0])
    if case == "time":
        layers[0]["features"][0]["time_start_bp"] = 9
    if case == "boolean_time":
        view["rows"][0]["declared_bin"]["younger_bp"] = 1
        layers[0]["features"][0]["time_start_bp"] = True
    if case == "boolean_coordinate":
        layers[0]["features"][0]["latitude"] = True
    if case == "age_type":
        layers[0]["features"][0]["age_type"] = "calibrated_bp"
    with pytest.raises(ValueError):
        validate_native_layers(view, layers)


def test_native_controls_belong_to_the_scrollable_drawer() -> None:
    class DrawerParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.stack: list[tuple[str, dict[str, str | None]]] = []
            self.elements: dict[str, tuple[dict[str, str | None], list[str]]] = {}

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            attributes = dict(attrs)
            identity = attributes.get("id")
            if identity:
                self.elements[identity] = (
                    attributes,
                    [item.get("class", "") or "" for _, item in self.stack],
                )
            if tag not in {"meta", "link", "input", "br", "hr", "img"}:
                self.stack.append((tag, attributes))

        def handle_endtag(self, tag: str) -> None:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    del self.stack[index:]
                    break

    parser = DrawerParser()
    parser.feed(_render(view_fixture()))
    for identity in (
        "lra-controls",
        "lra-role",
        "lra-site",
        "lra-taxon",
        "lra-bin",
        "lra-estimates",
        "lra-download",
    ):
        assert "control-panel-body" in parser.elements[identity][1]
    for identity in ("lra-role", "lra-site", "lra-taxon", "lra-bin"):
        assert "search-input" in (parser.elements[identity][0]["class"] or "").split()
    assert "lra-estimates-scroll" in " ".join(parser.elements["lra-estimates"][1])
    assert (
        "inline-button" in (parser.elements["lra-download"][0]["class"] or "").split()
    )
