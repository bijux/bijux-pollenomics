"""Supplied hierarchy and exact display identities remain separate from admission."""

from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
from importlib.resources import files
import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence

from ....atlas.static_assets.fixtures.scientific_evidence import (
    build_scientific_signals,
)
from ..support import run_node_json, template_block

SCRIPT = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/scientific-picker.js")
    .read_text()
)


def signals() -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = [dict(row) for row in build_scientific_signals()] + [
        {
            "signal_id": "pollen:subgroup:declared",
            "feature_key": "subgroup:declared",
            "label": "Declared subgroup",
            "resolution": "subgroup",
            "parent_signal_id": "pollen:group:cereals",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:taxon:other",
            "feature_key": "taxon:other",
            "label": "Other taxon",
            "resolution": "taxon",
            "status": "accepted",
        },
    ]
    raw[0]["synonyms"] = ["Explicit source synonym"]
    raw[0]["source_ecological_code"] = "NOT-A-SEARCH-ALIAS"
    return [
        dict(row)
        for row in normalize_atlas_evidence(
            detail_records=[],
            scientific_signals=raw,
            edge_records=[],
            sequence_records=[],
        ).scientific_signals
    ]


def observe(
    rows: object,
    initial: object = None,
    actions: object = None,
    query: object = "",
    pin_request: object = (),
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            template_block("function escapeHtml", "function normalizedMediaLinks")
            + SCRIPT
            + "const rows="
            + json.dumps(rows)
            + ";const initial="
            + json.dumps(initial if initial is not None else [])
            + ";const actions="
            + json.dumps(actions or [])
            + ";const query="
            + json.dumps(query)
            + ";const pinRequest="
            + json.dumps(pin_request)
            + r""";
const before=JSON.stringify({rows,initial,actions,pinRequest});
function scientificCueGlyph(cue){return {circle:'●',square:'■',triangle:'▲',diamond:'◆',cross:'✚',ring:'○'}[cue]}
const catalog=scientificPickerCatalog(rows),first=scientificPickerInitialState(catalog,initial,pinRequest);
let state=first.state;const outcomes=[];
for(const action of actions){const previous=state,prior=JSON.stringify(state),result=scientificPickerAction(catalog,state,action);outcomes.push({...result,same:result.state===previous,priorUnchanged:prior===JSON.stringify(previous)});state=result.state;}
console.log(JSON.stringify({catalog,first,state,outcomes,matches:scientificPickerSearch(catalog,query).map(row=>row.id),html:renderScientificPicker(catalog,state,query),unchanged:before===JSON.stringify({rows,initial,actions,pinRequest})}));
"""
        ),
    )


class Markup(HTMLParser):
    def __init__(self, value: str) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.words: list[str] = []
        self.feed(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.words.append(data)


def test_real_normalized_catalog_uses_only_supplied_hierarchy_and_default_selection() -> (
    None
):
    rows = signals()
    before = deepcopy(rows)
    observed = observe(rows, ["pollen:whole"])
    assert observed["catalog"]["status"] == "available"
    hierarchy = {r["id"]: r for r in observed["catalog"]["hierarchy"]}
    assert hierarchy["pollen:whole"]["depth"] == 0
    assert hierarchy["pollen:group:cereals"]["depth"] == 1
    assert hierarchy["pollen:role:direct-crop"]["depth"] == 2
    assert hierarchy["pollen:subgroup:declared"]["depth"] == 2
    assert hierarchy["pollen:taxon:other"]["depth"] == 0
    assert observed["state"] == {
        "pinnedIds": ["pollen:whole"],
        "visibleIds": ["pollen:whole"],
    }
    assert observed["unchanged"] is True and rows == before
    markup = Markup(observed["html"])
    assert any(
        tag == "input" and attrs.get("type") == "search" and attrs.get("aria-label")
        for tag, attrs in markup.tags
    )
    assert any(
        tag == "ol" and attrs.get("aria-label") == "Pinned comparison signals"
        for tag, attrs in markup.tags
    )
    assert (
        "descendants" in observed["html"]
        and "scientific membership" in observed["html"]
    )


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("TRITICUM", ["pollen:taxon:triticum"]),
        ("whole:pollen", ["pollen:whole"]),
        ("Explicit source synonym", ["pollen:taxon:triticum"]),
        ("NOT-A-SEARCH-ALIAS", []),
        ("[not a regex]", []),
    ],
)
def test_search_uses_literal_supplied_text_only(
    query: str, expected: list[str]
) -> None:
    observed = observe(signals(), query=query)
    assert observed["matches"] == expected
    assert observed["state"]["visibleIds"] == []


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate",
        "unknown_parent",
        "self_cycle",
        "cycle",
        "status",
        "resolution",
        "color",
        "cue",
        "synonyms",
    ],
)
def test_ambiguous_hierarchy_or_unqualified_metadata_visibly_refuses(
    defect: str,
) -> None:
    rows = signals()
    if defect == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif defect == "unknown_parent":
        rows[0]["parent_signal_id"] = "foreign"
    elif defect == "self_cycle":
        rows[0]["parent_signal_id"] = rows[0]["signal_id"]
    elif defect == "cycle":
        rows[0]["parent_signal_id"] = rows[1]["signal_id"]
        rows[1]["parent_signal_id"] = rows[0]["signal_id"]
    else:
        rows[0][
            {
                "status": "status",
                "resolution": "resolution",
                "color": "color",
                "cue": "non_color_cue",
                "synonyms": "synonyms",
            }[defect]
        ] = {
            "status": "pending",
            "resolution": "ECO-alias",
            "color": "red;unsafe",
            "cue": "invented",
            "synonyms": "alias",
        }[defect]
    observed = observe(rows)
    assert observed["catalog"]["status"] == "refused"
    assert observed["first"]["state"] is None and observed["first"]["error"]
    assert "Scientific picker unavailable" in observed["html"]
    assert "data-scientific-action" not in observed["html"]
    assert observed["unchanged"] is True


