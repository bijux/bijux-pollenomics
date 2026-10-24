"""Exact published relation links reuse the async drawer without substituting evidence."""

from __future__ import annotations

import json
from typing import Any

import pytest

from ...support import template_block
from .focus_support import browser
from .focus_support import published as published


def test_producer_projection_static_build_roundtrip_reuses_actual_async_drawer(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
await openEdgeDetail(supplied.edge,visiblePointEntries[0],true);
const before=savedHash,params=new URLSearchParams(before.slice(1));
window.location.hash=before;const parsed=parseHashState();
setFocusState(null);pendingEdgeFocus=parsed.edgeFocus;await renderMapState();
const held=savedHash;
console.log(JSON.stringify({before,held,after:savedHash,parsed,focus:focusState,tab:activeFocusTab,loads,unchanged:original===JSON.stringify(supplied)}));
""",
    )
    assert observed["unchanged"] is True
    assert observed["before"] == observed["after"]
    assert "countries=Norway" in observed["before"]
    assert "cross_border=only" in observed["before"]
    assert (
        observed["parsed"]["edgeFocus"]["atlasBuildId"]
        == published["manifest"]["build_id"]
    )
    assert observed["focus"]["edgeId"] == published["edge"]["edge_id"]
    assert observed["focus"]["scenarioId"] == published["edge"]["scenario_id"]
    assert observed["focus"]["detailTabs"]["relation"]["retained"] == "original"
    assert observed["parsed"]["edgeFocus"]["tab"] == "relation"
    assert observed["tab"] == "relation" and observed["loads"] == 2


@pytest.mark.parametrize(
    "defect",
    [
        "missing_edge",
        "missing_scenario",
        "missing_build",
        "duplicate_edge",
        "duplicate_scenario",
        "duplicate_build",
        "duplicate_tab",
        "mixed",
        "unknown_tab",
        "unknown_edge",
        "stale_build",
        "wrong_scenario",
        "duplicate_record",
        "legacy",
        "filtered_signal",
        "filtered_country",
        "unloaded_endpoint",
        "duplicate_endpoint",
    ],
)
def test_unavailable_shared_relation_never_substitutes_or_loads_details(
    published: dict[str, Any],
    defect: str,
) -> None:
    observed = browser(
        published,
        "const defect="
        + json.dumps(defect)
        + r""";
const p=new URLSearchParams({focus_edge:supplied.edge.edge_id,focus_scenario:supplied.edge.scenario_id,focus_build:STATIC_ATLAS_BOOTSTRAP.build_id,focus_tab:'relation'});
if(defect.startsWith('missing_'))p.delete('focus_'+defect.slice(8));
if(defect.startsWith('duplicate_')&&!['duplicate_record','duplicate_endpoint'].includes(defect))p.append('focus_'+defect.slice(10),p.get('focus_'+defect.slice(10)));
if(defect==='mixed')p.set('focus_record','source:record');
if(defect==='unknown_tab')p.set('focus_tab','<script>unsafe</script>');
if(defect==='unknown_edge')p.set('focus_edge','<img src=x>');
if(defect==='stale_build')p.set('focus_build','atlas-'+'0'.repeat(64));
if(defect==='wrong_scenario')p.set('focus_scenario','other');
if(defect==='duplicate_record')GOVERNED_EDGE_RECORDS.push(supplied.edge);
if(defect==='legacy')GOVERNED_EDGE_RECORDS=[{...supplied.edge}];
if(defect==='legacy')delete GOVERNED_EDGE_RECORDS[0].candidate_status;
if(defect==='filtered_signal')activeScientificSignalIds.clear();
if(defect==='filtered_country')activeCountries.clear();
if(defect==='unloaded_endpoint')visiblePointEntries.pop();
if(defect==='duplicate_endpoint')visiblePointEntries.push(visiblePointEntries[0]);
const parsed=edgeFocusFromHash(p,DETAIL_TAB_DEFINITIONS.map(row=>row[0]));
const restored=await restoreEdgeFocus(parsed);
console.log(JSON.stringify({restored,focus:focusState,loads,message:topbarStatePill.textContent,role:topbarStatePill.role}));
""",
    )
    assert observed["restored"] is False
    assert observed["focus"] is None and observed["loads"] == 0
    assert (
        observed["message"]
        == "Shared relation is unavailable under this published build, scenario and current filters."
    )
    assert observed["role"] == "status"


@pytest.mark.parametrize(
    "change",
    ["close", "reset", "filter", "new_focus", "new_edge", "endpoint", "replacement"],
)
def test_late_async_details_cannot_revive_superseded_relation_focus(
    published: dict[str, Any],
    change: str,
) -> None:
    observed = browser(
        published,
        "const change="
        + json.dumps(change)
        + r""";
delayed=true;const pending=restoreEdgeFocus(request());
if(change==='close')setFocusState(null);
if(change==='reset')await restoreDefaults();
if(change==='filter'){activeScientificSignalIds.clear();await renderMapState();}
if(change==='new_focus')setFocusState({kind:'point',layerKey:'points',featureKey:'record:other',recordId:'other'});
let newer;
if(change==='new_edge'){newer=openEdgeDetail(supplied.edge,visiblePointEntries[0]);}
if(change==='endpoint')visiblePointEntries.pop();
if(change==='replacement')GOVERNED_EDGE_RECORDS=[{...supplied.edge}];
releases[0]();const restored=await pending;
if(newer){releases[1]();await newer;}
console.log(JSON.stringify({restored,kind:focusState?.kind||null,record:focusState?.recordId||null,loads}));
""",
    )
    assert observed["restored"] is False and observed["loads"] == (
        2 if change == "new_edge" else 1
    )
    assert observed["kind"] == (
        "point" if change == "new_focus" else "edge" if change == "new_edge" else None
    )
    assert observed["record"] == ("other" if change == "new_focus" else None)


def test_point_links_exports_and_clear_remain_distinct_from_relation_links(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
setFocusState({kind:'point',layerKey:'points',featureKey:'node:source',recordId:'source:record'});
activeFocusTab='provenance';syncHashState();
const point=new URLSearchParams(savedHash.slice(1)),restored=sourceRecordFocusFromHash(point,['overview','provenance']);
const noEdge=edgeFocusFromHash(point,['overview','provenance']);
await restoreEdgeFocus(request());const edgeExport=sourcePollenExportAvailable(focusState);
setFocusState(null);const cleared=new URLSearchParams(savedHash.slice(1));
console.log(JSON.stringify({restored,noEdge,edgeExport,cleared:[...cleared.keys()].filter(key=>key.startsWith('focus_'))}));
""",
    )
    assert observed == {
        "restored": {
            "kind": "point",
            "layerKey": "points",
            "featureKey": "node:source",
            "recordId": "source:record",
            "tab": "provenance",
        },
        "noEdge": None,
        "edgeExport": False,
        "cleared": [],
    }


