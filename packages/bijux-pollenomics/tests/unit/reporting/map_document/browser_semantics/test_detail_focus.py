from __future__ import annotations

from pathlib import Path
import shutil

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

from ...atlas.static_assets.fixtures.scientific_evidence import (
    build_detail_records,
    build_scientific_point_layers,
    build_scientific_signals,
)
from .support import run_node_json, template_block


def build_detail_focus_candidate(directory: Path) -> Path:
    """Materialize a synthetic golden record using the production atlas producer."""
    directory.mkdir(parents=True, exist_ok=True)
    layers = build_scientific_point_layers()
    details = build_detail_records()
    tabs = details[0]["tabs"]
    assert isinstance(tabs, dict)
    tabs["samples"] = {
        "record_count": 26,
        "fields": ["sample_id", "depth_cm"],
        "records": [[f"sample:{index}", index] for index in range(26)],
    }
    assets = write_static_atlas_assets(
        directory,
        slug="detail-focus",
        version="keyboard-contract",
        point_layers=layers,
        polygon_layers=[],
        detail_records=details,
        scientific_signals=build_scientific_signals(),
    )
    policy = resolve_map_scope_policy(
        next(
            scope
            for scope in build_published_geography_plan(
                ("Sweden", "Norway")
            ).regional_scopes
            if scope.key == "nordic"
        )
    )
    document = directory / "index.html"
    document.write_text(
        render_multi_country_map_html(
            "Synthetic detail keyboard contract",
            "keyboard-contract",
            "2026-09-27",
            ("Sweden", "Norway"),
            policy,
            layers,
            [],
            "./_map_assets",
            static_assets=assets,
        ),
        encoding="utf-8",
    )
    source_assets = (
        Path(__file__).resolve().parents[5]
        / "src/bijux_pollenomics/reporting/assets/map"
    )
    shutil.copytree(source_assets, directory / "_map_assets", dirs_exist_ok=True)
    return document


def test_detail_tabs_keyboard_wrap_home_end_and_leave_tab_to_browser() -> None:
    handler = template_block(
        "focusTabs.addEventListener('keydown'", "focusPreviousButton.addEventListener"
    )
    observed = run_node_json(
        """
const DETAIL_TAB_DEFINITIONS=[['overview','Overview'],['samples','Samples'],['provenance','Provenance']];
let activeFocusTab='overview',renderCount=0,listener;
const focusTabs={addEventListener(type,callback){listener=callback;}};
function renderFocusDetail(){renderCount++;}
"""
        + handler
        + """
const moves=[];
for (const key of ['ArrowLeft','ArrowRight','End','Home','Tab']) {
  let prevented=false;
  listener({key,target:{matches(){return true;},dataset:{focusTab:activeFocusTab}},preventDefault(){prevented=true;}});
  moves.push({key,selected:activeFocusTab,prevented});
}
console.log(JSON.stringify({moves,renderCount}));
"""
    )
    assert observed == {
        "moves": [
            {"key": "ArrowLeft", "selected": "provenance", "prevented": True},
            {"key": "ArrowRight", "selected": "overview", "prevented": True},
            {"key": "End", "selected": "provenance", "prevented": True},
            {"key": "Home", "selected": "overview", "prevented": True},
            {"key": "Tab", "selected": "overview", "prevented": False},
        ],
        "renderCount": 4,
    }


def test_detail_focus_candidate_exposes_labelled_panel_and_loaded_sample_pages(
    tmp_path: Path,
) -> None:
    document = build_detail_focus_candidate(tmp_path)
    html = document.read_text(encoding="utf-8")
    assert 'role="tabpanel" tabindex="0"' in html
    assert 'aria-controls="focus-detail" tabindex="${activeFocusTab === key' in html
    assert (
        "focusDetail.setAttribute('aria-labelledby', `focus-tab-${activeFocusTab}`)"
        in html
    )
    assert "focusedTable" in html
    assert "restoreFocusFromCard()" in html
    assert (tmp_path / "_map_assets/leaflet/leaflet.js").is_file()