def test_empty_catalog_retains_zero_accepted_content() -> None:
    observed = observe([])
    assert observed["catalog"]["status"] == "available"
    assert observed["state"] == {"pinnedIds": [], "visibleIds": []}
    assert "No accepted scientific signals were supplied" in observed["html"]
    assert not any(tag == "button" for tag, _ in Markup(observed["html"]).tags)


def test_pin_hide_show_reorder_solo_remove_preserve_exact_mixed_resolution_rows() -> (
    None
):
    rows = signals()
    actions = [
        {"type": "pin", "id": id_}
        for id_ in (
            "pollen:taxon:triticum",
            "pollen:role:direct-crop",
            "pollen:subgroup:declared",
        )
    ]
    actions += [
        {"type": "hide", "id": "pollen:taxon:triticum"},
        {"type": "show", "id": "pollen:taxon:triticum"},
        {"type": "earlier", "id": "pollen:role:direct-crop"},
        {"type": "solo", "id": "pollen:role:direct-crop"},
        {"type": "remove", "id": "pollen:taxon:triticum"},
    ]
    observed = observe(rows, ["pollen:whole"], actions)
    states = [outcome["state"] for outcome in observed["outcomes"]]
    assert (
        "pollen:taxon:triticum" in states[3]["pinnedIds"]
        and "pollen:taxon:triticum" not in states[3]["visibleIds"]
    )
    assert states[4]["visibleIds"][-1] == "pollen:taxon:triticum"
    assert states[5]["pinnedIds"][:2] == ["pollen:whole", "pollen:role:direct-crop"]
    assert states[5]["visibleIds"] == states[4]["visibleIds"]
    assert observed["state"] == {
        "pinnedIds": [
            "pollen:whole",
            "pollen:role:direct-crop",
            "pollen:subgroup:declared",
        ],
        "visibleIds": ["pollen:role:direct-crop"],
    }
    assert all(
        outcome["error"] is None and outcome["priorUnchanged"]
        for outcome in observed["outcomes"]
    )
    assert observed["catalog"]["rows"] == rows and observed["unchanged"] is True
    for row in rows:
        if row["signal_id"] in observed["state"]["pinnedIds"]:
            assert f'data-cue="{row["non_color_cue"]}"' in observed["html"]
            assert f'style="color:{row["color"]}"' in observed["html"]


def test_solo_parent_does_not_select_source_memberships_or_descendants() -> None:
    observed = observe(
        signals(),
        ["pollen:whole"],
        [
            {"type": "pin", "id": "pollen:group:cereals"},
            {"type": "solo", "id": "pollen:group:cereals"},
        ],
    )
    selected = observed["state"]["visibleIds"]
    script = (
        "const SCIENTIFIC_SIGNALS="
        + json.dumps(signals())
        + ";const activeScientificSignalIds=new Set("
        + json.dumps(selected)
        + ");"
        + template_block(
            "function featureMatchesScientificSelection", "function pointFeatureVisible"
        )
        + "console.log(JSON.stringify([['pollen:whole'],['pollen:group:cereals'],['pollen:taxon:triticum'],['pollen:taxon:triticum','pollen:group:cereals']].map(ids=>featureMatchesScientificSelection({scientific_selection_enabled:true},{scientific_signal_ids:ids}))));"
    )
    assert run_node_json(script) == [False, True, False, True]