@pytest.mark.parametrize(
    "identity", ["no_build", "missing_edge", "missing_scenario", "legacy"]
)
def test_relation_without_complete_published_identity_has_no_shareable_link(
    published: dict[str, Any],
    identity: str,
) -> None:
    observed = browser(
        published,
        "const identity="
        + json.dumps(identity)
        + r""";
if(identity==='no_build')delete STATIC_ATLAS_BOOTSTRAP.build_id;
if(identity==='missing_scenario')delete supplied.edge.scenario_id;
if(identity==='missing_edge')delete supplied.edge.edge_id;
if(identity==='legacy')delete supplied.edge.candidate_status;
await openEdgeDetail(supplied.edge,visiblePointEntries[0]);
console.log(JSON.stringify({shareable:focusState.edgeShareable,keys:[...hash().keys()]}));
""",
    )
    assert observed == {"shareable": False, "keys": []}


def test_superseded_initial_render_waits_for_current_loaded_generation(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
pendingEdgeFocus=request();delaySelection=true;
const first=renderMapState(),second=renderMapState();
selections[0]();await first;const premature=loads;
selections[1]();await second;
console.log(JSON.stringify({premature,loads,kind:focusState?.kind,tab:activeFocusTab,pending:pendingEdgeFocus,unlocked:edgeFocusLoadState.restoring===null}));
""",
    )
    assert observed == {
        "premature": 0,
        "loads": 1,
        "kind": "edge",
        "tab": "relation",
        "pending": None,
        "unlocked": True,
    }


def test_reset_relation_guard_preserves_existing_point_focus(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
setFocusState({kind:'point',layerKey:'points',featureKey:'node:source',recordId:'source:record'});
await restoreDefaults();const point=focusState;
await restoreEdgeFocus(request());await restoreDefaults();
console.log(JSON.stringify({point:point.recordId,edgeCleared:focusState===null,hash:savedHash}));
""",
    )
    assert observed["point"] == "source:record" and observed["edgeCleared"] is True
    assert "focus_" not in observed["hash"]


@pytest.mark.parametrize("old_finishes_first", [True, False])
def test_current_render_owns_overlapping_restore_and_old_finally_cannot_clear_it(
    published: dict[str, Any],
    old_finishes_first: bool,
) -> None:
    observed = browser(
        published,
        "const oldFirst="
        + json.dumps(old_finishes_first)
        + r""";
pendingEdgeFocus=request();delayed=true;
const first=renderMapState();await Promise.resolve();await Promise.resolve();
const second=renderMapState();await Promise.resolve();await Promise.resolve();
if(oldFirst){releases[0]();await first;}else{releases[1]();await second;}
const intermediate={pending:pendingEdgeFocus!==null,kind:focusState?.kind||null};
if(oldFirst){releases[1]();await second;}else{releases[0]();await first;}
console.log(JSON.stringify({loads,intermediate,kind:focusState?.kind,tab:activeFocusTab,pending:pendingEdgeFocus,unlocked:edgeFocusLoadState.restoring===null}));
""",
    )
    assert observed["loads"] == 2
    assert observed["intermediate"] == (
        {"pending": True, "kind": None}
        if old_finishes_first
        else {"pending": False, "kind": "edge"}
    )
    assert observed["kind"] == "edge" and observed["tab"] == "relation"
    assert observed["pending"] is None and observed["unlocked"] is True


@pytest.mark.parametrize("route", ["copy", "render"])
@pytest.mark.parametrize("loss", ["country", "endpoint"])
def test_filtered_relation_is_cleared_and_cannot_copy_an_unrestorable_link(
    published: dict[str, Any],
    route: str,
    loss: str,
) -> None:
    observed = browser(
        published,
        template_block(
            "focusCopyLinkButton.addEventListener", "focusExportButton.addEventListener"
        )
        + "const route="
        + json.dumps(route)
        + ";const loss="
        + json.dumps(loss)
        + r""";
await openEdgeDetail(supplied.edge,visiblePointEntries[0]);
let busyStatus=null;
if(route==='copy'&&loss==='country'){
 delaySelection=true;const loading=renderMapState();await copyAction();busyStatus=focusExportStatus.textContent;
 delaySelection=false;selections[0]();await loading;
}
if(loss==='country')activeCountries.clear();else visiblePointEntries.pop();
if(route==='copy')await copyAction();else{
 renderLoadedMapState=()=>{renderActualFocusCard();syncHashState()};await renderMapState();
}
console.log(JSON.stringify({focus:focusState,copies,message:topbarStatePill.textContent,copyDisabled:focusCopyLinkButton.disabled,exportDisabled:focusExportButton.disabled,busyStatus,hash:savedHash}));
""",
    )
    assert observed["focus"] is None and observed["copies"] == 0
    if route == "copy" and loss == "country":
        assert (
            observed["busyStatus"]
            == "Relation link unavailable while selected evidence is loading."
        )
    assert "focus_" not in observed["hash"]
    if route == "render":
        assert observed["copyDisabled"] is observed["exportDisabled"] is True
    else:
        assert (
            observed["message"]
            == "Relation link unavailable under the current filters."
        )


def test_old_detail_completion_preserves_pending_while_new_generation_loads(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
pendingEdgeFocus=request();delayed=true;
const first=renderMapState();await Promise.resolve();await Promise.resolve();
delaySelection=true;const second=renderMapState();
releases[0]();await first;const retained=pendingEdgeFocus!==null;
selections[0]();await Promise.resolve();await Promise.resolve();
releases[1]();await second;
console.log(JSON.stringify({retained,loads,kind:focusState?.kind,tab:activeFocusTab,pending:pendingEdgeFocus}));
""",
    )
    assert observed == {
        "retained": True,
        "loads": 2,
        "kind": "edge",
        "tab": "relation",
        "pending": None,
    }


def test_manual_edge_callback_consumes_shared_request_before_intervening_render(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        r"""
GOVERNED_EDGE_RECORDS.push(supplied.manual);activeCountries.add('Sweden');crossBorderOnly=false;
renderEdgeLayers();pendingEdgeFocus=request();delayed=true;
const shared=restoreEdgeFocus(pendingEdgeFocus),manual=callbacks[1].click();
const consumed=pendingEdgeFocus===null;await renderMapState();
releases[0]();releases[1]();await shared;await manual;
console.log(JSON.stringify({consumed,loads,kind:focusState?.kind||null,pending:pendingEdgeFocus,unlocked:edgeFocusLoadState.restoring===null}));
""",
    )
    assert observed == {
        "consumed": True,
        "loads": 2,
        "kind": None,
        "pending": None,
        "unlocked": True,
    }