def test_more_than_six_existing_visible_ids_remain_visible_and_explicitly_unpinned() -> (
    None
):
    rows = signals()
    rows.append({**rows[-1], "signal_id": "extra", "feature_key": "taxon:extra"})
    selected = [row["signal_id"] for row in rows]
    observed = observe(rows, selected, [{"type": "pin", "id": "extra"}])
    assert observed["state"]["visibleIds"] == selected
    assert observed["state"]["pinnedIds"] == selected[:6]
    assert observed["outcomes"][0]["same"] is True and observed["outcomes"][0]["error"]
    assert "7 selected for display; Visible but unpinned: 1" in observed["html"]


@pytest.mark.parametrize(
    "action",
    [
        {"type": "pin", "id": "foreign"},
        {"type": "pin", "id": "pollen:whole"},
        {"type": "hide", "id": "pollen:taxon:other"},
        {"type": "unknown", "id": "pollen:whole"},
        {"type": "earlier", "id": "pollen:whole"},
        {"type": "later", "id": "pollen:whole"},
    ],
)
def test_refused_actions_keep_the_exact_existing_state(action: dict[str, str]) -> None:
    observed = observe(signals(), ["pollen:whole"], [action])
    assert observed["outcomes"][0]["error"] and observed["outcomes"][0]["same"] is True
    assert observed["state"] == observed["first"]["state"]


@pytest.mark.parametrize(
    "initial", [["foreign"], ["pollen:whole", "pollen:whole"], "pollen:whole"]
)
def test_invalid_existing_selection_is_not_silently_replaced(initial: object) -> None:
    observed = observe(signals(), initial)
    assert observed["first"]["state"] is None and observed["first"]["error"]


def test_shared_pin_order_and_hidden_pins_do_not_replace_visible_selection() -> None:
    pins = ["pollen:taxon:other", "pollen:whole"]
    selected = ["pollen:whole", "pollen:group:cereals"]
    observed = observe(signals(), selected, pin_request=[json.dumps(pins)])
    assert observed["state"] == {"pinnedIds": pins, "visibleIds": selected}
    assert "Hidden" in observed["html"] and observed["unchanged"] is True


def test_explicit_empty_pin_request_preserves_all_visible_ids() -> None:
    selected = [row["signal_id"] for row in signals()]
    observed = observe(signals(), selected, pin_request=["[]"])
    assert observed["state"] == {"pinnedIds": [], "visibleIds": selected}
    assert observed["unchanged"] is True


@pytest.mark.parametrize(
    "pin_request",
    [
        None,
        "[]",
        [None],
        [""],
        ["null"],
        ["{}"],
        ['"pollen:whole"'],
        ["[1]"],
        ['["foreign"]'],
        ['["pollen:whole","pollen:whole"]'],
        ["[]", "[]"],
    ],
)
def test_unavailable_shared_pin_requests_never_seed_default_pins(
    pin_request: object,
) -> None:
    observed = observe(signals(), ["pollen:whole"], pin_request=pin_request)
    assert observed["state"] is None and observed["first"]["error"]
    assert "unavailable" in observed["html"] and observed["unchanged"] is True


def test_shared_request_cannot_pin_seven_valid_signals() -> None:
    rows = signals()
    rows.append({**rows[-1], "signal_id": "extra", "feature_key": "taxon:extra"})
    selected = [row["signal_id"] for row in rows]
    observed = observe(rows, selected, pin_request=[json.dumps(selected)])
    assert observed["state"] is None and observed["first"]["error"]


def test_query_and_native_labels_are_escaped_with_accessible_exact_actions() -> None:
    rows = signals()
    hostile = '<img src=x onerror="unsafe()">'
    rows[0]["label"] = hostile
    observed = observe(rows, [rows[0]["signal_id"]], query=hostile)
    markup = Markup(observed["html"])
    assert not any(tag == "img" for tag, _ in markup.tags)
    assert hostile in " ".join(markup.words)
    assert any(
        tag == "input" and attrs.get("value") == hostile for tag, attrs in markup.tags
    )
    assert all(
        attrs.get("type") == "button"
        and attrs.get("aria-label")
        and attrs.get("data-scientific-id")
        for tag, attrs in markup.tags
        if tag == "button"
    )


def test_large_hierarchy_has_complete_search_data_and_bounded_markup() -> None:
    base = signals()[0]
    rows = [
        {
            **base,
            "signal_id": f"id-{index:03}",
            "feature_key": f"taxon:{index}",
            "parent_signal_id": None if index == 0 else f"id-{index - 1:03}",
        }
        for index in range(40)
    ]
    observed = observe(rows)
    assert len(observed["catalog"]["hierarchy"]) == len(observed["matches"]) == 40
    assert observed["catalog"]["hierarchy"][-1]["depth"] == 39
    assert sum(tag == "button" for tag, _ in Markup(observed["html"]).tags) == 25
    assert "first 25 of 40 matches" in observed["html"]
    assert observe(rows, query="id-039")["matches"] == ["id-039"]
